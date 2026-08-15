from fastapi import Depends, Header, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import Unauthorized
from app.db.models import User
from app.db.session import db_session


def _resolve_user(session: Session, api_key: str) -> User:
    stmt = select(User).where(User.api_key == api_key)
    user = session.execute(stmt).scalar_one_or_none()
    if user is None:
        # Do not reveal whether the key exists.
        raise Unauthorized()
    return user


def require_user(
    request: Request,
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
) -> User:
    if not x_api_key:
        raise Unauthorized()
    with db_session() as session:
        user = _resolve_user(session, x_api_key)
        request.state.user_id = user.id
        return user
