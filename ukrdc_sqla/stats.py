"""Models which relate to the generated facility error stats and data health database"""

from datetime import date as datetime_date
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, Date, DateTime, Integer, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class ErrorHistory(Base):
    __tablename__ = "error_history"

    facility: Mapped[str] = mapped_column(String, primary_key=True)
    date: Mapped[datetime_date] = mapped_column(Date, primary_key=True)
    count: Mapped[int | None] = mapped_column(Integer)


class MultipleUKRDCID(Base):
    __tablename__ = "multiple_ukrdcid"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    group_id: Mapped[int] = mapped_column(Integer, nullable=False)
    master_id: Mapped[int] = mapped_column(Integer, nullable=False)
    resolved: Mapped[bool] = mapped_column(Boolean, default=False)
    last_updated: Mapped[datetime | None] = mapped_column(DateTime)


class LastRunTimes(Base):
    __tablename__ = "last_run_times"
    table: Mapped[str] = mapped_column(String, primary_key=True)
    facility: Mapped[str] = mapped_column(String, primary_key=True, nullable=False)
    last_run_time: Mapped[datetime | None] = mapped_column(DateTime)
