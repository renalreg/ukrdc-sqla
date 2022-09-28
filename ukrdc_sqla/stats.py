"""Models which relate to the generated facility error stats and data health database"""
from sqlalchemy import Column, Date, DateTime, Integer, String, Boolean
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class ErrorHistory(Base):

    __tablename__ = "error_history"

    facility = Column(String, primary_key=True)
    date = Column(Date, primary_key=True)
    count = Column(Integer)


class MultipleUKRDCID(Base):
    __tablename__ = "multiple_ukrdcid"

    id = Column(Integer, primary_key=True, autoincrement=True)

    group_id = Column(Integer, nullable=False)
    master_id = Column(Integer, nullable=False)

    resolved = Column(Boolean, default=False)

    last_updated = Column(DateTime)


class LastRunTimes(Base):
    __tablename__ = "last_run_times"

    table = Column(String, primary_key=True)
    facility = Column(String, primary_key=True, nullable=False)
    last_run_time = Column(DateTime)
