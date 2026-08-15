from typing import Optional


class ApiError(Exception):
    """An error that carries the HTTP status the client should see."""

    def __init__(self, status_code: int, message: str, code: str = "error"):
        super().__init__(message)
        self.status_code = status_code
        self.message = message
        self.code = code


class BadRequest(ApiError):
    def __init__(self, message: str = "bad request"):
        super().__init__(400, message, "bad_request")


class Unauthorized(ApiError):
    def __init__(self, message: str = "invalid or missing API key"):
        super().__init__(401, message, "unauthorized")


class NotFound(ApiError):
    def __init__(self, message: str = "not found"):
        super().__init__(404, message, "not_found")


class LLMError(ApiError):
    """The model failed to produce usable SQL after a retry."""

    def __init__(self, message: str = "could not generate a query for that question"):
        super().__init__(502, message, "llm_error")


class WarehouseError(ApiError):
    """Snowflake rejected or failed to execute the query."""

    def __init__(self, message: str = "the data warehouse could not run that query"):
        super().__init__(502, message, "warehouse_error")


def error_body(code: str, message: str, request_id: Optional[str] = None) -> dict:
    """The one JSON shape every error response uses."""
    body = {"error": {"code": code, "message": message}}
    if request_id:
        body["error"]["request_id"] = request_id
    return body
