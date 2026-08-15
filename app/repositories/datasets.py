from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Dataset


class DatasetRepo:
    def __init__(self, session: Session):
        self._session = session

    def by_name(self, name: str) -> Dataset | None:
        stmt = select(Dataset).where(Dataset.name == name)
        return self._session.execute(stmt).scalar_one_or_none()
