"""Models which relate to the errors database"""

from typing import List

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, MetaData, String
from sqlalchemy.orm import Mapped, relationship, declarative_base
from sqlalchemy.sql.schema import Index

metadata = MetaData()
Base = declarative_base(metadata=metadata)


class Channel(Base):
    __tablename__ = "channels"

    id = Column(String, primary_key=True)
    name = Column("name", String)
    direction = Column(String)
    enabled = Column(Boolean, default=False)
    store_first_message = Column(Boolean, default=False)
    store_last_message = Column(Boolean, default=False)

    # Channel that can mark errors in this channel as RESOLVED
    resolved_by = Column(
        String,
        ForeignKey("channels.id"),
        default="4b6135e3-a401-4d61-a5bf-0c09f4dbf9f2",
    )

    messages: Mapped[List["Message"]] = relationship("Message", backref="channel")


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True)

    message_id = Column("message_id", Integer, unique=True)
    channel_id = Column("channel_id", String, ForeignKey("channels.id"))
    received = Column("received", DateTime)
    msg_status = Column("msg_status", String)
    connector_index = Column(Integer)
    connector_name = Column(String)
    resolved_by = Column(Integer)

    # Metadata
    ni = Column("ni", String)
    filename = Column("filename", String)
    facility = Column("facility", String)
    error = Column("error", String)
    status = Column("status", String)

    latests: Mapped[List["Latest"]] = relationship("Latest", back_populates="message")


class Facility(Base):
    __tablename__ = "facilities"

    facility = Column("facility", String, primary_key=True)


class Latest(Base):
    __tablename__ = "latests"

    ni = Column("ni", String, primary_key=True)
    facility = Column("facility", String, primary_key=True)

    message_id = Column("message_id", Integer, ForeignKey("messages.id"))
    message: Mapped["Message"] = relationship("Message", back_populates="latests")


Index("messages_ni_idx", Message.ni)
Index("messages_msg_status_idx", Message.msg_status)
Index("messages_received_idx", Message.received)
Index("messages_facility_idx", Message.facility)
Index("messages_filename_idx", Message.filename)
