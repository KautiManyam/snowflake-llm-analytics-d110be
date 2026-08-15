from sqlalchemy.orm import Session

from app.db.models import Dataset, KnowledgeRecord


def ingest_doc(session: Session, dataset: Dataset, title: str, body: str) -> KnowledgeRecord:
    """Store a curated documentation snippet (e.g. a metric definition)."""
    record = KnowledgeRecord(
        dataset_id=dataset.id,
        kind="doc",
        title=title.strip(),
        content=body.strip(),
    )
    session.add(record)
    session.flush()
    return record
