from collections.abc import Generator

from openai import OpenAI

from app.core.config import settings


client = OpenAI(
    api_key=settings.openrouter_api_key,
    base_url="https://openrouter.ai/api/v1",
)

MODEL = "openrouter/free"


def generate_response(prompt: str) -> str:
    response = client.chat.completions.create(
        model=MODEL,
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
        stream = client.chat.completions.create(
            model=MODEL,
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