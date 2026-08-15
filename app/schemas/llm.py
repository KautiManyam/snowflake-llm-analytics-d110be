from pydantic import BaseModel, Field


class SqlGeneration(BaseModel):
    """The structured result we require from the model."""

    sql: str = Field(..., description="A single read-only SELECT statement")
    explanation: str = Field(..., description="One-sentence plain-English explanation")
    tables_used: list[str] = Field(default_factory=list)
