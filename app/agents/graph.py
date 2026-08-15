from typing import Any, TypedDict

from langgraph.graph import END, START, StateGraph

from app.agents.sql_generator import generate
from app.agents.sql_validator import validate_and_fix
from app.agents.summarizer import summarize
from app.core.config import get_settings
from app.db.models import KnowledgeRecord
from app.services import cache
from app.services.snowflake_client import get_snowflake_client


class AgentState(TypedDict, total=False):
    question: str
    dataset_id: str
    records: list[KnowledgeRecord]
    generated_sql: str
    final_sql: str
    columns: list[str]
    rows: list[dict[str, Any]]
    answer: str
    cached: bool


def _cache_lookup_node(state: AgentState) -> AgentState:
    key = cache.result_key(state["dataset_id"], state["question"])
    hit = cache.get_json(key)
    if hit:
        return {**hit, "cached": True}
    return {"cached": False}


def _generate_node(state: AgentState) -> AgentState:
    if state.get("cached"):
        return {}
    gen = generate(state["question"], state["records"])
    return {"generated_sql": gen.sql}


def _validate_node(state: AgentState) -> AgentState:
    if state.get("cached"):
        return {}
    allowed = {r.title for r in state["records"] if r.kind == "schema"}
    final_sql = validate_and_fix(
        state["generated_sql"],
        allowed_tables=allowed,
        max_rows=get_settings().max_rows,
    )
    return {"final_sql": final_sql}


def _execute_node(state: AgentState) -> AgentState:
    if state.get("cached"):
        return {}
    columns, rows = get_snowflake_client().run_select(state["final_sql"], limit=get_settings().max_rows)
    return {"columns": columns, "rows": rows}


def _summarize_node(state: AgentState) -> AgentState:
    if state.get("cached"):
        return {}
    answer = summarize(state["question"], state["columns"], state["rows"])
    payload = {
        "generated_sql": state["generated_sql"],
        "final_sql": state["final_sql"],
        "columns": state["columns"],
        "rows": state["rows"],
        "answer": answer,
    }
    cache.set_json(
        cache.result_key(state["dataset_id"], state["question"]),
        payload,
        cache.RESULT_TTL,
    )
    return {"answer": answer}


def build_graph():
    graph = StateGraph(AgentState)
    graph.add_node("cache_lookup", _cache_lookup_node)
    graph.add_node("generate", _generate_node)
    graph.add_node("validate", _validate_node)
    graph.add_node("execute", _execute_node)
    graph.add_node("summarize", _summarize_node)

    graph.add_edge(START, "cache_lookup")
    graph.add_edge("cache_lookup", "generate")
    graph.add_edge("generate", "validate")
    graph.add_edge("validate", "execute")
    graph.add_edge("execute", "summarize")
    graph.add_edge("summarize", END)
    return graph.compile()


AGENT = build_graph()
