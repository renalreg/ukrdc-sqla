"""Models which relate to the generated facility error stats and data health database"""

from sqlalchemy import Column, Date, DateTime, Integer, String, Boolean
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class ErrorHistory(Base):
    __tablename__ = "error_history"

    facility = Column("facility", String, primary_key=True)
    date = Column("date", Date, primary_key=True)
    count = Column("count", Integer)


class MultipleUKRDCID(Base):
    __tablename__ = "multiple_ukrdcid"
    id = Column("id", Integer, primary_key=True, autoincrement=True)

    group_id = Column("group_id", Integer, nullable=False)
    master_id = Column("master_id", Integer, nullable=False)
    resolved = Column("resolved", Boolean, default=False)
    last_updated = Column("last_updated", DateTime)


class LastRunTimes(Base):
    __tablename__ = "last_run_times"

    table = Column("table", String, primary_key=True)
    facility = Column("facility", String, primary_key=True, nullable=False)
    last_run_time = Column("last_run_time", DateTime)
