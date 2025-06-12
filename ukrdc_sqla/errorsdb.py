"""Models which relate to the errors database"""

from typing import List

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, MetaData, String
from sqlalchemy.orm import Mapped, relationship, declarative_base

metadata = MetaData()
Base = declarative_base(metadata=metadata)


class Channel(Base):
    __tablename__ = "channels"

    id = Column(String, primary_key=True)

    name = Column("name", String)
    store_first_message = Column("store_first_message", Boolean)
    store_last_message = Column("store_last_message", Boolean)


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True)

    message_id = Column("message_id", Integer, unique=True)
    channel_id = Column("channel_id", String, ForeignKey("channels.id"))
    received = Column("received", DateTime)
    msg_status = Column("msg_status", String)
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
    message: Mapped[Message] = relationship("Message", back_populates="latests")
