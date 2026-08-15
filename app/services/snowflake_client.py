import datetime
import decimal
from typing import Any

from snowflake.snowpark import Session
from snowflake.snowpark.exceptions import SnowparkSQLException

from app.core.config import get_settings
from app.core.errors import BadRequest, WarehouseError


def _json_safe(value: Any) -> Any:
    """Normalize warehouse types into JSON-serializable values."""
    if isinstance(value, decimal.Decimal):
        return float(value)
    if isinstance(value, (datetime.date, datetime.datetime)):
        return value.isoformat()
    return value


class SnowflakeClient:
    def __init__(self) -> None:
        s = get_settings()
        self._session = Session.builder.configs(
            {
                "account": s.snowflake_account,
                "user": s.snowflake_user,
                "password": s.snowflake_password,
                "warehouse": s.snowflake_warehouse,
                "database": s.snowflake_database,
                "schema": s.snowflake_schema,
            }
        ).create()
        self._timeout = s.query_timeout_seconds

    def run_select(self, sql: str, limit: int) -> tuple[list[str], list[dict[str, Any]]]:
        """Execute a read-only SELECT, capped at `limit` rows."""
        stripped = sql.strip().rstrip(";")
        if not stripped.lower().startswith("select"):
            raise BadRequest("only SELECT statements may be executed")

        try:
            df = self._session.sql(stripped).limit(limit)
            with self._session.query_history():
                collected = df.collect(
                    statement_params={"STATEMENT_TIMEOUT_IN_SECONDS": self._timeout}
                )
        except SnowparkSQLException as exc:
            raise WarehouseError() from exc

        columns = [field.name for field in df.schema.fields]
        rows = [{c: _json_safe(row[c]) for c in columns} for row in collected]
        return columns, rows


_client: SnowflakeClient | None = None


def get_snowflake_client() -> SnowflakeClient:
    global _client
    if _client is None:
        _client = SnowflakeClient()
    return _client
