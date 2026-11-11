import hashlib
import json
from typing import Any

from redis import Redis
from redis.exceptions import RedisError

from app.core.config import settings

_client = Redis.from_url(settings.redis_url, decode_responses=True)


def cache_key(namespace: str, value: Any) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)
    digest = hashlib.sha256(encoded.encode("utf-8")).hexdigest()
    return f"enterprise-rag:{namespace}:{digest}"


def cache_get(key: str) -> Any | None:
    try:
        raw = _client.get(key)
        return json.loads(raw) if raw is not None else None
    except (RedisError, json.JSONDecodeError, TypeError, ValueError):
        return None


def cache_set(key: str, value: Any, ttl_seconds: int) -> None:
    try:
        _client.setex(key, max(1, ttl_seconds), json.dumps(value, ensure_ascii=False))
    except (RedisError, TypeError, ValueError):
        # Cache outages must not affect answers or ingestion.
        return
