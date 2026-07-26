"""Category repository."""

import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.category import Category


class CategoryRepository:
    """Repository for Category operations."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def get_by_id(self, category_id: uuid.UUID) -> Category | None:
        return self._session.scalars(select(Category).where(Category.id == category_id)).first()

    def get_by_name_and_type(
        self,
        name: str,
        category_type: str,
        user_id: uuid.UUID | None = None,
    ) -> Category | None:
        """Find a category by name and type. Checks user-specific first, then system defaults."""
        if user_id is not None:
            stmt = select(Category).where(
                func.lower(Category.name) == name.lower(),
                Category.type == category_type,
                Category.user_id == user_id,
            )
            result = self._session.scalars(stmt).first()
            if result:
                return result

        # Fall back to system category (user_id IS NULL)
        stmt = select(Category).where(
            func.lower(Category.name) == name.lower(),
            Category.type == category_type,
            Category.user_id.is_(None),
        )
        return self._session.scalars(stmt).first()

    def list_by_type(
        self,
        category_type: str | None = None,
        user_id: uuid.UUID | None = None,
    ) -> list[Category]:
        """List categories: system defaults + user's own. Optionally filtered by type."""
        stmt = select(Category).where(
            (Category.user_id.is_(None)) | (Category.user_id == user_id)
        )
        if category_type:
            stmt = stmt.where(Category.type == category_type)
        stmt = stmt.order_by(Category.type, Category.name)
        return list(self._session.scalars(stmt).all())

    def create(
        self,
        name: str,
        category_type: str,
        user_id: uuid.UUID,
    ) -> Category:
        """Create a custom user category."""
        category = Category(name=name, type=category_type, is_default=False, user_id=user_id)
        self._session.add(category)
        self._session.flush()
        return category

    def delete(self, category_id: uuid.UUID) -> bool:
        category = self.get_by_id(category_id)
        if category is None or category.is_default:
            return False
        self._session.delete(category)
        self._session.flush()
        return True
