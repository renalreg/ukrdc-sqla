"""Modules which relate to the Repository System Tables"""

from datetime import datetime
from typing import Optional

from sqlalchemy import String, DateTime, Integer
from sqlalchemy.orm import Mapped, synonym

from ukrdc_sqla.ukrdc import Base, mapped_column


class EventControl(Base):
    """This holds when Mirth functions last ran"""

    __tablename__ = "eventcontrol"

    event_type: Mapped[str] = mapped_column("eventtype", String, primary_key=True)
    event_date: Mapped[Optional[datetime]] = mapped_column("eventdate", DateTime)
    pending_event_date: Mapped[Optional[datetime]] = mapped_column(
        "pendingeventdate", DateTime
    )

    def __init__(self, et, ed, ped):
        self.event_type = et
        self.event_date = ed
        self.pending_event_date = ped


class ValidationError(Base):
    __tablename__ = "validationerror"

    vid: Mapped[int] = mapped_column(Integer, primary_key=True)
    pid: Mapped[Optional[str]] = mapped_column(String)
    updatedon: Mapped[Optional[datetime]] = mapped_column(DateTime)
    errortype: Mapped[Optional[str]] = mapped_column(String)
    message: Mapped[Optional[str]] = mapped_column(String)

    updated_on: Mapped[Optional[datetime]] = synonym("updatedon")
    error_type: Mapped[Optional[str]] = synonym("errortype")
