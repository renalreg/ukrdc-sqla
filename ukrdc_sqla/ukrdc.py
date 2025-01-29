"""Models which relate to the main UKRDC database"""

import decimal
import enum
from datetime import datetime, date
from typing import List, Optional

import sqlalchemy
from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    LargeBinary,
    MetaData,
    Numeric,
    String,
    Text,
    text,
)
from sqlalchemy.dialects.postgresql import ARRAY, BIT
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.orm import Mapped, relationship, synonym, declarative_base
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    if sqlalchemy.__version__.startswith("2."):
        from sqlalchemy.orm import DynamicMapped
        DynamicRel = DynamicMapped
    else:
        from sqlalchemy.orm import Query
        DynamicRel = Query
else:
    DynamicRel = None


metadata = MetaData()
Base = declarative_base(metadata=metadata)

GLOBAL_LAZY = "dynamic"


class PatientRecord(Base):
    __tablename__ = "patientrecord"

    pid: Mapped[str] = Column(String, primary_key=True)

    sendingfacility: Mapped[str] = Column(String(7), nullable=False)
    sendingextract: Mapped[str] = Column(String(6), nullable=False)
    localpatientid: Mapped[str] = Column(String(17), nullable=False)
    repositorycreationdate: Mapped[datetime] = Column(DateTime, nullable=False)
    repositoryupdatedate: Mapped[datetime] = Column(DateTime, nullable=False)
    migrated: Mapped[bool] = Column(
        Boolean, nullable=False, server_default=text("false")
    )
    creation_date: Mapped[DateTime] = Column(
        DateTime, nullable=False, server_default=text("now()")
    )
    ukrdcid: Mapped[Optional[str]] = Column(String(10), index=True)
    channelname: Mapped[Optional[str]] = Column(String(50))
    channelid: Mapped[Optional[str]] = Column(String(50))
    extracttime: Mapped[Optional[str]] = Column(String(50))
    startdate: Mapped[Optional[datetime]] = Column(DateTime)
    stopdate: Mapped[Optional[datetime]] = Column(DateTime)
    schemaversion: Mapped[Optional[str]] = Column(String(50))
    update_date: Mapped[Optional[datetime]] = Column(DateTime)

    # Relationships

    patient: Mapped["Patient"] = relationship(
        "Patient", backref="record", uselist=False, cascade="all, delete-orphan"
    )
    lab_orders: DynamicRel["LabOrder"] = relationship(
        "LabOrder", backref="record", lazy=GLOBAL_LAZY, cascade="all, delete-orphan"
    )
    result_items: DynamicRel["ResultItem"] = relationship(
        "ResultItem",
        secondary="laborder",
        primaryjoin="LabOrder.pid == PatientRecord.pid",
        secondaryjoin="ResultItem.order_id == LabOrder.id",
        lazy=GLOBAL_LAZY,
        viewonly=True,
    )
    observations: DynamicRel["Observation"] = relationship(
        "Observation", backref="record", lazy=GLOBAL_LAZY, cascade="all, delete-orphan"
    )
    social_histories: Mapped[List["SocialHistory"]] = relationship(
        "SocialHistory", cascade="all, delete-orphan"
    )
    family_histories: Mapped[List["FamilyHistory"]] = relationship(
        "FamilyHistory", cascade="all, delete-orphan"
    )
    allergies: DynamicRel["Allergy"] = relationship(
        "Allergy", lazy=GLOBAL_LAZY, cascade="all, delete-orphan"
    )
    diagnoses: DynamicRel["Diagnosis"] = relationship(
        "Diagnosis", lazy=GLOBAL_LAZY, cascade="all, delete-orphan"
    )
    cause_of_death: DynamicRel["CauseOfDeath"] = relationship(
        "CauseOfDeath", lazy=GLOBAL_LAZY, cascade="all, delete-orphan"
    )
    renaldiagnoses: DynamicRel["RenalDiagnosis"] = relationship(
        "RenalDiagnosis", lazy=GLOBAL_LAZY, cascade="all, delete-orphan"
    )
    medications: DynamicRel["Medication"] = relationship(
        "Medication", lazy=GLOBAL_LAZY, cascade="all, delete-orphan"
    )
    dialysis_sessions: DynamicRel["DialysisSession"] = relationship(
        "DialysisSession", lazy=GLOBAL_LAZY, cascade="all, delete-orphan"
    )
    vascular_accesses: DynamicRel["VascularAccess"] = relationship(
        "VascularAccess", lazy=GLOBAL_LAZY, cascade="all, delete-orphan"
    )
    procedures: DynamicRel["Procedure"] = relationship(
        "Procedure", lazy=GLOBAL_LAZY, cascade="all, delete-orphan"
    )
    documents: DynamicRel["Document"] = relationship(
        "Document", lazy=GLOBAL_LAZY, cascade="all, delete-orphan"
    )
    encounters: DynamicRel["Encounter"] = relationship(
        "Encounter", lazy=GLOBAL_LAZY, cascade="all, delete-orphan"
    )
    transplantlists: DynamicRel["TransplantList"] = relationship(
        "TransplantList", lazy=GLOBAL_LAZY, cascade="all, delete-orphan"
    )
    treatments: DynamicRel["Treatment"] = relationship(
        "Treatment", lazy=GLOBAL_LAZY, cascade="all, delete-orphan"
    )
    program_memberships: DynamicRel["ProgramMembership"] = relationship(
        "ProgramMembership", cascade="all, delete-orphan"
    )
    transplants: DynamicRel["Transplant"] = relationship(
        "Transplant", lazy=GLOBAL_LAZY, cascade="all, delete-orphan"
    )
    opt_outs: DynamicRel["OptOut"] = relationship("OptOut", lazy=GLOBAL_LAZY, cascade="all, delete-orphan")
    clinical_relationships: Mapped[List["ClinicalRelationship"]] = relationship(
        "ClinicalRelationship", cascade="all, delete-orphan"
    )
    surveys: DynamicRel["Survey"] = relationship(
        "Survey", lazy=GLOBAL_LAZY, cascade="all, delete-orphan"
    )
    pvdata = relationship("PVData", uselist=False, cascade="all, delete-orphan")
    pvdelete: DynamicRel["Survey"] = relationship("PVDelete", lazy=GLOBAL_LAZY, cascade="all, delete-orphan")

    # Synonyms
    id: Mapped[str] = synonym("pid")
    extract_time: Mapped[datetime] = synonym("extracttime")
    repository_creation_date: Mapped[datetime] = synonym("repositorycreationdate")
    repository_update_date: Mapped[datetime] = synonym("repositoryupdatedate")

    def __str__(self):
        return (
            f"{self.__class__.__name__}({self.pid}) <"
            f"UKRDCID:{self.ukrdcid} CREATED:{self.repository_creation_date}"
            f">"
        )


class Patient(Base):
    __tablename__ = "patient"

    pid: Mapped[str] = Column(String, ForeignKey("patientrecord.pid"), primary_key=True)
    creation_date: Mapped[datetime] = Column(
        DateTime, nullable=False, server_default=text("now()")
    )
    birthtime: Mapped[Optional[datetime]] = Column(DateTime)
    deathtime: Mapped[Optional[datetime]] = Column(DateTime)
    gender: Mapped[Optional[str]] = Column(String(2))
    countryofbirth: Mapped[Optional[str]] = Column(String(3))
    ethnicgroupcode: Mapped[Optional[str]] = Column(String(100))
    ethnicgroupcodestd: Mapped[Optional[str]] = Column(String(100))
    ethnicgroupdesc: Mapped[Optional[str]] = Column(String(100))
    occupationcode: Mapped[Optional[str]] = Column(String(100))
    occupationcodestd: Mapped[Optional[str]] = Column(String(100))
    occupationdesc: Mapped[Optional[str]] = Column(String(100))
    primarylanguagecode: Mapped[Optional[str]] = Column(String(100))
    primarylanguagecodestd: Mapped[Optional[str]] = Column(String(100))
    primarylanguagedesc: Mapped[Optional[str]] = Column(String(100))
    death: Mapped[Optional[bool]] = Column(Boolean)
    persontocontactname: Mapped[Optional[str]] = Column(String(100))
    persontocontact_relationship: Mapped[Optional[str]] = Column(String(20))
    persontocontact_contactnumber: Mapped[Optional[str]] = Column(String(20))
    persontocontact_contactnumbertype: Mapped[Optional[str]] = Column(String(20))
    persontocontact_contactnumbercomments: Mapped[Optional[str]] = Column(String(200))
    updatedon: Mapped[Optional[datetime]] = Column(DateTime)
    actioncode: Mapped[Optional[str]] = Column(String(3))
    externalid: Mapped[Optional[str]] = Column(String(100))
    bloodgroup: Mapped[Optional[str]] = Column(String(100))
    bloodrhesus: Mapped[Optional[str]] = Column(String(100))
    update_date: Mapped[Optional[datetime]] = Column(DateTime)

    # Synonyms
    id: Mapped[str] = synonym("pid")
    birth_time: Mapped[datetime] = synonym("birthtime")
    death_time: Mapped[datetime] = synonym("deathtime")
    country_of_birth: Mapped[str] = synonym("countryofbirth")
    ethnic_group_code: Mapped[str] = synonym("ethnicgroupcode")
    ethnic_group_code_std = synonym("ethnicgroupcodestd")
    ethnic_group_description: Mapped[str] = synonym("ethnicgroupdesc")
    person_to_contact_name: Mapped[str] = synonym("persontocontactname")
    person_to_contact_number: Mapped[str] = synonym("persontocontact_contactnumber")
    person_to_contact_relationship: Mapped[str] = synonym(
        "persontocontact_relationship"
    )
    person_to_contact_number_comments: Mapped[str] = synonym(
        "persontocontact_numbercomments"
    )
    person_to_contact_number_type: Mapped[str] = synonym(
        "persontocontact_contactnumbertype"
    )
    occupation_code: Mapped[str] = synonym("occupationcode")
    occupation_codestd: Mapped[str] = synonym("occupationcodestd")
    occupation_description: Mapped[str] = synonym("occupationdesc")
    primary_language: Mapped[str] = synonym("primarylanguagecode")
    primary_language_codestd: Mapped[str] = synonym("primarylanguagecodestd")
    primary_language_description: Mapped[str] = synonym("primarylanguagedesc")
    dead: Mapped[bool] = synonym("death")
    updated_on: Mapped[datetime] = synonym("updatedon")

    # Relationships

    numbers: DynamicRel["PatientNumber"] = relationship(
        "PatientNumber",
        backref="patient",
        lazy=GLOBAL_LAZY,
        cascade="all, delete-orphan",
    )
    names: DynamicRel["Name"] = relationship(
        "Name", lazy=GLOBAL_LAZY, cascade="all, delete-orphan"
    )
    contact_details: DynamicRel["ContactDetail"] = relationship(
        "ContactDetail", lazy=GLOBAL_LAZY, cascade="all, delete-orphan"
    )
    addresses: DynamicRel["Address"] = relationship(
        "Address", lazy=GLOBAL_LAZY, cascade="all, delete-orphan"
    )
    familydoctor: Mapped["FamilyDoctor"] = relationship(
        "FamilyDoctor", uselist=False, cascade="all, delete-orphan"
    )

    def __str__(self):
        return f"{self.__class__.__name__}({self.pid}) <{self.birth_time}>"

    @property
    def name(self) -> Optional["Name"]:
        """Return main patient name."""
        for name in self.names or []:
            if name.nameuse == "L":
                return name
        return None

    @property
    def first_ni_number(self) -> Optional[str]:
        """Find the first nhs,chi or hsc number for a patient."""
        types = "NHS", "CHI", "HSC"
        for number in self.numbers or []:
            if number.numbertype == "NI" and number.organization in types:
                return number.patientid
        return None

    @property
    def first_hospital_number(self) -> Optional[str]:
        """Find the first local hospital number for a patient."""
        hospital = "LOCALHOSP"
        for number in self.numbers or []:
            if number.numbertype == "MRN" and number.organization == hospital:
                return number.patientid
        return None


class CauseOfDeath(Base):
    __tablename__ = "causeofdeath"

    pid: Mapped[str] = Column(String, ForeignKey("patientrecord.pid"), primary_key=True)

    creation_date: Mapped[datetime] = Column(
        DateTime, nullable=False, server_default=text("now()")
    )
    diagnosistype: Mapped[Optional[str]] = Column(String(50))
    diagnosingcliniciancode: Mapped[Optional[str]] = Column(String(100))
    diagnosingcliniciancodestd: Mapped[Optional[str]] = Column(String(100))
    diagnosingcliniciandesc: Mapped[Optional[str]] = Column(String(100))
    diagnosiscode: Mapped[Optional[str]] = Column(String(100))
    diagnosiscodestd: Mapped[Optional[str]] = Column(String(100))
    diagnosisdesc: Mapped[Optional[str]] = Column(String(255))
    comments: Mapped[Optional[str]] = Column(Text)
    enteredon: Mapped[Optional[datetime]] = Column(DateTime)
    updatedon: Mapped[Optional[datetime]] = Column(DateTime)
    actioncode: Mapped[Optional[str]] = Column(String(3))
    externalid: Mapped[Optional[str]] = Column(String(100))
    update_date: Mapped[Optional[datetime]] = Column(DateTime)

    # Synonyms
    id: Mapped[str] = synonym(
        "pid"
    )  # this will not be correct if the primary key changes
    diagnosis_type: Mapped[str] = synonym("diagnosistype")
    diagnosing_clinician_code: Mapped[str] = synonym("diagnosingcliniciancode")
    diagnosing_clinician_code_std: Mapped[str] = synonym("diagnosingcliniciancodestd")
    diagnosing_clinician_desc: Mapped[str] = synonym("diagnosingcliniciandesc")
    diagnosis_code: Mapped[str] = synonym("diagnosiscode")
    diagnosis_code_std: Mapped[str] = synonym("diagnosiscodestd")
    diagnosis_desc: Mapped[str] = synonym("diagnosisdesc")
    entered_on: Mapped[datetime] = synonym("enteredon")
    updated_on: Mapped[datetime] = synonym("updatedon")
    action_code: Mapped[str] = synonym("actioncode")
    external_id: Mapped[str] = synonym("externalid")


class FamilyDoctor(Base):
    __tablename__ = "familydoctor"

    id: Mapped[str] = Column(String, ForeignKey("patient.pid"), primary_key=True)

    creation_date: Mapped[datetime] = Column(
        DateTime, nullable=False, server_default=text("now()")
    )
    gpname: Mapped[Optional[str]] = Column(String(100))
    gpid: Mapped[Optional[str]] = Column(
        String(20), ForeignKey("ukrdc_ods_gp_codes.code")
    )
    gppracticeid: Mapped[Optional[str]] = Column(
        String(20), ForeignKey("ukrdc_ods_gp_codes.code")
    )
    addressuse: Mapped[Optional[str]] = Column(String(10))
    fromtime: Mapped[Optional[date]] = Column(Date)
    totime: Mapped[Optional[date]] = Column(Date)
    street: Mapped[Optional[str]] = Column(String(100))
    town: Mapped[Optional[str]] = Column(String(100))
    county: Mapped[Optional[str]] = Column(String(100))
    postcode: Mapped[Optional[str]] = Column(String(10))
    countrycode: Mapped[Optional[str]] = Column(String(100))
    countrycodestd: Mapped[Optional[str]] = Column(String(100))
    countrydesc: Mapped[Optional[str]] = Column(String(100))
    contactuse: Mapped[Optional[str]] = Column(String(10))
    contactvalue: Mapped[Optional[str]] = Column(String(100))
    email: Mapped[Optional[str]] = Column(String(100))
    commenttext: Mapped[Optional[str]] = Column(String(100))
    update_date: Mapped[Optional[datetime]] = Column(DateTime)

    # Relationships

    gp_info:Mapped["GPInfo"] = relationship("GPInfo", foreign_keys=[gpid], uselist=False)
    gp_practice_info:Mapped["GPInfo"] = relationship(
        "GPInfo", foreign_keys=[gppracticeid], uselist=False
    )

    def __str__(self):
        return (
            f"{self.__class__.__name__}({self.id}) <" f"{self.gpname} {self.gpid}" f">"
        )


class GPInfo(Base):
    __tablename__ = "ukrdc_ods_gp_codes"

    code: Mapped[str] = Column(String(8), primary_key=True)

    creation_date: Mapped[datetime] = Column(
        DateTime, nullable=False, server_default=text("now()")
    )
    name: Mapped[Optional[str]] = Column(String(50))
    address1: Mapped[Optional[str]] = Column(String(35))
    postcode: Mapped[Optional[str]] = Column(String(8))
    phone: Mapped[Optional[str]] = Column(String(12))
    type: Mapped[Optional[enum.Enum]] = Column(Enum("GP", "PRACTICE", name="gp_type"))
    update_date: Mapped[Optional[datetime]] = Column(DateTime)

    # Synonyms

    gpname: Mapped[Optional[str]] = synonym("name")
    street: Mapped[Optional[str]] = synonym("address1")
    contactvalue: Mapped[Optional[str]] = synonym("phone")


class SocialHistory(Base):
    __tablename__ = "socialhistory"

    id: Mapped[str] = Column(String, primary_key=True)
    pid: Mapped[Optional[str]] = Column(String, ForeignKey("patientrecord.pid"))

    creation_date: Mapped[datetime] = Column(
        DateTime, nullable=False, server_default=text("now()")
    )
    idx: Mapped[Optional[int]] = Column(Integer)
    socialhabitcode: Mapped[Optional[str]] = Column(String(100))
    socialhabitcodestd: Mapped[Optional[str]] = Column(String(100))
    socialhabitdesc: Mapped[Optional[str]] = Column(String(100))
    updatedon: Mapped[Optional[datetime]] = Column(DateTime)
    actioncode: Mapped[Optional[str]] = Column(String(3))
    externalid: Mapped[Optional[str]] = Column(String(100))
    update_date: Mapped[Optional[datetime]] = Column(DateTime)


class FamilyHistory(Base):
    __tablename__ = "familyhistory"

    id: Mapped[str] = Column(String, primary_key=True)
    pid: Mapped[Optional[str]] = Column(String, ForeignKey("patientrecord.pid"))

    creation_date: Mapped[datetime] = Column(
        DateTime, nullable=False, server_default=text("now()")
    )
    idx: Mapped[Optional[int]] = Column(Integer)
    familymembercode: Mapped[Optional[str]] = Column(String(100))
    familymembercodestd: Mapped[Optional[str]] = Column(String(100))
    familymemberdesc: Mapped[Optional[str]] = Column(String(100))
    diagnosiscode: Mapped[Optional[str]] = Column(String(100))
    diagnosiscodestd: Mapped[Optional[str]] = Column(String(100))
    diagnosisdesc: Mapped[Optional[str]] = Column(String(100))
    notetext: Mapped[Optional[str]] = Column(String(100))
    enteredatcode: Mapped[Optional[str]] = Column(String(100))
    enteredatcodestd: Mapped[Optional[str]] = Column(String(100))
    enteredatdesc: Mapped[Optional[str]] = Column(String(100))
    fromtime: Mapped[Optional[datetime]] = Column(DateTime)
    totime: Mapped[Optional[datetime]] = Column(DateTime)
    updatedon: Mapped[Optional[datetime]] = Column(DateTime)
    actioncode: Mapped[Optional[str]] = Column(String(3))
    externalid: Mapped[Optional[str]] = Column(String(100))
    update_date: Mapped[Optional[datetime]] = Column(DateTime)


class Observation(Base):
    __tablename__ = "observation"

    id: Mapped[str] = Column(String, primary_key=True)
    pid: Mapped[Optional[str]] = Column(String, ForeignKey("patientrecord.pid"))

    creation_date: Mapped[datetime] = Column(
        DateTime, nullable=False, server_default=text("now()")
    )
    idx: Mapped[Optional[int]] = Column(Integer)
    observationtime: Mapped[Optional[datetime]] = Column(DateTime)
    observationcode: Mapped[Optional[str]] = Column(String(100))
    observationcodestd: Mapped[Optional[str]] = Column(String(100))
    observationdesc: Mapped[Optional[str]] = Column(String(100))
    observationvalue: Mapped[Optional[str]] = Column(String(100))
    observationunits: Mapped[Optional[str]] = Column(String(100))
    prepost: Mapped[Optional[str]] = Column(String(4))
    commenttext: Mapped[Optional[str]] = Column(String(100))
    cliniciancode: Mapped[Optional[str]] = Column(String(100))
    cliniciancodestd: Mapped[Optional[str]] = Column(String(100))
    cliniciandesc: Mapped[Optional[str]] = Column(String(100))
    enteredatcode: Mapped[Optional[str]] = Column(String(100))
    enteredatcodestd: Mapped[Optional[str]] = Column(String(100))
    enteredatdesc: Mapped[Optional[str]] = Column(String(100))
    enteringorganizationcode: Mapped[Optional[str]] = Column(String(100))
    enteringorganizationcodestd: Mapped[Optional[str]] = Column(String(100))
    enteringorganizationdesc: Mapped[Optional[str]] = Column(String(100))
    updatedon: Mapped[Optional[datetime]] = Column(DateTime)
    actioncode: Mapped[Optional[str]] = Column(String(3))
    externalid: Mapped[Optional[str]] = Column(String(100))
    update_date: Mapped[Optional[datetime]] = Column(DateTime)

    # Synonyms

    observation_time: Mapped[datetime] = synonym("observationtime")
    observation_code: Mapped[Optional[str]] = synonym("observationcode")
    observation_code_std: Mapped[Optional[str]] = synonym("observationcodestd")
    observation_desc: Mapped[Optional[str]] = synonym("observationdesc")
    observation_value: Mapped[Optional[str]] = synonym("observationvalue")
    observation_units: Mapped[Optional[str]] = synonym("observationunits")
    comment_text: Mapped[Optional[str]] = synonym("commenttext")
    clinician_code: Mapped[Optional[str]] = synonym("cliniciancode")
    clinician_code_std: Mapped[Optional[str]] = synonym("cliniciancodestd")
    clinician_desc: Mapped[Optional[str]] = synonym("cliniciandesc")
    entered_at: Mapped[Optional[str]] = synonym("enteredatcode")
    entered_at_description: Mapped[Optional[str]] = synonym("enteredatdesc")
    entering_organization_code: Mapped[Optional[str]] = synonym(
        "enteringorganizationcode"
    )
    entering_organization_description: Mapped[Optional[str]] = synonym(
        "enteringorganizationdesc"
    )
    updated_on: Mapped[Optional[datetime]] = synonym("updatedon")
    action_code: Mapped[Optional[str]] = synonym("actioncode")
    external_id: Mapped[Optional[str]] = synonym("externalid")
    pre_post: Mapped[Optional[str]] = synonym("prepost")

    def __str__(self):
        return (
            f"{self.__class__.__name__}({self.pid}) <"
            f"{self.observation_code} {self.observation_value}"
            f">"
        )


class OptOut(Base):
    __tablename__ = "optout"

    id: Mapped[str] = Column(String, primary_key=True)
    pid: Mapped[Optional[str]] = Column(String, ForeignKey("patientrecord.pid"))

    creation_date: Mapped[datetime] = Column(
        DateTime, nullable=False, server_default=text("now()")
    )
    idx: Mapped[Optional[int]] = Column(Integer)
    programname: Mapped[Optional[str]] = Column(String(100))
    programdescription: Mapped[Optional[str]] = Column(String(100))
    enteredbycode: Mapped[Optional[str]] = Column(String(100))
    enteredbycodestd: Mapped[Optional[str]] = Column(String(100))
    enteredbydesc: Mapped[Optional[str]] = Column(String(100))
    enteredatcode: Mapped[Optional[str]] = Column(String(100))
    enteredatcodestd: Mapped[Optional[str]] = Column(String(100))
    enteredatdesc: Mapped[Optional[str]] = Column(String(100))
    fromtime: Mapped[Optional[date]] = Column(Date)
    totime: Mapped[Optional[date]] = Column(Date)
    updatedon: Mapped[Optional[datetime]] = Column(DateTime)
    actioncode: Mapped[Optional[str]] = Column(String(3))
    externalid: Mapped[Optional[str]] = Column(String(100))
    update_date: Mapped[Optional[datetime]] = Column(DateTime)

    # Synonyms

    program_name: Mapped[str] = synonym("programname")
    program_description: Mapped[str] = synonym("programdescription")
    entered_by_code: Mapped[str] = synonym("enteredbycode")
    entered_by_code_std: Mapped[str] = synonym("enteredbycodestd")
    entered_by_desc: Mapped[str] = synonym("enteredbydesc")
    entered_at_code: Mapped[str] = synonym("enteredatcode")
    entered_at_code_std: Mapped[str] = synonym("enteredatcodestd")
    entered_at_desc: Mapped[str] = synonym("enteredatdesc")
    from_time: Mapped[date] = synonym("fromtime")
    to_time: Mapped[date] = synonym("totime")
    updated_on: Mapped[datetime] = synonym("updatedon")
    action_code: Mapped[str] = synonym("actioncode")
    external_id: Mapped[str] = synonym("externalid")


class Allergy(Base):
    __tablename__ = "allergy"

    id: Mapped[str] = Column(String, primary_key=True)
    pid: Mapped[Optional[str]] = Column(String, ForeignKey("patientrecord.pid"))

    creation_date: Mapped[datetime] = Column(
        DateTime, nullable=False, server_default=text("now()")
    )
    idx: Mapped[Optional[int]] = Column(Integer)
    allergycode: Mapped[Optional[str]] = Column(String(100))
    allergycodestd: Mapped[Optional[str]] = Column(String(100))
    allergydesc: Mapped[Optional[str]] = Column(String(100))
    allergycategorycode: Mapped[Optional[str]] = Column(String(100))
    allergycategorycodestd: Mapped[Optional[str]] = Column(String(100))
    allergycategorydesc: Mapped[Optional[str]] = Column(String(100))
    severitycode: Mapped[Optional[str]] = Column(String(100))
    severitycodestd: Mapped[Optional[String]] = Column(String(100))
    severitydesc: Mapped[Optional[str]] = Column(String(100))
    cliniciancode: Mapped[Optional[str]] = Column(String(100))
    cliniciancodestd: Mapped[Optional[str]] = Column(String(100))
    cliniciandesc: Mapped[Optional[str]] = Column(String(100))
    discoverytime: Mapped[Optional[datetime]] = Column(DateTime)
    confirmedtime: Mapped[Optional[datetime]] = Column(DateTime)
    commenttext: Mapped[Optional[str]] = Column(String(500))
    inactivetime: Mapped[Optional[datetime]] = Column(DateTime)
    freetextallergy: Mapped[Optional[str]] = Column(String(500))
    qualifyingdetails: Mapped[Optional[str]] = Column(String(500))
    updatedon: Mapped[Optional[datetime]] = Column(DateTime)
    actioncode: Mapped[Optional[str]] = Column(String(3))
    externalid: Mapped[Optional[str]] = Column(String(100))
    update_date: Mapped[Optional[datetime]] = Column(DateTime)


class Diagnosis(Base):
    __tablename__ = "diagnosis"

    id: Mapped[str] = Column(String, primary_key=True)
    pid: Mapped[Optional[str]] = Column(String, ForeignKey("patientrecord.pid"))

    creation_date: Mapped[datetime] = Column(
        DateTime, nullable=False, server_default=text("now()")
    )
    idx: Mapped[Optional[int]] = Column(Integer)
    diagnosistype: Mapped[Optional[str]] = Column(String(50))
    diagnosingcliniciancode: Mapped[Optional[str]] = Column(String(100))
    diagnosingcliniciancodestd: Mapped[Optional[str]] = Column(String(100))
    diagnosingcliniciandesc: Mapped[Optional[str]] = Column(String(100))
    diagnosiscode: Mapped[Optional[str]] = Column(String(100))
    diagnosiscodestd: Mapped[Optional[str]] = Column(String(100))
    diagnosisdesc: Mapped[Optional[str]] = Column(String(255))
    comments: Mapped[Optional[str]] = Column(Text)
    identificationtime: Mapped[Optional[datetime]] = Column(DateTime)
    onsettime: Mapped[Optional[datetime]] = Column(DateTime)
    enteredon: Mapped[Optional[datetime]] = Column(DateTime)
    updatedon: Mapped[Optional[datetime]] = Column(DateTime)
    actioncode: Mapped[Optional[str]] = Column(String(3))
    externalid: Mapped[Optional[str]] = Column(String(100))
    update_date: Mapped[Optional[datetime]] = Column(DateTime)
    enteredatcode: Mapped[Optional[str]] = Column(String(100))
    enteredatcodestd: Mapped[Optional[str]] = Column(String(100))
    enteredatdesc: Mapped[Optional[str]] = Column(String(100))
    encounternumber: Mapped[Optional[str]] = Column(String(100))
    verificationstatus: Mapped[Optional[str]] = Column(String(100))

    # Synonyms

    diagnosis_code: Mapped[str] = synonym("diagnosiscode")
    diagnosis_code_std: Mapped[str] = synonym("diagnosiscodestd")
    diagnosis_desc: Mapped[str] = synonym("diagnosisdesc")
    identification_time: Mapped[datetime] = synonym("identificationtime")
    onset_time: Mapped[datetime] = synonym("onsettime")


class RenalDiagnosis(Base):
    __tablename__ = "renaldiagnosis"

    pid: Mapped[str] = Column(String, ForeignKey("patientrecord.pid"), primary_key=True)

    creation_date: Mapped[datetime] = Column(
        DateTime, nullable=False, server_default=text("now()")
    )
    diagnosistype: Mapped[Optional[str]] = Column(String(50))
    diagnosiscode = Column("diagnosiscode", String)
    diagnosiscodestd = Column("diagnosiscodestd", String)
    diagnosisdesc = Column("diagnosisdesc", String)
    diagnosingcliniciancode: Mapped[Optional[str]] = Column(String(100))
    diagnosingcliniciancodestd: Mapped[Optional[str]] = Column(String(100))
    diagnosingcliniciandesc: Mapped[Optional[str]] = Column(String(100))
    comments: Mapped[Optional[str]] = Column(String)
    identificationtime = Column("identificationtime", DateTime)
    onsettime: Mapped[Optional[datetime]] = Column(DateTime)
    enteredon: Mapped[Optional[datetime]] = Column(DateTime)
    updatedon: Mapped[Optional[datetime]] = Column(DateTime)
    actioncode: Mapped[Optional[str]] = Column(String(3))
    externalid: Mapped[Optional[str]] = Column(String(100))
    update_date: Mapped[Optional[datetime]] = Column(DateTime)

    # Synonyms
    id: Mapped[str] = synonym("pid")  # see comment on cause of death
    diagnosis_code: Mapped[str] = synonym("diagnosiscode")
    diagnosis_code_std: Mapped[str] = synonym("diagnosiscodestd")
    diagnosis_desc: Mapped[str] = synonym("diagnosisdesc")
    identification_time: Mapped[datetime] = synonym("identificationtime")


class DialysisSession(Base):
    __tablename__ = "dialysissession"

    id: Mapped[str] = Column(String, primary_key=True)
    pid: Mapped[Optional[str]] = Column(String, ForeignKey("patientrecord.pid"))

    creation_date: Mapped[datetime] = Column(
        DateTime, nullable=False, server_default=text("now()")
    )
    idx: Mapped[Optional[int]] = Column(Integer)
    proceduretypecode: Mapped[Optional[str]] = Column(String(100))
    proceduretypecodestd: Mapped[Optional[str]] = Column(String(100))
    proceduretypedesc: Mapped[Optional[str]] = Column(String(100))
    cliniciancode: Mapped[Optional[str]] = Column(String(100))
    cliniciancodestd: Mapped[Optional[str]] = Column(String(100))
    cliniciandesc: Mapped[Optional[str]] = Column(String(100))
    proceduretime: Mapped[Optional[datetime]] = Column(DateTime)
    enteredbycode: Mapped[Optional[str]] = Column(String(100))
    enteredbycodestd: Mapped[Optional[str]] = Column(String(100))
    enteredbydesc: Mapped[Optional[str]] = Column(String(100))
    enteredatcode: Mapped[Optional[str]] = Column(String(100))
    enteredatcodestd: Mapped[Optional[str]] = Column(String(100))
    enteredatdesc: Mapped[Optional[str]] = Column(String(100))
    qhd19: Mapped[Optional[str]] = Column(String(255))
    qhd20: Mapped[Optional[str]] = Column(String(255))
    qhd21: Mapped[Optional[str]] = Column(String(255))
    qhd22: Mapped[Optional[str]] = Column(String(255))
    qhd30: Mapped[Optional[str]] = Column(String(255))
    qhd31: Mapped[Optional[str]] = Column(String(255))
    qhd32: Mapped[Optional[str]] = Column(String(255))
    qhd33: Mapped[Optional[str]] = Column(String(255))

    updatedon: Mapped[Optional[datetime]] = Column(DateTime)
    actioncode: Mapped[Optional[str]] = Column(String(3))
    externalid: Mapped[Optional[str]] = Column(String(100))
    update_date: Mapped[Optional[datetime]] = Column(DateTime)

    # Synonyms

    procedure_type_code: Mapped[str] = synonym("proceduretypecode")
    procedure_type_code_std: Mapped[str] = synonym("proceduretypecodestd")
    procedure_type_desc: Mapped[str] = synonym("proceduretypedesc")
    procedure_time: Mapped[datetime] = synonym("proceduretime")


class Transplant(Base):
    __tablename__ = "transplant"

    id: Mapped[str] = Column(String, primary_key=True)
    pid: Mapped[Optional[str]] = Column(String, ForeignKey("patientrecord.pid"))

    creation_date: Mapped[datetime] = Column(
        DateTime, nullable=False, server_default=text("now()")
    )
    idx: Mapped[Optional[int]] = Column(Integer)

    proceduretypecode: Mapped[Optional[str]] = Column(String(100))
    proceduretypecodestd: Mapped[Optional[str]] = Column(String(100))
    proceduretypedesc: Mapped[Optional[str]] = Column(String(100))

    cliniciancode: Mapped[Optional[str]] = Column(String(100))
    cliniciancodestd: Mapped[Optional[str]] = Column(String(100))
    cliniciandesc: Mapped[Optional[str]] = Column(String(100))

    proceduretime: Mapped[Optional[datetime]] = Column(DateTime)

    enteredbycode: Mapped[Optional[str]] = Column(String(100))
    enteredbycodestd: Mapped[Optional[str]] = Column(String(100))
    enteredbydesc: Mapped[Optional[str]] = Column(String(100))

    enteredatcode: Mapped[Optional[str]] = Column(String(100))
    enteredatcodestd: Mapped[Optional[str]] = Column(String(100))
    enteredatdesc: Mapped[Optional[str]] = Column(String(100))

    updatedon: Mapped[Optional[datetime]] = Column(DateTime)
    actioncode: Mapped[Optional[str]] = Column(String(3))
    externalid: Mapped[Optional[str]] = Column(String(100))

    tra64: Mapped[Optional[datetime]] = Column(DateTime)
    tra65: Mapped[Optional[str]] = Column(String(255))
    tra66: Mapped[Optional[str]] = Column(String(255))
    tra69: Mapped[Optional[datetime]] = Column(DateTime)
    tra76: Mapped[Optional[str]] = Column(String(255))
    tra77: Mapped[Optional[str]] = Column(String(255))
    tra78: Mapped[Optional[str]] = Column(String(255))
    tra79: Mapped[Optional[str]] = Column(String(255))
    tra80: Mapped[Optional[str]] = Column(String(255))
    tra8a: Mapped[Optional[str]] = Column(String(255))
    tra81: Mapped[Optional[str]] = Column(String(255))
    tra82: Mapped[Optional[str]] = Column(String(255))
    tra83: Mapped[Optional[str]] = Column(String(255))
    tra84: Mapped[Optional[str]] = Column(String(255))
    tra85: Mapped[Optional[str]] = Column(String(255))
    tra86: Mapped[Optional[str]] = Column(String(255))
    tra87: Mapped[Optional[str]] = Column(String(255))
    tra88: Mapped[Optional[str]] = Column(String(255))
    tra89: Mapped[Optional[str]] = Column(String(255))
    tra90: Mapped[Optional[str]] = Column(String(255))
    tra91: Mapped[Optional[str]] = Column(String(255))
    tra92: Mapped[Optional[str]] = Column(String(255))
    tra93: Mapped[Optional[str]] = Column(String(255))
    tra94: Mapped[Optional[str]] = Column(String(255))
    tra95: Mapped[Optional[str]] = Column(String(255))
    tra96: Mapped[Optional[str]] = Column(String(255))
    tra97: Mapped[Optional[str]] = Column(String(255))
    tra98: Mapped[Optional[str]] = Column(String(255))

    update_date: Mapped[Optional[datetime]] = Column(DateTime)

    # Synonyms

    procedure_type_code: Mapped[str] = synonym("proceduretypecode")
    procedure_type_code_std: Mapped[str] = synonym("proceduretypecodestd")
    procedure_type_desc: Mapped[str] = synonym("proceduretypedesc")
    procedure_time: Mapped[datetime] = synonym("proceduretime")


class VascularAccess(Base):
    __tablename__ = "vascularaccess"

    id: Mapped[str] = Column(String, primary_key=True)
    pid: Mapped[Optional[str]] = Column(String, ForeignKey("patientrecord.pid"))
    idx: Mapped[Optional[int]] = Column(Integer)

    creation_date: Mapped[datetime] = Column(
        DateTime, nullable=False, server_default=text("now()")
    )
    proceduretypecode: Mapped[Optional[str]] = Column(String(100))
    proceduretypecodestd: Mapped[Optional[str]] = Column(String(100))
    proceduretypedesc: Mapped[Optional[str]] = Column(String(100))
    cliniciancode: Mapped[Optional[str]] = Column(String(100))
    cliniciancodestd: Mapped[Optional[str]] = Column(String(100))
    cliniciandesc: Mapped[Optional[str]] = Column(String(100))
    proceduretime: Mapped[Optional[datetime]] = Column(DateTime)
    enteredbycode: Mapped[Optional[str]] = Column(String(100))
    enteredbycodestd: Mapped[Optional[str]] = Column(String(100))
    enteredbydesc: Mapped[Optional[str]] = Column(String(100))
    enteredatcode: Mapped[Optional[str]] = Column(String(100))
    enteredatcodestd: Mapped[Optional[str]] = Column(String(100))
    enteredatdesc: Mapped[Optional[str]] = Column(String(100))
    updatedon: Mapped[Optional[datetime]] = Column(DateTime)
    actioncode: Mapped[Optional[str]] = Column(String(3))
    externalid: Mapped[Optional[str]] = Column(String(100))

    acc19: Mapped[Optional[str]] = Column(String(255))
    acc20: Mapped[Optional[str]] = Column(String(255))
    acc21: Mapped[Optional[str]] = Column(String(255))
    acc22: Mapped[Optional[str]] = Column(String(255))
    acc30: Mapped[Optional[str]] = Column(String(255))
    acc40: Mapped[Optional[str]] = Column(String(255))

    update_date: Mapped[Optional[datetime]] = Column(DateTime)


class Procedure(Base):
    __tablename__ = "procedure"

    id: Mapped[str] = Column(String, primary_key=True)
    pid: Mapped[Optional[str]] = Column(String, ForeignKey("patientrecord.pid"))

    creation_date: Mapped[datetime] = Column(
        DateTime, nullable=False, server_default=text("now()")
    )
    idx: Mapped[Optional[int]] = Column(Integer)
    proceduretypecode: Mapped[Optional[str]] = Column(String(100))
    proceduretypecodestd: Mapped[Optional[str]] = Column(String(100))
    proceduretypedesc: Mapped[Optional[str]] = Column(String(100))
    cliniciancode: Mapped[Optional[str]] = Column(String(100))
    cliniciancodestd: Mapped[Optional[str]] = Column(String(100))
    cliniciandesc: Mapped[Optional[str]] = Column(String(100))
    proceduretime: Mapped[Optional[datetime]] = Column(DateTime)
    enteredbycode: Mapped[Optional[str]] = Column(String(100))
    enteredbycodestd: Mapped[Optional[str]] = Column(String(100))
    enteredbydesc: Mapped[Optional[str]] = Column(String(100))
    enteredatcode: Mapped[Optional[str]] = Column(String(100))
    enteredatcodestd: Mapped[Optional[str]] = Column(String(100))
    enteredatdesc: Mapped[Optional[str]] = Column(String(100))
    updatedon: Mapped[Optional[datetime]] = Column(DateTime)
    actioncode: Mapped[Optional[str]] = Column(String(3))
    externalid: Mapped[Optional[str]] = Column(String(100))
    update_date: Mapped[Optional[datetime]] = Column(DateTime)


class Encounter(Base):
    __tablename__ = "encounter"

    id: Mapped[str] = Column(String, primary_key=True)
    pid: Mapped[Optional[str]] = Column(String, ForeignKey("patientrecord.pid"))

    creation_date: Mapped[datetime] = Column(
        DateTime, nullable=False, server_default=text("now()")
    )
    idx: Mapped[Optional[int]] = Column(Integer)
    encounternumber: Mapped[Optional[str]] = Column(String(100))
    encountertype: Mapped[Optional[str]] = Column(String(100))
    fromtime: Mapped[Optional[datetime]] = Column(DateTime)
    totime: Mapped[Optional[datetime]] = Column(DateTime)
    admittingcliniciancode: Mapped[Optional[str]] = Column(String(100))
    admittingcliniciancodestd: Mapped[Optional[str]] = Column(String(100))
    admittingcliniciandesc: Mapped[Optional[str]] = Column(String(100))
    admitreasoncode: Mapped[Optional[str]] = Column(String(100))
    admitreasoncodestd: Mapped[Optional[str]] = Column(String(100))
    admitreasondesc: Mapped[Optional[str]] = Column(String(100))
    admissionsourcecode: Mapped[Optional[str]] = Column(String(100))
    admissionsourcecodestd: Mapped[Optional[str]] = Column(String(100))
    admissionsourcedesc: Mapped[Optional[str]] = Column(String(100))
    dischargereasoncode: Mapped[Optional[str]] = Column(String(100))
    dischargereasoncodestd: Mapped[Optional[str]] = Column(String(100))
    dischargereasondesc: Mapped[Optional[str]] = Column(String(100))
    dischargelocationcode: Mapped[Optional[str]] = Column(String(100))
    dischargelocationcodestd: Mapped[Optional[str]] = Column(String(100))
    dischargelocationdesc: Mapped[Optional[str]] = Column(String(100))
    healthcarefacilitycode: Mapped[Optional[str]] = Column(String(100))
    healthcarefacilitycodestd: Mapped[Optional[str]] = Column(String(100))
    healthcarefacilitydesc: Mapped[Optional[str]] = Column(String(100))
    enteredatcode: Mapped[Optional[str]] = Column(String(100))
    enteredatcodestd: Mapped[Optional[str]] = Column(String(100))
    enteredatdesc: Mapped[Optional[str]] = Column(String(100))
    visitdescription: Mapped[Optional[str]] = Column(String(100))
    updatedon: Mapped[Optional[datetime]] = Column(DateTime)
    actioncode: Mapped[Optional[str]] = Column(String(3))
    externalid: Mapped[Optional[str]] = Column(String(100))
    update_date: Mapped[Optional[datetime]] = Column(DateTime)

    # Synonyms

    from_time: Mapped[datetime] = synonym("fromtime")
    to_time: Mapped[datetime] = synonym("totime")


class ProgramMembership(Base):
    __tablename__ = "programmembership"

    id: Mapped[str] = Column(String, primary_key=True)
    pid: Mapped[Optional[str]] = Column(String, ForeignKey("patientrecord.pid"))

    creation_date: Mapped[datetime] = Column(
        DateTime, nullable=False, server_default=text("now()")
    )
    programname: Mapped[Optional[str]] = Column(String(100))
    programdescription: Mapped[Optional[str]] = Column(String(100))
    enteredbycode: Mapped[Optional[str]] = Column(String(100))
    enteredbycodestd: Mapped[Optional[str]] = Column(String(100))
    enteredbydesc: Mapped[Optional[str]] = Column(String(100))
    enteredatcode: Mapped[Optional[str]] = Column(String(100))
    enteredatcodestd: Mapped[Optional[str]] = Column(String(100))
    enteredatdesc: Mapped[Optional[str]] = Column(String(100))
    fromtime: Mapped[Optional[date]] = Column(Date)
    totime: Mapped[Optional[date]] = Column(Date)
    updatedon: Mapped[Optional[datetime]] = Column(DateTime)
    actioncode: Mapped[Optional[str]] = Column(String(3))
    externalid: Mapped[Optional[str]] = Column(String(100))
    update_date: Mapped[Optional[datetime]] = Column(DateTime)

    # Synonyms

    program_name: Mapped[str] = synonym("programname")
    from_time: Mapped[date] = synonym("fromtime")
    to_time: Mapped[date] = synonym("totime")

    def __str__(self):
        return (
            f"{self.__class__.__name__}({self.pid}) <"
            f"{self.program_name} {self.from_time}"
            f">"
        )


class ClinicalRelationship(Base):
    __tablename__ = "clinicalrelationship"

    id: Mapped[str] = Column(String, primary_key=True)
    pid: Mapped[Optional[str]] = Column(String, ForeignKey("patientrecord.pid"))

    creation_date: Mapped[datetime] = Column(
        DateTime, nullable=False, server_default=text("now()")
    )
    idx: Mapped[Optional[int]] = Column(Integer)
    cliniciancode: Mapped[Optional[str]] = Column(String(100))
    cliniciancodestd: Mapped[Optional[str]] = Column(String(100))
    cliniciandesc: Mapped[Optional[str]] = Column(String(100))
    facilitycode: Mapped[Optional[str]] = Column(String(100))
    facilitycodestd: Mapped[Optional[str]] = Column(String(100))
    facilitydesc: Mapped[Optional[str]] = Column(String(100))
    fromtime: Mapped[Optional[date]] = Column(Date)
    totime: Mapped[Optional[date]] = Column(Date)
    updatedon: Mapped[Optional[datetime]] = Column(DateTime)
    actioncode: Mapped[Optional[str]] = Column(String(3))
    externalid: Mapped[Optional[str]] = Column(String(100))
    update_date: Mapped[Optional[datetime]] = Column(DateTime)


class Name(Base):
    __tablename__ = "name"

    id: Mapped[str] = Column(String, primary_key=True)
    pid: Mapped[Optional[str]] = Column(String, ForeignKey("patient.pid"))

    creation_date: Mapped[datetime] = Column(
        DateTime, nullable=False, server_default=text("now()")
    )
    idx: Mapped[Optional[int]] = Column(Integer)
    nameuse: Mapped[Optional[str]] = Column(String(10))
    prefix: Mapped[Optional[str]] = Column(String(10))
    family: Mapped[Optional[str]] = Column(String(60))
    given: Mapped[Optional[str]] = Column(String(60))
    othergivennames: Mapped[Optional[str]] = Column(String(60))
    suffix: Mapped[Optional[str]] = Column(String(10))
    update_date: Mapped[Optional[datetime]] = Column(DateTime)

    def __str__(self):
        return (
            f"{self.__class__.__name__}({self.pid}) <"
            f"{self.given} {self.family}"
            f">"
        )


class PatientNumber(Base):
    __tablename__ = "patientnumber"

    id: Mapped[str] = Column(String, primary_key=True)
    pid: Mapped[Optional[str]] = Column(String, ForeignKey("patient.pid"))

    creation_date: Mapped[datetime] = Column(
        DateTime, nullable=False, server_default=text("now()")
    )
    idx: Mapped[Optional[int]] = Column(Integer)
    patientid: Mapped[Optional[str]] = Column(String(50), index=True)
    numbertype: Mapped[Optional[str]] = Column(String(3))
    organization: Mapped[Optional[str]] = Column(String(50))
    updatedon: Mapped[Optional[datetime]] = Column(DateTime)
    actioncode: Mapped[Optional[str]] = Column(String(3))
    externalid: Mapped[Optional[str]] = Column(String(100))
    update_date: Mapped[Optional[datetime]] = Column(DateTime)

    def __str__(self):
        return (
            f"{self.__class__.__name__}({self.pid}) <"
            f"{self.organization}:{self.numbertype}:{self.patientid}"
            ">"
        )


class Address(Base):
    __tablename__ = "address"

    id: Mapped[str] = Column(String, primary_key=True)
    pid: Mapped[Optional[str]] = Column(String, ForeignKey("patient.pid"))

    creation_date: Mapped[datetime] = Column(
        DateTime, nullable=False, server_default=text("now()")
    )
    idx: Mapped[Optional[int]] = Column(Integer)
    addressuse: Mapped[Optional[str]] = Column(String(10))
    fromtime: Mapped[Optional[date]] = Column(Date)
    totime: Mapped[Optional[date]] = Column(Date)
    street: Mapped[Optional[str]] = Column(String(100))
    town: Mapped[Optional[str]] = Column(String(100))
    county: Mapped[Optional[str]] = Column(String(100))
    postcode: Mapped[Optional[str]] = Column(String(10))
    countrycode: Mapped[Optional[str]] = Column(String(100))
    countrycodestd: Mapped[Optional[str]] = Column(String(100))
    countrydesc: Mapped[Optional[str]] = Column(String(100))
    update_date: Mapped[Optional[datetime]] = Column(DateTime)

    # Synonyms

    from_time: Mapped[date] = synonym("fromtime")
    to_time: Mapped[date] = synonym("totime")
    country_code: Mapped[str] = synonym("countrycode")
    country_code_std: Mapped[str] = synonym("countrycodestd")
    country_description: Mapped[str] = synonym("countrydesc")

    def __str__(self):
        return (
            f"{self.__class__.__name__}({self.pid}) <"
            f"{self.street} {self.town} {self.postcode}"
            f">"
        )


class ContactDetail(Base):
    __tablename__ = "contactdetail"

    id: Mapped[str] = Column(String, primary_key=True)
    pid: Mapped[Optional[str]] = Column(String, ForeignKey("patient.pid"))

    creation_date: Mapped[datetime] = Column(
        DateTime, nullable=False, server_default=text("now()")
    )
    idx: Mapped[Optional[int]] = Column(Integer)
    contactuse: Mapped[Optional[str]] = Column(String(10))
    contactvalue: Mapped[Optional[str]] = Column(String(100))
    commenttext: Mapped[Optional[str]] = Column(String(100))
    updatedon: Mapped[Optional[datetime]] = Column(DateTime)
    actioncode: Mapped[Optional[str]] = Column(String(3))
    externalid: Mapped[Optional[str]] = Column(String(100))
    update_date: Mapped[Optional[datetime]] = Column(DateTime)

    # Synonyms

    use: Mapped[str] = synonym("contactuse")
    value: Mapped[str] = synonym("contactvalue")

    def __str__(self):
        return f"{self.__class__.__name__}({self.pid}) <{self.use}:{self.value}>"


class Medication(Base):
    __tablename__ = "medication"

    id: Mapped[str] = Column(String, primary_key=True)
    pid: Mapped[Optional[str]] = Column(String, ForeignKey("patientrecord.pid"))

    creation_date: Mapped[datetime] = Column(
        DateTime, nullable=False, server_default=text("now()")
    )

    idx: Mapped[Optional[int]] = Column(Integer)
    repositoryupdatedate: Mapped[datetime] = Column(DateTime, nullable=False)
    prescriptionnumber: Mapped[Optional[str]] = Column(String(100))
    fromtime: Mapped[Optional[datetime]] = Column(DateTime)
    totime: Mapped[Optional[datetime]] = Column(DateTime)

    orderedbycode: Mapped[Optional[str]] = Column(String(100))
    orderedbycodestd: Mapped[Optional[str]] = Column(String(100))
    orderedbydesc: Mapped[Optional[str]] = Column(String(100))

    enteringorganizationcode: Mapped[Optional[str]] = Column(String(100))
    enteringorganizationcodestd: Mapped[Optional[str]] = Column(String(100))
    enteringorganizationdesc: Mapped[Optional[str]] = Column(String(100))

    routecode: Mapped[Optional[str]] = Column(String(10))
    routecodestd: Mapped[Optional[str]] = Column(String(100))
    routedesc: Mapped[Optional[str]] = Column(String(100))

    drugproductidcode: Mapped[Optional[str]] = Column(String(100))
    drugproductidcodestd: Mapped[Optional[str]] = Column(String(100))
    drugproductiddesc: Mapped[Optional[str]] = Column(String(100))

    drugproductgeneric: Mapped[Optional[str]] = Column(String(255))
    drugproductlabelname: Mapped[Optional[str]] = Column(String(255))

    drugproductformcode: Mapped[Optional[str]] = Column(String(100))
    drugproductformcodestd: Mapped[Optional[str]] = Column(String(100))
    drugproductformdesc: Mapped[Optional[str]] = Column(String(100))

    drugproductstrengthunitscode: Mapped[Optional[str]] = Column(String(100))
    drugproductstrengthunitscodestd: Mapped[Optional[str]] = Column(String(100))
    drugproductstrengthunitsdesc: Mapped[Optional[str]] = Column(String(100))

    frequency: Mapped[Optional[str]] = Column(String(255))
    commenttext: Mapped[Optional[str]] = Column(String(1000))
    dosequantity: Mapped[Optional[decimal.Decimal]] = Column(Numeric(19, 2))

    doseuomcode: Mapped[Optional[str]] = Column(String(100))
    doseuomcodestd: Mapped[Optional[str]] = Column(String(100))
    doseuomdesc: Mapped[Optional[str]] = Column(String(100))

    indication: Mapped[Optional[str]] = Column(String(100))
    updatedon: Mapped[Optional[datetime]] = Column(DateTime)
    actioncode: Mapped[Optional[str]] = Column(String(3))
    externalid: Mapped[Optional[str]] = Column(String(100))
    update_date: Mapped[Optional[datetime]] = Column(DateTime)
    encounternumber: Mapped[Optional[str]] = Column(String(100))

    # Synonyms

    repository_update_date: Mapped[datetime] = synonym("repositoryupdatedate")
    from_time: Mapped[datetime] = synonym("fromtime")
    to_time: Mapped[datetime] = synonym("totime")
    entering_organization_code: Mapped[str] = synonym("enteringorganizationcode")
    entering_organization_description: Mapped[str] = synonym("enteringorganizationdesc")
    route_code: Mapped[str] = synonym("routecode")
    route_code_std: Mapped[str] = synonym("routecodestd")
    route_desc: Mapped[str] = synonym("routedesc")
    drug_product_id_code: Mapped[str] = synonym("drugproductidcode")
    drug_product_id_description: Mapped[str] = synonym("drugproductiddesc")
    drug_product_generic: Mapped[str] = synonym("drugproductgeneric")
    comment: Mapped[str] = synonym("commenttext")
    dose_quantity: Mapped[str] = synonym("dosequantity")
    dose_uom_code: Mapped[str] = synonym("doseuomcode")
    dose_uom_code_std: Mapped[str] = synonym("doseuomcodestd")
    dose_uom_description: Mapped[str] = synonym("doseuomdesc")
    updated_on: Mapped[datetime] = synonym("updatedon")
    external_id: Mapped[str] = synonym("externalid")

    def __str__(self):
        return f"{self.__class__.__name__}({self.pid})"


class Survey(Base):
    __tablename__ = "survey"

    id: Mapped[str] = Column(String, primary_key=True)
    pid: Mapped[Optional[str]] = Column(String, ForeignKey("patientrecord.pid"))

    creation_date: Mapped[datetime] = Column(
        DateTime, nullable=False, server_default=text("now()")
    )
    surveytime: Mapped[datetime] = Column(DateTime, nullable=False)
    surveytypecode: Mapped[Optional[str]] = Column(String(100))
    surveytypecodestd: Mapped[Optional[str]] = Column(String(100))
    surveytypedesc: Mapped[Optional[str]] = Column(String(100))
    typeoftreatment: Mapped[Optional[str]] = Column(String(100))
    hdlocation: Mapped[Optional[str]] = Column(String(100))
    template: Mapped[Optional[str]] = Column(String(100))
    enteredbycode: Mapped[Optional[str]] = Column(String(100))
    enteredbycodestd: Mapped[Optional[str]] = Column(String(100))
    enteredbydesc: Mapped[Optional[str]] = Column(String(100))
    enteredatcode: Mapped[Optional[str]] = Column(String(100))
    enteredatcodestd: Mapped[Optional[str]] = Column(String(100))
    enteredatdesc: Mapped[Optional[str]] = Column(String(100))
    updatedon: Mapped[Optional[datetime]] = Column(DateTime)
    actioncode: Mapped[Optional[str]] = Column(String(3))
    externalid: Mapped[Optional[str]] = Column(String(100))
    update_date: Mapped[Optional[datetime]] = Column(DateTime)

    # Relationships

    questions:Mapped[List["Question"]] = relationship("Question", cascade="all, delete-orphan")
    scores:Mapped[List["Score"]] = relationship("Score", cascade="all, delete-orphan")
    levels:Mapped[List["Level"]] = relationship("Level", cascade="all, delete-orphan")

    def __str__(self):
        return (
            f"{self.__class__.__name__}({self.pid}) <"
            f"{self.surveytime}:{self.surveytypecode}"
            f">"
        )


class Question(Base):
    __tablename__ = "question"

    id: Mapped[str] = Column(String, primary_key=True)

    surveyid: Mapped[Optional[str]] = Column(String, ForeignKey("survey.id"))
    creation_date: Mapped[datetime] = Column(
        DateTime, nullable=False, server_default=text("now()")
    )
    idx: Mapped[Optional[int]] = Column(Integer)
    questiontypecode: Mapped[Optional[str]] = Column(String(100))
    questiontypecodestd: Mapped[Optional[str]] = Column(String(100))
    questiontypedesc: Mapped[Optional[str]] = Column(String(100))
    response: Mapped[Optional[str]] = Column(String(100))
    questiontext: Mapped[Optional[str]] = Column(String(100))
    update_date: Mapped[Optional[datetime]] = Column(DateTime)


class Score(Base):
    __tablename__ = "score"

    id: Mapped[str] = Column(String, primary_key=True)

    surveyid: Mapped[Optional[str]] = Column(String, ForeignKey("survey.id"))
    creation_date: Mapped[datetime] = Column(
        DateTime, nullable=False, server_default=text("now()")
    )
    idx: Mapped[Optional[int]] = Column(Integer)
    scorevalue: Mapped[Optional[str]] = Column(String(100))
    scoretypecode: Mapped[Optional[str]] = Column(String(100))
    scoretypecodestd: Mapped[Optional[str]] = Column(String(100))
    scoretypedesc: Mapped[Optional[str]] = Column(String(100))
    update_date: Mapped[Optional[datetime]] = Column(DateTime)

    # Synonyms

    value: Mapped[str] = synonym("scorevalue")


class Level(Base):
    __tablename__ = "level"

    id: Mapped[str] = Column(String, primary_key=True)

    surveyid: Mapped[Optional[str]] = Column(String, ForeignKey("survey.id"))
    creation_date: Mapped[datetime] = Column(
        DateTime, nullable=False, server_default=text("now()")
    )
    idx: Mapped[Optional[int]] = Column(Integer)
    levelvalue: Mapped[Optional[str]] = Column(String(100))
    leveltypecode: Mapped[Optional[str]] = Column(String(100))
    leveltypecodestd: Mapped[Optional[str]] = Column(String(100))
    leveltypedesc: Mapped[Optional[str]] = Column(String(100))
    update_date: Mapped[Optional[datetime]] = Column(DateTime)

    # Synonyms

    value: Mapped[str] = synonym("levelvalue")


class Document(Base):
    __tablename__ = "document"

    id: Mapped[str] = Column(String, primary_key=True)
    pid: Mapped[Optional[str]] = Column(String, ForeignKey("patientrecord.pid"))

    repositoryupdatedate: Mapped[datetime] = Column(DateTime, nullable=False)
    creation_date: Mapped[datetime] = Column(
        DateTime, nullable=False, server_default=text("now()")
    )
    idx: Mapped[Optional[int]] = Column(Integer)
    documenttime: Mapped[Optional[datetime]] = Column(DateTime)
    notetext: Mapped[Optional[str]] = Column(Text)
    documenttypecode: Mapped[Optional[str]] = Column(String(100))
    documenttypecodestd: Mapped[Optional[str]] = Column(String(100))
    documenttypedesc: Mapped[Optional[str]] = Column(String(100))
    cliniciancode: Mapped[Optional[str]] = Column(String(100))
    cliniciancodestd: Mapped[Optional[str]] = Column(String(100))
    cliniciandesc: Mapped[Optional[str]] = Column(String(100))
    documentname: Mapped[Optional[str]] = Column(String(100))
    statuscode: Mapped[Optional[str]] = Column(String(100))
    statuscodestd: Mapped[Optional[str]] = Column(String(100))
    statusdesc: Mapped[Optional[str]] = Column(String(100))
    enteredbycode: Mapped[Optional[str]] = Column(String(100))
    enteredbycodestd: Mapped[Optional[str]] = Column(String(100))
    enteredbydesc: Mapped[Optional[str]] = Column(String(100))
    enteredatcode: Mapped[Optional[str]] = Column(String(100))
    enteredatcodestd: Mapped[Optional[str]] = Column(String(100))
    enteredatdesc: Mapped[Optional[str]] = Column(String(100))
    filetype: Mapped[Optional[str]] = Column(String(100))
    filename: Mapped[Optional[str]] = Column(String(100))
    stream: Mapped[Optional[bytes]] = Column(LargeBinary)
    documenturl: Mapped[Optional[str]] = Column(String(100))
    updatedon: Mapped[Optional[datetime]] = Column(DateTime)
    actioncode: Mapped[Optional[str]] = Column(String(3))
    externalid: Mapped[Optional[str]] = Column(String(100))
    update_date: Mapped[Optional[datetime]] = Column(DateTime)

    # Synonyms

    repository_update_date = synonym("repositoryupdatedate")


class LabOrder(Base):
    __tablename__ = "laborder"

    id: Mapped[str] = Column(String, primary_key=True)
    pid: Mapped[Optional[str]] = Column(String, ForeignKey("patientrecord.pid"))

    creation_date = Column(
        DateTime, nullable=False, index=True, server_default=text("now()")
    )
    placerid: Mapped[Optional[str]] = Column(String(100))
    fillerid: Mapped[Optional[str]] = Column(String(100))
    receivinglocationcode: Mapped[Optional[str]] = Column(String(100))
    receivinglocationcodestd: Mapped[Optional[str]] = Column(String(100))
    receivinglocationdesc: Mapped[Optional[str]] = Column(String(100))
    orderedbycode: Mapped[Optional[str]] = Column(String(100))
    orderedbycodestd: Mapped[Optional[str]] = Column(String(100))
    orderedbydesc: Mapped[Optional[str]] = Column(String(100))
    orderitemcode: Mapped[Optional[str]] = Column(String(100))
    orderitemcodestd: Mapped[Optional[str]] = Column(String(100))
    orderitemdesc: Mapped[Optional[str]] = Column(String(100))
    prioritycode: Mapped[Optional[str]] = Column(String(100))
    prioritycodestd: Mapped[Optional[str]] = Column(String(100))
    prioritydesc: Mapped[Optional[str]] = Column(String(100))
    status: Mapped[Optional[str]] = Column(String(100))
    ordercategorycode: Mapped[Optional[str]] = Column(String(100))
    ordercategorycodestd: Mapped[Optional[str]] = Column(String(100))
    ordercategorydesc: Mapped[Optional[str]] = Column(String(100))
    specimensource: Mapped[Optional[str]] = Column(String(50))
    specimenreceivedtime: Mapped[Optional[datetime]] = Column(DateTime)
    specimencollectedtime: Mapped[Optional[datetime]] = Column(DateTime)
    duration: Mapped[Optional[str]] = Column(String(50))
    patientclasscode: Mapped[Optional[str]] = Column(String(100))
    patientclasscodestd: Mapped[Optional[str]] = Column(String(100))
    patientclassdesc: Mapped[Optional[str]] = Column(String(100))
    enteredon: Mapped[Optional[datetime]] = Column(DateTime)
    enteredatcode: Mapped[Optional[str]] = Column(String(100))
    enteredatcodestd: Mapped[Optional[str]] = Column(String(100))
    enteredatdesc: Mapped[Optional[str]] = Column(String(100))
    enteringorganizationcode: Mapped[Optional[str]] = Column(String(100))
    enteringorganizationcodestd: Mapped[Optional[str]] = Column(String(100))
    enteringorganizationdesc: Mapped[Optional[str]] = Column(String(100))
    updatedon: Mapped[Optional[datetime]] = Column(DateTime)
    actioncode: Mapped[Optional[str]] = Column(String(3))
    externalid: Mapped[Optional[str]] = Column(String(100))
    update_date: Mapped[Optional[datetime]] = Column(DateTime, index=True)
    repository_update_date: Mapped[Optional[datetime]] = Column(DateTime, index=True)

    # Synonyms

    receiving_location: Mapped[str] = synonym("receivinglocationcode")
    receiving_location_description: Mapped[str] = synonym("receivinglocationdesc")
    receiving_location_code_std: Mapped[str] = synonym("receivinglocationcodestd")
    placer_id: Mapped[str] = synonym("placerid")
    filler_id: Mapped[str] = synonym("fillerid")
    ordered_by: Mapped[str] = synonym("orderedbycode")
    ordered_by_description: Mapped[str] = synonym("orderedbydesc")
    ordered_by_code_std: Mapped[str] = synonym("orderedbycodestd")
    order_item: Mapped[str] = synonym("orderitemcode")
    order_item_description: Mapped[str] = synonym("orderitemdesc")
    order_item_code_std: Mapped[str] = synonym("orderitemcodestd")
    order_category: Mapped[str] = synonym("ordercategorycode")
    order_category_description: Mapped[str] = synonym("ordercategorydesc")
    order_category_code_std: Mapped[str] = synonym("ordercategorycodestd")
    specimen_collected_time: Mapped[datetime] = synonym("specimencollectedtime")
    specimen_received_time: Mapped[datetime] = synonym("specimenreceivedtime")
    priority: Mapped[str] = synonym("prioritycode")
    priority_description: Mapped[str] = synonym("prioritydesc")
    priority_code_std: Mapped[str] = synonym("prioritycodestd")
    specimen_source: Mapped[str] = synonym("specimensource")
    patient_class: Mapped[str] = synonym("patientclasscode")
    patient_class_description: Mapped[str] = synonym("patientclassdesc")
    patient_class_code_std: Mapped[str] = synonym("patientclasscodestd")
    entered_on: Mapped[datetime] = synonym("enteredon")
    entered_at: Mapped[str] = synonym("enteredatcode")
    entered_at_description: Mapped[str] = synonym("enteredatdesc")
    external_id: Mapped[str] = synonym("externalid")
    entering_organization_code: Mapped[str] = synonym("enteringorganizationcode")
    entering_organization_description: Mapped[str] = synonym("enteringorganizationdesc")
    entering_organization_code_std: Mapped[str] = synonym("enteringorganizationcodestd")

    # Relationships

    result_items: DynamicRel["ResultItem"] = relationship(
        "ResultItem",
        lazy=GLOBAL_LAZY,
        back_populates="order",
        cascade="all, delete-orphan",
    )


class ResultItem(Base):
    __tablename__ = "resultitem"

    id: Mapped[str] = Column(String, primary_key=True)

    order_id = Column("orderid", String, ForeignKey("laborder.id"))
    creation_date: Mapped[datetime] = Column(
        DateTime, nullable=False, server_default=text("now()")
    )
    resulttype: Mapped[Optional[str]] = Column(String(2))
    serviceidcode: Mapped[Optional[str]] = Column(String(100))
    serviceidcodestd: Mapped[Optional[str]] = Column(String(100))
    serviceiddesc: Mapped[Optional[str]] = Column(String(100))
    subid: Mapped[Optional[str]] = Column(String(50))
    resultvalue: Mapped[Optional[str]] = Column(String(20))
    resultvalueunits: Mapped[Optional[str]] = Column(String(30))
    referencerange: Mapped[Optional[str]] = Column(String(30))
    interpretationcodes: Mapped[Optional[str]] = Column(String(50))
    status: Mapped[Optional[str]] = Column(String(5))
    observationtime: Mapped[Optional[datetime]] = Column(DateTime)
    commenttext: Mapped[Optional[str]] = Column(String(1000))
    referencecomment: Mapped[Optional[str]] = Column(String(1000))
    prepost: Mapped[Optional[str]] = Column(String(4))
    enteredon: Mapped[Optional[datetime]] = Column(DateTime)
    updatedon: Mapped[Optional[datetime]] = Column(DateTime)
    actioncode: Mapped[Optional[str]] = Column(String(3))
    externalid: Mapped[Optional[str]] = Column(String(100))
    update_date: Mapped[Optional[datetime]] = Column(DateTime)

    # Proxies

    pid = association_proxy("order", "pid")

    # Synonyms

    result_type: Mapped[str] = synonym("resulttype")
    entered_on: Mapped[datetime] = synonym("enteredon")
    pre_post: Mapped[str] = synonym("prepost")
    service_id: Mapped[str] = synonym("serviceidcode")
    service_id_std: Mapped[str] = synonym("serviceidcodestd")
    service_id_description: Mapped[str] = synonym("serviceiddesc")
    sub_id: Mapped[str] = synonym("subid")
    value: Mapped[str] = synonym("resultvalue")
    value_units: Mapped[str] = synonym("resultvalueunits")
    reference_range: Mapped[str] = synonym("referencerange")
    interpretation_codes: Mapped[str] = synonym("interpretationcodes")
    observation_time: Mapped[datetime] = synonym("observationtime")
    comments: Mapped[str] = synonym("commenttext")
    reference_comment: Mapped[str] = synonym("referencecomment")

    # Relationships
    order: Mapped[List[LabOrder]] = relationship(
        "LabOrder", back_populates="result_items"
    )


class PVData(Base):
    __tablename__ = "pvdata"

    id: Mapped[str] = Column(String, ForeignKey("patientrecord.pid"), primary_key=True)

    creation_date: Mapped[datetime] = Column(
        DateTime, nullable=False, server_default=text("now()")
    )
    update_date: Mapped[Optional[datetime]] = Column(DateTime)

    diagnosisdate: Mapped[Optional[date]] = Column(Date)

    bloodgroup: Mapped[Optional[str]] = Column(String(10))

    rrtstatus: Mapped[Optional[str]] = Column(String(100))
    tpstatus: Mapped[Optional[str]] = Column(String(100))

    # Proxies

    rrtstatus_desc = association_proxy("rrtstatus_info", "description")
    tpstatus_desc = association_proxy("tpstatus_info", "description")

    # Relationships
    rrtstatus_info:Mapped[List["Code"]]= relationship(
        "Code",
        primaryjoin="and_(remote(Code.coding_standard)=='PV_RRTSTATUS', foreign(PVData.rrtstatus)==remote(Code.code))",
    )

    tpstatus_info:Mapped[List["Code"]] = relationship(
        "Code",
        primaryjoin="and_(remote(Code.coding_standard)=='PV_TPSTATUS', foreign(PVData.tpstatus)==remote(Code.code))",
    )

    def __str__(self):
        return f"{self.__class__.__name__}({self.id})"


class PVDelete(Base):
    __tablename__ = "pvdelete"

    did: Mapped[int] = Column(Integer, primary_key=True)

    pid: Mapped[Optional[str]] = Column(String, ForeignKey("patientrecord.pid"))
    creation_date: Mapped[datetime] = Column(
        DateTime, nullable=False, server_default=text("now()")
    )
    observationtime: Mapped[Optional[datetime]] = Column(DateTime)
    serviceidcode: Mapped[Optional[str]] = Column(String(100))
    update_date: Mapped[Optional[datetime]] = Column(DateTime)

    # Synonyms

    observation_time: Mapped[datetime] = synonym("observationtime")
    service_id: Mapped[str] = synonym("serviceidcode")


class Treatment(Base):
    __tablename__ = "treatment"

    id: Mapped[str] = Column(String, primary_key=True)
    pid: Mapped[Optional[str]] = Column(String, ForeignKey("patientrecord.pid"))

    creation_date: Mapped[datetime] = Column(
        DateTime, nullable=False, server_default=text("now()")
    )
    idx: Mapped[Optional[int]] = Column(Integer)
    encounternumber: Mapped[Optional[str]] = Column(String(100))
    encountertype: Mapped[Optional[str]] = Column(String(100))
    fromtime: Mapped[Optional[datetime]] = Column(DateTime)
    totime: Mapped[Optional[datetime]] = Column(DateTime)
    admittingcliniciancode: Mapped[Optional[str]] = Column(String(100))
    admittingcliniciancodestd: Mapped[Optional[str]] = Column(String(100))
    admittingcliniciandesc: Mapped[Optional[str]] = Column(String(100))
    admitreasoncode: Mapped[Optional[str]] = Column(String(100))
    admitreasoncodestd: Mapped[Optional[str]] = Column(String(100))
    admitreasondesc: Mapped[Optional[str]] = Column(String(100))
    admissionsourcecode: Mapped[Optional[str]] = Column(String(100))
    admissionsourcecodestd: Mapped[Optional[str]] = Column(String(100))
    admissionsourcedesc: Mapped[Optional[str]] = Column(String(100))
    dischargereasoncode: Mapped[Optional[str]] = Column(String(100))
    dischargereasoncodestd: Mapped[Optional[str]] = Column(String(100))
    dischargereasondesc: Mapped[Optional[str]] = Column(String(100))
    dischargelocationcode: Mapped[Optional[str]] = Column(String(100))
    dischargelocationcodestd: Mapped[Optional[str]] = Column(String(100))
    dischargelocationdesc: Mapped[Optional[str]] = Column(String(100))
    healthcarefacilitycode: Mapped[Optional[str]] = Column(String(100))
    healthcarefacilitycodestd: Mapped[Optional[str]] = Column(String(100))
    healthcarefacilitydesc: Mapped[Optional[str]] = Column(String(100))
    enteredatcode: Mapped[Optional[str]] = Column(String(100))
    enteredatcodestd: Mapped[Optional[str]] = Column(String(100))
    enteredatdesc: Mapped[Optional[str]] = Column(String(100))
    visitdescription: Mapped[Optional[str]] = Column(String(100))
    updatedon: Mapped[Optional[datetime]] = Column(DateTime)
    actioncode: Mapped[Optional[str]] = Column(String(3))
    externalid: Mapped[Optional[str]] = Column(String(100))
    hdp01: Mapped[Optional[str]] = Column(String(255))
    hdp02: Mapped[Optional[str]] = Column(String(255))
    hdp03: Mapped[Optional[str]] = Column(String(255))
    hdp04: Mapped[Optional[str]] = Column(String(255))
    qbl05: Mapped[Optional[str]] = Column(String(255))
    qbl06: Mapped[Optional[str]] = Column(String(255))
    qbl07: Mapped[Optional[str]] = Column(String(255))
    erf61: Mapped[Optional[str]] = Column(String(255))
    pat35: Mapped[Optional[str]] = Column(String(255))
    update_date: Mapped[Optional[datetime]] = Column(DateTime)

    # Synonyms

    encounter_number: Mapped[str] = synonym("encounternumber")
    encounter_type: Mapped[str] = synonym("encountertype")
    from_time: Mapped[datetime] = synonym("fromtime")
    to_time: Mapped[datetime] = synonym("totime")
    admitting_clinician_code: Mapped[str] = synonym("admittingcliniciancode")
    admitting_clinician_code_std: Mapped[str] = synonym("admittingcliniciancodestd")
    admitting_clinician_desc: Mapped[str] = synonym("admittingcliniciandesc")
    admission_source_code: Mapped[str] = synonym("admissionsourcecode")
    admission_source_code_std: Mapped[str] = synonym("admissionsourcecodestd")
    admission_source_desc: Mapped[str] = synonym("admissionsourcedesc")
    admit_reason_code: Mapped[str] = synonym("admitreasoncode")
    admit_reason_code_std: Mapped[str] = synonym("admitreasoncodestd")
    discharge_reason_code: Mapped[str] = synonym("dischargereasoncode")
    discharge_reason_code_std: Mapped[str] = synonym("dischargereasoncodestd")
    discharge_location_code: Mapped[str] = synonym("dischargelocationcode")
    discharge_location_code_std: Mapped[str] = synonym("dischargelocationcodestd")
    discharge_location_desc: Mapped[str] = synonym("dischargelocationdesc")
    health_care_facility_code: Mapped[str] = synonym("healthcarefacilitycode")
    health_care_facility_code_std: Mapped[str] = synonym("healthcarefacilitycodestd")
    health_care_facility_desc: Mapped[str] = synonym("healthcarefacilitydesc")
    entered_at_code: Mapped[str] = synonym("enteredatcode")
    visit_description: Mapped[str] = synonym("visitdescription")
    updated_on: Mapped[datetime] = synonym("updatedon")
    action_code: Mapped[str] = synonym("actioncode")
    external_id: Mapped[str] = synonym("externalid")

    # Proxies

    admit_reason_desc = association_proxy("admit_reason_code_item", "description")
    discharge_reason_desc = association_proxy(
        "discharge_reason_code_item", "description"
    )

    # Relationships

    admit_reason_code_item:Mapped[List["Code"]] = relationship(
        "Code",
        primaryjoin="and_(foreign(Treatment.admit_reason_code_std)==remote(Code.coding_standard), foreign(Treatment.admit_reason_code)==remote(Code.code))",
    )

    discharge_reason_code_item:Mapped[List["Code"]] = relationship(
        "Code",
        primaryjoin="and_(foreign(Treatment.discharge_reason_code_std)==remote(Code.coding_standard), foreign(Treatment.discharge_reason_code)==remote(Code.code))",
    )


class TransplantList(Base):
    __tablename__ = "transplantlist"

    id: Mapped[str] = Column(String, primary_key=True)
    pid: Mapped[Optional[str]] = Column(String, ForeignKey("patientrecord.pid"))

    idx: Mapped[Optional[int]] = Column(Integer)
    creation_date: Mapped[datetime] = Column(
        DateTime, nullable=False, server_default=text("now()")
    )
    encounternumber: Mapped[Optional[str]] = Column(String(100))
    encountertype: Mapped[Optional[str]] = Column(String(100))
    fromtime: Mapped[Optional[datetime]] = Column(DateTime)
    totime: Mapped[Optional[datetime]] = Column(DateTime)
    admittingcliniciancode: Mapped[Optional[str]] = Column(String(100))
    admittingcliniciancodestd: Mapped[Optional[str]] = Column(String(100))
    admittingcliniciandesc: Mapped[Optional[str]] = Column(String(100))
    admitreasoncode: Mapped[Optional[str]] = Column(String(100))
    admitreasoncodestd: Mapped[Optional[str]] = Column(String(100))
    admitreasondesc: Mapped[Optional[str]] = Column(String(100))
    admissionsourcecode: Mapped[Optional[str]] = Column(String(100))
    admissionsourcecodestd: Mapped[Optional[str]] = Column(String(100))
    admissionsourcedesc: Mapped[Optional[str]] = Column(String(100))
    dischargereasoncode: Mapped[Optional[str]] = Column(String(100))
    dischargereasoncodestd: Mapped[Optional[str]] = Column(String(100))
    dischargereasondesc: Mapped[Optional[str]] = Column(String(100))
    dischargelocationcode: Mapped[Optional[str]] = Column(String(100))
    dischargelocationcodestd: Mapped[Optional[str]] = Column(String(100))
    dischargelocationdesc: Mapped[Optional[str]] = Column(String(100))
    healthcarefacilitycode: Mapped[Optional[str]] = Column(String(100))
    healthcarefacilitycodestd: Mapped[Optional[str]] = Column(String(100))
    healthcarefacilitydesc: Mapped[Optional[str]] = Column(String(100))
    enteredatcode: Mapped[Optional[str]] = Column(String(100))
    enteredatcodestd: Mapped[Optional[str]] = Column(String(100))
    enteredatdesc: Mapped[Optional[str]] = Column(String(100))
    visitdescription: Mapped[Optional[str]] = Column(String(100))
    updatedon: Mapped[Optional[datetime]] = Column(DateTime)
    actioncode: Mapped[Optional[str]] = Column(String(3))
    externalid: Mapped[Optional[str]] = Column(String(100))
    update_date: Mapped[Optional[datetime]] = Column(DateTime)


class Code(Base):
    __tablename__ = "code_list"

    coding_standard: Mapped[str] = Column(String(256), primary_key=True)
    code: Mapped[str] = Column(String(256), primary_key=True)
    creation_date: Mapped[datetime] = Column(
        DateTime, nullable=False, server_default=text("now()")
    )
    description: Mapped[Optional[str]] = Column(String(256))
    object_type: Mapped[Optional[str]] = Column(String(256))
    update_date: Mapped[Optional[datetime]] = Column(DateTime)
    units: Mapped[Optional[str]] = Column(String(256))
    pkb_reference_range: Mapped[Optional[str]] = Column(String(10))
    pkb_comment: Mapped[Optional[str]] = Column(String(365))


class CodeExclusion(Base):
    __tablename__ = "code_exclusion"

    coding_standard: Mapped[str] = Column(String, primary_key=True)
    code: Mapped[str] = Column(String, primary_key=True)
    system: Mapped[str] = Column(String, primary_key=True)


class CodeMap(Base):
    __tablename__ = "code_map"

    source_coding_standard: Mapped[str] = Column(String(256), primary_key=True)
    source_code: Mapped[str] = Column(String(256), primary_key=True)
    destination_coding_standard: Mapped[str] = Column(String(256), primary_key=True)
    destination_code: Mapped[str] = Column(String(256), primary_key=True)

    creation_date: Mapped[datetime] = Column(
        DateTime, nullable=False, server_default=text("now()")
    )
    update_date: Mapped[Optional[datetime]] = Column(DateTime)


class Facility(Base):
    __tablename__ = "facility"

    code = Column("code", String, primary_key=True)
    creation_date: Mapped[datetime] = Column(
        DateTime, nullable=False, server_default=text("now()")
    )
    pkb_out: Mapped[Optional[bool]] = Column(Boolean, server_default=text("false"))
    pkb_in: Mapped[Optional[bool]] = Column(Boolean, server_default=text("false"))
    pkb_msg_exclusions: Mapped[Optional[List[str]]] = Column(ARRAY(Text()))
    update_date: Mapped[Optional[datetime]] = Column(DateTime)

    # Proxies

    description = association_proxy("code_info", "description")

    # Relationships

    code_info:Mapped[List["Code"]] = relationship(
        "Code",
        primaryjoin="and_(remote(Code.coding_standard)=='RR1+', foreign(Facility.code)==remote(Code.code))",
    )


class RRCodes(Base):
    __tablename__ = "rr_codes"

    id: Mapped[str] = Column(String, primary_key=True)
    rr_code = Column("rr_code", String, primary_key=True)

    description_1: Mapped[Optional[str]] = Column(String(255))
    description_2: Mapped[Optional[str]] = Column(String(70))
    description_3: Mapped[Optional[str]] = Column(String(60))

    old_value: Mapped[Optional[str]] = Column(String(10))
    old_value_2: Mapped[Optional[str]] = Column(String(10))
    new_value: Mapped[Optional[str]] = Column(String(10))


class Locations(Base):
    __tablename__ = "locations"

    centre_code: Mapped[str] = Column(String(10), primary_key=True)
    centre_name: Mapped[Optional[str]] = Column(String(255))
    country_code: Mapped[Optional[str]] = Column(String(6))
    region_code: Mapped[Optional[str]] = Column(String(10))
    paed_unit: Mapped[Optional[int]] = Column(Integer)


class RRDataDefinition(Base):
    __tablename__ = "rr_data_definition"

    upload_key: Mapped[str] = Column(String(5), primary_key=True)

    table_name = Column("TABLE_NAME", String(30), nullable=False)
    feild_name: Mapped[str] = Column(String(30), nullable=False)
    code_id: Mapped[Optional[str]] = Column(String(10))
    mandatory: Mapped[Optional[decimal.Decimal]] = Column(Numeric(1, 0))

    type = Column("TYPE", String(1))

    alt_constraint: Mapped[Optional[str]] = Column(String(30))
    alt_desc: Mapped[Optional[str]] = Column(String(30))
    extra_val: Mapped[Optional[str]] = Column(String(1))
    error_type: Mapped[Optional[int]] = Column(Integer)
    paed_mand: Mapped[Optional[decimal.Decimal]] = Column(Numeric(1, 0))
    ckd5_mand_numeric = Column("ckd5_mand", Numeric(1, 0))
    dependant_field: Mapped[Optional[str]] = Column(String(30))
    alt_validation: Mapped[Optional[str]] = Column(String(30))

    file_prefix: Mapped[Optional[str]] = Column(String(20))

    load_min: Mapped[Optional[decimal.Decimal]] = Column(Numeric(38, 4))
    load_max: Mapped[Optional[decimal.Decimal]] = Column(Numeric(38, 4))
    remove_min: Mapped[Optional[decimal.Decimal]] = Column(Numeric(38, 4))
    remove_max: Mapped[Optional[decimal.Decimal]] = Column(Numeric(38, 4))
    in_month: Mapped[Optional[decimal.Decimal]] = Column(Numeric(1, 0))
    aki_mand: Mapped[Optional[decimal.Decimal]] = Column(Numeric(1, 0))
    rrt_mand: Mapped[Optional[decimal.Decimal]] = Column(Numeric(1, 0))
    cons_mand: Mapped[Optional[decimal.Decimal]] = Column(Numeric(1, 0))
    ckd4_mand: Mapped[Optional[decimal.Decimal]] = Column(Numeric(1, 0))
    valid_before_dob: Mapped[Optional[decimal.Decimal]] = Column(Numeric(1, 0))
    valid_after_dod: Mapped[Optional[decimal.Decimal]] = Column(Numeric(1, 0))
    in_quarter: Mapped[Optional[decimal.Decimal]] = Column(Numeric(1, 0))

    # Synonyms

    code_type: Mapped[str] = synonym("type")


class ModalityCodes(Base):
    __tablename__ = "modality_codes"

    registry_code: Mapped[str] = Column(String(8), primary_key=True)

    registry_code_desc: Mapped[Optional[str]] = Column(String(100))
    registry_code_type: Mapped[str] = Column(String(3), nullable=False)
    acute: Mapped[bool] = Column(BIT(1), nullable=False)
    transfer_in: Mapped[bool] = Column(BIT(1), nullable=False)
    ckd: Mapped[bool] = Column(BIT(1), nullable=False)
    cons: Mapped[bool] = Column(BIT(1), nullable=False)
    rrt: Mapped[bool] = Column(BIT(1), nullable=False)
    equiv_modality: Mapped[Optional[str]] = Column(String(8))
    end_of_care: Mapped[bool] = Column(BIT(1), nullable=False)
    is_imprecise: Mapped[bool] = Column(BIT(1), nullable=False)
    nhsbt_transplant_type: Mapped[Optional[str]] = Column(String(4))
    transfer_out: Mapped[Optional[bool]] = Column(BIT(1))


class SatelliteMap(Base):
    __tablename__ = "satellite_map"

    satellite_code: Mapped[str] = Column(String(10), primary_key=True)
    main_unit_code: Mapped[str] = Column(String(10), primary_key=True)

    creation_date: Mapped[datetime] = Column(
        DateTime, nullable=False, server_default=text("now()")
    )
    update_date: Mapped[Optional[datetime]] = Column(DateTime)
