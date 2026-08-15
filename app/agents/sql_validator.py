import re

from app.core.errors import BadRequest

_FORBIDDEN = ("insert", "update", "delete", "merge", "drop", "alter", "create", "truncate")


def validate_and_fix(sql: str, *, allowed_tables: set[str], max_rows: int) -> str:
    """Reject unsafe SQL and enforce a LIMIT. Returns the final SQL to run."""
    cleaned = sql.strip().rstrip(";")
    low = cleaned.lower()

    if not low.startswith("select"):
        raise BadRequest("generated query is not a SELECT")
    if any(re.search(rf"\b{kw}\b", low) for kw in _FORBIDDEN):
        raise BadRequest("generated query contains a forbidden keyword")

    referenced = set(re.findall(r"\bfrom\s+([a-z0-9_\.]+)|\bjoin\s+([a-z0-9_\.]+)", low))
    flat = {t for pair in referenced for t in pair if t}
    unknown = {t.split(".")[-1] for t in flat} - {t.lower() for t in allowed_tables}
    if allowed_tables and unknown:
        raise BadRequest(f"query references unknown tables: {sorted(unknown)}")

    if not re.search(r"\blimit\s+\d+\b", low):
        cleaned = f"{cleaned} LIMIT {max_rows}"
    return cleaned
