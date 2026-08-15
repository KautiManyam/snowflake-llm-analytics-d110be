import hashlib
import json
import os
import re
from typing import Any, Optional

import redis

_redis = redis.Redis.from_url(os.environ.get("REDIS_URL", "redis://localhost:6379/0"))

CONTEXT_TTL = 3600   # schema/context changes rarely
RESULT_TTL = 60      # results are time-sensitive


def _normalize(question: str) -> str:
    return re.sub(r"\s+", " ", question.strip().lower())


def context_key(dataset_id: str) -> str:
    return f"ctx:{dataset_id}"


def result_key(dataset_id: str, question: str) -> str:
    digest = hashlib.sha256(_normalize(question).encode()).hexdigest()[:16]
    return f"res:{dataset_id}:{digest}"


def get_json(key: str) -> Optional[Any]:
    raw = _redis.get(key)
    return json.loads(raw) if raw else None


def set_json(key: str, value: Any, ttl: int) -> None:
    _redis.set(key, json.dumps(value), ex=ttl)
