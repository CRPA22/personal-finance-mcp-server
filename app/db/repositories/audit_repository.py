"""Audit log repository."""

import uuid

from sqlalchemy.orm import Session

from app.models import AuditLog


class AuditRepository:
    """Repository for audit log operations."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def log(
        self,
        user_id: uuid.UUID | None,
        action: str,
        entity_type: str,
        entity_id: str | None = None,
        metadata: dict | None = None,
    ) -> AuditLog:
        """Create an audit log entry."""
        entry = AuditLog(
            user_id=user_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            metadata_=metadata,
        )
        self._session.add(entry)
        self._session.flush()
        return entry
