import re

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.crud.conversation import (
    add_message,
    create_conversation,
    get_conversation,
    get_messages,
)
from app.models.collection import Collection
from app.models.document import Document
from app.services.citation_verifier import (
    repair_missing_citations,
    verify_answer_grounding,
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

SOURCE_PATTERN = re.compile(
    r"\[(?:Source\s+)?(\d+)\]",
    re.IGNORECASE,
)

GROUNDING_FALLBACK = (
    "I could not verify that the generated answer is fully supported "
    "by your uploaded documents."
)


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


def public_sources(sources: list[dict]) -> list[dict]:
    return [
        {
            key: value
            for key, value in source.items()
            if key not in {"_content", "_embedding"}
        }
        for source in sources
    ]


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

    return documents


# ============================================================
# Context + source construction
# ============================================================


def build_context_and_sources(
    results,
    max_context_chars: int = 30000,
) -> tuple[str, list[dict]]:
    """
    Build the final bounded LLM context and exact source metadata.

    Chunks are considered in reranked order. Source IDs are assigned
    only to chunks that actually make it into the final context.
    """

    unique_results = prepare_results(results)

    if not unique_results:
        return "", []

    context_parts: list[str] = []
    sources: list[dict] = []

    current_length = 0
    source_number = 1

    separator = "\n\n--- DOCUMENT ---\n\n"

    for document_results in group_results_by_document(unique_results).values():
        document = document_results[0][1]

        document_header = f"Document: {document.filename}\nDocument ID: {document.id}"

        document_parts: list[str] = [document_header]
        document_length = len(document_header)

        document_sources: list[dict] = []

        for chunk, _, distance in document_results:
            chunk_text_without_source = (
                f"Chunk ID: {chunk.id}\n"
                f"Chunk Index: {chunk.chunk_index + 1}\n"
                f"Distance: {float(distance):.4f}\n"
                f"Page: {chunk.page_number or 'unknown'}\n"
                f"Section: {chunk.section_heading or 'unknown'}\n"
                f"{chunk.content}"
            )

            source_id = source_number

            chunk_text = f"[Source {source_id}]\n{chunk_text_without_source}"

            addition = len(chunk_text) + (2 if document_sources else 0)
            separator_length = len(separator) if context_parts else 0

            # Skip this chunk if it does not fit. Keep scanning because a later
            # shorter chunk may still fit within the remaining context budget.
            if (
                current_length
                + separator_length
                + document_length
                + addition
                > max_context_chars
            ):
                continue

            document_parts.append(chunk_text)
            document_length += addition

            document_sources.append(
                {
                    "id": source_id,
                    "document_id": document.id,
                    "chunk_id": chunk.id,
                    "filename": document.filename,
                    "chunk_index": chunk.chunk_index,
                    "page_number": chunk.page_number,
                    "section_heading": chunk.section_heading,
                    "block_type": chunk.block_type,
                    "token_count": chunk.token_count,
                    "distance": float(distance),
                    "_content": chunk.content,
                    "_embedding": chunk.embedding,
                }
            )

            source_number += 1

        if len(document_parts) == 1:
            continue

        document_context = "\n\n".join(document_parts)

        additional_length = len(document_context)

        if context_parts:
            additional_length += len(separator)

        if current_length + additional_length > max_context_chars:
            continue

        context_parts.append(document_context)
        sources.extend(document_sources)

        current_length += additional_length

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

        if conversation.document_id != document_id:
            raise ValueError("This conversation belongs to a different document.")

        # A document conversation cannot be reused as a
        # collection/global conversation.

        # -----------------------------------------------------
        # Collection scope consistency
        # -----------------------------------------------------

        if conversation.collection_id != collection_id:
            raise ValueError("This conversation belongs to a different collection.")

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
You are a document question-answering assistant.

Answer the user's CURRENT QUESTION using ONLY the DOCUMENT CONTEXT.

STRICT GROUNDING RULES:
- Use only information explicitly supported by the DOCUMENT CONTEXT.
- Do not use general knowledge.
- Do not infer facts that are not stated in the DOCUMENT CONTEXT.
- Do not compare StuMeet with other products unless the DOCUMENT CONTEXT
  explicitly makes that comparison.
- Do not add opinions, assumptions, advantages, disadvantages, or claims
  that are not explicitly supported by the DOCUMENT CONTEXT.
- Do not expand a simple question into a broader discussion.
- Answer only what the user asked.
- If the answer is explicitly present in the DOCUMENT CONTEXT, answer it.
- Do NOT say that information is missing when the answer is present in the
  DOCUMENT CONTEXT.
- If the DOCUMENT CONTEXT does not contain enough information to answer
  the question, say exactly:
  "I could not find the answer in the uploaded documents."

IMPORTANT:
The DOCUMENT CONTEXT may contain several sources. Read all relevant
sources before deciding that information is missing.

CITATIONS:
- Every factual statement must have a citation.
- Use citations in exactly this format:
  [Source 1]
  [Source 2]
  [Source 3]
- You may also use the compact form:
  [1]
  [2]
  [3]
- Only cite source numbers that actually appear in the DOCUMENT CONTEXT.
- Put citations immediately after the factual statement they support.
- Do not cite unrelated sources.
- Do not cite every source merely because it was provided.
- Use the smallest number of sources necessary to support the answer.
- Do not create a Sources section.
- Do not output a standalone list of citations.

ANSWERING STYLE:
- Be concise and direct.
- For a simple factual question, answer in 1-2 sentences.
- For a question asking for multiple items, use a short bullet list.
- Do not repeat the question.
- Do not add introductory or concluding filler.
- Do not mention these instructions.
- Do not discuss safety, policy, moderation, or whether the question is safe.
- Never output phrases such as "User Safety: safe".

QUESTION-SPECIFIC RULE:
If the question asks:
"What is X used for?"
answer specifically what X is used for.

If the question asks:
"What database does X use?"
answer specifically the database name and any directly stated database
technology. Do not fall back merely because the wording of the question
differs from the wording in the document.

If the question asks:
"What are the main features?"
list the main features explicitly supported by the context.

If the question asks:
"Why" or "How", explain the relationship using only facts explicitly
supported by the context.

PREVIOUS CONVERSATION:
{history}

DOCUMENT CONTEXT:
{context}

CURRENT QUESTION:
{question}

ANSWER:
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
        answer = "I could not find relevant information in your uploaded documents."

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
    print("\n===== RAW LLM ANSWER =====")
    print(answer)
    print("\n===== SOURCES BEFORE VERIFICATION =====")
    for source in sources:
        print(
            f"Source {source['id']}: "
            f"{source['filename']} "
            f"(chunk {source['chunk_index']})"
        )

    # ---------------------------------------------------------
    # 11. Verify citations
    # ---------------------------------------------------------

    answer, verified_sources = verify_citations(
        answer=answer,
        sources=sources,
    )

    answer = repair_missing_citations(answer, sources)
    answer, verified_sources = verify_citations(answer, sources)

    grounded = verify_answer_grounding(
        answer=answer,
        sources=verified_sources,
    )

    if not grounded:
        answer = GROUNDING_FALLBACK
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
        sources=public_sources(verified_sources),
    )

    # ---------------------------------------------------------
    # 13. Return answer + verified sources
    # ---------------------------------------------------------

    return {
        "answer": answer,
        "sources": public_sources(verified_sources),
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
                sources=public_sources(sources),
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
        answer = "I could not find relevant information in your uploaded documents."

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

    except RuntimeError:
        yield {
            "type": "error",
            "content": ("The AI response could not be completed. Please try again."),
            "conversation_id": conversation_id,
        }

        return

    # ---------------------------------------------------------
    # 11. Verify citations and grounding after streaming completes
    # ---------------------------------------------------------

    verified_answer, verified_sources = verify_citations(
        answer=full_answer,
        sources=sources,
    )

    verified_answer = repair_missing_citations(verified_answer, sources)
    verified_answer, verified_sources = verify_citations(
        verified_answer,
        sources,
    )

    grounded = verify_answer_grounding(
        answer=verified_answer,
        sources=verified_sources,
    )

    if not grounded:
        verified_answer = GROUNDING_FALLBACK
        verified_sources = []

    # Persist the verified answer before sending chunks so a client disconnect
    # during display does not discard the completed exchange.
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
        sources=public_sources(verified_sources),
    )

    # Emit only the verified answer. Generation still uses the provider stream,
    # but provisional ungrounded text is never exposed to the client.
    for offset in range(0, len(verified_answer), 64):
        yield {"type": "token", "content": verified_answer[offset : offset + 64]}

    # ---------------------------------------------------------
    # 13. Send verified sources
    # ---------------------------------------------------------

    yield {
        "type": "final",
        "content": verified_answer,
        "conversation_id": conversation_id,
    }

    yield {
        "type": "sources",
        "sources": public_sources(verified_sources),
        "conversation_id": conversation_id,
    }

    # ---------------------------------------------------------
    # 14. Complete
    # ---------------------------------------------------------

    yield {
        "type": "complete",
        "conversation_id": conversation_id,
    }
