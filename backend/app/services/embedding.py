from functools import lru_cache

from sentence_transformers import SentenceTransformer

from app.core.config import settings
from app.services.cache import cache_get, cache_key, cache_set

MODEL_NAME = settings.embedding_model


@lru_cache(maxsize=2)
def _load_model(model_name: str) -> SentenceTransformer:
    model = SentenceTransformer(model_name)
    dimensions = model.get_sentence_embedding_dimension()
    if dimensions != 384:
        raise ValueError(
            f"Embedding model {model_name} returns {dimensions} dimensions; this database requires 384."
        )
    return model


def generate_embedding(text: str, model_name: str = MODEL_NAME) -> list[float]:
    return generate_embeddings([text], model_name=model_name)[0]


def generate_embeddings(
    texts: list[str],
    model_name: str = MODEL_NAME,
) -> list[list[float]]:
    if not texts:
        return []

    output: list[list[float] | None] = [None] * len(texts)
    missing_indices: list[int] = []
    missing_texts: list[str] = []
    keys = [cache_key("embedding", {"model": model_name, "text": text}) for text in texts]
    for index, key in enumerate(keys):
        cached = cache_get(key)
        if isinstance(cached, list) and len(cached) == 384:
            try:
                output[index] = [float(value) for value in cached]
                continue
            except (TypeError, ValueError):
                pass
        missing_indices.append(index)
        missing_texts.append(texts[index])

    if missing_texts:
        embeddings = _load_model(model_name).encode(missing_texts, normalize_embeddings=True).tolist()
        for index, embedding in zip(missing_indices, embeddings, strict=True):
            vector = [float(value) for value in embedding]
            output[index] = vector
            cache_set(keys[index], vector, ttl_seconds=86400)

    return [embedding or [] for embedding in output]
