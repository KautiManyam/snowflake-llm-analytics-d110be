from sqlalchemy.orm import Session

from app.db.models import QueryLog


class QueryLogRepo:
    def __init__(self, session: Session):
        self._session = session

    def start(self, request_id: str, user_id: str, dataset_id: str | None, question: str) -> QueryLog:
        log = QueryLog(
            request_id=request_id,
            user_id=user_id,
            dataset_id=dataset_id,
            question=question,
            status="pending",
        )
        self._session.add(log)
        self._session.flush()
        return log

    def finish(self, log: QueryLog, *, status: str, final_sql: str, duration_ms: int, row_count: int) -> None:
        log.status = status
        log.final_sql = final_sql
        log.duration_ms = duration_ms
        log.row_count = row_count
