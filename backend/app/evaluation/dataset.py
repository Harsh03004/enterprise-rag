from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class EvaluationCase:
    id: str
    category: str
    question: str
    expected_answer: str | None = None
    expected_keywords: list[str] = field(default_factory=list)
    relevant_chunk_ids: list[int] = field(default_factory=list)
    should_fallback: bool = False

    @classmethod
    def from_dict(cls, data: dict) -> "EvaluationCase":
        return cls(
            id=str(data["id"]),
            category=str(data["category"]),
            question=str(data["question"]),
            expected_answer=data.get("expected_answer"),
            expected_keywords=[str(x) for x in data.get("expected_keywords", [])],
            relevant_chunk_ids=[int(x) for x in data.get("relevant_chunk_ids", [])],
            should_fallback=bool(data.get("should_fallback", False)),
        )


def load_dataset(path: str | Path) -> list[EvaluationCase]:
    with Path(path).open("r", encoding="utf-8") as file:
        data = json.load(file)

    if not isinstance(data, list):
        raise ValueError("Evaluation dataset must contain a JSON list.")

    return [EvaluationCase.from_dict(item) for item in data]