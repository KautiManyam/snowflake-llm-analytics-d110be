import re

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import KnowledgeRecord
from app.services import cache

_WORD = re.compile(r"[a-z0-9_]+")


def _tokens(text: str) -> set[str]:
    return set(_WORD.findall(text.lower()))


class KnowledgeRepo:
    def __init__(self, session: Session):
        self._session = session

    def retrieve(self, dataset_id: str, question: str, top_k: int = 6) -> list[KnowledgeRecord]:
        """Naive keyword retrieval, scoped to one dataset."""
        stmt = select(KnowledgeRecord).where(KnowledgeRecord.dataset_id == dataset_id)
        records = list(self._session.execute(stmt).scalars().all())

        q_tokens = _tokens(question)
        scored = []
        for rec in records:
            overlap = len(q_tokens & _tokens(rec.title + " " + rec.content))
            score = overlap + (1 if rec.kind == "schema" else 0)
            scored.append((score, rec))

        scored.sort(key=lambda pair: pair[0], reverse=True)
        return [rec for _, rec in scored[:top_k]]

    def context_text(self, dataset_id: str, question: str, top_k: int = 6) -> str:
        """Retrieved context as a single string, cached per dataset."""
        cached = cache.get_json(cache.context_key(dataset_id))
        if cached is not None:
            return cached
        records = self.retrieve(dataset_id, question, top_k)
        text = "\n".join(r.content for r in records)
        cache.set_json(cache.context_key(dataset_id), text, cache.CONTEXT_TTL)
        return text
