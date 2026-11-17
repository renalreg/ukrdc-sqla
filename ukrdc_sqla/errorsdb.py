"""Models which relate to the errors database"""

from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Channel(Base):
    __tablename__ = "channels"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str | None] = mapped_column(String)
    direction: Mapped[str | None] = mapped_column(String)
    enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    store_first_message: Mapped[bool] = mapped_column(Boolean, default=False)
    store_last_message: Mapped[bool] = mapped_column(Boolean, default=False)
    resolved_by: Mapped[str | None] = mapped_column(
        String,
        ForeignKey("channels.id"),
        default="4b6135e3-a401-4d61-a5bf-0c09f4dbf9f2",
    )

    # --- Relationships ---
    messages: Mapped[list["Message"]] = relationship("Message", backref="channel")


class Message(Base):
    __tablename__ = "messages"
    __table_args__ = (
        UniqueConstraint(
            "message_id",
            "channel_id",
            "msg_status",
            name="messages_message_id_channel_id_msg_status_key",
        ),
        Index("messages_ni_idx", "ni"),
        Index("messages_msg_status_idx", "msg_status"),
        Index("messages_received_idx", "received"),
        Index("messages_facility_idx", "facility"),
        Index("messages_filename_idx", "filename"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    message_id: Mapped[int | None] = mapped_column(Integer)
    channel_id: Mapped[str | None] = mapped_column(String, ForeignKey("channels.id"))
    received: Mapped[datetime | None] = mapped_column(DateTime)
    msg_status: Mapped[str | None] = mapped_column(String)
    connector_index: Mapped[int | None] = mapped_column(Integer)
    connector_name: Mapped[str | None] = mapped_column(String)
    resolved_by: Mapped[int | None] = mapped_column(Integer)
    # Metadata
    ni: Mapped[str | None] = mapped_column(String)
    filename: Mapped[str | None] = mapped_column(String)
    facility: Mapped[str | None] = mapped_column(String)
    error: Mapped[str | None] = mapped_column(String)
    status: Mapped[str | None] = mapped_column(String)
    source: Mapped[str | None] = mapped_column(String)

    latests: Mapped[list["Latest"]] = relationship("Latest", back_populates="message")


class Facility(Base):
    __tablename__ = "facilities"

    facility: Mapped[str] = mapped_column(String, primary_key=True)


class Latest(Base):
    __tablename__ = "latests"

    ni: Mapped[str] = mapped_column("ni", String, primary_key=True)
    facility: Mapped[str] = mapped_column("facility", String, primary_key=True)
    message_id: Mapped[int | None] = mapped_column(
        "message_id", Integer, ForeignKey("messages.id")
    )

    # --- Relationships ---
    message: Mapped["Message"] = relationship("Message", back_populates="latests")
