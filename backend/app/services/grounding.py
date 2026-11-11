"""Sentence-level grounding of generated answers.

Every factual sentence in an answer must be *entailed* by text in a source it
cites, judged by a small CPU natural-language-inference model. This replaces
embedding similarity, which measures topical closeness rather than support
("Zoom lacks security" is close to "Zoom bombing was reported" but not
supported by it).

For each sentence:
  - supported by a cited source           -> kept unchanged
  - supported only by an uncited source   -> kept, citation corrected
  - supported by no source                -> removed

Sentences are edited in place, so markdown (lists, headings, code) survives.
Short connective lines ("Here is what I found:") and headings are not claims
and are left alone.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from functools import lru_cache
from itertools import pairwise
from math import sqrt

from app.core.config import settings
from app.services.embedding import generate_embeddings

logger = logging.getLogger(__name__)

SOURCE_PATTERN = re.compile(r"\[(?:Source\s+)?(\d+)\]", re.IGNORECASE)
# A sentence ends at . ! or ? followed by whitespace; citations directly after
# the punctuation ("claim. [Source 1] Next") stay with the preceding sentence.
SENTENCE_BOUNDARY = re.compile(r"(?<=[.!?])((?:\s*\[(?:Source\s+)?\d+\])*)\s+")
LINE_PREFIX = re.compile(r"^(\s*(?:#{1,6}\s+|[-*•+]\s+|\d+[.)]\s+|>\s*)?)")
MARKDOWN_NOISE = re.compile(r"[*_`#>]")

PARTIAL_NOTE = "_Some statements were removed because they could not be verified in your documents._"

# Evidence candidates per sentence that are scored by the entailment model.
CANDIDATES_PER_SENTENCE = 6
# Share of a claim's content words that must appear in a source for the
# lexical fallback (calibrated on the evaluation set; see calibrate_grounding.py).
LEXICAL_MIN_COVERAGE = 0.9
STOPWORDS = frozenset(["a", "an", "the", "and", "or", "of", "to", "in", "on", "for", "with", "by", "as", "at", "from", "is", "are", "was", "were", "be", "been", "it", "its", "this", "that", "these", "those", "which", "who", "whom", "what", "when", "where", "why", "how", "do", "does", "did", "not", "no", "can", "may", "must", "should", "will", "would", "also", "such", "than", "then", "there", "their", "they", "them", "he", "she", "his", "her", "we", "our", "you", "your", "i", "about", "into", "over", "under", "up", "out", "so", "if", "but", "just", "only", "very", "more", "most", "according", "mentions", "states", "describes", "report", "document", "documents", "via", "specifically", "including", "include", "includes", "using", "use", "uses", "used", "offers", "offer", "provides", "provide", "like", "e", "g"])


@dataclass
class Sentence:
    start: int
    end: int
    text: str
    citations: list[int]
    claim: str
    is_claim: bool
    is_heading: bool = False


@dataclass
class SentenceVerdict:
    claim: str
    cited: list[int]
    supported_by: int | None
    entailment: float
    action: str  # kept | added | corrected | removed | not_a_claim
    basis: str = ""  # entailment | lexical | none


@dataclass
class GroundingResult:
    answer: str
    status: str  # verified | partial | unsupported
    cited_ids: list[int]
    verdicts: list[SentenceVerdict] = field(default_factory=list)

    @property
    def removed(self) -> int:
        return sum(1 for verdict in self.verdicts if verdict.action == "removed")

    @property
    def corrected(self) -> int:
        return sum(1 for verdict in self.verdicts if verdict.action == "corrected")


# ---------------------------------------------------------------------------
# Answer and evidence segmentation
# ---------------------------------------------------------------------------


def _clean_claim(text: str) -> str:
    return re.sub(r"\s+", " ", MARKDOWN_NOISE.sub("", SOURCE_PATTERN.sub("", text))).strip()


def split_sentences(answer: str) -> list[Sentence]:
    """Split an answer into sentences with character spans into the original text."""
    sentences: list[Sentence] = []
    offset = 0
    for line in answer.splitlines(keepends=True):
        body = line.rstrip("\r\n")
        prefix = LINE_PREFIX.match(body).group(1)
        is_heading = prefix.lstrip().startswith("#")
        cursor = len(prefix)
        pieces: list[tuple[int, int]] = []
        for boundary in SENTENCE_BOUNDARY.finditer(body, cursor):
            end = boundary.start() + len(boundary.group(1))
            pieces.append((cursor, end))
            cursor = boundary.end()
        pieces.append((cursor, len(body.rstrip())))

        for start, end in pieces:
            text = body[start:end]
            if not text.strip():
                continue
            claim = _clean_claim(text)
            citations = [int(value) for value in SOURCE_PATTERN.findall(text)]
            words = re.findall(r"[A-Za-z0-9]+", claim)
            is_claim = (
                not is_heading
                and bool(words)
                and not claim.endswith(":")
                and (len(words) >= 3 or bool(citations))
            )
            sentences.append(
                Sentence(offset + start, offset + end, text, citations, claim, is_claim, is_heading)
            )
        offset += len(line)
    return sentences


def evidence_units(content: str) -> list[str]:
    """Sentences, adjacent sentence pairs, and table rows (with their header)."""
    units: list[str] = []
    table_header: str | None = None
    prose: list[str] = []

    def flush_prose() -> None:
        text = " ".join(prose).strip()
        prose.clear()
        if not text:
            return
        parts = [part.strip() for part in re.split(r"(?<=[.!?])\s+", text) if part.strip()]
        units.extend(parts)
        units.extend(f"{first} {second}" for first, second in pairwise(parts))

    for raw_line in content.splitlines():
        line = raw_line.strip()
        if line.startswith("|") and line.endswith("|"):
            flush_prose()
            cells = " ".join(cell.strip() for cell in line.strip("|").split("|"))
            if table_header is None:
                table_header = cells
                units.append(cells)
            else:
                units.append(f"{table_header}. {cells}")
            continue
        table_header = None
        if not line:
            flush_prose()
        else:
            prose.append(line)
    flush_prose()
    return list(dict.fromkeys(unit for unit in units if len(unit) > 3))


# ---------------------------------------------------------------------------
# Scoring
# ---------------------------------------------------------------------------


@lru_cache(maxsize=1)
def _load_entailment_model(model_name: str):
    from sentence_transformers import CrossEncoder

    model = CrossEncoder(model_name, device="cpu")
    labels = {str(label).lower(): int(index) for index, label in model.config.id2label.items()}
    if "entailment" not in labels:
        raise ValueError(f"Grounding model {model_name} has no 'entailment' label: {labels}")
    return model, labels["entailment"]


def entailment_scores(pairs: list[tuple[str, str]]) -> list[float]:
    """Probability that each (premise, hypothesis) premise entails the hypothesis."""
    if not pairs:
        return []
    model, entailment_index = _load_entailment_model(settings.grounding_model)
    probabilities = model.predict(pairs, apply_softmax=True, batch_size=16, show_progress_bar=False)
    return [float(row[entailment_index]) for row in probabilities]


def _cosine(vector_a, vector_b) -> float:
    dot = sum(a * b for a, b in zip(vector_a, vector_b, strict=False))
    norm = sqrt(sum(a * a for a in vector_a)) * sqrt(sum(b * b for b in vector_b))
    return dot / norm if norm else 0.0


def _hypothesis(claim: str, question: str | None) -> str:
    # Fragments such as "8.99 USD per month" carry no subject; give the model
    # the question so it can judge them as an answer rather than in isolation.
    if question and len(claim.split()) < 6:
        return f"{question.strip()} {claim}"
    return claim


def _document_label(filename: str) -> str:
    return re.sub(r"[_-]+", " ", re.sub(r"\.[A-Za-z0-9]+$", "", filename or "")).strip()


def _context_prefix(source: dict, question: str | None) -> str:
    """Context an answer may legitimately restate (document, section, question).

    Entailment models treat any restated detail as unsupported ("Northwind
    Analytics employees" vs a sentence that only says "employees"); calibration
    showed this prefix roughly doubles correct answers kept.
    """
    parts = [f"Document: {_document_label(source.get('filename', ''))}."]
    if source.get("section_heading"):
        parts.append(f"Section: {source['section_heading']}.")
    if question:
        parts.append(f"Question: {question.strip()}")
    return " ".join(parts) + "\n"


def _stem(token: str) -> str:
    """Crude suffix stripping so "storing"/"stores"/"stored" match "store"."""
    if token[0].isdigit() or len(token) <= 4:
        return token
    for suffix in ("ing", "ed", "es", "s"):
        if token.endswith(suffix) and len(token) - len(suffix) >= 4:
            return token[: -len(suffix)]
    return token


def _tokens(text: str) -> list[str]:
    return [_stem(token) for token in re.findall(r"[a-z0-9]+(?:\.[0-9]+)?", text.lower())]


def _stem(token: str) -> str:
    """Crude suffix stripping so "enables"/"enable"/"enabled" match. Numbers are untouched."""
    if token.isdigit() or len(token) <= 4:
        return token
    for suffix in ("ing", "ed", "es", "s"):
        if token.endswith(suffix) and len(token) - len(suffix) >= 3:
            return token[: -len(suffix)].rstrip("e")
    return token.rstrip("e")


def lexically_supported(claim: str, question: str | None, content: str) -> bool:
    """Every number and nearly every content word of the claim appears in the source.

    Catches faithful paraphrases and table lookups the small entailment model
    misses; a changed number never passes because it is absent from the source.
    """
    question_tokens = set(_tokens(question or ""))
    words = [token for token in _tokens(claim) if token not in STOPWORDS]
    numbers = [token for token in words if re.fullmatch(r"\d+(?:\.\d+)?", token)]
    content_words = [token for token in words if token not in question_tokens and not token.isdigit()]
    source_tokens = set(_tokens(content))
    source_stems = {_stem(token) for token in source_tokens}
    if numbers and not all(number in source_tokens for number in numbers):
        return False
    if not content_words:
        # The claim only restates question terms ("No, the X1 does not support
        # Matter"); those terms must then appear in the source themselves.
        content_words = [token for token in words if not token.isdigit()]
        if not content_words:
            return bool(numbers)
    coverage = sum(_stem(token) in source_stems for token in content_words) / len(content_words)
    return coverage >= LEXICAL_MIN_COVERAGE


def _best_support(
    claim: Sentence,
    claim_embedding: list[float],
    question: str | None,
    source_ids: list[int],
    evidence: list[tuple[int, str, list[float]]],
    sources: dict[int, dict],
    threshold: float,
    combine: bool = False,
) -> tuple[int | None, float, str]:
    """Best supporting source among source_ids: (source_id, entailment, basis)."""
    if not source_ids:
        return None, 0.0, "none"
    hypothesis = _hypothesis(claim.claim, question)
    candidates = [item for item in evidence if item[0] in source_ids]
    ranked = sorted(candidates, key=lambda item: _cosine(claim_embedding, item[2]), reverse=True)
    pairs: list[tuple[int, str]] = []
    for source_id, unit, _embedding in ranked[:CANDIDATES_PER_SENTENCE]:
        pairs.append((source_id, unit))
        pairs.append((source_id, _context_prefix(sources[source_id], question) + unit))
    for source_id in source_ids:
        pairs.append((source_id, _context_prefix(sources[source_id], question) + sources[source_id]["_content"]))

    scores = entailment_scores([(premise, hypothesis) for _source_id, premise in pairs])
    best: dict[int, float] = {}
    for (source_id, _premise), score in zip(pairs, scores, strict=True):
        best[source_id] = max(best.get(source_id, 0.0), score)
    top_id = max(best, key=best.get) if best else source_ids[0]
    top_score = best.get(top_id, 0.0)
    if top_score >= threshold:
        return top_id, top_score, "entailment"
    for source_id in source_ids:
        if lexically_supported(claim.claim, question, sources[source_id]["_content"]):
            return source_id, best.get(source_id, 0.0), "lexical"
    # A sentence citing several sources may combine facts from them; check the
    # cited sources together (only for its own citations, never all sources).
    if combine and len(source_ids) > 1:
        combined = "\n".join(sources[source_id]["_content"] for source_id in source_ids)
        if lexically_supported(claim.claim, question, combined):
            return top_id, top_score, "lexical"
    return top_id, top_score, "none"


# ---------------------------------------------------------------------------
# Answer rewriting
# ---------------------------------------------------------------------------


def _with_citation(text: str, source_id: int) -> str:
    """Replace a sentence's citations with one citation, before final punctuation."""
    bare = SOURCE_PATTERN.sub("", text).rstrip()
    bare = re.sub(r"\s+([.!?,;:])", r"\1", bare)
    match = re.search(r"([.!?]+)$", bare)
    if match:
        return f"{bare[: match.start()].rstrip()} [Source {source_id}]{match.group(1)}"
    return f"{bare} [Source {source_id}]"


def _tidy(text: str) -> str:
    lines = []
    for line in text.splitlines():
        stripped = line.rstrip()
        # Drop list items or quote lines emptied by removed sentences.
        if re.fullmatch(r"\s*(?:[-*•+]|\d+[.)]|>)\s*", stripped):
            continue
        lines.append(re.sub(r"(?<=\S) {2,}", " ", stripped))
    tidied = "\n".join(lines)
    return re.sub(r"\n{3,}", "\n\n", tidied).strip()


def ground_answer(
    answer: str,
    sources: list[dict],
    question: str | None = None,
    min_entailment: float | None = None,
) -> GroundingResult:
    """Keep only answer sentences that a source entails; fix or drop the rest."""
    threshold = settings.grounding_min_entailment if min_entailment is None else min_entailment
    sentences = split_sentences(answer or "")
    claims = [sentence for sentence in sentences if sentence.is_claim]
    sources_by_id = {
        int(source["id"]): {**source, "_content": source.get("_content") or ""}
        for source in sources
        if source.get("id") is not None
    }
    contents = {source_id: source["_content"] for source_id, source in sources_by_id.items()}
    if not claims or not contents:
        return GroundingResult(answer="", status="unsupported", cited_ids=[])

    units = [
        (source_id, unit)
        for source_id, content in contents.items()
        for unit in evidence_units(content)
    ]
    if not units:
        return GroundingResult(answer="", status="unsupported", cited_ids=[])

    embeddings = generate_embeddings([claim.claim for claim in claims] + [unit for _, unit in units])
    claim_embeddings = embeddings[: len(claims)]
    evidence = [
        (source_id, unit, embedding)
        for (source_id, unit), embedding in zip(units, embeddings[len(claims) :], strict=True)
    ]

    replacements: dict[int, str] = {}
    verdicts: list[SentenceVerdict] = []
    cited_ids: set[int] = set()

    for sentence, claim_embedding in zip(claims, claim_embeddings, strict=True):
        cited = [source_id for source_id in dict.fromkeys(sentence.citations) if source_id in sources_by_id]
        support_id, score, basis = _best_support(
            sentence, claim_embedding, question, cited, evidence, sources_by_id, threshold, combine=True
        )
        action = "kept"
        if basis == "none":
            # The cited source does not support it; another retrieved source may.
            others = [source_id for source_id in sources_by_id if source_id not in cited]
            other_id, other_score, other_basis = _best_support(
                sentence, claim_embedding, question, others, evidence, sources_by_id, threshold
            )
            if other_basis != "none":
                support_id, score, basis = other_id, other_score, other_basis
            action = "corrected" if basis != "none" else "removed"

        if action == "removed":
            replacements[sentence.start] = ""
        else:
            cited_ids.add(int(support_id))
            if action == "corrected" or support_id not in cited or not cited:
                replacements[sentence.start] = _with_citation(sentence.text, int(support_id))
                action = "corrected" if cited else "added"
            else:
                # The sentence keeps all its citations; expose every cited source.
                cited_ids.update(cited)
        verdicts.append(SentenceVerdict(sentence.claim, cited, support_id, round(score, 4), action, basis))

    for sentence in sentences:
        if not sentence.is_claim:
            verdicts.append(SentenceVerdict(sentence.claim, sentence.citations, None, 0.0, "not_a_claim"))

    kept_claims = sum(1 for verdict in verdicts if verdict.action in {"kept", "added", "corrected"})
    if not kept_claims:
        return GroundingResult(answer="", status="unsupported", cited_ids=[], verdicts=verdicts)

    pieces: list[str] = []
    cursor = 0
    for sentence in sentences:
        if sentence.start in replacements:
            pieces.append(answer[cursor : sentence.start])
            pieces.append(replacements[sentence.start])
            cursor = sentence.end
    pieces.append(answer[cursor:])
    grounded = _tidy("".join(pieces))

    removed = any(verdict.action == "removed" for verdict in verdicts)
    if removed:
        grounded = f"{grounded}\n\n{PARTIAL_NOTE}"
    logger.info(
        "Grounding: %s claims kept, %s corrected, %s removed",
        kept_claims,
        sum(1 for verdict in verdicts if verdict.action == "corrected"),
        sum(1 for verdict in verdicts if verdict.action == "removed"),
    )
    return GroundingResult(
        answer=grounded,
        status="partial" if removed else "verified",
        cited_ids=sorted(cited_ids),
        verdicts=verdicts,
    )
