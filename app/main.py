import uuid

from fastapi import Depends, FastAPI, Request
from fastapi.responses import JSONResponse

from app.agents.graph import AGENT
from app.core.errors import ApiError, error_body
from app.core.logging import configure_logging, logger, timed
from app.db.models import User
from app.db.session import db_session
from app.repositories.datasets import DatasetRepo
from app.repositories.knowledge import KnowledgeRepo
from app.repositories.query_logs import QueryLogRepo
from app.schemas.query import AskRequest, AskResponse, VizSpec
from app.security.auth import require_user

configure_logging()
app = FastAPI(title="Snowflake LLM Analytics Agent")


@app.exception_handler(ApiError)
async def handle_api_error(request: Request, exc: ApiError) -> JSONResponse:
    request_id = getattr(request.state, "request_id", None)
    logger.warning(
        "request.failed",
        extra={"request_id": request_id, "extra_fields": {"code": exc.code, "status": exc.status_code}},
    )
    return JSONResponse(
        status_code=exc.status_code,
        content=error_body(exc.code, exc.message, request_id),
    )


@app.exception_handler(Exception)
async def handle_unexpected(request: Request, exc: Exception) -> JSONResponse:
    request_id = getattr(request.state, "request_id", None)
    logger.error("request.unhandled", extra={"request_id": request_id, "extra_fields": {"error": str(exc)}})
    return JSONResponse(status_code=500, content=error_body("internal_error", "internal server error", request_id))


@app.post("/ask", response_model=AskResponse)
async def ask(req: AskRequest, user: User = Depends(require_user)) -> AskResponse:
    request_id = str(uuid.uuid4())
    timings: dict[str, int] = {}

    with db_session() as session:
        dataset = DatasetRepo(session).by_name(req.dataset)
        if dataset is None:
            raise NotFoundDataset(req.dataset)
        log = QueryLogRepo(session).start(request_id, user.id, dataset.id, req.question)

        try:
            with timed(timings, "retrieve_ms"):
                records = KnowledgeRepo(session).retrieve(dataset.id, req.question)
            with timed(timings, "agent_ms"):
                state = AGENT.invoke(
                    {"question": req.question, "dataset_id": dataset.id, "records": records}
                )
        except ApiError:
            QueryLogRepo(session).finish(
                log, status="failed", final_sql="", duration_ms=sum(timings.values()), row_count=0
            )
            raise

        QueryLogRepo(session).finish(
            log,
            status="success",
            final_sql=state["final_sql"],
            duration_ms=sum(timings.values()),
            row_count=len(state["rows"]),
        )

    logger.info(
        "ask.completed",
        extra={"request_id": request_id, "extra_fields": {**timings, "rows": len(state["rows"])}},
    )
    return AskResponse(
        request_id=request_id,
        answer=state["answer"],
        generated_sql=state["generated_sql"],
        final_sql=state["final_sql"],
        columns=state["columns"],
        rows=state["rows"],
        viz=VizSpec(),
    )


from app.core.errors import NotFound


class NotFoundDataset(NotFound):
    def __init__(self, name: str):
        super().__init__(f"unknown dataset: {name}")
