from app.db.session import SessionLocal
from app.services.rag import answer_question


USER_ID = 4
DOCUMENT_ID = 8

TESTS = [
    # Basic factual retrieval
    (
        "Basic",
        "What is StuMeet?",
    ),
    (
        "Basic",
        "What are the main features of StuMeet?",
    ),
    (
        "Basic",
        "What problem is StuMeet designed to solve?",
    ),
    (
        "Basic",
        "What technologies are mentioned in the document?",
    ),
    (
        "Basic",
        "What role do host controls play in StuMeet?",
    ),

    # Specific information
    (
        "Specific",
        "What is WebRTC used for in StuMeet?",
    ),
    (
        "Specific",
        "What is Socket.IO used for in StuMeet?",
    ),
    (
        "Specific",
        "What authentication mechanisms are used?",
    ),
    (
        "Specific",
        "What functionality is provided by Meetings and Custom Rooms?",
    ),
    (
        "Specific",
        "What does the document mention about educational use of the platform?",
    ),

    # Whole-document / synthesis
    (
        "Synthesis",
        "What are the major topics covered in this document?",
    ),
    (
        "Synthesis",
        "Create a structured overview of everything important in this document.",
    ),
    (
        "Synthesis",
        "What are the main ideas presented throughout the document, and how do they connect?",
    ),
    (
        "Synthesis",
        "Give me the key points from every major part of this document.",
    ),
    (
        "Synthesis",
        "Explain the document from beginning to end.",
    ),

    # Reasoning
    (
        "Reasoning",
        "How do the different features of StuMeet work together to achieve the project's objective?",
    ),
    (
        "Reasoning",
        "How does the technical implementation support the goals of StuMeet?",
    ),
    (
        "Reasoning",
        "Which problems in existing platforms are directly addressed by StuMeet?",
    ),

    # Grounding / hallucination tests
    (
        "Grounding",
        "According to the document, what database does StuMeet use?",
    ),
    (
        "Grounding",
        "According to the document, what programming language was used to develop StuMeet?",
    ),
    (
        "Grounding",
        "According to the document, what cloud provider hosts StuMeet?",
    ),
    (
        "Grounding",
        "According to the document, what was the exact deployment date of StuMeet?",
    ),
    (
        "Grounding",
        "According to the document, how many users can join a StuMeet meeting?",
    ),
    (
        "Grounding",
        "What does the document say about quantum computing?",
    ),

    # Adversarial / unrelated
    (
        "Negative",
        "What is the capital of Japan?",
    ),
    (
        "Negative",
        "Explain nuclear fusion according to the document.",
    ),
    (
        "Negative",
        "What is the current price of Bitcoin according to the document?",
    ),
]


def extract_answer(result):
    if isinstance(result, str):
        return result

    if isinstance(result, dict):
        return (
            result.get("answer")
            or result.get("content")
            or result.get("response")
            or str(result)
        )

    return str(result)


def main():
    db = SessionLocal()

    total = len(TESTS)
    passed = 0
    failed = 0

    print("=" * 80)
    print("ENTERPRISE RAG AUTOMATED TEST SUITE")
    print("=" * 80)
    print(f"User ID:     {USER_ID}")
    print(f"Document ID: {DOCUMENT_ID}")
    print(f"Total tests: {total}")
    print("=" * 80)

    for number, (category, question) in enumerate(TESTS, start=1):

        print()
        print("=" * 80)
        print(f"TEST {number}/{total}")
        print(f"CATEGORY: {category}")
        print(f"QUESTION: {question}")
        print("=" * 80)

        try:
            result = answer_question(
                db=db,
                question=question,
                user_id=USER_ID,
                document_id=DOCUMENT_ID,
                collection_id=None,
                conversation_id=None,
            )

            answer = extract_answer(result)

            print()
            print("ANSWER:")
            print("-" * 80)
            print(answer)
            print("-" * 80)

            lowered = answer.lower()

            fallback_phrases = [
                "i could not find relevant information",
                "could not find relevant information",
                "i couldn't find relevant information",
            ]

            is_fallback = any(
                phrase in lowered
                for phrase in fallback_phrases
            )

            # For grounding/negative questions, fallback is generally
            # the expected behavior.
            if category in {"Grounding", "Negative"}:
                if is_fallback:
                    print("RESULT: PASS")
                    passed += 1
                else:
                    print(
                        "RESULT: REVIEW "
                        "(LLM returned an answer; inspect grounding)"
                    )
                    failed += 1
            else:
                if is_fallback:
                    print("RESULT: FAIL")
                    failed += 1
                else:
                    print("RESULT: PASS")
                    passed += 1

        except Exception as exc:
            print()
            print("ERROR:")
            print(repr(exc))
            print("RESULT: FAIL")
            failed += 1

    db.close()

    print()
    print("=" * 80)
    print("FINAL TEST SUMMARY")
    print("=" * 80)
    print(f"TOTAL:  {total}")
    print(f"PASSED: {passed}")
    print(f"FAILED: {failed}")
    print("=" * 80)


if __name__ == "__main__":
    main()
