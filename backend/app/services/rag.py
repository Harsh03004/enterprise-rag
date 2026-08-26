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
from app.services.retrieval import search_similar_chunks


def build_context(results) -> str:
    context_parts = []

    for chunk, document, distance in results:
        context_parts.append(
            f"[Source {chunk.chunk_index + 1}]\n"
            f"Document: {document.filename}\n"
            f"Content:\n{chunk.content}"
        )

    return "\n\n---\n\n".join(context_parts)


def build_sources(
    results,
    document_id: int | None = None,
) -> list[dict]:
    sources = []

    for index, (chunk, document, distance) in enumerate(
        results,
        start=1,
    ):
        if document_id is not None and document.id != document_id:
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

    # Only keep the most recent messages.
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
    # 2. Save user message
    # ---------------------------------------------------------

    add_message(
        db=db,
        conversation_id=conversation_id,
        role="user",
        content=question,
    )

    # ---------------------------------------------------------
    # 3. Try to identify a specific document
    # ---------------------------------------------------------

    if document_id is None:
        document_reference = extract_document_reference(question)

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
                    role="assistant",
                    content=answer,
                )

                return {
                    "answer": answer,
                    "sources": sources,
                    "conversation_id": conversation_id,
                }

    # ---------------------------------------------------------
    # 4. Perform semantic retrieval
    # ---------------------------------------------------------

    results = search_similar_chunks(
        db=db,
        query=question,
        user_id=user_id,
        document_id=document_id,
        limit=limit,
    )

    # ---------------------------------------------------------
    # 5. No relevant chunks
    # ---------------------------------------------------------

    if not results:
        answer = (
            "I could not find relevant information "
            "in your uploaded documents."
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

    # ---------------------------------------------------------
    # 6. Build RAG context
    # ---------------------------------------------------------

    context = build_context(results)

    # ---------------------------------------------------------
    # 7. Load conversation history
    # ---------------------------------------------------------

    history = build_conversation_context(
        db=db,
        conversation_id=conversation_id,
    )

    # ---------------------------------------------------------
    # 8. Build grounded RAG prompt
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
    # 9. Generate answer
    # ---------------------------------------------------------

    answer = generate_response(prompt)

    # ---------------------------------------------------------
    # 10. Save assistant response
    # ---------------------------------------------------------

    add_message(
        db=db,
        conversation_id=conversation_id,
        role="assistant",
        content=answer,
    )

    # ---------------------------------------------------------
    # 11. Return answer + sources
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
    conversation_id: int | None = None,
    limit: int = 5,
):
    # ---------------------------------------------------------
    # 1. Resolve/create conversation
    # ---------------------------------------------------------

    conversation,document_id = resolve_conversation(
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
    # 2. Save user message
    # ---------------------------------------------------------

    add_message(
        db=db,
        conversation_id=conversation_id,
        role="user",
        content=question,
    )

    # ---------------------------------------------------------
    # 3. Resolve document reference
    # ---------------------------------------------------------

    if document_id is None:
        document_reference = extract_document_reference(question)

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

                yield {
                    "type": "error",
                    "content": (
                        f'I found multiple documents matching '
                        f'"{document_reference}". Please choose one.'
                    ),
                    "sources": sources,
                    "conversation_id": conversation_id,
                }
                return

    # ---------------------------------------------------------
    # 4. Retrieve relevant chunks
    # ---------------------------------------------------------

    results = search_similar_chunks(
        db=db,
        query=question,
        user_id=user_id,
        document_id=document_id,
        limit=limit,
    )

    if not results:
        answer = (
            "I could not find relevant information "
            "in your uploaded documents."
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

    # ---------------------------------------------------------
    # 5. Build document context
    # ---------------------------------------------------------

    context = build_context(results)

    # ---------------------------------------------------------
    # 6. Load previous conversation
    # ---------------------------------------------------------

    history = build_conversation_context(
        db=db,
        conversation_id=conversation_id,
    )

    # ---------------------------------------------------------
    # 7. Build grounded prompt
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
    # 8. Stream answer
    # ---------------------------------------------------------

    full_answer = ""

    for token in stream_response(prompt):
        full_answer += token

        yield {
            "type": "token",
            "content": token,
        }

    # ---------------------------------------------------------
    # 9. Save completed assistant response
    # ---------------------------------------------------------

    add_message(
        db=db,
        conversation_id=conversation_id,
        role="assistant",
        content=full_answer,
    )

    # ---------------------------------------------------------
    # 10. Send sources
    # ---------------------------------------------------------

    yield {
        "type": "sources",
        "sources": build_sources(
            results,
            document_id,
        ),
        "conversation_id": conversation_id,
    }

    yield {
        "type": "complete",
        "conversation_id": conversation_id,
    }