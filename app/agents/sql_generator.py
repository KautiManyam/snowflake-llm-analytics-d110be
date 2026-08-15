from app.db.models import KnowledgeRecord
from app.schemas.llm import SqlGeneration
from app.services.llm_client import generate_sql


def build_context(records: list[KnowledgeRecord]) -> str:
    """Render retrieved schema/doc records into a prompt-ready block."""
    schema = [r.content for r in records if r.kind == "schema"]
    docs = [f"- {r.title}: {r.content}" for r in records if r.kind == "doc"]
    parts = []
    if schema:
        parts.append("SCHEMA:\n" + "\n".join(schema))
    if docs:
        parts.append("DEFINITIONS:\n" + "\n".join(docs))
    return "\n\n".join(parts)


def generate(question: str, records: list[KnowledgeRecord]) -> SqlGeneration:
    context = build_context(records)
    try:
        return generate_sql(question, context)
    except ValueError:
        # One stricter retry before giving up.
        return generate_sql(question, context, strict=True)
