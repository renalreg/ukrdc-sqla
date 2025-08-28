"""
Not to be confused with the main ukrdc database models. These models are for
querying the removed_xml_archive on the ukrdc cluster. These are pretty similar
to the v5 database models (by design because they are a stopgap until we have
the capacity to store it)
"""

from sqlalchemy.orm import relationship, Mapped, synonym, declarative_base
from sqlalchemy import (
    MetaData,
    Column,
    Integer,
    String,
    DateTime,
    ForeignKey,
    UniqueConstraint,
)
from sqlalchemy.sql import func
from typing import List

metadata = MetaData()
Base = declarative_base(metadata=metadata)

GLOBAL_LAZY = "dynamic"


class Patient(Base):
    __tablename__ = "patient_demog"

    id = Column(Integer, primary_key=True, autoincrement=True)
    creation_date = Column(DateTime, nullable=False, server_default=func.now())

    sendingfacility = Column(String(7), nullable=False)

    nationalid = Column(
        String(50), index=True, nullable=False
    )  # patientnumber in ukrdc
    numbertype = Column(String(3), nullable=False)
    organization = Column(String(50), nullable=False)

    patientid = synonym("nationalid")

    # Define a composite primary key constraint
    __table_args__ = (
        UniqueConstraint("sendingfacility", "nationalid", "numbertype", "organization"),
    )

    treatments: Mapped[List["Treatment"]] = relationship(
        "Treatment", lazy=GLOBAL_LAZY, cascade="all, delete-orphan"
    )
    assessments: Mapped[List["Assessment"]] = relationship(
        "Assessment", lazy=GLOBAL_LAZY, cascade="all, delete-orphan"
    )
    dialysisprescriptions: Mapped[List["DialysisPrescription"]] = relationship(
        "DialysisPrescription", lazy=GLOBAL_LAZY, cascade="all, delete-orphan"
    )
    diagnoses: Mapped[List["Diagnosis"]] = relationship(
        "Diagnosis", lazy=GLOBAL_LAZY, cascade="all, delete-orphan"
    )
    cause_of_death: Mapped[List["CauseOfDeath"]] = relationship(
        "CauseOfDeath", lazy=GLOBAL_LAZY, cascade="all, delete-orphan"
    )
    renaldiagnoses: Mapped[List["RenalDiagnosis"]] = relationship(
        "RenalDiagnosis", lazy=GLOBAL_LAZY, cascade="all, delete-orphan"
    )


# Hopefully there is enough redundancy here to ensure we can track down the treatment record
# to which the qbl05 relates. The primary key in the ukrdc is pid+fromtime should be more than enough here
class Treatment(Base):
    __tablename__ = "treatment"

    id = Column(Integer, primary_key=True, autoincrement=True)
    # index treatments appear
    # It should be noted that this is null for treatment storage added prior to
    # TNG-1046. In this case if there are multiple treatments they should not
    # be matched using the idx field. This should be carefully thought about
    # anyway.
    idx = Column(Integer)

    patientid = Column(Integer, ForeignKey("patient_demog.id", ondelete="CASCADE"))

    creation_date = Column(DateTime, nullable=False, server_default=func.now())
    update_date = Column(DateTime, onupdate=func.now())

    encounternumber = Column(String(100))
    encountertype = Column(String(100))

    fromtime = Column(DateTime)
    totime = Column(DateTime)

    admitreasoncode = Column(String(100))
    admitreasoncodestd = Column(String(100))
    admitreasondesc = Column(String(255))

    qbl05 = Column(String(255))


# Assessments - doesn't currently exist
class Assessment(Base):
    __tablename__ = "assessment"

    # keys
    id = Column(Integer, primary_key=True, autoincrement=True)
    patientid = Column(Integer, ForeignKey("patient_demog.id", ondelete="CASCADE"))

    creation_date = Column(DateTime, nullable=False, server_default=func.now())
    update_date = Column(DateTime, onupdate=func.now())

    # data to store
    assessmentstart = Column(DateTime)
    assessmentend = Column(DateTime)

    assessmenttypecode = Column(String(100))
    assessmenttypecodestd = Column(String(100))
    assessmenttypecodedesc = Column(String(100))

    assessmentoutcomecode = Column(String(100))
    assessmentoutcomecodestd = Column(String(100))
    assessmentoutcomecodedesc = Column(String(100))


# DialysisPrescriptions - doesn't currently exist
class DialysisPrescription(Base):
    __tablename__ = "dialysisprescription"

    # keys
    id = Column(Integer, primary_key=True, autoincrement=True)
    patientid = Column(Integer, ForeignKey("patient_demog.id", ondelete="CASCADE"))

    creation_date = Column(DateTime, nullable=False, server_default=func.now())
    update_date = Column(DateTime, onupdate=func.now())

    # data to store
    enteredon = Column(DateTime)

    fromtime = Column(DateTime)
    totime = Column(DateTime)

    sessiontype = Column(String(5))
    sessionsperweek = Column(Integer)

    timedialysed = Column(Integer)
    vascularaccess = Column(String(5))


class Diagnosis(Base):
    __tablename__ = "diagnosis"

    id = Column(Integer, primary_key=True, autoincrement=True)
    patientid = Column(Integer, ForeignKey("patient_demog.id", ondelete="CASCADE"))

    creation_date = Column(DateTime, nullable=False, server_default=func.now())
    update_date = Column(DateTime, onupdate=func.now())

    diagnosistype = Column(String(50))
    diagnosiscode = Column("diagnosiscode", String)
    diagnosiscodestd = Column("diagnosiscodestd", String)

    # new data
    biopsyperformed = Column("biopsyperformed", String)
    verificationstatus = Column("verificationstatus", String)


class CauseOfDeath(Base):
    """
    Store all columns that show up in the XML schema,
    because we now accept more than one item,
    so need to store all data for those additional items.
    """

    __tablename__ = "causeofdeath"

    id = Column(Integer, primary_key=True, autoincrement=True)

    patientid = Column(Integer, ForeignKey("patient_demog.id", ondelete="CASCADE"))

    creation_date = Column(DateTime, nullable=False, server_default=func.now())
    update_date = Column(DateTime, onupdate=func.now())

    diagnosistype = Column(String(50))

    diagnosiscode = Column(String(100))
    diagnosiscodestd = Column(String(100))
    diagnosisdesc = Column(String(255))

    comments = Column(String)
    verificationstatus = Column(String)

    enteredon = Column(DateTime)
    updatedon = Column(DateTime)

    externalid = Column(String(100))


class RenalDiagnosis(Base):
    """
    Store all columns that show up in the XML schema,
    because we now accept more than one item,
    so need to store all data for those additional items.
    """

    __tablename__ = "renaldiagnosis"

    id = Column(Integer, primary_key=True, autoincrement=True)

    patientid = Column(Integer, ForeignKey("patient_demog.id", ondelete="CASCADE"))

    creation_date = Column(DateTime, nullable=False, server_default=func.now())
    update_date = Column(DateTime, onupdate=func.now())

    diagnosistype = Column(String(50))

    diagnosiscode = Column("diagnosiscode", String)
    diagnosiscodestd = Column("diagnosiscodestd", String)
    diagnosisdesc = Column("diagnosisdesc", String)

    diagnosingcliniciancode = Column(String(100))
    diagnosingcliniciancodestd = Column(String(100))
    diagnosingcliniciandesc = Column(String(100))

    biopsyperformed = Column(String)
    comments = Column(String)

    identificationtime = Column("identificationtime", DateTime)
    onsettime = Column(DateTime)

    verificationstatus = Column(String)

    enteredon = Column(DateTime)
    updatedon = Column(DateTime)

    externalid = Column(String(100))


class PatientNumberSubstitute(Base):
    """Create a lookup for instances where the patient number cannot be
    shortened to the character limit of the ukrdc. Note that we don't link to
    patient_demog because this is just and integer lookup.
    """

    __tablename__ = "patientnumbersubstitute"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # original ukrdc patient number
    ukrdc_patientid = Column(String(50))
    ukrdc_organisation = Column(String(50))
