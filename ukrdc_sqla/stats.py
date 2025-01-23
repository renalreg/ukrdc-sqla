"""Models which relate to the generated facility error stats and data health database"""

from sqlalchemy import Date, DateTime, Integer, String, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import mapped_column

Base = declarative_base()


class ErrorHistory(Base):
    __tablename__ = "error_history"

    facility = mapped_column("facility", String, primary_key=True)
    date = mapped_column("date", Date, primary_key=True)
    count = mapped_column("count", Integer)


class MultipleUKRDCID(Base):
    __tablename__ = "multiple_ukrdcid"
    id = mapped_column("id", Integer, primary_key=True, autoincrement=True)

    group_id = mapped_column("group_id", Integer, nullable=False)
    master_id = mapped_column("master_id", Integer, nullable=False)
    resolved = mapped_column("resolved", Boolean, default=False)
    last_updated = mapped_column("last_updated", DateTime)


class LastRunTimes(Base):
    __tablename__ = "last_run_times"

    table = mapped_column("table", String, primary_key=True)
    facility = mapped_column("facility", String, primary_key=True, nullable=False)
    last_run_time = mapped_column("last_run_time", DateTime)
