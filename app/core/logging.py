import json
import logging
import sys
import time
from contextlib import contextmanager
from typing import Iterator


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "level": record.levelname,
            "message": record.getMessage(),
            "request_id": getattr(record, "request_id", None),
        }
        if record.__dict__.get("extra_fields"):
            payload.update(record.__dict__["extra_fields"])
        return json.dumps(payload)


def configure_logging() -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(logging.INFO)


logger = logging.getLogger("analytics")


@contextmanager
def timed(bucket: dict[str, int], name: str) -> Iterator[None]:
    """Record elapsed milliseconds for `name` into `bucket`."""
    start = time.perf_counter()
    try:
        yield
    finally:
        bucket[name] = int((time.perf_counter() - start) * 1000)
