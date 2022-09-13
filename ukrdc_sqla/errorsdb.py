"""Models which relate to the errors database"""
from typing import Any, List

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, MetaData, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Mapped, relationship

metadata = MetaData()
Base: Any = declarative_base(metadata=metadata)


class Channel(Base):
    __tablename__ = "channels"

    id = Column(String, primary_key=True)
    name = Column(String)
    store_first_message = Column(Boolean)
    store_last_message = Column(Boolean)


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True)
    message_id = Column(Integer, unique=True)
    channel_id = Column(String, ForeignKey("channels.id"))
    received = Column(DateTime)
    msg_status = Column(String)
    ni = Column(String)
    filename = Column(String)
    facility = Column(String)
    error = Column(String)
    status = Column(String)

    latests: Mapped[List["Latest"]] = relationship("Latest", back_populates="message")


class Facility(Base):
    __tablename__ = "facilities"

    facility = Column(String, primary_key=True)


class Latest(Base):
    __tablename__ = "latests"

    ni = Column(String, primary_key=True)
    facility = Column(String, primary_key=True)

    message_id = Column(Integer, ForeignKey("messages.id"))
    message: Mapped[Message] = relationship("Message", back_populates="children")
