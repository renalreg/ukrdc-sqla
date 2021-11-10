"""Models which relate to the generated statistics database"""
from sqlalchemy import Column, Date, DateTime, Integer, String
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class FacilityStats(Base):

    __tablename__ = "facility_stats"

    facility = Column(String, primary_key=True)

    # Total distinct UKRDC IDs for the facility
    total_patients = Column(Integer)

    # Total distinct NIs in the errordb for the facility
    patients_receiving_messages = Column(Integer)

    # Distinct NIs in the errordb for the facility most recently receiving errors
    patients_receiving_errors = Column(Integer)

    last_updated = Column(DateTime)


class ErrorHistory(Base):

    __tablename__ = "error_history"

    facility = Column(String, primary_key=True)
    date = Column(Date, primary_key=True)
    count = Column(Integer)


class PatientsLatestErrors(Base):

    __tablename__ = "patients_latest_errors"

    # Patient NI. Should be unique combined with facility as a patient only has one
    # latest message per facility.
    ni = Column(String, primary_key=True)
    facility = Column(String, primary_key=True)

    # The latest error message ID (primary key, not Mirth message ID) for the patient
    id = Column(Integer)

    last_updated = Column(DateTime)