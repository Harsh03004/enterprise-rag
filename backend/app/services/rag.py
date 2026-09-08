import re
from app.services.citation_verifier import verify_answer_grounding
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.collection import Collection
from app.models.document import Document

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

# ============================================================
# Citation helpers
# ============================================================

SOURCE_PATTERN = re.compile(r"\[Source\s+(\d+)\]", re.IGNORECASE)


def extract_citation_ids(answer: str) -> set[int]:
    """
    Extract all [Source N] citation IDs from an answer.
    """
    if not answer:
        return set()

    return {int(match) for match in SOURCE_PATTERN.findall(answer)}


def verify_citations(
    answer: str,
    sources: list[dict],
) -> tuple[str, list[dict]]:
    """
    Verify that every [Source N] citation in the answer
    refers to a source that actually exists in the final
    context.

    Invalid source references are removed.

    Only sources actually cited by the answer are returned.
    """

    if not answer:
        return answer, []

    valid_source_ids = {int(source["id"]) for source in sources}

    cited_source_ids = extract_citation_ids(answer)

    # Remove citations that refer to sources that do not exist.
    def replace_invalid_citation(match):
        source_id = int(match.group(1))

        if source_id in valid_source_ids:
            return match.group(0)

        return ""

    verified_answer = SOURCE_PATTERN.sub(
        replace_invalid_citation,
        answer,
    )

    # Only expose sources actually cited by the answer.
    verified_sources = [
        source
        for source in sources
        if int(source["id"]) in cited_source_ids
        and int(source["id"]) in valid_source_ids
    ]

    return verified_answer, verified_sources


# ============================================================
# Result preparation
# ============================================================


def prepare_results(
    results,
) -> list[tuple]:
    """
    Remove duplicate/empty chunks while preserving relevance.

    This is shared by context and source construction so both
    operate on exactly the same chunks.
    """

    if not results:
        return []

    unique_results = []
    seen_content: set[str] = set()

    for chunk, document, distance in results:
        normalized_content = " ".join(chunk.content.split()).strip().lower()

        if not normalized_content:
            continue

        if normalized_content in seen_content:
            continue

        seen_content.add(normalized_content)

        unique_results.append((chunk, document, distance))

    return unique_results


def group_results_by_document(
    results,
) -> dict[int, list[tuple]]:
    """
    Group results by document and restore original chunk order.
    """

    documents: dict[int, list[tuple]] = {}

    for chunk, document, distance in results:
        documents.setdefault(
            document.id,
            [],
        ).append((chunk, document, distance))

    for document_results in documents.values():
        document_results.sort(key=lambda item: item[0].chunk_index)

    return documents


# ============================================================
# Context + source construction
# ============================================================


def build_context_and_sources(
    results,
    max_context_chars: int = 12000,
) -> tuple[str, list[dict]]:
    """
    Build the final bounded LLM context and the exact source
    metadata belonging to that context.

    Source numbering is assigned only to chunks that actually
    make it into the final context.
    """

    unique_results = prepare_results(results)

    if not unique_results:
        return "", []

    documents = group_results_by_document(unique_results)

    context_parts: list[str] = []
    sources: list[dict] = []

    current_length = 0
    source_number = 1

    separator = "\n\n--- DOCUMENT ---\n\n"

    for document_results in documents.values():
        document = document_results[0][1]

        document_header = [
            f"Document: {document.filename}",
            f"Document ID: {document.id}",
        ]

        document_parts = list(document_header)

        document_sources: list[dict] = []

        for chunk, _, distance in document_results:
            chunk_text = (
                f"[Source {source_number}]\n"
                f"Chunk ID: {chunk.id}\n"
                f"Chunk Index: {chunk.chunk_index + 1}\n"
                f"Distance: {float(distance):.4f}\n"
                f"{chunk.content}"
            )

            document_parts.append(chunk_text)

            document_sources.append(
                {
                    "id": source_number,
                    "document_id": document.id,
                    "filename": document.filename,
                    "chunk_index": chunk.chunk_index,
                    "distance": float(distance),
                    "_content": chunk.content,
                    "_embedding": chunk.embedding,
                }
            )

            source_number += 1

        document_context = "\n\n".join(document_parts)

        additional_length = len(document_context)

        if context_parts:
            additional_length += len(separator)

        # Entire document fits.
        if current_length + additional_length <= max_context_chars:
            context_parts.append(document_context)

            sources.extend(document_sources)

            current_length += additional_length
            continue

        # Remaining context space.
        remaining = max_context_chars - current_length

        if context_parts:
            remaining -= len(separator)

        if remaining <= 0:
            break

        # We need to include as many complete chunks as possible.
        partial_parts: list[str] = []
        partial_sources: list[dict] = []
        partial_length = 0

        for index, (
            chunk,
            _,
            distance,
        ) in enumerate(document_results):

            source_id = document_sources[index]["id"]

            chunk_text = (
                f"[Source {source_id}]\n"
                f"Chunk ID: {chunk.id}\n"
                f"Chunk Index: {chunk.chunk_index + 1}\n"
                f"Distance: {float(distance):.4f}\n"
                f"{chunk.content}"
            )

            addition = len(chunk_text)

            if partial_parts:
                addition += 2

            if partial_length + addition > remaining:
                break

            partial_parts.append(chunk_text)

            partial_sources.append(document_sources[index])

            partial_length += addition

        if partial_parts:
            partial_context = "\n\n".join(
                [
                    *document_header,
                    *partial_parts,
                ]
            )

            # If the header itself makes this exceed the remaining
            # space, fall back to a hard character bound.
            if len(partial_context) > remaining:
                partial_context = partial_context[:remaining].rstrip()

            if partial_context:
                context_parts.append(partial_context)

                # Only include source metadata for chunks that
                # actually survived into the context.
                sources.extend(partial_sources)

        break

    context = separator.join(context_parts)

    return context, sources


def build_context(
    results,
    max_context_chars: int = 12000,
) -> str:
    """
    Backwards-compatible context builder.
    """

    context, _ = build_context_and_sources(
        results,
        max_context_chars=max_context_chars,
    )

    return context


def build_sources(
    results,
    document_id: int | None = None,
) -> list[dict]:
    """
    Backwards-compatible source builder.

    Uses the same context construction logic so source IDs
    remain aligned with the actual context.
    """

    filtered_results = results

    if document_id is not None:
        filtered_results = [result for result in results if result[1].id == document_id]

    _, sources = build_context_and_sources(filtered_results)

    return sources


# ============================================================
# Conversation context
# ============================================================


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
        history_parts.append(f"{message.role.capitalize()}: {message.content}")

    return "\n".join(history_parts)


# ============================================================
# Conversation resolution
# ============================================================


def resolve_conversation(
    db: Session,
    user_id: int,
    conversation_id: int | None,
    question: str,
    document_id: int | None = None,
    collection_id: int | None = None,
):
    """
    Resolve an existing conversation or create a new one.

    Conversation scopes:

    - document_id=None, collection_id=None
        Global / All Documents conversation.

    - document_id=None, collection_id=<id>
        Collection / Project conversation.

    - document_id=<id>, collection_id=None
        Individual document conversation.

    A conversation can never be switched between scopes.
    """

    # ---------------------------------------------------------
    # Validate requested collection ownership
    # ---------------------------------------------------------

    if collection_id is not None:
        collection = db.scalar(
            select(Collection).where(
                Collection.id == collection_id,
                Collection.user_id == user_id,
            )
        )

        if collection is None:
            raise ValueError("Collection not found or does not belong to the user.")

    # ---------------------------------------------------------
    # Validate requested document ownership
    # ---------------------------------------------------------

    if document_id is not None:
        document = db.scalar(
            select(Document).where(
                Document.id == document_id,
                Document.user_id == user_id,
            )
        )

        if document is None:
            raise ValueError("Document not found or does not belong to the user.")

        # A document + collection scope is only valid when the
        # document actually belongs to that collection.
        if collection_id is not None and document.collection_id != collection_id:
            raise ValueError(
                "The selected document does not belong to this collection."
            )

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
            raise ValueError("Conversation not found or does not belong to the user.")

        # -----------------------------------------------------
        # Document scope consistency
        # -----------------------------------------------------

        if (
            conversation.document_id is not None
            and document_id is not None
            and conversation.document_id != document_id
        ):
            raise ValueError("This conversation belongs to a different document.")

        # A document conversation cannot be reused as a
        # collection/global conversation.
        

        # -----------------------------------------------------
        # Collection scope consistency
        # -----------------------------------------------------

        if (
            conversation.collection_id is not None
            and collection_id is not None
            and conversation.collection_id != collection_id
        ):
            raise ValueError("This conversation belongs to a different collection.")

        # A collection conversation cannot be reused as a
        # global/document conversation.
        if conversation.collection_id is not None and collection_id is None:
            raise ValueError("This conversation belongs to a specific collection.")

        # A global conversation cannot suddenly become scoped.
        if (
            conversation.document_id is None
            and conversation.collection_id is None
            and (document_id is not None or collection_id is not None)
        ):
            raise ValueError(
                "This conversation is an All Documents conversation "
                "and cannot be used with a different scope."
            )

        # Always use the scope stored on the conversation.
        document_id = conversation.document_id
        collection_id = conversation.collection_id

        return conversation, document_id, collection_id

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
        collection_id=collection_id,
    )

    return conversation, document_id, collection_id


# ============================================================
# Grounded prompt
# ============================================================


def build_rag_prompt(
    question: str,
    history: str,
    context: str,
) -> str:
    """
    Build the grounded RAG prompt used by both normal and
    streaming answers.
    """

    return f"""
You are an AI assistant answering questions about uploaded documents.

Use ONLY the information provided in the document context below.

CITATION RULES:
- Every factual claim must be supported by the document context.
- When making a factual claim, cite the supporting source using its
  source number in this exact format: [Source 1], [Source 2], etc.
- Use the source number that directly supports the claim.
- If multiple sources support a claim, cite all relevant sources.
- Do not cite a source that does not support the claim.
- Do not invent source numbers.
- Only use source numbers that actually appear in the document context.
- Do not cite information from the previous conversation as evidence.
- If the document context does not contain enough information to answer
  the question, say that you could not find the answer in the uploaded
  documents.
- Do not use outside knowledge to fill gaps.
- Keep citations immediately after the claim they support.
- Do not create a Sources section at the end.
- Do not mention the citation rules in your answer.

Previous conversation:

{history}

Document context:

{context}

Current question:

{question}

Answer:
"""


# ============================================================
# Non-streaming RAG
# ============================================================


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

    conversation, document_id, collection_id = resolve_conversation(
        db=db,
        user_id=user_id,
        conversation_id=conversation_id,
        question=question,
        document_id=document_id,
        collection_id=collection_id,
    )
    conversation_id = conversation.id

    # ---------------------------------------------------------
    # 2. Try to identify a specific document
    # ---------------------------------------------------------

    document_reference = None

    if document_id is None and collection_id is None:
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

            answer = (
                f"I found multiple documents matching "
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
        answer = "I could not find relevant information " "in your uploaded documents."

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
    # to the context/source builders.
    results = [result for result, score in ranked_results]

    # ---------------------------------------------------------
    # 8. Build context + exact source metadata
    # ---------------------------------------------------------

    context, sources = build_context_and_sources(results)

    # ---------------------------------------------------------
    # 9. Build grounded RAG prompt
    # ---------------------------------------------------------

    prompt = build_rag_prompt(
        question=question,
        history=history,
        context=context,
    )

    # ---------------------------------------------------------
    # 10. Generate answer
    # ---------------------------------------------------------

    answer = generate_response(prompt)

    # ---------------------------------------------------------
    # 11. Verify citations
    # ---------------------------------------------------------

    answer, verified_sources = verify_citations(
        answer=answer,
        sources=sources,
    )

    grounded = verify_answer_grounding(
        answer=answer,
        sources=verified_sources,
    )

    if not grounded:
        answer = (
            "I could not verify that the generated answer is "
            "fully supported by your uploaded documents."
        )
        verified_sources = []

    # ---------------------------------------------------------
    # 12. Save conversation messages
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
    # 13. Return answer + verified sources
    # ---------------------------------------------------------

    return {
        "answer": answer,
        "sources": [
            {
                key: value
                for key, value in source.items()
                if key not in {"_content", "_embedding"}
            }
            for source in verified_sources
        ],
        "conversation_id": conversation_id,
    }


# ============================================================
# Streaming RAG
# ============================================================


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

    conversation, document_id, collection_id = resolve_conversation(
        db=db,
        user_id=user_id,
        conversation_id=conversation_id,
        question=question,
        document_id=document_id,
        collection_id=collection_id,
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
            "collection_id": conversation.collection_id,
            "title": conversation.title,
            "created_at": conversation.created_at.isoformat(),
            "updated_at": conversation.updated_at.isoformat(),
        },
    }

    # ---------------------------------------------------------
    # 2. Resolve document reference
    # ---------------------------------------------------------

    document_reference = None

    if document_id is None and collection_id is None:
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

            answer = (
                f"I found multiple documents matching "
                f'"{document_reference}". Please choose one.'
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
        answer = "I could not find relevant information " "in your uploaded documents."

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
    results = [result for result, score in ranked_results]

    # ---------------------------------------------------------
    # 8. Build document context + exact sources
    # ---------------------------------------------------------

    context, sources = build_context_and_sources(results)

    # ---------------------------------------------------------
    # 9. Build grounded prompt
    # ---------------------------------------------------------

    prompt = build_rag_prompt(
        question=question,
        history=history,
        context=context,
    )

    # ---------------------------------------------------------
    # 10. Stream answer
    # ---------------------------------------------------------

    full_answer = ""

    try:
        for token in stream_response(prompt):
            full_answer += token

            yield {
                "type": "token",
                "content": token,
            }

    except Exception:
        yield {
            "type": "error",
            "content": ("The AI response could not be completed. " "Please try again."),
            "conversation_id": conversation_id,
        }

        return

    # ---------------------------------------------------------
    # 11. Verify citations after streaming completes
    # ---------------------------------------------------------

    verified_answer, verified_sources = verify_citations(
        answer=full_answer,
        sources=sources,
    )

    # ---------------------------------------------------------
    # 12. Save completed conversation messages
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
        content=verified_answer,
    )

    # ---------------------------------------------------------
    # 13. Send verified sources
    # ---------------------------------------------------------

    yield {
        "type": "sources",
        "sources": verified_sources,
        "conversation_id": conversation_id,
    }

    # ---------------------------------------------------------
    # 14. Complete
    # ---------------------------------------------------------

    yield {
        "type": "complete",
        "conversation_id": conversation_id,
    }
