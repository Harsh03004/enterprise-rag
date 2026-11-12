from collections.abc import Generator
from contextvars import ContextVar

import httpx
from openai import OpenAI

from app.core.config import settings

GEMINI_BASE_URL = (
    "https://generativelanguage.googleapis.com/v1beta/openai/"
)
# Unreachable providers fail within seconds (connect timeout) while slow
# generations, e.g. a CPU-only local model, still get time to finish.
_TIMEOUT = httpx.Timeout(settings.llm_timeout_seconds, connect=5.0)
_LAST_USED: ContextVar[tuple[str, str] | None] = ContextVar("llm_last_used", default=None)


def get_last_used_provider() -> tuple[str, str] | None:
    return _LAST_USED.get()


def reset_last_used_provider() -> None:
    _LAST_USED.set(None)


def _provider_failure_hint(provider: str) -> str:
    if provider == "ollama":
        return "Check OLLAMA_BASE_URL, confirm Ollama is reachable, and verify that the model is installed."
    if provider == "gemini":
        return "Check GEMINI_API_KEY, network access, and the configured Gemini model."
    if provider == "openrouter":
        return (
            "Check OPENROUTER_API_KEY and the configured OpenRouter model; free models are "
            "rate limited (per minute and per day)."
        )
    return "Check the provider configuration and network access."


def _messages(prompt: str, system_prompt: str | None, model: str) -> list[dict]:
    """Chat messages for one request.

    Qwen3 models "think" before answering by default. The hidden reasoning
    counts against max_tokens and can consume it entirely, leaving an empty
    answer (seen on most CPU-run cases). RAG answers are short lookups, so the
    documented /no_think switch is appended for these models.
    """
    if "qwen3" in model.lower():
        prompt = f"{prompt}\n/no_think"
    return ([{"role": "system", "content": system_prompt}] if system_prompt else []) + [
        {"role": "user", "content": prompt}
    ]


def _request_options(provider: str, model: str) -> dict:
    """Provider-specific request parameters.

    Gemini 2.5 Flash/Flash-Lite think by default; the hidden reasoning shares
    the max_tokens budget and costs quota. RAG answers are short lookups, so
    thinking is turned off where the API allows it (not possible for 2.5 Pro
    or Gemini 3 models).
    """
    name = model.lower()
    if provider == "gemini" and name.startswith("gemini-2.5") and "pro" not in name:
        return {"reasoning_effort": "none"}
    if provider == "gemini" and name.startswith("gemini-3"):
        # Thinking cannot be disabled on Gemini 3; use the smallest budget.
        return {"reasoning_effort": "low"}
    return {}


def _get_client(config: dict | None = None, provider: str | None = None) -> tuple[OpenAI, str]:
    """
    Return the configured LLM client and model.

    Supported providers:
    - gemini
    - ollama
    - openrouter
    """

    config = config or {}
    provider = (provider or str(config.get("provider", settings.llm_provider))).lower()

    if provider == "ollama":
        return (
            OpenAI(
                timeout=_TIMEOUT,
                api_key="ollama",
                # A local server that refuses or drops connections will not
                # recover within the retry window; fail fast instead.
                max_retries=1,
                base_url=settings.ollama_base_url,
            ),
            str(config.get("ollama_model", settings.ollama_model)),
        )

    if provider == "gemini":
        return (
            OpenAI(
                api_key=settings.gemini_api_key,
                base_url=GEMINI_BASE_URL,
                # Free-tier 429s are retried with backoff (honours Retry-After);
                # a stalled request fails after 90 s instead of the default 10 min.
                max_retries=3,
                timeout=httpx.Timeout(90.0, connect=5.0),
            ),
            str(config.get("gemini_model", settings.gemini_model)),
        )

    if provider == "openrouter":
        if not settings.openrouter_api_key:
            raise ValueError("OPENROUTER_API_KEY is not set.")
        return (
            OpenAI(
                api_key=settings.openrouter_api_key,
                base_url=settings.openrouter_base_url,
                # Free models return 429 under load; the client backs off and
                # honours Retry-After.
                max_retries=3,
                timeout=httpx.Timeout(90.0, connect=5.0),
            ),
            str(config.get("openrouter_model", settings.openrouter_model)),
        )

    raise ValueError(
        f"Unsupported LLM provider: {settings.llm_provider}"
    )


def generate_response(
    prompt: str,
    config: dict | None = None,
    system_prompt: str | None = None,
) -> str:
    config = config or {}
    providers = [str(config.get("provider", settings.llm_provider))]
    fallback = config.get("fallback_provider")
    if fallback and fallback not in providers:
        providers.append(str(fallback))
    last_error = None
    last_provider = providers[0]
    last_model = "unknown"
    for provider in providers:
        try:
            client, model = _get_client(config, provider)
            last_provider, last_model = provider, model
            response = client.chat.completions.create(
                model=model,
                messages=_messages(prompt, system_prompt, model),
                temperature=float(config.get("temperature", 0.1)),
                max_tokens=int(config.get("max_output_tokens", 800)),
                **_request_options(provider, model),
            )
            content = response.choices[0].message.content if response.choices else None
            if not isinstance(content, str) or not content.strip():
                raise ValueError("Provider returned an empty response.")
            _LAST_USED.set((provider, model))
            return content
        except Exception as exc:
            last_error = exc
    raise RuntimeError(
        f"LLM generation failed for {last_provider}/{last_model}: {last_error}. "
        f"{_provider_failure_hint(last_provider)}"
    ) from last_error


def stream_response(
    prompt: str,
    config: dict | None = None,
    system_prompt: str | None = None,
) -> Generator[str, None, None]:
    """
    Stream an LLM response token by token.

    The function yields only non-empty text content so callers
    can forward the chunks directly to the frontend.
    """

    config = config or {}
    primary = str(config.get("provider", settings.llm_provider))
    providers = [primary]
    fallback = config.get("fallback_provider")
    if fallback and fallback not in providers:
        providers.append(str(fallback))
    last_error = None
    last_provider = primary
    last_model = "unknown"
    for provider in providers:
        emitted = False
        try:
            client, model = _get_client(config, provider)
            last_provider, last_model = provider, model
            stream = client.chat.completions.create(
                model=model,
                messages=_messages(prompt, system_prompt, model),
                stream=True,
                temperature=float(config.get("temperature", 0.1)),
                max_tokens=int(config.get("max_output_tokens", 800)),
                **_request_options(provider, model),
            )
            for chunk in stream:
                if not chunk.choices:
                    continue
                delta = chunk.choices[0].delta
                content = delta.content if delta is not None else None
                if content:
                    emitted = True
                    yield content
            if not emitted:
                last_error = ValueError("Provider returned an empty response.")
                continue
            _LAST_USED.set((provider, model))
            return
        except Exception as exc:
            last_error = exc
            if emitted:
                break
    raise RuntimeError(
        f"LLM streaming failed for {last_provider}/{last_model}: {last_error}. "
        f"{_provider_failure_hint(last_provider)}"
    ) from last_error
