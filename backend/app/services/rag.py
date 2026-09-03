from sqlalchemy.orm import Session

from app.crud.conversation import (
    add_message,
    create_conversation,
    get_conversation,
    get_messages,
)
from app.services.document_search import (
    extract_document_reference,
    find_documents,
)
from app.services.llm import generate_response, stream_response
from app.services.query_rewriting import rewrite_query
from app.services.reranking import (
    has_sufficient_confidence,
    rerank_chunks,
)
from app.services.retrieval import search_similar_chunks


def build_context(
    results,
    max_context_chars: int = 12000,
) -> str:
    """
    Build a structured, bounded context for the LLM.

    Results are expected to be ordered by relevance.
    Chunks are grouped by document while preserving the
    original chunk order within each document.

    Duplicate chunk content is removed and the final
    context is limited by character count.
    """

    if not results:
        return ""

    # ---------------------------------------------------------
    # 1. Remove duplicate chunks while preserving relevance
    # ---------------------------------------------------------

    unique_results = []
    seen_content: set[str] = set()

    for chunk, document, distance in results:
        normalized_content = " ".join(
            chunk.content.split()
        ).strip().lower()

        if not normalized_content:
            continue

        if normalized_content in seen_content:
            continue

        seen_content.add(normalized_content)

        unique_results.append(
            (chunk, document, distance)
        )

    # ---------------------------------------------------------
    # 2. Group chunks by document
    # ---------------------------------------------------------

    documents: dict[int, list[tuple]] = {}

    for chunk, document, distance in unique_results:
        documents.setdefault(
            document.id,
            [],
        ).append(
            (chunk, document, distance)
        )

    # ---------------------------------------------------------
    # 3. Restore original chunk order
    # ---------------------------------------------------------

    for document_results in documents.values():
        document_results.sort(
            key=lambda item: item[0].chunk_index
        )

    # ---------------------------------------------------------
    # 4. Build bounded context
    # ---------------------------------------------------------

    context_parts = []
    current_length = 0

    for document_results in documents.values():
        document = document_results[0][1]

        document_header = (
            f"Document: {document.filename}\n"
            f"Document ID: {document.id}\n"
        )

        document_parts = [
            document_header
        ]

        for chunk, _, distance in document_results:
            chunk_text = (
                f"[Chunk ID: {chunk.id} | "
                f"Chunk Index: {chunk.chunk_index + 1} | "
                f"Distance: {float(distance):.4f}]\n"
                f"{chunk.content}"
            )

            document_parts.append(chunk_text)

        document_context = "\n\n".join(
            document_parts
        )

        separator = "\n\n--- DOCUMENT ---\n\n"

        additional_length = len(
            document_context
        )

        if context_parts:
            additional_length += len(separator)

        if (
            current_length + additional_length
            > max_context_chars
        ):
            remaining = (
                max_context_chars
                - current_length
            )

            if remaining <= 0:
                break

            if context_parts:
                remaining -= len(separator)

            if remaining <= 0:
                break

            truncated_context = (
                document_context[:remaining]
                .rstrip()
            )

            if truncated_context:
                context_parts.append(
                    truncated_context
                )

            break

        context_parts.append(
            document_context
        )

        current_length += additional_length

    return separator.join(context_parts)


def build_sources(
    results,
    document_id: int | None = None,
) -> list[dict]:
    sources = []

    for index, (chunk, document, distance) in enumerate(
        results,
        start=1,
    ):
        if (
            document_id is not None
            and document.id != document_id
        ):
            continue

        sources.append(
            {
                "id": index,
                "document_id": document.id,
                "filename": document.filename,
                "chunk_index": chunk.chunk_index,
                "distance": float(distance),
            }
        )

    return sources


def build_conversation_context(
    db: Session,
    conversation_id: int | None,
    max_messages: int = 10,
) -> str:
    """
    Load recent conversation messages and format them
    for inclusion in the LLM prompt.
    """

    if conversation_id is None:
        return ""

    messages = get_messages(
        db=db,
        conversation_id=conversation_id,
    )

    messages = messages[-max_messages:]

    if not messages:
        return ""

    history_parts = []

    for message in messages:
        history_parts.append(
            f"{message.role.capitalize()}: {message.content}"
        )

    return "\n".join(history_parts)


def resolve_conversation(
    db: Session,
    user_id: int,
    conversation_id: int | None,
    question: str,
    document_id: int | None = None,
):
    """
    Resolve an existing conversation or create a new one.

    Rules:

    - Existing conversation must belong to the current user.
    - If an existing conversation is tied to a document,
      the requested document must match it.
    - A new conversation stores the selected document_id.
    - document_id=None means the conversation searches
      across all documents.
    """

    # ---------------------------------------------------------
    # Existing conversation
    # ---------------------------------------------------------

    if conversation_id is not None:
        conversation = get_conversation(
            db=db,
            conversation_id=conversation_id,
            user_id=user_id,
        )

        if conversation is None:
            raise ValueError(
                "Conversation not found or does not belong to the user."
            )

        # -----------------------------------------------------
        # Protect conversation/document consistency
        # -----------------------------------------------------

        if (
            conversation.document_id is not None
            and document_id is not None
            and conversation.document_id != document_id
        ):
            raise ValueError(
                "This conversation belongs to a different document."
            )

        # If the conversation already has a document,
        # always use that document.
        if conversation.document_id is not None:
            document_id = conversation.document_id

        return conversation, document_id

    # ---------------------------------------------------------
    # Create new conversation
    # ---------------------------------------------------------

    title = question[:80].strip()

    if not title:
        title = "New conversation"

    conversation = create_conversation(
        db=db,
        user_id=user_id,
        title=title,
        document_id=document_id,
    )

    return conversation, document_id


def answer_question(
    db: Session,
    user_id: int,
    question: str,
    document_id: int | None = None,
    collection_id: int | None = None,
    conversation_id: int | None = None,
    limit: int = 5,
):
    # ---------------------------------------------------------
    # 1. Resolve/create conversation
    # ---------------------------------------------------------

    conversation, document_id = resolve_conversation(
        db=db,
        user_id=user_id,
        conversation_id=conversation_id,
        question=question,
        document_id=document_id,
    )

    conversation_id = conversation.id

    # ---------------------------------------------------------
    # 2. Try to identify a specific document
    # ---------------------------------------------------------

    if document_id is None:
        document_reference = extract_document_reference(
            question
        )

        if document_reference:
            matched_documents = find_documents(
                db=db,
                user_id=user_id,
                query=document_reference,
            )

            # Exactly one matching document
            if len(matched_documents) == 1:
                document_id = matched_documents[0].id

            # Multiple matching documents
            elif len(matched_documents) > 1:
                sources = [
                    {
                        "id": index,
                        "document_id": document.id,
                        "filename": document.filename,
                        "chunk_index": -1,
                        "distance": 0.0,
                    }
                    for index, document in enumerate(
                        matched_documents,
                        start=1,
                    )
                ]

                answer = (
                    f'I found multiple documents matching '
                    f'"{document_reference}". '
                    f"Please choose one."
                )

                add_message(
                    db=db,
                    conversation_id=conversation_id,
                    role="user",
                    content=question,
                )

                add_message(
                    db=db,
                    conversation_id=conversation_id,
                    role="assistant",
                    content=answer,
                )

                return {
                    "answer": answer,
                    "sources": sources,
                    "conversation_id": conversation_id,
                }

    # ---------------------------------------------------------
    # 3. Load previous conversation history
    # ---------------------------------------------------------

    history = build_conversation_context(
        db=db,
        conversation_id=conversation_id,
    )

    # ---------------------------------------------------------
    # 4. Rewrite query for retrieval
    # ---------------------------------------------------------

    search_query = rewrite_query(
        question=question,
        conversation_history=history,
    )

    # ---------------------------------------------------------
    # 5. Perform hybrid retrieval
    # ---------------------------------------------------------

    candidates = search_similar_chunks(
        db=db,
        query=search_query,
        user_id=user_id,
        document_id=document_id,
        collection_id=collection_id,
        limit=limit,
        candidate_limit=limit * 4,
    )

    # ---------------------------------------------------------
    # 6. Rerank candidates
    # ---------------------------------------------------------

    ranked_results = rerank_chunks(
        query=search_query,
        results=candidates,
        limit=limit,
    )

    # ---------------------------------------------------------
    # 7. Confidence check
    # ---------------------------------------------------------

    if not has_sufficient_confidence(ranked_results):
        answer = (
            "I could not find relevant information "
            "in your uploaded documents."
        )

        add_message(
            db=db,
            conversation_id=conversation_id,
            role="user",
            content=question,
        )

        add_message(
            db=db,
            conversation_id=conversation_id,
            role="assistant",
            content=answer,
        )

        return {
            "answer": answer,
            "sources": [],
            "conversation_id": conversation_id,
        }

    # Remove reranker scores before passing results
    # to the existing context/source builders.
    results = [
        result
        for result, score in ranked_results
    ]

    # ---------------------------------------------------------
    # 8. Build RAG context
    # ---------------------------------------------------------

    context = build_context(results)

    # ---------------------------------------------------------
    # 9. Build grounded RAG prompt
    # ---------------------------------------------------------

    prompt = f"""
You are an AI assistant answering questions about uploaded documents.

Use ONLY the information provided in the document context below.

If the document context does not contain enough information to answer
the question, say that you could not find the answer in the uploaded
documents.

Do not invent facts or information that is not present in the context.

Previous conversation:

{history}

Document context:

{context}

Current question:

{question}

Answer:
"""

    # ---------------------------------------------------------
    # 10. Generate answer
    # ---------------------------------------------------------

    answer = generate_response(prompt)

    # ---------------------------------------------------------
    # 11. Save conversation messages
    # ---------------------------------------------------------

    add_message(
        db=db,
        conversation_id=conversation_id,
        role="user",
        content=question,
    )

    add_message(
        db=db,
        conversation_id=conversation_id,
        role="assistant",
        content=answer,
    )

    # ---------------------------------------------------------
    # 12. Return answer + sources
    # ---------------------------------------------------------

    return {
        "answer": answer,
        "sources": build_sources(
            results,
            document_id,
        ),
        "conversation_id": conversation_id,
    }


def stream_answer(
    db: Session,
    user_id: int,
    question: str,
    document_id: int | None = None,
    collection_id: int | None = None,
    conversation_id: int | None = None,
    limit: int = 5,
):
    # ---------------------------------------------------------
    # 1. Resolve/create conversation
    # ---------------------------------------------------------

    conversation, document_id = resolve_conversation(
        db=db,
        user_id=user_id,
        conversation_id=conversation_id,
        question=question,
        document_id=document_id,
    )

    conversation_id = conversation.id

    # ---------------------------------------------------------
    # 1.5 Send conversation information to frontend
    # ---------------------------------------------------------

    yield {
        "type": "conversation",
        "conversation": {
            "id": conversation.id,
            "user_id": conversation.user_id,
            "document_id": conversation.document_id,
            "title": conversation.title,
            "created_at": conversation.created_at.isoformat(),
            "updated_at": conversation.updated_at.isoformat(),
        },
    }

    # ---------------------------------------------------------
    # 2. Resolve document reference
    # ---------------------------------------------------------

    if document_id is None:
        document_reference = extract_document_reference(
            question
        )

        if document_reference:
            matched_documents = find_documents(
                db=db,
                user_id=user_id,
                query=document_reference,
            )

            if len(matched_documents) == 1:
                document_id = matched_documents[0].id

            elif len(matched_documents) > 1:
                sources = [
                    {
                        "id": index,
                        "document_id": document.id,
                        "filename": document.filename,
                        "chunk_index": -1,
                        "distance": 0.0,
                    }
                    for index, document in enumerate(
                        matched_documents,
                        start=1,
                    )
                ]

                add_message(
                    db=db,
                    conversation_id=conversation_id,
                    role="user",
                    content=question,
                )

                answer = (
                    f'I found multiple documents matching '
                    f'"{document_reference}". Please choose one.'
                )

                add_message(
                    db=db,
                    conversation_id=conversation_id,
                    role="assistant",
                    content=answer,
                )

                yield {
                    "type": "error",
                    "content": answer,
                    "sources": sources,
                    "conversation_id": conversation_id,
                }

                return

    # ---------------------------------------------------------
    # 3. Load previous conversation history
    # ---------------------------------------------------------

    history = build_conversation_context(
        db=db,
        conversation_id=conversation_id,
    )

    # ---------------------------------------------------------
    # 4. Rewrite query for retrieval
    # ---------------------------------------------------------

    search_query = rewrite_query(
        question=question,
        conversation_history=history,
    )

    # ---------------------------------------------------------
    # 5. Retrieve candidate chunks
    # ---------------------------------------------------------

    candidates = search_similar_chunks(
        db=db,
        query=search_query,
        user_id=user_id,
        document_id=document_id,
        collection_id=collection_id,
        limit=limit,
        candidate_limit=limit * 4,
    )

    # ---------------------------------------------------------
    # 6. Rerank candidates
    # ---------------------------------------------------------

    ranked_results = rerank_chunks(
        query=search_query,
        results=candidates,
        limit=limit,
    )

    # ---------------------------------------------------------
    # 7. Confidence check
    # ---------------------------------------------------------

    if not has_sufficient_confidence(ranked_results):
        answer = (
            "I could not find relevant information "
            "in your uploaded documents."
        )

        add_message(
            db=db,
            conversation_id=conversation_id,
            role="user",
            content=question,
        )

        add_message(
            db=db,
            conversation_id=conversation_id,
            role="assistant",
            content=answer,
        )

        yield {
            "type": "error",
            "content": answer,
            "sources": [],
            "conversation_id": conversation_id,
        }

        return

    # Remove reranker scores before building context.
    results = [
        result
        for result, score in ranked_results
    ]

    # ---------------------------------------------------------
    # 8. Build document context
    # ---------------------------------------------------------

    context = build_context(results)

    # ---------------------------------------------------------
    # 9. Build grounded prompt
    # ---------------------------------------------------------

    prompt = f"""
You are an AI assistant answering questions about uploaded documents.

Use ONLY the information provided in the document context below.

If the document context does not contain enough information to answer
the question, say that you could not find the answer in the uploaded
documents.

Do not invent facts or information that is not present in the context.

Previous conversation:

{history}

Document context:

{context}

Current question:

{question}

Answer:
"""

    # ---------------------------------------------------------
    # 10. Stream answer
    # ---------------------------------------------------------

    full_answer = ""

    for token in stream_response(prompt):
        full_answer += token

        yield {
            "type": "token",
            "content": token,
        }

    # ---------------------------------------------------------
    # 11. Save completed conversation messages
    # ---------------------------------------------------------

    add_message(
        db=db,
        conversation_id=conversation_id,
        role="user",
        content=question,
    )

    add_message(
        db=db,
        conversation_id=conversation_id,
        role="assistant",
        content=full_answer,
    )

    # ---------------------------------------------------------
    # 12. Send sources
    # ---------------------------------------------------------

    yield {
        "type": "sources",
        "sources": build_sources(
            results,
            document_id,
        ),
        "conversation_id": conversation_id,
    }

    # ---------------------------------------------------------
    # 13. Complete
    # ---------------------------------------------------------

    yield {
        "type": "complete",
        "conversation_id": conversation_id,
    }