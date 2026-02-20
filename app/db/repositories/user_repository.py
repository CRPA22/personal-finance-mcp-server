"""User repository."""

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import User


class UserRepository:
    """Repository for User CRUD operations."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def get_by_id(self, user_id: uuid.UUID) -> User | None:
        """Get user by id."""
        stmt = select(User).where(User.id == user_id)
        return self._session.scalars(stmt).first()

    def get_by_email(self, email: str) -> User | None:
        """Get user by email."""
        stmt = select(User).where(User.email == email)
        return self._session.scalars(stmt).first()
