"""Models that relate to the audit database."""

from datetime import datetime

from sqlalchemy import (
    DateTime,
    ForeignKey,
    String,
)
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    synonym,
)

from ukrdc_sqla.utils.structure import mapped_column


class Base(DeclarativeBase):
    pass


class AccessEvent(Base):
    """Represents an access event in the audit database."""

    __tablename__ = "access_event"

    id: Mapped[str] = mapped_column(String, primary_key=True, nullable=False)
    time: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    uid: Mapped[str] = mapped_column(String, nullable=False)
    cid: Mapped[str] = mapped_column(String)

    sub: Mapped[str] = mapped_column(String)
    client_host: Mapped[str] = mapped_column(String)
    path: Mapped[str] = mapped_column(String)
    method: Mapped[str] = mapped_column(String)
    body: Mapped[str] = mapped_column(String)


class AuditEvent(Base):
    """Represents an audit event in the audit database."""

    __tablename__ = "audit_event"

    id: Mapped[str] = mapped_column(String, primary_key=True, nullable=False)

    parent_id: Mapped[str] = mapped_column(String)
    access_event_id: Mapped[str] = mapped_column(String, ForeignKey("access_event.id"))
    resource: Mapped[str] = mapped_column(String)
    resource_id: Mapped[str] = mapped_column(String)
    operation: Mapped[str] = mapped_column(String)

    # Synonyms
    ukrdc_pid: Mapped[str] = synonym("resource_id")
