import re
from math import sqrt

from app.services.embedding import generate_embeddings


SOURCE_PATTERN = re.compile(
    r"\[(?:Source\s+)?(\d+)\]",
    re.IGNORECASE,
)


def extract_citation_ids(text: str) -> list[int]:
    if not text:
        return []

    seen: set[int] = set()
    citation_ids: list[int] = []

    for match in SOURCE_PATTERN.findall(text):
        source_id = int(match)

        if source_id not in seen:
            seen.add(source_id)
            citation_ids.append(source_id)

    return citation_ids


def _split_claims(answer: str) -> list[str]:
    if not answer:
        return []

    text = re.sub(r"[*_`#]", "", answer)

    return [
        claim.strip()
        for claim in re.split(
            r"(?<=[.!?])\s+",
            text.strip(),
        )
        if claim.strip()
    ]


def _remove_citations(text: str) -> str:
    return SOURCE_PATTERN.sub("", text).strip()


def _cosine_similarity(
    vector_a,
    vector_b,
) -> float:
    if not vector_a or not vector_b:
        return 0.0

    dot_product = sum(
        a * b
        for a, b in zip(vector_a, vector_b)
    )

    magnitude_a = sqrt(
        sum(a * a for a in vector_a)
    )

    magnitude_b = sqrt(
        sum(b * b for b in vector_b)
    )

    if magnitude_a == 0.0 or magnitude_b == 0.0:
        return 0.0

    return dot_product / (
        magnitude_a * magnitude_b
    )


def verify_answer_grounding(
    answer: str,
    sources: list[dict],
    similarity_threshold: float = 0.45,
) -> bool:
    """
    Verify that cited factual claims are semantically supported
    by their cited document chunks.

    Source embeddings are reused directly from PostgreSQL.

    Answer claim embeddings are generated in one batch to avoid
    repeatedly invoking the embedding model.
    """

    if not answer.strip():
        return False

    if not sources:
        return False

    source_map = {}

    for source in sources:
        source_id = source.get("id")
        embedding = source.get("_embedding")

        if source_id is None or embedding is None:
            continue

        source_map[int(source_id)] = source

    if not source_map:
        return False

    claims = _split_claims(answer)

    claim_data = []

    for claim in claims:
        raw_citation_ids = SOURCE_PATTERN.findall(
            claim
        )

        if not raw_citation_ids:
            continue

        citation_ids = [
            int(source_id)
            for source_id in raw_citation_ids
            if int(source_id) in source_map
        ]

        if not citation_ids:
            return False

        claim_text = _remove_citations(claim)

        if not claim_text:
            continue

        claim_data.append(
            (
                claim_text,
                citation_ids,
            )
        )

    if not claim_data:
        return False

    # Generate embeddings for every cited claim in ONE model call.
    claim_embeddings = generate_embeddings(
        [claim_text for claim_text, _ in claim_data]
    )

    for (
        (_, citation_ids),
        claim_embedding,
    ) in zip(
        claim_data,
        claim_embeddings,
    ):
        supported = False

        for source_id in citation_ids:
            source_embedding = source_map[source_id][
                "_embedding"
            ]

            similarity = _cosine_similarity(
                claim_embedding,
                source_embedding,
            )
            
            print(
                f"\n[GROUNDING] Source {source_id} "
                f"similarity = {similarity:.4f}"
            )

            if similarity >= similarity_threshold:
                supported = True
                break

        if not supported:
            return False

    return True
