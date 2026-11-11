"""Calibrate sentence-level grounding on saved evaluation answers.

Replays the model drafts stored in an evaluation result file. No LLM is
called: answers and retrieved chunks are reused and only the CPU entailment
and embedding models run.

For every answer sentence it scores support under several premise variants,
and for a corrupted copy of each sentence (numbers changed) it measures how
often a wrong statement would still be accepted:

    python evaluation/calibrate_grounding.py evaluation_runs/<run>.json

Variants:
  sentence          best single source sentence / sentence pair
  sentence+context  the same, prefixed with document name, section and question
  chunk+context     the whole retrieved chunk, prefixed the same way
  best              the highest of the above
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

import torch
from sqlalchemy import select

from app.db.session import SessionLocal
from app.evaluation.corpus import EVALUATION_USER_EMAIL
from app.evaluation.dataset import load_dataset
from app.evaluation.metrics import matched_facts
from app.models.document import Document
from app.models.document_chunk import DocumentChunk
from app.models.user import User
from app.services import grounding
from app.services.embedding import generate_embeddings
from app.services.rag import (
    build_context_and_sources,
    is_model_refusal,
    verify_citations,
)

THRESHOLDS = (0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9)
VARIANTS = ("sentence", "sentence+context", "chunk+context", "best")
EVALUATION_DIR = Path(__file__).resolve().parent
TOP_UNITS = 6


def document_label(filename: str) -> str:
    return re.sub(r"[_-]+", " ", Path(filename).stem).strip()


def context_prefix(source: dict, question: str) -> str:
    parts = [f"Document: {document_label(source.get('filename', ''))}."]
    if source.get("section_heading"):
        parts.append(f"Section: {source['section_heading']}.")
    parts.append(f"Question: {question}")
    return " ".join(parts) + "\n"


def corrupt(claim: str) -> str | None:
    """Change the first number so the statement becomes false."""
    match = re.search(r"\d+(?:\.\d+)?", claim)
    if not match:
        return None
    value = match.group(0)
    wrong = str(int(float(value)) + 7) if "." not in value else f"{float(value) + 7:.2f}"
    return claim[: match.start()] + wrong + claim[match.end() :]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("results")
    parser.add_argument("--threads", type=int, default=2)
    args = parser.parse_args()
    torch.set_num_threads(args.threads)

    run = json.loads(Path(args.results).read_text(encoding="utf-8"))
    cases = {case.id: case for case in load_dataset(EVALUATION_DIR / "dataset.json").cases}

    db = SessionLocal()
    try:
        user = db.scalar(select(User).where(User.email == EVALUATION_USER_EMAIL))
        chunks = {
            (document.filename, chunk.chunk_index): (chunk, document)
            for chunk, document in db.execute(
                select(DocumentChunk, Document)
                .join(Document, Document.id == DocumentChunk.document_id)
                .where(Document.user_id == user.id)
            ).all()
        }
        replays = []
        for result in run["results"]:
            draft = result.get("draft_answer") or ""
            if not draft or is_model_refusal(draft):
                continue
            retrieved = [
                (*chunks[(item["filename"], item["chunk_index"])], 0.0)
                for item in result["retrieved"]
                if (item["filename"], item["chunk_index"]) in chunks
            ]
            _context, sources = build_context_and_sources(retrieved, max_context_chars=30000)
            answer, _cited = verify_citations(draft, sources)
            replays.append((result, cases.get(result["case_id"]), answer, sources))
    finally:
        db.close()

    # ---- Score every claim (and a corrupted copy) under each variant --------
    def claim_scores(claim: str, question: str, sources: list[dict]) -> dict[str, float]:
        hypothesis = grounding._hypothesis(claim, question)
        claim_embedding = generate_embeddings([claim])[0]
        pairs: list[tuple[str, str, str]] = []  # (variant, premise, hypothesis)
        for source in sources:
            units = grounding.evidence_units(source.get("_content") or "")
            if units:
                unit_embeddings = generate_embeddings(units)
                ranked = sorted(
                    zip(units, unit_embeddings, strict=True),
                    key=lambda item: grounding._cosine(claim_embedding, item[1]),
                    reverse=True,
                )[:TOP_UNITS]
                prefix = context_prefix(source, question)
                for unit, _embedding in ranked:
                    pairs.append(("sentence", unit, hypothesis))
                    pairs.append(("sentence+context", prefix + unit, hypothesis))
            pairs.append(("chunk+context", context_prefix(source, question) + (source.get("_content") or ""), hypothesis))
        scores = grounding.entailment_scores([(premise, hyp) for _v, premise, hyp in pairs]) if pairs else []
        best = {variant: 0.0 for variant in VARIANTS}
        for (variant, _premise, _hyp), score in zip(pairs, scores, strict=True):
            best[variant] = max(best[variant], score)
        best["best"] = max(best[variant] for variant in VARIANTS[:-1])
        return best

    records = []
    for index, (result, case, answer, sources) in enumerate(replays, start=1):
        claims = [sentence for sentence in grounding.split_sentences(answer) if sentence.is_claim]
        claim_records = []
        for sentence in claims:
            scores = claim_scores(sentence.claim, result["question"], sources)
            wrong = corrupt(sentence.claim)
            wrong_scores = claim_scores(wrong, result["question"], sources) if wrong else None
            claim_records.append({"claim": sentence.claim, "scores": scores, "corrupted": wrong_scores})
        records.append({"case_id": result["case_id"], "case": case, "answer": answer, "claims": claim_records})
        print(f"  scored {index}/{len(replays)} {result['case_id']}", flush=True)

    # ---- Sweep thresholds -----------------------------------------------------
    before = sum(
        bool(r["case"] and r["case"].required_facts and all(matched_facts(r["answer"], r["case"].required_facts)))
        for r in records
    )
    corrupted_total = sum(1 for r in records for c in r["claims"] if c["corrupted"])
    print()
    print(f"{len(records)} answers, {sum(len(r['claims']) for r in records)} claims; "
          f"{before} answers have all required facts before grounding; {corrupted_total} corrupted claims")
    print(f"{'variant':<17} {'thr':>4} {'answers kept whole':>18} {'rejected':>8} {'facts ok':>8} {'wrong accepted':>14}")
    summary = []
    for variant in VARIANTS:
        for threshold in THRESHOLDS:
            whole = rejected = facts_ok = 0
            for record in records:
                kept = [c for c in record["claims"] if c["scores"][variant] >= threshold]
                whole += len(kept) == len(record["claims"])
                rejected += not kept
                text = " ".join(c["claim"] for c in kept)
                case = record["case"]
                facts_ok += bool(case and case.required_facts and all(matched_facts(text, case.required_facts)))
            wrong_accepted = sum(
                1 for r in records for c in r["claims"] if c["corrupted"] and c["corrupted"][variant] >= threshold
            )
            summary.append({"variant": variant, "threshold": threshold, "whole": whole, "rejected": rejected,
                            "facts_ok": facts_ok, "wrong_accepted": wrong_accepted})
            print(f"{variant:<17} {threshold:>4.1f} {whole:>18} {rejected:>8} {facts_ok:>8} "
                  f"{wrong_accepted:>8}/{corrupted_total}")

    output = Path(args.results).with_name(Path(args.results).stem + "-grounding-calibration.json")
    output.write_text(
        json.dumps(
            {"summary": summary, "claims": [{k: v for k, v in r.items() if k != "case"} for r in records]},
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"Per-claim scores: {output}")


if __name__ == "__main__":
    main()
