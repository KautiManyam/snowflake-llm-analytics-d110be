from sqlalchemy.orm import Session

from app.db.models import Dataset, KnowledgeRecord
from app.services.snowflake_client import get_snowflake_client


def ingest_schema(session: Session, dataset: Dataset) -> int:
    """Snapshot a dataset's table/column schema into knowledge records."""
    client = get_snowflake_client()
    sql = (
        "SELECT table_name, column_name, data_type "
        f"FROM {dataset.sf_database}.information_schema.columns "
        f"WHERE table_schema = '{dataset.sf_schema}' "
        "ORDER BY table_name, ordinal_position"
    )
    _, rows = client.run_select(sql, limit=1000)

    by_table: dict[str, list[str]] = {}
    for r in rows:
        by_table.setdefault(r["TABLE_NAME"], []).append(
            f"{r['COLUMN_NAME']} {r['DATA_TYPE']}"
        )

    count = 0
    for table, columns in by_table.items():
        session.add(
            KnowledgeRecord(
                dataset_id=dataset.id,
                kind="schema",
                title=table,
                content=f"TABLE {table} ({', '.join(columns)})",
            )
        )
        count += 1
    return count
