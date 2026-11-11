"""Evaluation dataset format (version 2).

A dataset is a JSON object::

    {
      "version": 2,
      "corpus": ["handbook.md", ...],      # files in the corpus directory
      "cases": [ ... ]
    }

Each case::

    {
      "id": "handbook-leave-001",
      "category": "Specific",
      "question": "How many days of annual leave do employees get?",
      "reference_answer": "24 days per calendar year.",   # documentation only
      "required_facts": [["24 days", "twenty-four days"]],
      "forbidden": ["10 days"],
      "relevant_passages": [
        {"document": "handbook.md", "quote": "24 days of paid annual leave"}
      ],
      "should_fallback": false
    }

required_facts lists every fact a correct answer must contain; each fact is a
list of accepted phrasings (a bare string is shorthand for one phrasing).
forbidden lists phrases whose presence makes the answer wrong (near-miss facts
from similar passages). relevant_passages identify supporting evidence by a
short verbatim quote instead of database IDs, so labels survive re-chunking
and re-ingestion.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

DATASET_VERSION = 2


@dataclass(frozen=True)
class Passage:
    document: str
    quote: str


@dataclass
class EvaluationCase:
    id: str
    category: str
    question: str
    should_fallback: bool = False
    reference_answer: str | None = None
    required_facts: list[list[str]] = field(default_factory=list)
    forbidden: list[str] = field(default_factory=list)
    relevant_passages: list[Passage] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict) -> EvaluationCase:
        case_id = str(data["id"])
        facts = []
        for fact in data.get("required_facts", []):
            phrasings = [fact] if isinstance(fact, str) else list(fact)
            phrasings = [str(phrase).strip() for phrase in phrasings if str(phrase).strip()]
            if not phrasings:
                raise ValueError(f"Case {case_id}: a required fact has no phrasings.")
            facts.append(phrasings)

        passages = []
        for passage in data.get("relevant_passages", []):
            document = str(passage.get("document", "")).strip()
            quote = str(passage.get("quote", "")).strip()
            if not document or not quote:
                raise ValueError(f"Case {case_id}: relevant passages need a document and a quote.")
            passages.append(Passage(document=document, quote=quote))

        case = cls(
            id=case_id,
            category=str(data["category"]),
            question=str(data["question"]),
            should_fallback=bool(data.get("should_fallback", False)),
            reference_answer=data.get("reference_answer"),
            required_facts=facts,
            forbidden=[str(phrase) for phrase in data.get("forbidden", [])],
            relevant_passages=passages,
        )
        if not case.should_fallback and not case.required_facts:
            raise ValueError(f"Case {case_id}: answerable cases need at least one required fact.")
        if not case.should_fallback and not case.relevant_passages:
            raise ValueError(f"Case {case_id}: answerable cases need at least one relevant passage.")
        return case


@dataclass
class EvaluationDataset:
    corpus: list[str]
    cases: list[EvaluationCase]


def load_dataset(path: str | Path) -> EvaluationDataset:
    with Path(path).open("r", encoding="utf-8") as file:
        data = json.load(file)

    if not isinstance(data, dict) or data.get("version") != DATASET_VERSION:
        raise ValueError(
            f"Evaluation dataset must be a version {DATASET_VERSION} JSON object "
            '({"version": 2, "corpus": [...], "cases": [...]}).'
        )

    corpus = [str(name) for name in data.get("corpus", [])]
    cases = [EvaluationCase.from_dict(item) for item in data.get("cases", [])]

    seen: set[str] = set()
    for case in cases:
        if case.id in seen:
            raise ValueError(f"Duplicate evaluation case id: {case.id}")
        seen.add(case.id)
        for passage in case.relevant_passages:
            if passage.document not in corpus:
                raise ValueError(
                    f"Case {case.id}: passage document {passage.document!r} is not in the corpus list."
                )

    return EvaluationDataset(corpus=corpus, cases=cases)
