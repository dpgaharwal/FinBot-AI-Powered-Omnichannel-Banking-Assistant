import redis
import json
from app.core.config import settings

# Redis singleton
r = redis.Redis(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    db=settings.REDIS_DB,
    decode_responses=True
)


def ping():
    return r.ping()


# Session cache
def save_session(session_id: str, state: dict, ttl_seconds: int = 3600):
    serializable = {
        k: v for k, v in state.items()
        if k not in ["messages"]
    }
    r.setex(f"session:{session_id}", ttl_seconds, json.dumps(serializable, default=str))


def get_session(session_id: str) -> dict | None:
    data = r.get(f"session:{session_id}")
    return json.loads(data) if data else None


def delete_session(session_id: str):
    r.delete(f"session:{session_id}")


# Idempotency keys — prevent duplicate EMI payments
def set_idempotency_key(key: str, value: str, ttl_seconds: int = 86400) -> bool:
    return r.set(f"idempotency:{key}", value, nx=True, ex=ttl_seconds)


def get_idempotency_key(key: str) -> str | None:
    return r.get(f"idempotency:{key}")


# Rate limiting
def is_rate_limited(user_id: str, action: str, limit: int, window_seconds: int) -> bool:
    key = f"ratelimit:{action}:{user_id}"
    pipe = r.pipeline()
    pipe.incr(key)
    pipe.expire(key, window_seconds)
    results = pipe.execute()
    return results[0] > limit


# Conversation cache — cache frequent policy queries
def cache_rag_response(query: str, response: str, ttl_seconds: int = 1800):
    r.setex(f"rag:{hash(query)}", ttl_seconds, response)


def get_cached_rag_response(query: str) -> str | None:
    return r.get(f"rag:{hash(query)}")