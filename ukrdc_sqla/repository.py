"""Modules which relate to the Repository System Tables"""

from sqlalchemy import Column, String, DateTime, Integer

from ukrdc_sqla.ukrdc import Base


class EventControl(Base):
    """This holds when Mirth functions last ran"""

    __tablename__ = "eventcontrol"

    event_type = Column("eventtype", String, primary_key=True)
    event_date = Column("eventdate", DateTime)
    pending_event_date = Column("pendingeventdate", DateTime)

    def __init__(self, et, ed, ped):
        self.event_type = et
        self.event_date = ed
        self.pending_event_date = ped


class ValidationError(Base):
    __tablename__ = "validationerror"

    vid = Column(Integer, primary_key=True)
    pid = Column(String)
    updated_on = Column("updatedon", DateTime)
    error_type = Column("errortype", String)
    message = Column(String)
