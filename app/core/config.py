from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Snowflake
    snowflake_account: str = ""
    snowflake_user: str = ""
    snowflake_password: str = ""
    snowflake_warehouse: str = "COMPUTE_WH"
    snowflake_database: str = "ANALYTICS"
    snowflake_schema: str = "PUBLIC"

    # Guardrails
    max_rows: int = 1000
    query_timeout_seconds: int = 30

    class Config:
        env_prefix = ""
        env_file = ".env"


@lru_cache
def get_settings() -> Settings:
    return Settings()
