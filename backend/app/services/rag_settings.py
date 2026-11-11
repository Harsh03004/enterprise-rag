from copy import deepcopy

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.app_setting import AppSetting

CONFIG_KEY = "rag"
# Questions whose best chunk scores below this are refused before any LLM
# call. Calibrated on the evaluation set (gemini-3.1-flash-lite baseline):
# answerable questions scored >= -1.19, off-topic ones down to -10.9, so -3
# refuses clearly unrelated questions while keeping a ~1.8 margin.
DEFAULT_MINIMUM_SCORE = -3.0
PROVIDERS = frozenset({"ollama", "gemini", "openrouter"})
DEFAULTS = {
    "provider": settings.llm_provider.lower(),
    "fallback_provider": "",
    "ollama_model": settings.ollama_model,
    "gemini_model": settings.gemini_model,
    "openrouter_model": settings.openrouter_model,
    "retrieval_top_k": 5,
    "candidate_multiplier": 4,
    "rerank_limit": 5,
    "minimum_reranker_score": DEFAULT_MINIMUM_SCORE,
    "max_context_chars": 30000,
    "temperature": 0.1,
    "max_output_tokens": 800,
    "chunk_size": 400,
    "chunk_overlap": 50,
    "input_cost_per_1k_tokens_usd": 0.0,
    "output_cost_per_1k_tokens_usd": 0.0,
    "query_cache_enabled": True,
    "query_cache_ttl_seconds": 300,
    "embedding_model": settings.embedding_model,
    "embedding_dimensions": 384,
}


def validate_config(candidate: dict) -> dict:
    if not isinstance(candidate, dict):
        raise ValueError("RAG settings must be a JSON object.")
    unknown = set(candidate) - set(DEFAULTS)
    if unknown:
        raise ValueError(f"Unsupported setting(s): {', '.join(sorted(unknown))}.")
    config = {**DEFAULTS, **candidate}
    if (
        not isinstance(config["provider"], str)
        or config["provider"] not in PROVIDERS
    ):
        raise ValueError("Provider must be ollama, gemini or openrouter.")
    fallback = config["fallback_provider"]
    if (
        not isinstance(fallback, str)
        or fallback not in {"", *PROVIDERS}
        or fallback == config["provider"]
    ):
        raise ValueError("Fallback provider must be empty or differ from the primary provider.")
    for name, minimum, maximum in (
        ("retrieval_top_k", 1, 20),
        ("candidate_multiplier", 1, 10),
        ("rerank_limit", 1, 20),
        ("max_context_chars", 1000, 100000),
        ("chunk_size", 100, 2000),
        ("query_cache_ttl_seconds", 1, 3600),
    ):
        value = config[name]
        if isinstance(value, bool) or not isinstance(value, int) or not minimum <= value <= maximum:
            raise ValueError(f"{name} must be an integer between {minimum} and {maximum}.")
    if not isinstance(config["query_cache_enabled"], bool):
        raise ValueError("query_cache_enabled must be true or false.")
    overlap = config["chunk_overlap"]
    if isinstance(overlap, bool) or not isinstance(overlap, int) or not 0 <= overlap < config["chunk_size"]:
        raise ValueError("chunk_overlap must be non-negative and smaller than chunk_size.")
    score = config["minimum_reranker_score"]
    if isinstance(score, bool) or not isinstance(score, int | float) or not -100 <= score <= 100:
        raise ValueError("minimum_reranker_score must be between -100 and 100.")
    temperature = config["temperature"]
    if isinstance(temperature, bool) or not isinstance(temperature, int | float) or not 0 <= temperature <= 2:
        raise ValueError("temperature must be between 0 and 2.")
    tokens = config["max_output_tokens"]
    if isinstance(tokens, bool) or not isinstance(tokens, int) or not 64 <= tokens <= 8192:
        raise ValueError("max_output_tokens must be an integer between 64 and 8192.")
    for name in ("input_cost_per_1k_tokens_usd", "output_cost_per_1k_tokens_usd"):
        value = config[name]
        if isinstance(value, bool) or not isinstance(value, int | float) or not 0 <= value <= 1000:
            raise ValueError(f"{name} must be between 0 and 1000 USD per 1K tokens.")
    for name in ("ollama_model", "gemini_model", "openrouter_model"):
        value = config[name]
        if not isinstance(value, str) or not value.strip() or len(value) > 255:
            raise ValueError(f"{name} must be a non-empty string of at most 255 characters.")
        config[name] = value.strip()
    # Embedding dimensions and model are locked because changing either requires
    # re-embedding every chunk and a matching pgvector migration.
    if (
        not isinstance(config["embedding_model"], str)
        or config["embedding_model"]
        not in {
            "BAAI/bge-small-en-v1.5",
            "sentence-transformers/all-MiniLM-L6-v2",
        }
    ):
        raise ValueError("Embedding model must be a supported 384-dimensional model.")
    if config["embedding_model"] != settings.embedding_model:
        raise ValueError("Set EMBEDDING_MODEL in deployment configuration and reindex all documents to change it.")
    config["embedding_dimensions"] = DEFAULTS["embedding_dimensions"]
    return config


def get_rag_config(db: Session) -> dict:
    saved = db.get(AppSetting, CONFIG_KEY)
    value = deepcopy(saved.value) if saved else deepcopy(DEFAULTS)
    value["embedding_model"] = settings.embedding_model
    return validate_config(value)


def save_rag_config(db: Session, updates: dict) -> dict:
    if not isinstance(updates, dict):
        raise ValueError("RAG settings updates must be a JSON object.")
    if "embedding_model" in updates and updates["embedding_model"] != settings.embedding_model:
        raise ValueError("Embedding model is configured through EMBEDDING_MODEL; changing it requires a document reindex.")
    existing = db.get(AppSetting, CONFIG_KEY)
    merged = {**(existing.value if existing else DEFAULTS), **updates}
    merged["embedding_model"] = settings.embedding_model
    config = validate_config(merged)
    if existing is None:
        existing = AppSetting(key=CONFIG_KEY, value=config)
        db.add(existing)
    else:
        existing.value = config
    db.commit()
    return config
