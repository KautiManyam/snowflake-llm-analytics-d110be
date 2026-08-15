from typing import Any

from app.schemas.query import VizSpec


def _is_numeric(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def recommend(columns: list[str], rows: list[dict[str, Any]]) -> VizSpec:
    """Pick a chart from the result shape. Heuristic-first, UI-agnostic."""
    if not rows or not columns:
        return VizSpec(chart="table")

    sample = rows[0]
    numeric = [c for c in columns if _is_numeric(sample.get(c))]
    categorical = [c for c in columns if c not in numeric]

    # One category + one measure → bar. A time-like category → line.
    if len(numeric) == 1 and len(categorical) == 1:
        cat = categorical[0]
        chart = "line" if any(k in cat.lower() for k in ("date", "month", "day", "time")) else "bar"
        return VizSpec(chart=chart, x=cat, y=numeric[0])

    return VizSpec(chart="table")
