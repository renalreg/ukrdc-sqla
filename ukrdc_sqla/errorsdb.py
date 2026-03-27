"""Models which relate to the errors database"""

from datetime import datetime
from typing import List, Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, relationship, DeclarativeBase, mapped_column
from sqlalchemy.sql.schema import Index


class Base(DeclarativeBase):
    pass


class Channel(Base):
    __tablename__ = "channels"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[Optional[str]] = mapped_column("name", String)
    direction: Mapped[Optional[str]] = mapped_column(String)
    enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    store_first_message: Mapped[bool] = mapped_column(Boolean, default=False)
    store_last_message: Mapped[bool] = mapped_column(Boolean, default=False)
    resolved_by: Mapped[Optional[str]] = mapped_column(
        String,
        ForeignKey("channels.id"),
        default="4b6135e3-a401-4d61-a5bf-0c09f4dbf9f2",
    )

    # --- Relationships ---
    messages: Mapped[List["Message"]] = relationship("Message", backref="channel")


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    message_id: Mapped[Optional[int]] = mapped_column(
        "message_id", Integer, unique=True
    )
    channel_id: Mapped[Optional[str]] = mapped_column(
        "channel_id", String, ForeignKey("channels.id")
    )
    received: Mapped[Optional[datetime]] = mapped_column("received", DateTime)
    msg_status: Mapped[Optional[str]] = mapped_column("msg_status", String)
    connector_index: Mapped[Optional[int]] = mapped_column(Integer)
    connector_name: Mapped[Optional[str]] = mapped_column(String)
    resolved_by: Mapped[Optional[int]] = mapped_column(Integer)
    # Metadata
    ni: Mapped[Optional[str]] = mapped_column("ni", String)
    filename: Mapped[Optional[str]] = mapped_column("filename", String)
    facility: Mapped[Optional[str]] = mapped_column("facility", String)
    error: Mapped[Optional[str]] = mapped_column("error", String)
    status: Mapped[Optional[str]] = mapped_column("status", String)

    latests: Mapped[List["Latest"]] = relationship("Latest", back_populates="message")


class Facility(Base):
    __tablename__ = "facilities"

    facility: Mapped[str] = mapped_column("facility", String, primary_key=True)


class Latest(Base):
    __tablename__ = "latests"

    ni: Mapped[str] = mapped_column("ni", String, primary_key=True)
    facility: Mapped[str] = mapped_column("facility", String, primary_key=True)
    message_id: Mapped[Optional[int]] = mapped_column(
        "message_id", Integer, ForeignKey("messages.id")
    )

    # --- Relationships ---
    message: Mapped["Message"] = relationship("Message", back_populates="latests")


Index("messages_ni_idx", Message.ni)
Index("messages_msg_status_idx", Message.msg_status)
Index("messages_received_idx", Message.received)
Index("messages_facility_idx", Message.facility)
Index("messages_filename_idx", Message.filename)
