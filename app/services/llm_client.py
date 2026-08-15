import json

from openai import OpenAI, OpenAIError

from app.core.errors import LLMError
from app.schemas.llm import SqlGeneration

_client = OpenAI()

_SYSTEM = (
    "You translate analytics questions into a single read-only Snowflake SELECT. "
    "Use ONLY the tables and columns in the provided context. "
    "Never write INSERT, UPDATE, DELETE, MERGE, or DDL. "
    "Respond with the required JSON schema."
)


def generate_sql(question: str, context: str, *, strict: bool = False) -> SqlGeneration:
    system = _SYSTEM
    if strict:
        system += " The previous attempt was invalid. Return ONLY a valid SELECT and valid JSON."

    try:
        completion = _client.chat.completions.parse(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {question}"},
            ],
            response_format=SqlGeneration,
            temperature=0,
        )
    except OpenAIError as exc:
        # Operational detail stays in logs; the client sees a safe message.
        raise LLMError() from exc

    parsed = completion.choices[0].message.parsed
    if parsed is None:
        raise ValueError("model returned no structured output")
    return parsed
