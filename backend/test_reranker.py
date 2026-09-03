from app.db.session import SessionLocal
from app.services.retrieval import search_similar_chunks
from app.services.reranking import score_chunks


db = SessionLocal()

try:
    user_id = 4
    document_id = 8

    questions = [
        "What was the main objective of the project?",
        "What was the total budget allocated to the project?",
    ]

    for question in questions:
        print("\n" + "=" * 80)
        print(f"QUESTION: {question}")
        print("=" * 80)

        candidates = search_similar_chunks(
            db=db,
            query=question,
            user_id=user_id,
            document_id=document_id,
            limit=5,
            candidate_limit=20,
        )

        scored = score_chunks(
            query=question,
            results=candidates,
        )

        scored.sort(
            key=lambda item: item[1],
            reverse=True,
        )

        for index, (result, score) in enumerate(
            scored[:10],
            start=1,
        ):
            chunk, document, distance = result

            print(f"\nRank: {index}")
            print(f"Reranker score: {score:.4f}")
            print(f"Vector distance: {distance:.4f}")
            print(f"Chunk index: {chunk.chunk_index}")
            print(f"Content: {chunk.content[:300]}")

finally:
    db.close()
