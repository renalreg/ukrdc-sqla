"""Models which relate to the errors database"""

from typing import Any

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, MetaData, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Mapped, relationship, mapped_column

metadata = MetaData()
Base: Any = declarative_base(metadata=metadata)


class Channel(Base):
    __tablename__ = "channels"

    id = mapped_column(String, primary_key=True)

    name = mapped_column("name", String)
    store_first_message = mapped_column("store_first_message", Boolean)
    store_last_message = mapped_column("store_last_message", Boolean)


class Message(Base):
    __tablename__ = "messages"

    id = mapped_column(Integer, primary_key=True)

    message_id = mapped_column("message_id", Integer, unique=True)
    channel_id = mapped_column("channel_id", String, ForeignKey("channels.id"))
    received = mapped_column("received", DateTime)
    msg_status = mapped_column("msg_status", String)
    ni = mapped_column("ni", String)
    filename = mapped_column("filename", String)
    facility = mapped_column("facility", String)
    error = mapped_column("error", String)
    status = mapped_column("status", String)

    latests:Mapped["Latest"] = relationship("Latest", back_populates="message")


class Facility(Base):
    __tablename__ = "facilities"

    facility = mapped_column("facility", String, primary_key=True)


class Latest(Base):
    __tablename__ = "latests"

    ni = mapped_column("ni", String, primary_key=True)
    facility = mapped_column("facility", String, primary_key=True)

    message_id = mapped_column("message_id", Integer, ForeignKey("messages.id"))
    message: Mapped[Message] = relationship("Message", back_populates="latests")
