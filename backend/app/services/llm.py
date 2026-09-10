from collections.abc import Generator

from openai import OpenAI

from app.core.config import settings


GEMINI_BASE_URL = (
    "https://generativelanguage.googleapis.com/v1beta/openai/"
)

OLLAMA_BASE_URL = "http://localhost:11434/v1"


def _get_client() -> tuple[OpenAI, str]:
    """
    Return the configured LLM client and model.

    Supported providers:
    - gemini
    - ollama
    """

    provider = settings.llm_provider.lower()

    if provider == "ollama":
        return (
            OpenAI(
                api_key="ollama",
                base_url=OLLAMA_BASE_URL,
            ),
            settings.ollama_model,
        )

    if provider == "gemini":
        return (
            OpenAI(
                api_key=settings.gemini_api_key,
                base_url=GEMINI_BASE_URL,
            ),
            settings.gemini_model,
        )

    raise ValueError(
        f"Unsupported LLM provider: {settings.llm_provider}"
    )


def generate_response(prompt: str) -> str:
    client, model = _get_client()

    response = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
    )

    return response.choices[0].message.content or ""


def stream_response(prompt: str) -> Generator[str, None, None]:
    """
    Stream an LLM response token by token.

    The function yields only non-empty text content so callers
    can forward the chunks directly to the frontend.
    """

    try:
        client, model = _get_client()

        stream = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            stream=True,
        )

        for chunk in stream:
            if not chunk.choices:
                continue

            delta = chunk.choices[0].delta

            if delta is None:
                continue

            content = delta.content

            if content:
                yield content

    except Exception as exc:
        raise RuntimeError(
            f"LLM streaming failed: {exc}"
        ) from exc