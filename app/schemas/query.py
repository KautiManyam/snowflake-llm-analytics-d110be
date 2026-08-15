from typing import Any, Literal, Optional

from pydantic import BaseModel, Field


class AskRequest(BaseModel):
    """What a client sends to ask an analytics question."""

    question: str = Field(..., min_length=1, max_length=2000)
    dataset: str = Field("default", description="Logical dataset name to query")
    limit: int = Field(100, ge=1, le=1000, description="Max rows to return")


class VizSpec(BaseModel):
    """A UI-agnostic visualization recommendation."""

    chart: Literal["table", "bar", "line"] = "table"
    x: Optional[str] = None
    y: Optional[str] = None


class AskResponse(BaseModel):
    """The structured answer returned to the client."""

    request_id: str
    answer: str
    generated_sql: str
    final_sql: str
    columns: list[str] = []
    rows: list[dict[str, Any]] = []
    viz: VizSpec = VizSpec()
