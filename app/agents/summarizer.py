from typing import Any

from app.schemas.query import VizSpec
from app.services import viz


def summarize(question: str, columns: list[str], rows: list[dict[str, Any]]) -> str:
    """Deterministic natural-language summary of a result set."""
    if not rows:
        return f"No rows matched: {question}"

    n = len(rows)
    lead = f"Returned {n} row{'s' if n != 1 else ''} with columns {', '.join(columns)}."
    numeric = [c for c in columns if isinstance(rows[0].get(c), (int, float))]
    if numeric:
        col = numeric[0]
        total = sum(float(r[col]) for r in rows if r.get(col) is not None)
        lead += f" Total {col} across the result is {total:,.2f}."
    return lead


def recommend_viz(columns: list[str], rows: list[dict[str, Any]]) -> VizSpec:
    return viz.recommend(columns, rows)
