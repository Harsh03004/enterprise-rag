from app.services.llm import generate_response


def rewrite_query(
    question: str,
    conversation_history: str,
) -> str:
    """
    Rewrite a user's question into a standalone search query.

    The rewritten query is used only for document retrieval.
    The original question is still used when generating the answer.
    """

    if not conversation_history.strip():
        return question

    prompt = f"""
You rewrite user questions for document retrieval.

Your task is to produce ONE standalone search query that captures
the information needed to answer the user's current question.

Use the conversation history to resolve references such as:
- "it"
- "this"
- "that"
- "the project"
- "the document"
- "they"
- "when was it"

Rules:
- Preserve the user's original intent.
- Include important names, terms, entities, and context from the conversation.
- Do not answer the question.
- Do not add information that is not present in the conversation.
- If the question is already standalone, return it essentially unchanged.
- Return ONLY the rewritten search query.
- Do not use quotes.
- Do not explain your reasoning.

Conversation history:
{conversation_history}

Current question:
{question}

Search query:
"""

    rewritten = generate_response(prompt).strip()

    if not rewritten:
        return question

    return rewritten