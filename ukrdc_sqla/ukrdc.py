"""Models which relate to the main UKRDC database"""

from dataclasses import dataclass
from datetime import date
from datetime import datetime
from decimal import Decimal
from typing import List, Optional, Union, Tuple, Any

from sqlalchemy import (
    Boolean,
    ForeignKeyConstraint,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    LargeBinary,
    Numeric,
    String,
    Text,
    text,
    Enum,
)
from sqlalchemy.dialects.postgresql import ARRAY, BIT, JSON
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.orm import (
    Mapped,
    relationship,
    synonym,
    mapped_column as _mapped_column,
    DeclarativeBase,
    MappedColumn,
)


@dataclass
class ColumnInfo:
    label: str
    description: str


def mapped_column(
    *args: Any,
    sqla_info: Optional[ColumnInfo] = None,
    **kwargs: Any,
) -> MappedColumn:
    """A mapped_column wrapper that supports typed metadata via a ColumnInfo dataclass."""
    info = dict(kwargs.pop("info", {}) or {})
    if sqla_info:
        info["sqla_info"] = sqla_info
        if "comment" not in kwargs and sqla_info.description:
            kwargs["comment"] = sqla_info.description
    return _mapped_column(*args, info=info, **kwargs)


def get_column_info(model, column_name: str) -> Optional[ColumnInfo]:
    """Retrieve ColumnInfo for a given column by name."""
    col = model.__table__.c[column_name]
    return col.info.get("sqla_info")


class Base(DeclarativeBase):
    pass


GLOBAL_LAZY = "dynamic"


class SendingExtractMetadata(Base):
    """Metadata about sending extracts including schedule status and configuration."""

    __tablename__ = "sendingextractmetadata"

    sendingextract: Mapped[str] = mapped_column(String(100), primary_key=True)
    on_schedule: Mapped[int] = mapped_column(BIT(1), nullable=False)
    metadata_: Mapped[Optional[dict[str, Any]]] = mapped_column(
        "metadata", JSON, nullable=True
    )
    comment: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class PatientRecord(Base):
    __tablename__ = "patientrecord"

    pid: Mapped[str] = mapped_column(String, primary_key=True)
    sendingfacility: Mapped[str] = mapped_column(String(7), nullable=False)
    sendingextract: Mapped[str] = mapped_column(String(6), nullable=False)
    localpatientid: Mapped[str] = mapped_column(String(17), nullable=False)
    repositorycreationdate: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    repositoryupdatedate: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    migrated: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("false")
    )
    creation_date: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=text("now()")
    )
    ukrdcid: Mapped[Optional[str]] = mapped_column(String(10), index=True)
    channelname: Mapped[Optional[str]] = mapped_column(String(50))
    channelid: Mapped[Optional[str]] = mapped_column(String(50))
    extracttime: Mapped[Optional[str]] = mapped_column(String(50))
    startdate: Mapped[Optional[datetime]] = mapped_column(DateTime)
    stopdate: Mapped[Optional[datetime]] = mapped_column(DateTime)
    schemaversion: Mapped[Optional[str]] = mapped_column(String(50))
    update_date: Mapped[Optional[datetime]] = mapped_column(DateTime)

    # Relationships

    patient: Mapped["Patient"] = relationship(
        "Patient", back_populates="record", uselist=False, cascade="all, delete-orphan"
    )
    lab_orders: Mapped[List["LabOrder"]] = relationship(
        "LabOrder",
        back_populates="record",
        lazy=GLOBAL_LAZY,
        cascade="all, delete-orphan",
    )
    result_items: Mapped[List["ResultItem"]] = relationship(
        "ResultItem",
        secondary="laborder",
        primaryjoin="LabOrder.pid == PatientRecord.pid",
        secondaryjoin="ResultItem.order_id == LabOrder.id",
        lazy=GLOBAL_LAZY,
        viewonly=True,
    )
    observations: Mapped[List["Observation"]] = relationship(
        "Observation",
        back_populates="record",
        lazy=GLOBAL_LAZY,
        cascade="all, delete-orphan",
    )
    social_histories: Mapped[List["SocialHistory"]] = relationship(
        "SocialHistory", cascade="all, delete-orphan"
    )
    family_histories: Mapped[List["FamilyHistory"]] = relationship(
        "FamilyHistory", cascade="all, delete-orphan"
    )
    allergies: Mapped[List["Allergy"]] = relationship(
        "Allergy", lazy=GLOBAL_LAZY, cascade="all, delete-orphan"
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
    medications: Mapped[List["Medication"]] = relationship(
        "Medication", lazy=GLOBAL_LAZY, cascade="all, delete-orphan"
    )
    dialysis_sessions: Mapped[List["DialysisSession"]] = relationship(
        "DialysisSession", lazy=GLOBAL_LAZY, cascade="all, delete-orphan"
    )
    vascular_accesses: Mapped[List["VascularAccess"]] = relationship(
        "VascularAccess", lazy=GLOBAL_LAZY, cascade="all, delete-orphan"
    )
    procedures: Mapped[List["Procedure"]] = relationship(
        "Procedure", lazy=GLOBAL_LAZY, cascade="all, delete-orphan"
    )
    documents: Mapped[List["Document"]] = relationship(
        "Document", lazy=GLOBAL_LAZY, cascade="all, delete-orphan"
    )
    encounters: Mapped[List["Encounter"]] = relationship(
        "Encounter", lazy=GLOBAL_LAZY, cascade="all, delete-orphan"
    )
    transplantlists: Mapped[List["TransplantList"]] = relationship(
        "TransplantList", lazy=GLOBAL_LAZY, cascade="all, delete-orphan"
    )
    treatments: Mapped[List["Treatment"]] = relationship(
        "Treatment", lazy=GLOBAL_LAZY, cascade="all, delete-orphan"
    )
    program_memberships: Mapped[List["ProgramMembership"]] = relationship(
        "ProgramMembership", cascade="all, delete-orphan"
    )
    transplants: Mapped[List["Transplant"]] = relationship(
        "Transplant", lazy=GLOBAL_LAZY, cascade="all, delete-orphan"
    )
    opt_outs = relationship("OptOut", lazy=GLOBAL_LAZY, cascade="all, delete-orphan")
    clinical_relationships = relationship(
        "ClinicalRelationship", cascade="all, delete-orphan"
    )
    surveys: Mapped[List["Survey"]] = relationship(
        "Survey", lazy=GLOBAL_LAZY, cascade="all, delete-orphan"
    )
    pvdata: Mapped["PVData"] = relationship(
        "PVData", uselist=False, cascade="all, delete-orphan"
    )
    pvdelete: Mapped[List["PVDelete"]] = relationship(
        "PVDelete", lazy=GLOBAL_LAZY, cascade="all, delete-orphan"
    )

    # Synonyms
    id: Mapped[str] = synonym("pid")
    extract_time: Mapped[Optional[str]] = synonym("extracttime")
    repository_creation_date: Mapped[Optional[datetime]] = synonym(
        "repositorycreationdate"
    )
    repository_update_date: Mapped[Optional[datetime]] = synonym("repositoryupdatedate")

    def __str__(self):
        return (
            f"{self.__class__.__name__}({self.pid}) <"
            f"UKRDCID:{self.ukrdcid} CREATED:{self.repositorycreationdate}"
            f">"
        )


class Patient(Base):
    __tablename__ = "patient"

    pid: Mapped[str] = mapped_column(
        String,
        ForeignKey("patientrecord.pid"),
        primary_key=True,
        sqla_info=ColumnInfo(
            label="Patient ID",
            description="Unique identifier for the patient record, referencing patientrecord.pid.",
        ),
    )
    creation_date: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=text("now()"),
        sqla_info=ColumnInfo(
            label="Creation Date",
            description="Date and time when the record was created.",
        ),
    )
    birthtime: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        sqla_info=ColumnInfo(
            label="Date of Birth", description="Patient’s date of birth."
        ),
    )
    deathtime: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        sqla_info=ColumnInfo(
            label="Date of Death",
            description="Patient’s date of death, if applicable.",
        ),
    )
    gender: Mapped[Optional[str]] = mapped_column(
        String(2),
        sqla_info=ColumnInfo(
            label="Gender",
            description="Administrative gender of the patient (1, 2, 9).",
        ),
    )
    countryofbirth: Mapped[Optional[str]] = mapped_column(
        String(3),
        sqla_info=ColumnInfo(
            label="Country of Birth",
            description="Country code representing the patient’s country of birth from NHS Data Dictionary ISO 3166-1. Use the 3-char alphabetic code.",
        ),
    )
    ethnicgroupcode: Mapped[Optional[str]] = mapped_column(
        String(100),
        sqla_info=ColumnInfo(
            label="Ethnic Group Code",
            description="Code representing the patient’s ethnic group from NHS Data Dictionary: https://www.datadictionary.nhs.uk/data_elements/ethnic_category.html",
        ),
    )
    ethnicgroupcodestd: Mapped[Optional[str]] = mapped_column(
        String(100),
        sqla_info=ColumnInfo(
            label="Ethnic Group Code Standard",
            description="Coding standard used for the ethnic group code (NHS_DATA_DICTIONARY).",
        ),
    )
    ethnicgroupdesc: Mapped[Optional[str]] = mapped_column(
        String(100),
        sqla_info=ColumnInfo(
            label="Ethnic Group Description",
            description="Text description of the patient’s ethnic group.",
        ),
    )
    occupationcode: Mapped[Optional[str]] = mapped_column(
        String(100),
        sqla_info=ColumnInfo(
            label="Occupation Code",
            description="Code representing the patient’s occupation from NHS Data Dictionary.",
        ),
    )
    occupationcodestd: Mapped[Optional[str]] = mapped_column(
        String(100),
        sqla_info=ColumnInfo(
            label="Occupation Code Standard",
            description="Coding standard used for the occupation code (NHS_DATA_DICTIONARY_EMPLOYMENT_STATUS).",
        ),
    )
    occupationdesc: Mapped[Optional[str]] = mapped_column(
        String(100),
        sqla_info=ColumnInfo(
            label="Occupation Description",
            description="Text description of the patient’s occupation.",
        ),
    )
    primarylanguagecode: Mapped[Optional[str]] = mapped_column(
        String(100),
        sqla_info=ColumnInfo(
            label="Primary Language Code",
            description="Code representing the patient’s primary language from NHS Data Dictionary.",
        ),
    )
    primarylanguagecodestd: Mapped[Optional[str]] = mapped_column(
        String(100),
        sqla_info=ColumnInfo(
            label="Primary Language Code Standard",
            description="Coding standard used for the primary language code (NHS_DATA_DICTIONARY_LANGUAGE_CODE).",
        ),
    )
    primarylanguagedesc: Mapped[Optional[str]] = mapped_column(
        String(100),
        sqla_info=ColumnInfo(
            label="Primary Language Description",
            description="Text description of the patient’s primary language.",
        ),
    )
    death: Mapped[Optional[bool]] = mapped_column(
        Boolean,
        sqla_info=ColumnInfo(
            label="Deceased",
            description="Indicates whether the patient is deceased.",
        ),
    )
    persontocontactname: Mapped[Optional[str]] = mapped_column(
        String(100),
        sqla_info=ColumnInfo(
            label="Contact Person Name",
            description="Name of the person to contact about the patient's care. This element should not be submitted without prior discussion with the UKRR.",
        ),
    )
    persontocontact_relationship: Mapped[Optional[str]] = mapped_column(
        String(20),
        sqla_info=ColumnInfo(
            label="Contact Person Relationship",
            description="Relationship of the contact person to the patient.",
        ),
    )
    persontocontact_contactnumber: Mapped[Optional[str]] = mapped_column(
        String(20),
        sqla_info=ColumnInfo(
            label="Contact Person Number",
            description="Telephone number of the contact person.",
        ),
    )
    persontocontact_contactnumbertype: Mapped[Optional[str]] = mapped_column(
        String(20),
        sqla_info=ColumnInfo(
            label="Contact Number Type", description="Type of contact number."
        ),
    )
    persontocontact_contactnumbercomments: Mapped[Optional[str]] = mapped_column(
        String(200),
        sqla_info=ColumnInfo(
            label="Contact Number Comments",
            description="Additional comments related to the contact number.",
        ),
    )
    updatedon: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        sqla_info=ColumnInfo(label="Updated On", description="Last Modified Date"),
    )
    actioncode: Mapped[Optional[str]] = mapped_column(
        String(3),
        sqla_info=ColumnInfo(
            label="Action Code",
            description="Code representing the action performed on the patient record.",
        ),
    )
    externalid: Mapped[Optional[str]] = mapped_column(
        String(100),
        sqla_info=ColumnInfo(label="External ID", description="Unique Identifier"),
    )
    bloodgroup: Mapped[Optional[str]] = mapped_column(
        String(100),
        sqla_info=ColumnInfo(
            label="Blood Group",
            description="Patient’s blood type, current, from NHS Data Dictionary (A, B, AB, 0).",
        ),
    )
    bloodrhesus: Mapped[Optional[str]] = mapped_column(
        String(100),
        sqla_info=ColumnInfo(
            label="Blood Rhesus",
            description="Patient’s blood rhesus, current, from NHS Data Dictionary (POS, NEG).",
        ),
    )
    update_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        sqla_info=ColumnInfo(
            label="Update Date",
            description="Date and time when the record was last updated.",
        ),
    )

    # Synonyms
    id: Mapped[str] = synonym("pid")
    birth_time: Mapped[Optional[datetime]] = synonym("birthtime")
    death_time: Mapped[Optional[datetime]] = synonym("deathtime")
    country_of_birth: Mapped[Optional[str]] = synonym("countryofbirth")
    ethnic_group_code: Mapped[Optional[str]] = synonym("ethnicgroupcode")
    ethnic_group_code_std: Mapped[Optional[str]] = synonym("ethnicgroupcodestd")
    ethnic_group_description: Mapped[Optional[str]] = synonym("ethnicgroupdesc")
    person_to_contact_name: Mapped[Optional[str]] = synonym("persontocontactname")
    person_to_contact_number: Mapped[Optional[str]] = synonym(
        "persontocontact_contactnumber"
    )
    person_to_contact_relationship: Mapped[Optional[str]] = synonym(
        "persontocontact_relationship"
    )
    person_to_contact_number_comments: Mapped[Optional[str]] = synonym(
        "persontocontact_numbercomments"
    )
    person_to_contact_number_type: Mapped[Optional[str]] = synonym(
        "persontocontact_contactnumbertype"
    )
    occupation_code: Mapped[Optional[str]] = synonym("occupationcode")
    occupation_codestd: Mapped[Optional[str]] = synonym("occupationcodestd")
    occupation_description: Mapped[Optional[str]] = synonym("occupationdesc")
    primary_language: Mapped[Optional[str]] = synonym("primarylanguagecode")
    primary_language_codestd: Mapped[Optional[str]] = synonym("primarylanguagecodestd")
    primary_language_description: Mapped[Optional[str]] = synonym("primarylanguagedesc")
    dead: Mapped[Optional[bool]] = synonym("death")
    updated_on: Mapped[Optional[datetime]] = synonym("updatedon")

    # Relationships
    numbers: Mapped[List["PatientNumber"]] = relationship(
        "PatientNumber",
        back_populates="patient",
        lazy=GLOBAL_LAZY,
        cascade="all, delete-orphan",
    )
    names: Mapped[List["Name"]] = relationship(
        "Name", lazy=GLOBAL_LAZY, cascade="all, delete-orphan"
    )
    contact_details: Mapped[List["ContactDetail"]] = relationship(
        "ContactDetail", lazy=GLOBAL_LAZY, cascade="all, delete-orphan"
    )
    addresses: Mapped[List["Address"]] = relationship(
        "Address", lazy=GLOBAL_LAZY, cascade="all, delete-orphan"
    )
    familydoctor: Mapped["FamilyDoctor"] = relationship(
        "FamilyDoctor", uselist=False, cascade="all, delete-orphan"
    )
    record: Mapped["PatientRecord"] = relationship(
        "PatientRecord",
        back_populates="patient",
        uselist=False,
        primaryjoin="Patient.pid == PatientRecord.pid",
    )

    def __str__(self):
        return f"{self.__class__.__name__}({self.pid}) <{self.birthtime}>"

    @property
    def name(self) -> Optional["Name"]:
        """Return main patient name."""
        for name in self.names or []:
            if name.nameuse == "L":
                return name
        return None

    @property
    def first_ni_number(
        self, org: bool = False
    ) -> Optional[Union[str, Tuple[str, str]]]:
        """Find the first NHS, CHI, or HSC number for a patient.
        Returns a string by default, or a tuple if org=True."""
        types = {"NHS", "CHI", "HSC"}
        for number in self.numbers or []:
            if number.numbertype == "NI" and number.organization in types:
                return (
                    (number.patientid, number.organization) if org else number.patientid
                )
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

    pid: Mapped[str] = mapped_column(
        String, ForeignKey("patientrecord.pid"), primary_key=True
    )

    creation_date: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=text("now()")
    )
    diagnosistype: Mapped[Optional[str]] = mapped_column(
        String(50),
        sqla_info=ColumnInfo(
            label="Diagnosis Type",
            description="Type of cause of death diagnosis",
        ),
    )
    diagnosingcliniciancode: Mapped[Optional[str]] = mapped_column(String(100))
    diagnosingcliniciancodestd: Mapped[Optional[str]] = mapped_column(String(100))
    diagnosingcliniciandesc: Mapped[Optional[str]] = mapped_column(String(100))
    diagnosiscode: Mapped[Optional[str]] = mapped_column(
        String(100),
        sqla_info=ColumnInfo(
            label="Diagnosis Code",
            description="Code representing the cause of death diagnosis)",
        ),
    )
    diagnosiscodestd: Mapped[Optional[str]] = mapped_column(
        String(100),
        sqla_info=ColumnInfo(
            label="Diagnosis Code Standard",
            description="Coding standard used for the cause of death diagnosis)",
        ),
    )
    diagnosisdesc: Mapped[Optional[str]] = mapped_column(
        String(255),
        sqla_info=ColumnInfo(
            label="Diagnosis Description",
            description="Text description of the cause of death diagnosis",
        ),
    )
    comments: Mapped[Optional[str]] = mapped_column(Text)
    enteredon: Mapped[Optional[datetime]] = mapped_column(DateTime)
    updatedon: Mapped[Optional[datetime]] = mapped_column(DateTime)
    actioncode: Mapped[Optional[str]] = mapped_column(String(3))
    externalid: Mapped[Optional[str]] = mapped_column(String(100))
    update_date: Mapped[Optional[datetime]] = mapped_column(DateTime)
    # Synonyms
    id: Mapped[str] = synonym(
        "pid"
    )  # this will not be correct if the primary key changes
    diagnosis_type: Mapped[Optional[str]] = synonym("diagnosistype")
    diagnosing_clinician_code: Mapped[Optional[str]] = synonym(
        "diagnosingcliniciancode"
    )
    diagnosing_clinician_code_std: Mapped[Optional[str]] = synonym(
        "diagnosingcliniciancodestd"
    )
    diagnosing_clinician_desc: Mapped[Optional[str]] = synonym(
        "diagnosingcliniciandesc"
    )
    diagnosis_code: Mapped[Optional[str]] = synonym("diagnosiscode")
    diagnosis_code_std: Mapped[Optional[str]] = synonym("diagnosiscodestd")
    diagnosis_desc: Mapped[Optional[str]] = synonym("diagnosisdesc")
    entered_on: Mapped[Optional[datetime]] = synonym("enteredon")
    updated_on: Mapped[Optional[datetime]] = synonym("updatedon")
    action_code: Mapped[Optional[str]] = synonym("actioncode")
    external_id: Mapped[Optional[str]] = synonym("externalid")


class FamilyDoctor(Base):
    __tablename__ = "familydoctor"

    id: Mapped[str] = mapped_column(String, ForeignKey("patient.pid"), primary_key=True)

    creation_date: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=text("now()")
    )
    gpname: Mapped[Optional[str]] = mapped_column(String(100))

    gpid: Mapped[Optional[str]] = mapped_column(
        String(20), ForeignKey("ukrdc_ods_gp_codes.code")
    )
    gppracticeid: Mapped[Optional[str]] = mapped_column(
        String(20), ForeignKey("ukrdc_ods_gp_codes.code")
    )

    addressuse: Mapped[Optional[str]] = mapped_column(String(10))
    fromtime: Mapped[Optional[date]] = mapped_column(Date)
    totime: Mapped[Optional[date]] = mapped_column(Date)
    street: Mapped[Optional[str]] = mapped_column(String(100))
    town: Mapped[Optional[str]] = mapped_column(String(100))
    county: Mapped[Optional[str]] = mapped_column(String(100))
    postcode: Mapped[Optional[str]] = mapped_column(String(10))
    countrycode: Mapped[Optional[str]] = mapped_column(String(100))
    countrycodestd: Mapped[Optional[str]] = mapped_column(String(100))
    countrydesc: Mapped[Optional[str]] = mapped_column(String(100))
    contactuse: Mapped[Optional[str]] = mapped_column(String(10))
    contactvalue: Mapped[Optional[str]] = mapped_column(String(100))
    email: Mapped[Optional[str]] = mapped_column(String(100))
    commenttext: Mapped[Optional[str]] = mapped_column(String(100))
    update_date: Mapped[Optional[datetime]] = mapped_column(DateTime)

    # Relationships

    gp_info: Mapped["GPInfo"] = relationship(
        "GPInfo", foreign_keys=[gpid], uselist=False
    )
    gp_practice_info: Mapped["GPInfo"] = relationship(
        "GPInfo", foreign_keys=[gppracticeid], uselist=False
    )

    def __str__(self):
        return f"{self.__class__.__name__}({self.id}) <{self.gpname} {self.gpid}>"


class GPInfo(Base):
    __tablename__ = "ukrdc_ods_gp_codes"

    code: Mapped[str] = mapped_column(String(8), primary_key=True)

    creation_date: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=text("now()")
    )
    name: Mapped[Optional[str]] = mapped_column(String(50))
    address1: Mapped[Optional[str]] = mapped_column(String(35))
    postcode: Mapped[Optional[Optional[str]]] = mapped_column(String)
    phone: Mapped[Optional[str]] = mapped_column(String(12))
    type: Mapped[Optional[str]] = mapped_column(Enum("GP", "PRACTICE", name="gp_type"))
    update_date: Mapped[Optional[datetime]] = mapped_column(DateTime)

    # Synonyms

    gpname: Mapped[Optional[str]] = synonym("name")
    street: Mapped[Optional[str]] = synonym("address1")
    contactvalue: Mapped[Optional[str]] = synonym("phone")


class SocialHistory(Base):
    __tablename__ = "socialhistory"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    pid: Mapped[str] = mapped_column(String, ForeignKey("patientrecord.pid"))

    creation_date: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=text("now()")
    )
    idx: Mapped[Optional[int]] = mapped_column(Integer)
    socialhabitcode: Mapped[Optional[str]] = mapped_column(String(100))
    socialhabitcodestd: Mapped[Optional[str]] = mapped_column(String(100))
    socialhabitdesc: Mapped[Optional[str]] = mapped_column(String(100))
    updatedon: Mapped[Optional[datetime]] = mapped_column(DateTime)
    actioncode: Mapped[Optional[str]] = mapped_column(String(3))
    externalid: Mapped[Optional[str]] = mapped_column(String(100))
    update_date: Mapped[Optional[datetime]] = mapped_column(DateTime)


class FamilyHistory(Base):
    __tablename__ = "familyhistory"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    pid: Mapped[str] = mapped_column(String, ForeignKey("patientrecord.pid"))

    creation_date: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=text("now()")
    )
    idx: Mapped[Optional[int]] = mapped_column(Integer)
    familymembercode: Mapped[Optional[str]] = mapped_column(String(100))
    familymembercodestd: Mapped[Optional[str]] = mapped_column(String(100))
    familymemberdesc: Mapped[Optional[str]] = mapped_column(String(100))
    diagnosiscode: Mapped[Optional[str]] = mapped_column(String(100))
    diagnosiscodestd: Mapped[Optional[str]] = mapped_column(String(100))
    diagnosisdesc: Mapped[Optional[str]] = mapped_column(String(100))
    notetext: Mapped[Optional[str]] = mapped_column(String(100))
    enteredatcode: Mapped[Optional[str]] = mapped_column(String(100))
    enteredatcodestd: Mapped[Optional[str]] = mapped_column(String(100))
    enteredatdesc: Mapped[Optional[str]] = mapped_column(String(100))
    fromtime: Mapped[Optional[datetime]] = mapped_column(DateTime)
    totime: Mapped[Optional[datetime]] = mapped_column(DateTime)
    updatedon: Mapped[Optional[datetime]] = mapped_column(DateTime)
    actioncode: Mapped[Optional[str]] = mapped_column(String(3))
    externalid: Mapped[Optional[str]] = mapped_column(String(100))
    update_date: Mapped[Optional[datetime]] = mapped_column(DateTime)


class Observation(Base):
    __tablename__ = "observation"

    id: Mapped[str] = mapped_column(
        String,
        primary_key=True,
        sqla_info=ColumnInfo(
            label="Observation ID",
            description="Unique identifier for the observation record.",
        ),
    )
    pid: Mapped[str] = mapped_column(
        String,
        ForeignKey("patientrecord.pid"),
        sqla_info=ColumnInfo(
            label="Patient ID",
            description="Identifier of the patient associated with this observation.",
        ),
    )
    creation_date: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=text("now()"),
        sqla_info=ColumnInfo(
            label="Creation Date",
            description="Date and time when the observation record was created.",
        ),
    )
    idx: Mapped[Optional[int]] = mapped_column(
        Integer,
        sqla_info=ColumnInfo(label="Index", description="Index for the observation."),
    )
    observationtime: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        sqla_info=ColumnInfo(
            label="Observation Time",
            description="Date and time when the observation was made.",
        ),
    )
    observationcode: Mapped[Optional[str]] = mapped_column(
        String(100),
        sqla_info=ColumnInfo(
            label="Observation Code",
            description="Code for the observation - UKRR, PV or SNOMED Coding Standards.",
        ),
    )
    observationcodestd: Mapped[Optional[str]] = mapped_column(
        String(100),
        sqla_info=ColumnInfo(
            label="Observation Code Standard",
            description="Coding standard used for the observation code (UKRR, PV, SNOMED).",
        ),
    )
    observationdesc: Mapped[Optional[str]] = mapped_column(
        String(100),
        sqla_info=ColumnInfo(
            label="Observation Description",
            description="Text description of the observation recorded.",
        ),
    )
    observationvalue: Mapped[Optional[str]] = mapped_column(
        String(100),
        sqla_info=ColumnInfo(
            label="Observation Value",
            description="The measured or observed value.",
        ),
    )
    observationunits: Mapped[Optional[str]] = mapped_column(
        String(100),
        sqla_info=ColumnInfo(
            label="Observation Units",
            description="Units of measurement for the observation value.",
        ),
    )
    prepost: Mapped[Optional[str]] = mapped_column(
        String(4),
        sqla_info=ColumnInfo(
            label="Pre/Post Indicator",
            description="Indicates whether the observation was made PRE or POST dialysis (PRE, POST, UNK, NA).",
        ),
    )
    commenttext: Mapped[Optional[str]] = mapped_column(
        String(100),
        sqla_info=ColumnInfo(
            label="Comment Text",
            description="Free-text comment associated with the observation.",
        ),
    )
    cliniciancode: Mapped[Optional[str]] = mapped_column(
        String(100),
        sqla_info=ColumnInfo(
            label="Clinician Code",
            description="Code identifying the clinician associated with this observation.",
        ),
    )
    cliniciancodestd: Mapped[Optional[str]] = mapped_column(
        String(100),
        sqla_info=ColumnInfo(
            label="Clinician Code Standard",
            description="Coding standard used for the clinician code.",
        ),
    )
    cliniciandesc: Mapped[Optional[str]] = mapped_column(
        String(100),
        sqla_info=ColumnInfo(
            label="Clinician Description",
            description="Name or description of the clinician.",
        ),
    )
    enteredatcode: Mapped[Optional[str]] = mapped_column(
        String(100),
        sqla_info=ColumnInfo(
            label="Entered At Code",
            description="Code for the location where the observation was entered.",
        ),
    )
    enteredatcodestd: Mapped[Optional[str]] = mapped_column(
        String(100),
        sqla_info=ColumnInfo(
            label="Entered At Code Standard",
            description="Coding standard used for the entered-at code.",
        ),
    )
    enteredatdesc: Mapped[Optional[str]] = mapped_column(
        String(100),
        sqla_info=ColumnInfo(
            label="Entered At Description",
            description="Text description of the location where the observation was entered.",
        ),
    )
    enteringorganizationcode: Mapped[Optional[str]] = mapped_column(
        String(100),
        sqla_info=ColumnInfo(
            label="Entering Organization Code",
            description="Code identifying the organization entering the observation.",
        ),
    )
    enteringorganizationcodestd: Mapped[Optional[str]] = mapped_column(
        String(100),
        sqla_info=ColumnInfo(
            label="Entering Organization Code Standard",
            description="Coding standard used for the entering organization code.",
        ),
    )
    enteringorganizationdesc: Mapped[Optional[str]] = mapped_column(
        String(100),
        sqla_info=ColumnInfo(
            label="Entering Organization Description",
            description="Text description of the organization entering the observation.",
        ),
    )
    updatedon: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        sqla_info=ColumnInfo(label="Updated On", description="Last Modified Date"),
    )
    actioncode: Mapped[Optional[str]] = mapped_column(
        String(3),
        sqla_info=ColumnInfo(
            label="Action Code",
            description="Code representing the action performed on the observation record.",
        ),
    )
    externalid: Mapped[Optional[str]] = mapped_column(
        String(100),
        sqla_info=ColumnInfo(label="External ID", description="Unique Identifier"),
    )
    update_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        sqla_info=ColumnInfo(
            label="Update Date",
            description="Date and time when the record was last updated.",
        ),
    )

    # Relationships

    record: Mapped["PatientRecord"] = relationship(
        "PatientRecord", back_populates="observations", uselist=False
    )

    # Synonyms

    observation_time: Mapped[Optional[datetime]] = synonym("observationtime")
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
            f"{self.observationcode} {self.observationvalue}"
            f">"
        )


class OptOut(Base):
    __tablename__ = "optout"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    pid: Mapped[str] = mapped_column(String, ForeignKey("patientrecord.pid"))

    creation_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=False, server_default=text("now()")
    )
    idx: Mapped[Optional[int]] = mapped_column(Integer)
    programname: Mapped[Optional[str]] = mapped_column(String(100))
    programdescription: Mapped[Optional[str]] = mapped_column(String(100))
    enteredbycode: Mapped[Optional[str]] = mapped_column(String(100))
    enteredbycodestd: Mapped[Optional[str]] = mapped_column(String(100))
    enteredbydesc: Mapped[Optional[str]] = mapped_column(String(100))
    enteredatcode: Mapped[Optional[str]] = mapped_column(String(100))
    enteredatcodestd: Mapped[Optional[str]] = mapped_column(String(100))
    enteredatdesc: Mapped[Optional[str]] = mapped_column(String(100))
    fromtime: Mapped[Optional[date]] = mapped_column(Date)
    totime: Mapped[Optional[date]] = mapped_column(Date)
    updatedon: Mapped[Optional[datetime]] = mapped_column(DateTime)
    actioncode: Mapped[Optional[str]] = mapped_column(String(3))
    externalid: Mapped[Optional[str]] = mapped_column(String(100))
    update_date: Mapped[Optional[datetime]] = mapped_column(DateTime)

    # Synonyms

    program_name: Mapped[Optional[str]] = synonym("programname")
    program_description: Mapped[Optional[str]] = synonym("programdescription")
    entered_by_code: Mapped[Optional[str]] = synonym("enteredbycode")
    entered_by_code_std: Mapped[Optional[str]] = synonym("enteredbycodestd")
    entered_by_desc: Mapped[Optional[str]] = synonym("enteredbydesc")
    entered_at_code: Mapped[Optional[str]] = synonym("enteredatcode")
    entered_at_code_std: Mapped[Optional[str]] = synonym("enteredatcodestd")
    entered_at_desc: Mapped[Optional[str]] = synonym("enteredatdesc")
    from_time: Mapped[Optional[date]] = synonym("fromtime")
    to_time: Mapped[Optional[date]] = synonym("totime")
    updated_on: Mapped[Optional[datetime]] = synonym("updatedon")
    action_code: Mapped[Optional[str]] = synonym("actioncode")
    external_id: Mapped[Optional[str]] = synonym("externalid")


class Allergy(Base):
    __tablename__ = "allergy"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    pid: Mapped[str] = mapped_column(String, ForeignKey("patientrecord.pid"))

    creation_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=False, server_default=text("now()")
    )
    idx: Mapped[Optional[int]] = mapped_column(Integer)
    allergycode: Mapped[Optional[str]] = mapped_column(String(100))
    allergycodestd: Mapped[Optional[str]] = mapped_column(String(100))
    allergydesc: Mapped[Optional[str]] = mapped_column(String(100))
    allergycategorycode: Mapped[Optional[str]] = mapped_column(String(100))
    allergycategorycodestd: Mapped[Optional[str]] = mapped_column(String(100))
    allergycategorydesc: Mapped[Optional[str]] = mapped_column(String(100))
    severitycode: Mapped[Optional[str]] = mapped_column(String(100))
    severitycodestd: Mapped[Optional[str]] = mapped_column(String(100))
    severitydesc: Mapped[Optional[str]] = mapped_column(String(100))
    cliniciancode: Mapped[Optional[str]] = mapped_column(String(100))
    cliniciancodestd: Mapped[Optional[str]] = mapped_column(String(100))
    cliniciandesc: Mapped[Optional[str]] = mapped_column(String(100))
    discoverytime: Mapped[Optional[datetime]] = mapped_column(DateTime)
    confirmedtime: Mapped[Optional[datetime]] = mapped_column(DateTime)
    commenttext: Mapped[Optional[str]] = mapped_column(String(500))
    inactivetime: Mapped[Optional[datetime]] = mapped_column(DateTime)
    freetextallergy: Mapped[Optional[str]] = mapped_column(String(500))
    qualifyingdetails: Mapped[Optional[str]] = mapped_column(String(500))
    updatedon: Mapped[Optional[datetime]] = mapped_column(DateTime)
    actioncode: Mapped[Optional[str]] = mapped_column(String(3))
    externalid: Mapped[Optional[str]] = mapped_column(String(100))
    update_date: Mapped[Optional[datetime]] = mapped_column(DateTime)


class Diagnosis(Base):
    __tablename__ = "diagnosis"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    pid: Mapped[str] = mapped_column(String, ForeignKey("patientrecord.pid"))

    creation_date: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=text("now()")
    )
    idx: Mapped[Optional[int]] = mapped_column(Integer)
    diagnosistype: Mapped[Optional[str]] = mapped_column(
        String(50),
        sqla_info=ColumnInfo(
            label="Diagnosis Type",
            description="Type of diagnosis",
        ),
    )
    diagnosingcliniciancode: Mapped[Optional[str]] = mapped_column(String(100))
    diagnosingcliniciancodestd: Mapped[Optional[str]] = mapped_column(String(100))
    diagnosingcliniciandesc: Mapped[Optional[str]] = mapped_column(String(100))
    diagnosiscode: Mapped[Optional[str]] = mapped_column(
        String(100),
        sqla_info=ColumnInfo(
            label="Diagnosis Code",
            description="Code representing the diagnosis. This should also include any diagnosis that has been submitted elsewhere as a Primary Renal Diagnosis.",
        ),
    )
    diagnosiscodestd: Mapped[Optional[str]] = mapped_column(
        String(100),
        sqla_info=ColumnInfo(
            label="Diagnosis Code Standard",
            description="Coding standard used for the diagnosis",
        ),
    )
    diagnosisdesc: Mapped[Optional[str]] = mapped_column(
        String(255),
        sqla_info=ColumnInfo(
            label="Diagnosis Description",
            description="Text description of the diagnosis",
        ),
    )
    comments: Mapped[Optional[str]] = mapped_column(Text)
    identificationtime: Mapped[Optional[datetime]] = mapped_column(DateTime)
    onsettime: Mapped[Optional[datetime]] = mapped_column(DateTime)
    enteredon: Mapped[Optional[datetime]] = mapped_column(DateTime)
    updatedon: Mapped[Optional[datetime]] = mapped_column(DateTime)
    actioncode: Mapped[Optional[str]] = mapped_column(String(3))
    externalid: Mapped[Optional[str]] = mapped_column(String(100))
    update_date: Mapped[Optional[datetime]] = mapped_column(DateTime)
    enteredatcode: Mapped[Optional[str]] = mapped_column(String(100))
    enteredatcodestd: Mapped[Optional[str]] = mapped_column(String(100))
    enteredatdesc: Mapped[Optional[str]] = mapped_column(String(100))
    encounternumber: Mapped[Optional[str]] = mapped_column(String(100))
    verificationstatus: Mapped[Optional[str]] = mapped_column(String(100))

    # Synonyms

    diagnosis_code: Mapped[Optional[str]] = synonym("diagnosiscode")
    diagnosis_code_std: Mapped[Optional[str]] = synonym("diagnosiscodestd")
    diagnosis_desc: Mapped[Optional[str]] = synonym("diagnosisdesc")
    identification_time: Mapped[Optional[datetime]] = synonym("identificationtime")
    onset_time: Mapped[Optional[datetime]] = synonym("onsettime")


class RenalDiagnosis(Base):
    __tablename__ = "renaldiagnosis"

    pid: Mapped[str] = mapped_column(
        String, ForeignKey("patientrecord.pid"), primary_key=True
    )

    creation_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=False, server_default=text("now()")
    )
    diagnosistype: Mapped[Optional[str]] = mapped_column(
        String(50),
        sqla_info=ColumnInfo(
            label="Diagnosis Type",
            description="Type of renal diagnosis",
        ),
    )
    diagnosiscode: Mapped[Optional[str]] = mapped_column(
        "diagnosiscode",
        String,
        sqla_info=ColumnInfo(
            label="Diagnosis Code",
            description="Code representing the renal diagnosis",
        ),
    )
    diagnosiscodestd: Mapped[Optional[str]] = mapped_column(
        "diagnosiscodestd",
        String,
        sqla_info=ColumnInfo(
            label="Diagnosis Code Standard",
            description="Coding standard used for the renal diagnosis",
        ),
    )
    diagnosisdesc: Mapped[Optional[str]] = mapped_column(
        "diagnosisdesc",
        String,
        sqla_info=ColumnInfo(
            label="Diagnosis Description",
            description="Text description of the renal diagnosis",
        ),
    )
    diagnosingcliniciancode: Mapped[Optional[str]] = mapped_column(String(100))
    diagnosingcliniciancodestd: Mapped[Optional[str]] = mapped_column(String(100))
    diagnosingcliniciandesc: Mapped[Optional[str]] = mapped_column(String(100))
    comments: Mapped[Optional[str]] = mapped_column(String)
    identificationtime: Mapped[Optional[datetime]] = mapped_column(
        "identificationtime", DateTime
    )
    onsettime: Mapped[Optional[datetime]] = mapped_column(DateTime)
    enteredon: Mapped[Optional[datetime]] = mapped_column(DateTime)
    updatedon: Mapped[Optional[datetime]] = mapped_column(DateTime)
    actioncode: Mapped[Optional[str]] = mapped_column(String(3))
    externalid: Mapped[Optional[str]] = mapped_column(String(100))
    update_date: Mapped[Optional[datetime]] = mapped_column(DateTime)

    # Synonyms
    id: Mapped[str] = synonym("pid")  # see comment on cause of death
    diagnosis_code: Mapped[Optional[str]] = synonym("diagnosiscode")
    diagnosis_code_std: Mapped[Optional[str]] = synonym("diagnosiscodestd")
    diagnosis_desc: Mapped[Optional[str]] = synonym("diagnosisdesc")
    identification_time: Mapped[Optional[datetime]] = synonym("identificationtime")


class DialysisSession(Base):
    __tablename__ = "dialysissession"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    pid: Mapped[str] = mapped_column(String, ForeignKey("patientrecord.pid"))

    creation_date: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=text("now()")
    )
    idx: Mapped[Optional[int]] = mapped_column(Integer)
    proceduretypecode: Mapped[Optional[str]] = mapped_column(
        String(100),
        sqla_info=ColumnInfo(
            label="Procedure Type Code",
            description="Code representing dialysis procedure type",
        ),
    )
    proceduretypecodestd: Mapped[Optional[str]] = mapped_column(String(100))
    proceduretypedesc: Mapped[Optional[str]] = mapped_column(String(100))
    cliniciancode: Mapped[Optional[str]] = mapped_column(String(100))
    cliniciancodestd: Mapped[Optional[str]] = mapped_column(String(100))
    cliniciandesc: Mapped[Optional[str]] = mapped_column(String(100))
    proceduretime: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        sqla_info=ColumnInfo(
            label="Procedure Time",
            description="Date and time of dialysis session",
        ),
    )
    enteredbycode: Mapped[Optional[str]] = mapped_column(String(100))
    enteredbycodestd: Mapped[Optional[str]] = mapped_column(String(100))
    enteredbydesc: Mapped[Optional[str]] = mapped_column(String(100))
    enteredatcode: Mapped[Optional[str]] = mapped_column(String(100))
    enteredatcodestd: Mapped[Optional[str]] = mapped_column(String(100))
    enteredatdesc: Mapped[Optional[str]] = mapped_column(String(100))
    qhd19: Mapped[Optional[str]] = mapped_column(String(255))
    qhd20: Mapped[Optional[str]] = mapped_column(
        String(255),
        sqla_info=ColumnInfo(
            label="QHD20",
            description="Vascular access used",
        ),
    )
    qhd21: Mapped[Optional[str]] = mapped_column(String(255))
    qhd22: Mapped[Optional[str]] = mapped_column(String(255))
    qhd30: Mapped[Optional[str]] = mapped_column(String(255))
    qhd31: Mapped[Optional[str]] = mapped_column(
        String(255),
        sqla_info=ColumnInfo(
            label="QHD31",
            description="Time dialysed in minutes",
        ),
    )
    qhd32: Mapped[Optional[str]] = mapped_column(String(255))
    qhd33: Mapped[Optional[str]] = mapped_column(String(255))

    updatedon: Mapped[Optional[datetime]] = mapped_column(DateTime)
    actioncode: Mapped[Optional[str]] = mapped_column(String(3))
    externalid: Mapped[Optional[str]] = mapped_column(String(100))
    update_date: Mapped[Optional[datetime]] = mapped_column(DateTime)

    # Synonyms

    procedure_type_code: Mapped[Optional[str]] = synonym("proceduretypecode")
    procedure_type_code_std: Mapped[Optional[str]] = synonym("proceduretypecodestd")
    procedure_type_desc: Mapped[Optional[str]] = synonym("proceduretypedesc")
    procedure_time: Mapped[Optional[datetime]] = synonym("proceduretime")


class Transplant(Base):
    __tablename__ = "transplant"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    pid: Mapped[str] = mapped_column(String, ForeignKey("patientrecord.pid"))

    creation_date: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=text("now()")
    )
    idx: Mapped[Optional[int]] = mapped_column(Integer)

    proceduretypecode: Mapped[Optional[str]] = mapped_column(
        String(100),
        sqla_info=ColumnInfo(
            label="Procedure Type Code",
            description="Code representing transplant procedure type",
        ),
    )
    proceduretypecodestd: Mapped[Optional[str]] = mapped_column(String(100))
    proceduretypedesc: Mapped[Optional[str]] = mapped_column(String(100))

    cliniciancode: Mapped[Optional[str]] = mapped_column(String(100))
    cliniciancodestd: Mapped[Optional[str]] = mapped_column(String(100))
    cliniciandesc: Mapped[Optional[str]] = mapped_column(String(100))

    proceduretime: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        sqla_info=ColumnInfo(
            label="Procedure Time",
            description="Date of kidney transplant",
        ),
    )

    enteredbycode: Mapped[Optional[str]] = mapped_column(String(100))
    enteredbycodestd: Mapped[Optional[str]] = mapped_column(String(100))
    enteredbydesc: Mapped[Optional[str]] = mapped_column(String(100))

    enteredatcode: Mapped[Optional[str]] = mapped_column(
        String(100),
        sqla_info=ColumnInfo(
            label="Entered At Code",
            description="Code for the location where the transplant information was entered",
        ),
    )
    enteredatcodestd: Mapped[Optional[str]] = mapped_column(
        String(100),
        sqla_info=ColumnInfo(
            label="Entered At Code Standard",
            description="Coding standard used for the entered-at code",
        ),
    )
    enteredatdesc: Mapped[Optional[str]] = mapped_column(
        String(100),
        sqla_info=ColumnInfo(
            label="Entered At Description",
            description="Text description of the location where the transplant information was entered",
        ),
    )

    updatedon: Mapped[Optional[datetime]] = mapped_column(DateTime)
    actioncode: Mapped[Optional[str]] = mapped_column(String(3))
    externalid: Mapped[Optional[str]] = mapped_column(String(100))

    tra64: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        sqla_info=ColumnInfo(
            label="TRA64",
            description="Date of kidney transplant failure",
        ),
    )
    tra65: Mapped[Optional[str]] = mapped_column(String(255))
    tra66: Mapped[Optional[str]] = mapped_column(String(255))
    tra69: Mapped[Optional[datetime]] = mapped_column(DateTime)
    tra76: Mapped[Optional[str]] = mapped_column(String(255))
    tra77: Mapped[Optional[str]] = mapped_column(
        String(255),
        sqla_info=ColumnInfo(
            label="TRA77",
            description="Donor type, NHSBT type",
        ),
    )
    tra78: Mapped[Optional[str]] = mapped_column(String(255))
    tra79: Mapped[Optional[str]] = mapped_column(String(255))
    tra80: Mapped[Optional[str]] = mapped_column(String(255))
    tra8a: Mapped[Optional[str]] = mapped_column(String(255))
    tra81: Mapped[Optional[str]] = mapped_column(String(255))
    tra82: Mapped[Optional[str]] = mapped_column(String(255))
    tra83: Mapped[Optional[str]] = mapped_column(String(255))
    tra84: Mapped[Optional[str]] = mapped_column(String(255))
    tra85: Mapped[Optional[str]] = mapped_column(String(255))
    tra86: Mapped[Optional[str]] = mapped_column(String(255))
    tra87: Mapped[Optional[str]] = mapped_column(String(255))
    tra88: Mapped[Optional[str]] = mapped_column(String(255))
    tra89: Mapped[Optional[str]] = mapped_column(String(255))
    tra90: Mapped[Optional[str]] = mapped_column(String(255))
    tra91: Mapped[Optional[str]] = mapped_column(String(255))
    tra92: Mapped[Optional[str]] = mapped_column(String(255))
    tra93: Mapped[Optional[str]] = mapped_column(String(255))
    tra94: Mapped[Optional[str]] = mapped_column(String(255))
    tra95: Mapped[Optional[str]] = mapped_column(String(255))
    tra96: Mapped[Optional[str]] = mapped_column(String(255))
    tra97: Mapped[Optional[str]] = mapped_column(String(255))
    tra98: Mapped[Optional[str]] = mapped_column(String(255))

    update_date: Mapped[Optional[datetime]] = mapped_column(DateTime)

    # Synonyms

    procedure_type_code: Mapped[Optional[str]] = synonym("proceduretypecode")
    procedure_type_code_std: Mapped[Optional[str]] = synonym("proceduretypecodestd")
    procedure_type_desc: Mapped[Optional[str]] = synonym("proceduretypedesc")
    procedure_time: Mapped[Optional[datetime]] = synonym("proceduretime")


class VascularAccess(Base):
    __tablename__ = "vascularaccess"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    pid: Mapped[str] = mapped_column(String, ForeignKey("patientrecord.pid"))
    idx: Mapped[Optional[int]] = mapped_column(Integer)

    creation_date: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=text("now()")
    )
    proceduretypecode: Mapped[Optional[str]] = mapped_column(String(100))
    proceduretypecodestd: Mapped[Optional[str]] = mapped_column(String(100))
    proceduretypedesc: Mapped[Optional[str]] = mapped_column(String(100))
    cliniciancode: Mapped[Optional[str]] = mapped_column(String(100))
    cliniciancodestd: Mapped[Optional[str]] = mapped_column(String(100))
    cliniciandesc: Mapped[Optional[str]] = mapped_column(String(100))
    proceduretime: Mapped[Optional[datetime]] = mapped_column(DateTime)
    enteredbycode: Mapped[Optional[str]] = mapped_column(String(100))
    enteredbycodestd: Mapped[Optional[str]] = mapped_column(String(100))
    enteredbydesc: Mapped[Optional[str]] = mapped_column(String(100))
    enteredatcode: Mapped[Optional[str]] = mapped_column(String(100))
    enteredatcodestd: Mapped[Optional[str]] = mapped_column(String(100))
    enteredatdesc: Mapped[Optional[str]] = mapped_column(String(100))
    updatedon: Mapped[Optional[datetime]] = mapped_column(DateTime)
    actioncode: Mapped[Optional[str]] = mapped_column(String(3))
    externalid: Mapped[Optional[str]] = mapped_column(String(100))

    acc19: Mapped[Optional[str]] = mapped_column(String(255))
    acc20: Mapped[Optional[str]] = mapped_column(String(255))
    acc21: Mapped[Optional[str]] = mapped_column(String(255))
    acc22: Mapped[Optional[str]] = mapped_column(String(255))
    acc30: Mapped[Optional[str]] = mapped_column(String(255))
    acc40: Mapped[Optional[str]] = mapped_column(String(255))

    update_date: Mapped[Optional[datetime]] = mapped_column(DateTime)


class Procedure(Base):
    __tablename__ = "procedure"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    pid: Mapped[str] = mapped_column(String, ForeignKey("patientrecord.pid"))

    creation_date: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=text("now()")
    )
    idx: Mapped[Optional[int]] = mapped_column(Integer)
    proceduretypecode: Mapped[Optional[str]] = mapped_column(String(100))
    proceduretypecodestd: Mapped[Optional[str]] = mapped_column(String(100))
    proceduretypedesc: Mapped[Optional[str]] = mapped_column(String(100))
    cliniciancode: Mapped[Optional[str]] = mapped_column(String(100))
    cliniciancodestd: Mapped[Optional[str]] = mapped_column(String(100))
    cliniciandesc: Mapped[Optional[str]] = mapped_column(String(100))
    proceduretime: Mapped[Optional[datetime]] = mapped_column(DateTime)
    enteredbycode: Mapped[Optional[str]] = mapped_column(String(100))
    enteredbycodestd: Mapped[Optional[str]] = mapped_column(String(100))
    enteredbydesc: Mapped[Optional[str]] = mapped_column(String(100))
    enteredatcode: Mapped[Optional[str]] = mapped_column(String(100))
    enteredatcodestd: Mapped[Optional[str]] = mapped_column(String(100))
    enteredatdesc: Mapped[Optional[str]] = mapped_column(String(100))
    updatedon: Mapped[Optional[datetime]] = mapped_column(DateTime)
    actioncode: Mapped[Optional[str]] = mapped_column(String(3))
    externalid: Mapped[Optional[str]] = mapped_column(String(100))
    update_date: Mapped[Optional[datetime]] = mapped_column(DateTime)


class Encounter(Base):
    __tablename__ = "encounter"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    pid: Mapped[str] = mapped_column(String, ForeignKey("patientrecord.pid"))

    creation_date: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=text("now()")
    )
    idx: Mapped[Optional[int]] = mapped_column(Integer)
    encounternumber: Mapped[Optional[str]] = mapped_column(String(100))
    encountertype: Mapped[Optional[str]] = mapped_column(String(100))
    fromtime: Mapped[Optional[datetime]] = mapped_column(DateTime)
    totime: Mapped[Optional[datetime]] = mapped_column(DateTime)
    admittingcliniciancode: Mapped[Optional[str]] = mapped_column(String(100))
    admittingcliniciancodestd: Mapped[Optional[str]] = mapped_column(String(100))
    admittingcliniciandesc: Mapped[Optional[str]] = mapped_column(String(100))
    admitreasoncode: Mapped[Optional[str]] = mapped_column(String(100))
    admitreasoncodestd: Mapped[Optional[str]] = mapped_column(String(100))
    admitreasondesc: Mapped[Optional[str]] = mapped_column(String(100))
    admissionsourcecode: Mapped[Optional[str]] = mapped_column(String(100))
    admissionsourcecodestd: Mapped[Optional[str]] = mapped_column(String(100))
    admissionsourcedesc: Mapped[Optional[str]] = mapped_column(String(100))
    dischargereasoncode: Mapped[Optional[str]] = mapped_column(String(100))
    dischargereasoncodestd: Mapped[Optional[str]] = mapped_column(String(100))
    dischargereasondesc: Mapped[Optional[str]] = mapped_column(String(100))
    dischargelocationcode: Mapped[Optional[str]] = mapped_column(String(100))
    dischargelocationcodestd: Mapped[Optional[str]] = mapped_column(String(100))
    dischargelocationdesc: Mapped[Optional[str]] = mapped_column(String(100))
    healthcarefacilitycode: Mapped[Optional[str]] = mapped_column(String(100))
    healthcarefacilitycodestd: Mapped[Optional[str]] = mapped_column(String(100))
    healthcarefacilitydesc: Mapped[Optional[str]] = mapped_column(String(100))
    enteredatcode: Mapped[Optional[str]] = mapped_column(String(100))
    enteredatcodestd: Mapped[Optional[str]] = mapped_column(String(100))
    enteredatdesc: Mapped[Optional[str]] = mapped_column(String(100))
    visitdescription: Mapped[Optional[str]] = mapped_column(String(100))
    updatedon: Mapped[Optional[datetime]] = mapped_column(DateTime)
    actioncode: Mapped[Optional[str]] = mapped_column(String(3))
    externalid: Mapped[Optional[str]] = mapped_column(String(100))
    update_date: Mapped[Optional[datetime]] = mapped_column(DateTime)

    # Synonyms

    from_time: Mapped[Optional[datetime]] = synonym("fromtime")
    to_time: Mapped[Optional[datetime]] = synonym("totime")


class ProgramMembership(Base):
    __tablename__ = "programmembership"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    pid: Mapped[str] = mapped_column(String, ForeignKey("patientrecord.pid"))

    creation_date: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=text("now()")
    )
    programname: Mapped[Optional[str]] = mapped_column(String(100))
    programdescription: Mapped[Optional[str]] = mapped_column(String(100))
    enteredbycode: Mapped[Optional[str]] = mapped_column(String(100))
    enteredbycodestd: Mapped[Optional[str]] = mapped_column(String(100))
    enteredbydesc: Mapped[Optional[str]] = mapped_column(String(100))
    enteredatcode: Mapped[Optional[str]] = mapped_column(String(100))
    enteredatcodestd: Mapped[Optional[str]] = mapped_column(String(100))
    enteredatdesc: Mapped[Optional[str]] = mapped_column(String(100))
    fromtime: Mapped[Optional[date]] = mapped_column(Date)
    totime: Mapped[Optional[date]] = mapped_column(Date)
    updatedon: Mapped[Optional[datetime]] = mapped_column(DateTime)
    actioncode: Mapped[Optional[str]] = mapped_column(String(3))
    externalid: Mapped[Optional[str]] = mapped_column(String(100))
    update_date: Mapped[Optional[datetime]] = mapped_column(DateTime)
    # Synonyms
    program_name: Mapped[Optional[str]] = synonym("programname")
    from_time: Mapped[Optional[date]] = synonym("fromtime")
    to_time: Mapped[Optional[date]] = synonym("totime")

    def __str__(self):
        return (
            f"{self.__class__.__name__}({self.pid}) <"
            f"{self.programname} {self.fromtime}"
            f">"
        )


class ClinicalRelationship(Base):
    __tablename__ = "clinicalrelationship"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    pid: Mapped[str] = mapped_column(String, ForeignKey("patientrecord.pid"))

    creation_date: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=text("now()")
    )
    idx: Mapped[Optional[int]] = mapped_column(Integer)
    cliniciancode: Mapped[Optional[str]] = mapped_column(String(100))
    cliniciancodestd: Mapped[Optional[str]] = mapped_column(String(100))
    cliniciandesc: Mapped[Optional[str]] = mapped_column(String(100))
    facilitycode: Mapped[Optional[str]] = mapped_column(String(100))
    facilitycodestd: Mapped[Optional[str]] = mapped_column(String(100))
    facilitydesc: Mapped[Optional[str]] = mapped_column(String(100))
    fromtime: Mapped[Optional[date]] = mapped_column(Date)
    totime: Mapped[Optional[date]] = mapped_column(Date)
    updatedon: Mapped[Optional[datetime]] = mapped_column(DateTime)
    actioncode: Mapped[Optional[str]] = mapped_column(String(3))
    externalid: Mapped[Optional[str]] = mapped_column(String(100))
    update_date: Mapped[Optional[datetime]] = mapped_column(DateTime)


class Name(Base):
    __tablename__ = "name"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    pid: Mapped[str] = mapped_column(String, ForeignKey("patient.pid"))

    creation_date: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=text("now()")
    )
    idx: Mapped[Optional[int]] = mapped_column(Integer)
    nameuse: Mapped[Optional[str]] = mapped_column(String(10))
    prefix: Mapped[Optional[str]] = mapped_column(String(10))
    family: Mapped[Optional[str]] = mapped_column(String(60))
    given: Mapped[Optional[str]] = mapped_column(String(60))
    othergivennames: Mapped[Optional[str]] = mapped_column(String(60))
    suffix: Mapped[Optional[str]] = mapped_column(String(10))
    update_date: Mapped[Optional[datetime]] = mapped_column(DateTime)

    def __str__(self):
        return f"{self.__class__.__name__}({self.pid}) <{self.given} {self.family}>"


class PatientNumber(Base):
    __tablename__ = "patientnumber"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    pid: Mapped[str] = mapped_column(String, ForeignKey("patient.pid"))

    creation_date: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=text("now()")
    )
    idx: Mapped[Optional[int]] = mapped_column(Integer)
    patientid: Mapped[Optional[str]] = mapped_column(String(50), index=True)
    numbertype: Mapped[Optional[str]] = mapped_column(String(3))
    organization: Mapped[Optional[str]] = mapped_column(String(50))
    updatedon: Mapped[Optional[datetime]] = mapped_column(DateTime)
    actioncode: Mapped[Optional[str]] = mapped_column(String(3))
    externalid: Mapped[Optional[str]] = mapped_column(String(100))
    update_date: Mapped[Optional[datetime]] = mapped_column(DateTime)

    patient: Mapped["Patient"] = relationship("Patient", back_populates="numbers")

    def __str__(self):
        return (
            f"{self.__class__.__name__}({self.pid}) <"
            f"{self.organization}:{self.numbertype}:{self.patientid}"
            ">"
        )


class Address(Base):
    __tablename__ = "address"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    pid: Mapped[str] = mapped_column(String, ForeignKey("patient.pid"))

    creation_date: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=text("now()")
    )
    idx: Mapped[Optional[int]] = mapped_column(Integer)
    addressuse: Mapped[Optional[str]] = mapped_column(String(10))
    fromtime: Mapped[Optional[date]] = mapped_column(Date)
    totime: Mapped[Optional[date]] = mapped_column(Date)
    street: Mapped[Optional[str]] = mapped_column(String(100))
    town: Mapped[Optional[str]] = mapped_column(String(100))
    county: Mapped[Optional[str]] = mapped_column(String(100))
    postcode: Mapped[Optional[Optional[str]]] = mapped_column(String)
    countrycode: Mapped[Optional[str]] = mapped_column(String(100))
    countrycodestd: Mapped[Optional[str]] = mapped_column(String(100))
    countrydesc: Mapped[Optional[str]] = mapped_column(String(100))
    update_date: Mapped[Optional[datetime]] = mapped_column(DateTime)

    # Synonyms

    from_time: Mapped[Optional[date]] = synonym("fromtime")
    to_time: Mapped[Optional[date]] = synonym("totime")
    country_code: Mapped[Optional[str]] = synonym("countrycode")
    country_code_std: Mapped[Optional[str]] = synonym("countrycodestd")
    country_description: Mapped[Optional[str]] = synonym("countrydesc")

    def __str__(self):
        return (
            f"{self.__class__.__name__}({self.pid}) <"
            f"{self.street} {self.town} {self.postcode}"
            f">"
        )


class ContactDetail(Base):
    __tablename__ = "contactdetail"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    pid: Mapped[str] = mapped_column(String, ForeignKey("patient.pid"))

    creation_date: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=text("now()")
    )
    idx: Mapped[Optional[int]] = mapped_column(Integer)
    contactuse: Mapped[Optional[str]] = mapped_column(String(10))
    contactvalue: Mapped[Optional[str]] = mapped_column(String(100))
    commenttext: Mapped[Optional[str]] = mapped_column(String(100))
    updatedon: Mapped[Optional[datetime]] = mapped_column(DateTime)
    actioncode: Mapped[Optional[str]] = mapped_column(String(3))
    externalid: Mapped[Optional[str]] = mapped_column(String(100))
    update_date: Mapped[Optional[datetime]] = mapped_column(DateTime)

    # Synonyms
    use: Mapped[Optional[str]] = synonym("contactuse")
    value: Mapped[Optional[str]] = synonym("contactvalue")

    def __str__(self):
        return f"{self.__class__.__name__}({self.pid}) <{self.contactuse}:{self.contactvalue}>"


class Medication(Base):
    __tablename__ = "medication"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    pid: Mapped[str] = mapped_column(String, ForeignKey("patientrecord.pid"))

    creation_date: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=text("now()")
    )

    idx: Mapped[Optional[int]] = mapped_column(Integer)
    repositoryupdatedate: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    prescriptionnumber: Mapped[Optional[str]] = mapped_column(String(100))
    fromtime: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        sqla_info=ColumnInfo(
            label="From Time",
            description="Start time of the prescription",
        ),
    )
    totime: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        sqla_info=ColumnInfo(
            label="To Time",
            description="End time of the prescription",
        ),
    )

    orderedbycode: Mapped[Optional[str]] = mapped_column(String(100))
    orderedbycodestd: Mapped[Optional[str]] = mapped_column(String(100))
    orderedbydesc: Mapped[Optional[str]] = mapped_column(String(100))

    enteringorganizationcode: Mapped[Optional[str]] = mapped_column(String(100))
    enteringorganizationcodestd: Mapped[Optional[str]] = mapped_column(String(100))
    enteringorganizationdesc: Mapped[Optional[str]] = mapped_column(String(100))

    routecode: Mapped[Optional[str]] = mapped_column(
        String(10),
        sqla_info=ColumnInfo(
            label="Route Code",
            description="Code representing medication route",
        ),
    )
    routecodestd: Mapped[Optional[str]] = mapped_column(String(100))
    routedesc: Mapped[Optional[str]] = mapped_column(String(100))

    drugproductidcode: Mapped[Optional[str]] = mapped_column(
        String(100),
        sqla_info=ColumnInfo(
            label="Drug Product ID Code",
            description="Code of the drug product",
        ),
    )
    drugproductidcodestd: Mapped[Optional[str]] = mapped_column(
        String(100),
        sqla_info=ColumnInfo(
            label="Drug Product ID Code Standard",
            description="Coding standard used for the drug product",
        ),
    )
    drugproductiddesc: Mapped[Optional[str]] = mapped_column(
        String(100),
        sqla_info=ColumnInfo(
            label="Drug Product ID Description",
            description="Text description of the drug product",
        ),
    )

    drugproductgeneric: Mapped[Optional[str]] = mapped_column(
        String(255),
        sqla_info=ColumnInfo(
            label=" Drug Product Generic",
            description="Drug product generic",
        ),
    )
    drugproductlabelname: Mapped[Optional[str]] = mapped_column(
        String(255),
        sqla_info=ColumnInfo(
            label="Drug Product Label Name",
            description="Drug product label name",
        ),
    )

    drugproductformcode: Mapped[Optional[str]] = mapped_column(String(100))
    drugproductformcodestd: Mapped[Optional[str]] = mapped_column(String(100))
    drugproductformdesc: Mapped[Optional[str]] = mapped_column(String(100))

    drugproductstrengthunitscode: Mapped[Optional[str]] = mapped_column(String(100))
    drugproductstrengthunitscodestd: Mapped[Optional[str]] = mapped_column(String(100))
    drugproductstrengthunitsdesc: Mapped[Optional[str]] = mapped_column(String(100))

    frequency: Mapped[Optional[str]] = mapped_column(
        String(255),
        sqla_info=ColumnInfo(
            label="Frequency",
            description="Medication frequency",
        ),
    )
    commenttext: Mapped[Optional[str]] = mapped_column(
        String(1000),
        sqla_info=ColumnInfo(
            label="Comment Text",
            description="Free-text comment associated with the medication",
        ),
    )
    dosequantity: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(19, 2),
        sqla_info=ColumnInfo(
            label="Dose Quantity",
            description="Dose of the medication",
        ),
    )

    doseuomcode: Mapped[Optional[str]] = mapped_column(
        String(100),
        sqla_info=ColumnInfo(
            label="Dose UoM Code",
            description="Medication units code",
        ),
    )
    doseuomcodestd: Mapped[Optional[str]] = mapped_column(String(100))
    doseuomdesc: Mapped[Optional[str]] = mapped_column(String(100))

    indication: Mapped[Optional[str]] = mapped_column(String(100))
    updatedon: Mapped[Optional[datetime]] = mapped_column(DateTime)
    actioncode: Mapped[Optional[str]] = mapped_column(String(3))
    externalid: Mapped[Optional[str]] = mapped_column(String(100))
    update_date: Mapped[Optional[datetime]] = mapped_column(DateTime)
    encounternumber: Mapped[Optional[str]] = mapped_column(String(100))

    # Synonyms

    repository_update_date: Mapped[datetime] = synonym("repositoryupdatedate")
    from_time: Mapped[Optional[datetime]] = synonym("fromtime")
    to_time: Mapped[Optional[datetime]] = synonym("totime")
    entering_organization_code: Mapped[Optional[str]] = synonym(
        "enteringorganizationcode"
    )
    entering_organization_description: Mapped[Optional[str]] = synonym(
        "enteringorganizationdesc"
    )
    route_code: Mapped[Optional[str]] = synonym("routecode")
    route_code_std: Mapped[Optional[str]] = synonym("routecodestd")
    route_desc: Mapped[Optional[str]] = synonym("routedesc")
    drug_product_id_code: Mapped[Optional[str]] = synonym("drugproductidcode")
    drug_product_id_description: Mapped[Optional[str]] = synonym("drugproductiddesc")
    drug_product_generic: Mapped[Optional[str]] = synonym("drugproductgeneric")
    comment: Mapped[Optional[str]] = synonym("commenttext")
    dose_quantity: Mapped[Optional[Decimal]] = synonym("dosequantity")
    dose_uom_code: Mapped[Optional[str]] = synonym("doseuomcode")
    dose_uom_code_std: Mapped[Optional[str]] = synonym("doseuomcodestd")
    dose_uom_description: Mapped[Optional[str]] = synonym("doseuomdesc")
    updated_on: Mapped[Optional[datetime]] = synonym("updatedon")
    external_id: Mapped[Optional[str]] = synonym("externalid")

    def __str__(self):
        return f"{self.__class__.__name__}({self.pid})"


class Survey(Base):
    __tablename__ = "survey"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    pid: Mapped[str] = mapped_column(String, ForeignKey("patientrecord.pid"))

    creation_date: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=text("now()")
    )
    surveytime: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    surveytypecode: Mapped[Optional[str]] = mapped_column(String(100))
    surveytypecodestd: Mapped[Optional[str]] = mapped_column(String(100))
    surveytypedesc: Mapped[Optional[str]] = mapped_column(String(100))
    typeoftreatment: Mapped[Optional[str]] = mapped_column(String(100))
    hdlocation: Mapped[Optional[str]] = mapped_column(String(100))
    template: Mapped[Optional[str]] = mapped_column(String(100))
    enteredbycode: Mapped[Optional[str]] = mapped_column(String(100))
    enteredbycodestd: Mapped[Optional[str]] = mapped_column(String(100))
    enteredbydesc: Mapped[Optional[str]] = mapped_column(String(100))
    enteredatcode: Mapped[Optional[str]] = mapped_column(String(100))
    enteredatcodestd: Mapped[Optional[str]] = mapped_column(String(100))
    enteredatdesc: Mapped[Optional[str]] = mapped_column(String(100))
    updatedon: Mapped[Optional[datetime]] = mapped_column(DateTime)
    actioncode: Mapped[Optional[str]] = mapped_column(String(3))
    externalid: Mapped[Optional[str]] = mapped_column(String(100))
    update_date: Mapped[Optional[datetime]] = mapped_column(DateTime)

    # Relationships

    questions = relationship("Question", cascade="all, delete-orphan")
    scores = relationship("Score", cascade="all, delete-orphan")
    levels = relationship("Level", cascade="all, delete-orphan")

    def __str__(self):
        return (
            f"{self.__class__.__name__}({self.pid}) <"
            f"{self.surveytime}:{self.surveytypecode}"
            f">"
        )


class Question(Base):
    __tablename__ = "question"

    id: Mapped[str] = mapped_column(String, primary_key=True)

    surveyid: Mapped[str] = mapped_column(String, ForeignKey("survey.id"))
    creation_date: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=text("now()")
    )
    idx: Mapped[Optional[int]] = mapped_column(Integer)
    questiontypecode: Mapped[Optional[str]] = mapped_column(String(100))
    questiontypecodestd: Mapped[Optional[str]] = mapped_column(String(100))
    questiontypedesc: Mapped[Optional[str]] = mapped_column(String(100))
    response: Mapped[Optional[str]] = mapped_column(String(100))
    questiontext: Mapped[Optional[str]] = mapped_column(String(100))
    update_date: Mapped[Optional[datetime]] = mapped_column(DateTime)


class Score(Base):
    __tablename__ = "score"

    id: Mapped[str] = mapped_column(String, primary_key=True)

    surveyid: Mapped[str] = mapped_column(String, ForeignKey("survey.id"))
    creation_date: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=text("now()")
    )
    idx: Mapped[Optional[int]] = mapped_column(Integer)
    scorevalue: Mapped[Optional[str]] = mapped_column(String(100))
    scoretypecode: Mapped[Optional[str]] = mapped_column(String(100))
    scoretypecodestd: Mapped[Optional[str]] = mapped_column(String(100))
    scoretypedesc: Mapped[Optional[str]] = mapped_column(String(100))
    update_date: Mapped[Optional[datetime]] = mapped_column(DateTime)

    # Synonyms

    value: Mapped[Optional[str]] = synonym("scorevalue")


class Level(Base):
    __tablename__ = "level"

    id: Mapped[str] = mapped_column(String, primary_key=True)

    surveyid: Mapped[str] = mapped_column(String, ForeignKey("survey.id"))
    creation_date: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=text("now()")
    )
    idx: Mapped[Optional[int]] = mapped_column(Integer)
    levelvalue: Mapped[Optional[str]] = mapped_column(String(100))
    leveltypecode: Mapped[Optional[str]] = mapped_column(String(100))
    leveltypecodestd: Mapped[Optional[str]] = mapped_column(String(100))
    leveltypedesc: Mapped[Optional[str]] = mapped_column(String(100))
    update_date: Mapped[Optional[datetime]] = mapped_column(DateTime)

    # Synonyms

    value: Mapped[Optional[str]] = synonym("levelvalue")


class Document(Base):
    __tablename__ = "document"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    pid: Mapped[str] = mapped_column(String, ForeignKey("patientrecord.pid"))

    repositoryupdatedate: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    creation_date: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=text("now()")
    )
    idx: Mapped[Optional[int]] = mapped_column(Integer)
    documenttime: Mapped[Optional[datetime]] = mapped_column(DateTime)
    notetext: Mapped[Optional[str]] = mapped_column(Text)
    documenttypecode: Mapped[Optional[str]] = mapped_column(String(100))
    documenttypecodestd: Mapped[Optional[str]] = mapped_column(String(100))
    documenttypedesc: Mapped[Optional[str]] = mapped_column(String(100))
    cliniciancode: Mapped[Optional[str]] = mapped_column(String(100))
    cliniciancodestd: Mapped[Optional[str]] = mapped_column(String(100))
    cliniciandesc: Mapped[Optional[str]] = mapped_column(String(100))
    documentname: Mapped[Optional[str]] = mapped_column(String(100))
    statuscode: Mapped[Optional[str]] = mapped_column(String(100))
    statuscodestd: Mapped[Optional[str]] = mapped_column(String(100))
    statusdesc: Mapped[Optional[str]] = mapped_column(String(100))
    enteredbycode: Mapped[Optional[str]] = mapped_column(String(100))
    enteredbycodestd: Mapped[Optional[str]] = mapped_column(String(100))
    enteredbydesc: Mapped[Optional[str]] = mapped_column(String(100))
    enteredatcode: Mapped[Optional[str]] = mapped_column(String(100))
    enteredatcodestd: Mapped[Optional[str]] = mapped_column(String(100))
    enteredatdesc: Mapped[Optional[str]] = mapped_column(String(100))
    filetype: Mapped[Optional[str]] = mapped_column(String(100))
    filename: Mapped[Optional[str]] = mapped_column(String(100))
    stream: Mapped[Optional[bytes]] = mapped_column(LargeBinary)
    documenturl: Mapped[Optional[str]] = mapped_column(String(100))
    updatedon: Mapped[Optional[datetime]] = mapped_column(DateTime)
    actioncode: Mapped[Optional[str]] = mapped_column(String(3))
    externalid: Mapped[Optional[str]] = mapped_column(String(100))
    update_date: Mapped[Optional[datetime]] = mapped_column(DateTime)

    # Synonyms

    repository_update_date: Mapped[datetime] = synonym("repositoryupdatedate")


class LabOrder(Base):
    __tablename__ = "laborder"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    pid: Mapped[str] = mapped_column(String, ForeignKey("patientrecord.pid"))

    creation_date = mapped_column(
        DateTime, nullable=False, index=True, server_default=text("now()")
    )
    placerid: Mapped[Optional[str]] = mapped_column(String(100))
    fillerid: Mapped[Optional[str]] = mapped_column(String(100))
    receivinglocationcode: Mapped[Optional[str]] = mapped_column(String(100))
    receivinglocationcodestd: Mapped[Optional[str]] = mapped_column(String(100))
    receivinglocationdesc: Mapped[Optional[str]] = mapped_column(String(100))
    orderedbycode: Mapped[Optional[str]] = mapped_column(String(100))
    orderedbycodestd: Mapped[Optional[str]] = mapped_column(String(100))
    orderedbydesc: Mapped[Optional[str]] = mapped_column(String(100))
    orderitemcode: Mapped[Optional[str]] = mapped_column(String(100))
    orderitemcodestd: Mapped[Optional[str]] = mapped_column(String(100))
    orderitemdesc: Mapped[Optional[str]] = mapped_column(String(100))
    prioritycode: Mapped[Optional[str]] = mapped_column(String(100))
    prioritycodestd: Mapped[Optional[str]] = mapped_column(String(100))
    prioritydesc: Mapped[Optional[str]] = mapped_column(String(100))
    status: Mapped[Optional[str]] = mapped_column(String(100))
    ordercategorycode: Mapped[Optional[str]] = mapped_column(String(100))
    ordercategorycodestd: Mapped[Optional[str]] = mapped_column(String(100))
    ordercategorydesc: Mapped[Optional[str]] = mapped_column(String(100))
    specimensource: Mapped[Optional[str]] = mapped_column(String(50))
    specimenreceivedtime: Mapped[Optional[datetime]] = mapped_column(DateTime)
    specimencollectedtime: Mapped[Optional[datetime]] = mapped_column(DateTime)
    duration: Mapped[Optional[str]] = mapped_column(String(50))
    patientclasscode: Mapped[Optional[str]] = mapped_column(String(100))
    patientclasscodestd: Mapped[Optional[str]] = mapped_column(String(100))
    patientclassdesc: Mapped[Optional[str]] = mapped_column(String(100))
    enteredon: Mapped[Optional[datetime]] = mapped_column(DateTime)
    enteredatcode: Mapped[Optional[str]] = mapped_column(String(100))
    enteredatcodestd: Mapped[Optional[str]] = mapped_column(String(100))
    enteredatdesc: Mapped[Optional[str]] = mapped_column(String(100))
    enteringorganizationcode: Mapped[Optional[str]] = mapped_column(String(100))
    enteringorganizationcodestd: Mapped[Optional[str]] = mapped_column(String(100))
    enteringorganizationdesc: Mapped[Optional[str]] = mapped_column(String(100))
    updatedon: Mapped[Optional[datetime]] = mapped_column(DateTime)
    actioncode: Mapped[Optional[str]] = mapped_column(String(3))
    externalid: Mapped[Optional[str]] = mapped_column(String(100))
    update_date: Mapped[Optional[datetime]] = mapped_column(DateTime, index=True)
    repository_update_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime, index=True
    )

    # Relationships

    result_items: Mapped[List["ResultItem"]] = relationship(
        "ResultItem",
        lazy=GLOBAL_LAZY,
        back_populates="order",
        cascade="all, delete-orphan",
    )
    record: Mapped["PatientRecord"] = relationship(
        "PatientRecord", back_populates="lab_orders", uselist=False
    )

    # Synonyms

    receiving_location: Mapped[Optional[str]] = synonym("receivinglocationcode")
    receiving_location_description: Mapped[Optional[str]] = synonym(
        "receivinglocationdesc"
    )
    receiving_location_code_std: Mapped[Optional[str]] = synonym(
        "receivinglocationcodestd"
    )
    placer_id: Mapped[Optional[str]] = synonym("placerid")
    filler_id: Mapped[Optional[str]] = synonym("fillerid")
    ordered_by: Mapped[Optional[str]] = synonym("orderedbycode")
    ordered_by_description: Mapped[Optional[str]] = synonym("orderedbydesc")
    ordered_by_code_std: Mapped[Optional[str]] = synonym("orderedbycodestd")
    order_item: Mapped[Optional[str]] = synonym("orderitemcode")
    order_item_description: Mapped[Optional[str]] = synonym("orderitemdesc")
    order_item_code_std: Mapped[Optional[str]] = synonym("orderitemcodestd")
    order_category: Mapped[Optional[str]] = synonym("ordercategorycode")
    order_category_description: Mapped[Optional[str]] = synonym("ordercategorydesc")
    order_category_code_std: Mapped[Optional[str]] = synonym("ordercategorycodestd")
    specimen_collected_time: Mapped[Optional[datetime]] = synonym(
        "specimencollectedtime"
    )
    specimen_received_time: Mapped[Optional[datetime]] = synonym("specimenreceivedtime")
    priority: Mapped[Optional[str]] = synonym("prioritycode")
    priority_description: Mapped[Optional[str]] = synonym("prioritydesc")
    priority_code_std: Mapped[Optional[str]] = synonym("prioritycodestd")
    specimen_source: Mapped[Optional[str]] = synonym("specimensource")
    patient_class: Mapped[Optional[str]] = synonym("patientclasscode")
    patient_class_description: Mapped[Optional[str]] = synonym("patientclassdesc")
    patient_class_code_std: Mapped[Optional[str]] = synonym("patientclasscodestd")
    entered_on: Mapped[Optional[datetime]] = synonym("enteredon")
    entered_at: Mapped[Optional[str]] = synonym("enteredatcode")
    entered_at_description: Mapped[Optional[str]] = synonym("enteredatdesc")
    external_id: Mapped[Optional[str]] = synonym("externalid")
    entering_organization_code: Mapped[Optional[str]] = synonym(
        "enteringorganizationcode"
    )
    entering_organization_description: Mapped[Optional[str]] = synonym(
        "enteringorganizationdesc"
    )
    entering_organization_code_std: Mapped[Optional[str]] = synonym(
        "enteringorganizationcodestd"
    )


class ResultItem(Base):
    __tablename__ = "resultitem"

    id: Mapped[str] = mapped_column(
        String,
        primary_key=True,
        sqla_info=ColumnInfo(
            label="Result Item ID",
            description="Unique identifier for the result item.",
        ),
    )
    orderid: Mapped[str] = mapped_column(
        "orderid",
        String,
        ForeignKey("laborder.id"),
        sqla_info=ColumnInfo(
            label="Order ID",
            description="Identifier of the related laboratory order.",
        ),
    )
    creation_date: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=text("now()"),
        sqla_info=ColumnInfo(
            label="Creation Date",
            description="Date and time when the result item was created.",
        ),
    )
    resulttype: Mapped[Optional[str]] = mapped_column(
        String(2),
        sqla_info=ColumnInfo(label="Result Type", description="Type of result."),
    )
    serviceidcode: Mapped[Optional[str]] = mapped_column(
        String(100),
        sqla_info=ColumnInfo(
            label="Service ID Code",
            description="Test code identifying the laboratory service or test performed.",
        ),
    )
    serviceidcodestd: Mapped[Optional[str]] = mapped_column(
        String(100),
        sqla_info=ColumnInfo(
            label="Service ID Code Standard",
            description="Coding standard used for the service ID (SNOMED, LOINC, UKRR, PV, LOCAL).",
        ),
    )
    serviceiddesc: Mapped[Optional[str]] = mapped_column(
        String(100),
        sqla_info=ColumnInfo(
            label="Service ID Description",
            description="Text description of the laboratory service or test performed.",
        ),
    )
    subid: Mapped[Optional[str]] = mapped_column(
        String(50), sqla_info=ColumnInfo(label="Sub ID", description="Sub-Test Id.")
    )
    resultvalue: Mapped[Optional[str]] = mapped_column(
        String(20),
        sqla_info=ColumnInfo(
            label="Result Value",
            description="The measured or observed value.",
        ),
    )
    resultvalueunits: Mapped[Optional[str]] = mapped_column(
        String(30),
        sqla_info=ColumnInfo(
            label="Result Value Units",
            description="Units of measurement for the result value.",
        ),
    )
    referencerange: Mapped[Optional[str]] = mapped_column(
        String(30),
        sqla_info=ColumnInfo(
            label="Reference Range",
            description="Reference range for the test result.",
        ),
    )
    interpretationcodes: Mapped[Optional[str]] = mapped_column(
        String(50),
        sqla_info=ColumnInfo(
            label="Interpretation Codes",
            description="Code(s) indicating interpretation of the result (POS, NEG, UNK).",
        ),
    )
    status: Mapped[Optional[str]] = mapped_column(
        String(5),
        sqla_info=ColumnInfo(
            label="Result Status",
            description="Status of the result (F, P, D).",
        ),
    )
    observationtime: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        sqla_info=ColumnInfo(
            label="Observation Time",
            description="Date and time when the observation or measurement was made.",
        ),
    )
    commenttext: Mapped[Optional[str]] = mapped_column(
        String(1000),
        sqla_info=ColumnInfo(
            label="Comment Text",
            description="Free-text comment associated with the result.",
        ),
    )
    referencecomment: Mapped[Optional[str]] = mapped_column(
        String(1000),
        sqla_info=ColumnInfo(
            label="Reference Comment",
            description="Reference comment provided with the result.",
        ),
    )
    prepost: Mapped[Optional[str]] = mapped_column(
        String(4),
        sqla_info=ColumnInfo(
            label="Pre/Post Indicator",
            description="Indicates whether the sample was taken PRE or POST dialysis (PRE, POST, UNK, NA).",
        ),
    )
    enteredon: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        sqla_info=ColumnInfo(
            label="Entered On",
            description="Date and time when the result was entered into the system.",
        ),
    )
    updatedon: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        sqla_info=ColumnInfo(label="Updated On", description="Last Modified Date"),
    )
    actioncode: Mapped[Optional[str]] = mapped_column(
        String(3),
        sqla_info=ColumnInfo(
            label="Action Code",
            description="Code representing the action performed on the result record.",
        ),
    )
    externalid: Mapped[Optional[str]] = mapped_column(
        String(100),
        sqla_info=ColumnInfo(label="External ID", description="Unique Identifier"),
    )
    update_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        sqla_info=ColumnInfo(
            label="Update Date",
            description="Date and time when the record was last updated.",
        ),
    )

    # Proxies

    pid = association_proxy("order", "pid")

    # Relationships
    order: Mapped["LabOrder"] = relationship("LabOrder", back_populates="result_items")

    # Synonyms
    order_id: Mapped[str] = synonym("orderid")
    result_type: Mapped[Optional[str]] = synonym("resulttype")
    entered_on: Mapped[Optional[datetime]] = synonym("enteredon")
    pre_post: Mapped[Optional[str]] = synonym("prepost")
    service_id: Mapped[Optional[str]] = synonym("serviceidcode")
    service_id_std: Mapped[Optional[str]] = synonym("serviceidcodestd")
    service_id_description: Mapped[Optional[str]] = synonym("serviceiddesc")
    sub_id: Mapped[Optional[str]] = synonym("subid")
    value: Mapped[Optional[str]] = synonym("resultvalue")
    value_units: Mapped[Optional[str]] = synonym("resultvalueunits")
    reference_range: Mapped[Optional[str]] = synonym("referencerange")
    interpretation_codes: Mapped[Optional[str]] = synonym("interpretationcodes")
    observation_time: Mapped[Optional[datetime]] = synonym("observationtime")
    comments: Mapped[Optional[str]] = synonym("commenttext")
    reference_comment: Mapped[Optional[str]] = synonym("referencecomment")


class PVData(Base):
    __tablename__ = "pvdata"

    id: Mapped[str] = mapped_column(
        String, ForeignKey("patientrecord.pid"), primary_key=True
    )

    creation_date: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=text("now()")
    )
    update_date: Mapped[Optional[datetime]] = mapped_column(DateTime)

    diagnosisdate: Mapped[Optional[date]] = mapped_column(Date)

    bloodgroup: Mapped[Optional[str]] = mapped_column(String(10))

    rrtstatus: Mapped[Optional[str]] = mapped_column(String(100))
    tpstatus: Mapped[Optional[str]] = mapped_column(String(100))

    # Proxies

    rrtstatus_desc = association_proxy("rrtstatus_info", "description")
    tpstatus_desc = association_proxy("tpstatus_info", "description")

    # Relationships
    rrtstatus_info = relationship(
        "Code",
        primaryjoin="and_(remote(Code.coding_standard)=='PV_RRTSTATUS', foreign(PVData.rrtstatus)==remote(Code.code))",
    )

    tpstatus_info = relationship(
        "Code",
        primaryjoin="and_(remote(Code.coding_standard)=='PV_TPSTATUS', foreign(PVData.tpstatus)==remote(Code.code))",
    )

    def __str__(self):
        return f"{self.__class__.__name__}({self.id})"


class PVDelete(Base):
    __tablename__ = "pvdelete"

    did: Mapped[int] = mapped_column(Integer, primary_key=True)

    pid: Mapped[str] = mapped_column(String, ForeignKey("patientrecord.pid"))
    creation_date: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=text("now()")
    )
    observationtime: Mapped[Optional[datetime]] = mapped_column(DateTime)
    serviceidcode: Mapped[Optional[str]] = mapped_column(String(100))
    update_date: Mapped[Optional[datetime]] = mapped_column(DateTime)

    # Synonyms

    observation_time: Mapped[Optional[datetime]] = synonym("observationtime")
    service_id: Mapped[Optional[str]] = synonym("serviceidcode")


class Treatment(Base):
    __tablename__ = "treatment"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    pid: Mapped[str] = mapped_column(String, ForeignKey("patientrecord.pid"))

    creation_date: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=text("now()")
    )
    idx: Mapped[Optional[int]] = mapped_column(Integer)
    encounternumber: Mapped[Optional[str]] = mapped_column(String(100))
    encountertype: Mapped[Optional[str]] = mapped_column(String(100))
    fromtime: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        sqla_info=ColumnInfo(
            label="From Time",
            description="Start of treatment date",
        ),
    )
    totime: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        sqla_info=ColumnInfo(
            label="To Time",
            description="End of treatment date",
        ),
    )
    admittingcliniciancode: Mapped[Optional[str]] = mapped_column(String(100))
    admittingcliniciancodestd: Mapped[Optional[str]] = mapped_column(String(100))
    admittingcliniciandesc: Mapped[Optional[str]] = mapped_column(String(100))
    admitreasoncode: Mapped[Optional[str]] = mapped_column(
        String(100),
        sqla_info=ColumnInfo(
            label="Admission Reason Code",
            description="Treatment modality code",
        ),
    )
    admitreasoncodestd: Mapped[Optional[str]] = mapped_column(
        String(100),
        sqla_info=ColumnInfo(
            label="Admission Reason Code Standard",
            description="Treatment modality code standard",
        ),
    )
    admitreasondesc: Mapped[Optional[str]] = mapped_column(
        String(100),
        sqla_info=ColumnInfo(
            label="Admission Reason Description",
            description="Text description of treatment modality",
        ),
    )
    admissionsourcecode: Mapped[Optional[str]] = mapped_column(
        String(100),
        sqla_info=ColumnInfo(
            label="Admission Source Code",
            description="Code representing prior main renal unit",
        ),
    )
    admissionsourcecodestd: Mapped[Optional[str]] = mapped_column(
        String(100),
        sqla_info=ColumnInfo(
            label="Admission Source Code Standard",
            description="Coding standard used for the admission source",
        ),
    )
    admissionsourcedesc: Mapped[Optional[str]] = mapped_column(
        String(100),
        sqla_info=ColumnInfo(
            label="Admission Source Description",
            description="Text description of admission source",
        ),
    )
    dischargereasoncode: Mapped[Optional[str]] = mapped_column(String(100))
    dischargereasoncodestd: Mapped[Optional[str]] = mapped_column(String(100))
    dischargereasondesc: Mapped[Optional[str]] = mapped_column(String(100))
    dischargelocationcode: Mapped[Optional[str]] = mapped_column(
        String(100),
        sqla_info=ColumnInfo(
            label="Discharge Location Code",
            description="Code representing destination main renal unit",
        ),
    )
    dischargelocationcodestd: Mapped[Optional[str]] = mapped_column(
        String(100),
        sqla_info=ColumnInfo(
            label="Discharge location Code Standard",
            description="Coding standard used for the discharge location code",
        ),
    )
    dischargelocationdesc: Mapped[Optional[str]] = mapped_column(
        String(100),
        sqla_info=ColumnInfo(
            label="Discharge Location Description",
            description="Text description of discharge location",
        ),
    )
    healthcarefacilitycode: Mapped[Optional[str]] = mapped_column(
        String(100),
        sqla_info=ColumnInfo(
            label="Healthcare Facility Code",
            description="Code representing the treatment centre",
        ),
    )
    healthcarefacilitycodestd: Mapped[Optional[str]] = mapped_column(
        String(100),
        sqla_info=ColumnInfo(
            label="Healthcare Facility Code Standard",
            description="Coding standard used for the treatment centre",
        ),
    )
    healthcarefacilitydesc: Mapped[Optional[str]] = mapped_column(
        String(100),
        sqla_info=ColumnInfo(
            label="Healthcare Facility Description",
            description="Text description of the treatment centre",
        ),
    )
    enteredatcode: Mapped[Optional[str]] = mapped_column(String(100))
    enteredatcodestd: Mapped[Optional[str]] = mapped_column(String(100))
    enteredatdesc: Mapped[Optional[str]] = mapped_column(String(100))
    visitdescription: Mapped[Optional[str]] = mapped_column(String(100))
    updatedon: Mapped[Optional[datetime]] = mapped_column(DateTime)
    actioncode: Mapped[Optional[str]] = mapped_column(String(3))
    externalid: Mapped[Optional[str]] = mapped_column(String(100))
    hdp01: Mapped[Optional[str]] = mapped_column(String(255))
    hdp02: Mapped[Optional[str]] = mapped_column(String(255))
    hdp03: Mapped[Optional[str]] = mapped_column(String(255))
    hdp04: Mapped[Optional[str]] = mapped_column(String(255))
    qbl05: Mapped[Optional[str]] = mapped_column(
        String(255),
        sqla_info=ColumnInfo(
            label="QBL05",
            description="HD treatment location",
        ),
    )
    qbl06: Mapped[Optional[str]] = mapped_column(String(255))
    qbl07: Mapped[Optional[str]] = mapped_column(String(255))
    erf61: Mapped[Optional[str]] = mapped_column(String(255))
    pat35: Mapped[Optional[str]] = mapped_column(String(255))
    update_date: Mapped[Optional[datetime]] = mapped_column(DateTime)

    # Proxies

    admit_reason_desc = association_proxy("admit_reason_code_item", "description")
    discharge_reason_desc = association_proxy(
        "discharge_reason_code_item", "description"
    )

    # Relationships

    admit_reason_code_item = relationship(
        "Code",
        primaryjoin="and_(foreign(Treatment.admit_reason_code_std)==remote(Code.coding_standard), foreign(Treatment.admit_reason_code)==remote(Code.code))",
    )

    discharge_reason_code_item = relationship(
        "Code",
        primaryjoin="and_(foreign(Treatment.discharge_reason_code_std)==remote(Code.coding_standard), foreign(Treatment.discharge_reason_code)==remote(Code.code))",
    )

    # Synonyms

    encounter_number: Mapped[Optional[str]] = synonym("encounternumber")
    encounter_type: Mapped[Optional[str]] = synonym("encountertype")
    from_time: Mapped[Optional[datetime]] = synonym("fromtime")
    to_time: Mapped[Optional[datetime]] = synonym("totime")
    admitting_clinician_code: Mapped[Optional[str]] = synonym("admittingcliniciancode")
    admitting_clinician_code_std: Mapped[Optional[str]] = synonym(
        "admittingcliniciancodestd"
    )
    admitting_clinician_desc: Mapped[Optional[str]] = synonym("admittingcliniciandesc")
    admission_source_code: Mapped[Optional[str]] = synonym("admissionsourcecode")
    admission_source_code_std: Mapped[Optional[str]] = synonym("admissionsourcecodestd")
    admission_source_desc: Mapped[Optional[str]] = synonym("admissionsourcedesc")
    admit_reason_code: Mapped[Optional[str]] = synonym("admitreasoncode")
    admit_reason_code_std: Mapped[Optional[str]] = synonym("admitreasoncodestd")
    discharge_reason_code: Mapped[Optional[str]] = synonym("dischargereasoncode")
    discharge_reason_code_std: Mapped[Optional[str]] = synonym("dischargereasoncodestd")
    discharge_location_code: Mapped[Optional[str]] = synonym("dischargelocationcode")
    discharge_location_code_std: Mapped[Optional[str]] = synonym(
        "dischargelocationcodestd"
    )
    discharge_location_desc: Mapped[Optional[str]] = synonym("dischargelocationdesc")
    health_care_facility_code: Mapped[Optional[str]] = synonym("healthcarefacilitycode")
    health_care_facility_code_std: Mapped[Optional[str]] = synonym(
        "healthcarefacilitycodestd"
    )
    health_care_facility_desc: Mapped[Optional[str]] = synonym("healthcarefacilitydesc")
    entered_at_code: Mapped[Optional[str]] = synonym("enteredatcode")
    visit_description: Mapped[Optional[str]] = synonym("visitdescription")
    updated_on: Mapped[Optional[datetime]] = synonym("updatedon")
    action_code: Mapped[Optional[str]] = synonym("actioncode")
    external_id: Mapped[Optional[str]] = synonym("externalid")


class TransplantList(Base):
    __tablename__ = "transplantlist"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    pid: Mapped[str] = mapped_column(String, ForeignKey("patientrecord.pid"))

    idx: Mapped[int] = mapped_column(Integer)
    creation_date: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=text("now()")
    )
    encounternumber: Mapped[Optional[str]] = mapped_column(String(100))
    encountertype: Mapped[Optional[str]] = mapped_column(String(100))
    fromtime: Mapped[Optional[datetime]] = mapped_column(DateTime)
    totime: Mapped[Optional[datetime]] = mapped_column(DateTime)
    admittingcliniciancode: Mapped[Optional[str]] = mapped_column(String(100))
    admittingcliniciancodestd: Mapped[Optional[str]] = mapped_column(String(100))
    admittingcliniciandesc: Mapped[Optional[str]] = mapped_column(String(100))
    admitreasoncode: Mapped[Optional[str]] = mapped_column(String(100))
    admitreasoncodestd: Mapped[Optional[str]] = mapped_column(String(100))
    admitreasondesc: Mapped[Optional[str]] = mapped_column(String(100))
    admissionsourcecode: Mapped[Optional[str]] = mapped_column(String(100))
    admissionsourcecodestd: Mapped[Optional[str]] = mapped_column(String(100))
    admissionsourcedesc: Mapped[Optional[str]] = mapped_column(String(100))
    dischargereasoncode: Mapped[Optional[str]] = mapped_column(String(100))
    dischargereasoncodestd: Mapped[Optional[str]] = mapped_column(String(100))
    dischargereasondesc: Mapped[Optional[str]] = mapped_column(String(100))
    dischargelocationcode: Mapped[Optional[str]] = mapped_column(String(100))
    dischargelocationcodestd: Mapped[Optional[str]] = mapped_column(String(100))
    dischargelocationdesc: Mapped[Optional[str]] = mapped_column(String(100))
    healthcarefacilitycode: Mapped[Optional[str]] = mapped_column(String(100))
    healthcarefacilitycodestd: Mapped[Optional[str]] = mapped_column(String(100))
    healthcarefacilitydesc: Mapped[Optional[str]] = mapped_column(String(100))
    enteredatcode: Mapped[Optional[str]] = mapped_column(String(100))
    enteredatcodestd: Mapped[Optional[str]] = mapped_column(String(100))
    enteredatdesc: Mapped[Optional[str]] = mapped_column(String(100))
    visitdescription: Mapped[Optional[str]] = mapped_column(String(100))
    updatedon: Mapped[Optional[datetime]] = mapped_column(DateTime)
    actioncode: Mapped[Optional[str]] = mapped_column(String(3))
    externalid: Mapped[Optional[str]] = mapped_column(String(100))
    update_date: Mapped[Optional[datetime]] = mapped_column(DateTime)


class Code(Base):
    __tablename__ = "code_list"

    coding_standard: Mapped[str] = mapped_column(String(256), primary_key=True)
    code: Mapped[str] = mapped_column(String(256), primary_key=True)
    creation_date: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=text("now()")
    )
    description: Mapped[Optional[str]] = mapped_column(String(256))
    object_type: Mapped[Optional[str]] = mapped_column(String(256))
    update_date: Mapped[Optional[datetime]] = mapped_column(DateTime)
    units: Mapped[Optional[str]] = mapped_column(String(256))
    pkb_reference_range: Mapped[Optional[str]] = mapped_column(String(10))
    pkb_comment: Mapped[Optional[str]] = mapped_column(String(365))


class CodeExclusion(Base):
    __tablename__ = "code_exclusion"

    coding_standard: Mapped[str] = mapped_column(String, primary_key=True)
    code: Mapped[str] = mapped_column(String, primary_key=True)
    system: Mapped[str] = mapped_column(String, primary_key=True)


class CodeMap(Base):
    __tablename__ = "code_map"

    source_coding_standard: Mapped[str] = mapped_column(String(256), primary_key=True)
    source_code: Mapped[str] = mapped_column(String(256), primary_key=True)
    destination_coding_standard: Mapped[str] = mapped_column(
        String(256), primary_key=True
    )
    destination_code: Mapped[str] = mapped_column(String(256), primary_key=True)

    creation_date: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=text("now()")
    )
    update_date: Mapped[Optional[datetime]] = mapped_column(DateTime)


class Facility(Base):
    __tablename__ = "facility_new"

    # New columns matching SQL schema
    facilitycode: Mapped[str] = mapped_column(
        "facilitycode", String(100), primary_key=True
    )
    facilitycodestd: Mapped[str] = mapped_column(
        "facilitycodestd", String(100), primary_key=True
    )
    facilitytype: Mapped[str] = mapped_column(
        "facilitytype", String(100), nullable=False
    )
    pkbout: Mapped[bool] = mapped_column(
        "pkbout", Boolean, nullable=False, server_default=text("false")
    )
    pkbmsgexclusions: Mapped[Optional[str]] = mapped_column(
        "pkbmsgexclusions", ARRAY(Text)
    )
    pkb_pv_msg_exclusions: Mapped[Optional[str]] = mapped_column(
        "pkb_pv_msg_exclusions", ARRAY(Text)
    )
    pkb_ukrdc_msg_exclusions: Mapped[Optional[str]] = mapped_column(
        "pkb_ukrdc_msg_exclusions", ARRAY(Text)
    )
    ukrdcoutpkb: Mapped[bool] = mapped_column(
        "ukrdcoutpkb", Boolean, nullable=False, server_default=text("false")
    )
    pvoutpkb: Mapped[bool] = mapped_column(
        "pvoutpkb", Boolean, nullable=False, server_default=text("false")
    )
    startdate: Mapped[Optional[datetime]] = mapped_column("startdate", DateTime)
    enddate: Mapped[Optional[datetime]] = mapped_column("enddate", DateTime)
    firstdataquarter: Mapped[Optional[int]] = mapped_column("firstdataquarter", Integer)
    pkboutstartdate: Mapped[Optional[datetime]] = mapped_column(
        "pkboutstartdate", DateTime
    )
    creation_date: Mapped[datetime] = mapped_column(
        "creation_date", DateTime, nullable=False, server_default=text("now()")
    )
    update_date: Mapped[datetime] = mapped_column(
        "update_date", DateTime, nullable=False, server_default=text("now()")
    )

    # Foreign Key to code_list
    __table_args__ = (
        ForeignKeyConstraint(
            ["facilitycode", "facilitycodestd"],
            ["code_list.code", "code_list.coding_standard"],
            onupdate="CASCADE",
            ondelete="RESTRICT",
        ),
    )

    # Synonyms for old column names (backward compatibility)
    code: Mapped[str] = synonym("facilitycode")
    coding_standard: Mapped[str] = synonym("facilitycodestd")
    pkb_out: Mapped[bool] = synonym("pkbout")
    pkb_msg_exclusions: Mapped[Optional[str]] = synonym("pkbmsgexclusions")
    rdastartdate: Mapped[Optional[datetime]] = synonym("startdate")
    rdaenddate: Mapped[Optional[datetime]] = synonym("enddate")
    rdafirstdataquarter: Mapped[Optional[int]] = synonym("firstdataquarter")

    description = association_proxy("code_info", "description")

    code_info = relationship(
        "Code",
        primaryjoin="and_(remote(Code.coding_standard)==foreign(Facility.facilitycodestd), "
        "foreign(Facility.facilitycode)==remote(Code.code))",
    )

    # v1 compatibility: provide a placeholder pkb_inboud flag to represent
    # depricated column
    @property
    def pkb_in(self) -> bool:
        return False


class RRCodes(Base):
    __tablename__ = "rr_codes"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    rr_code = mapped_column("rr_code", String, primary_key=True)

    description_1: Mapped[Optional[str]] = mapped_column(String(255))
    description_2: Mapped[Optional[str]] = mapped_column(String(70))
    description_3: Mapped[Optional[str]] = mapped_column(String(60))

    old_value: Mapped[Optional[str]] = mapped_column(String(10))
    old_value_2: Mapped[Optional[str]] = mapped_column(String(10))
    new_value: Mapped[Optional[str]] = mapped_column(String(10))


class Locations(Base):
    __tablename__ = "locations"

    centre_code: Mapped[str] = mapped_column(String(10), primary_key=True)
    centre_name: Mapped[Optional[str]] = mapped_column(String(255))
    country_code: Mapped[Optional[str]] = mapped_column(String(6))
    region_code: Mapped[Optional[str]] = mapped_column(String(10))
    paed_unit: Mapped[Optional[int]] = mapped_column(Integer)


class RRDataDefinition(Base):
    __tablename__ = "rr_data_definition"

    upload_key: Mapped[str] = mapped_column(String(5), primary_key=True)

    table_name = mapped_column("TABLE_NAME", String(30), nullable=False)
    field_name: Mapped[str] = mapped_column(String(30), nullable=False)
    code_id: Mapped[Optional[str]] = mapped_column(String(10))
    mandatory: Mapped[Optional[Decimal]] = mapped_column(Numeric(1, 0))

    code_type: Mapped[Optional[str]] = mapped_column("TYPE", String(1))

    alt_constraint: Mapped[Optional[str]] = mapped_column(String(30))
    alt_desc: Mapped[Optional[str]] = mapped_column(String(30))
    extra_val: Mapped[Optional[str]] = mapped_column(String(1))
    error_type: Mapped[Optional[int]] = mapped_column(Integer)
    paed_mand: Mapped[Optional[Decimal]] = mapped_column(Numeric(1, 0))
    ckd5_mand_numeric: Mapped[Optional[Decimal]] = mapped_column(
        "ckd5_mand", Numeric(1, 0)
    )
    dependant_field: Mapped[Optional[str]] = mapped_column(String(30))
    alt_validation: Mapped[Optional[str]] = mapped_column(String(30))

    file_prefix: Mapped[Optional[str]] = mapped_column(String(20))

    load_min: Mapped[Optional[Decimal]] = mapped_column(Numeric(38, 4))
    load_max: Mapped[Optional[Decimal]] = mapped_column(Numeric(38, 4))
    remove_min: Mapped[Optional[Decimal]] = mapped_column(Numeric(38, 4))
    remove_max: Mapped[Optional[Decimal]] = mapped_column(Numeric(38, 4))
    in_month: Mapped[Optional[Decimal]] = mapped_column(Numeric(1, 0))
    aki_mand: Mapped[Optional[Decimal]] = mapped_column(Numeric(1, 0))
    rrt_mand: Mapped[Optional[Decimal]] = mapped_column(Numeric(1, 0))
    cons_mand: Mapped[Optional[Decimal]] = mapped_column(Numeric(1, 0))
    ckd4_mand: Mapped[Optional[Decimal]] = mapped_column(Numeric(1, 0))
    valid_before_dob: Mapped[Optional[Decimal]] = mapped_column(Numeric(1, 0))
    valid_after_dod: Mapped[Optional[Decimal]] = mapped_column(Numeric(1, 0))
    in_quarter: Mapped[Optional[Decimal]] = mapped_column(Numeric(1, 0))

    # Synonyms

    TYPE: Mapped[Optional[str]] = synonym("code_type")
    ckd5_mand: Mapped[Optional[str]] = synonym("ckd5_mand_numeric")
    # historical typo for compatibility tests
    feild_name: Mapped[Optional[str]] = synonym("field_name")


class ModalityCodes(Base):
    __tablename__ = "modality_codes"

    registry_code: Mapped[str] = mapped_column(String(8), primary_key=True)

    registry_code_desc: Mapped[Optional[str]] = mapped_column(String(100))
    registry_code_type: Mapped[str] = mapped_column(String(3), nullable=False)
    acute: Mapped[int] = mapped_column(BIT(1), nullable=False)
    transfer_in: Mapped[int] = mapped_column(BIT(1), nullable=False)
    ckd: Mapped[int] = mapped_column(BIT(1), nullable=False)
    cons: Mapped[int] = mapped_column(BIT(1), nullable=False)
    rrt: Mapped[int] = mapped_column(BIT(1), nullable=False)
    equiv_modality: Mapped[Optional[str]] = mapped_column(String(8))
    end_of_care: Mapped[int] = mapped_column(BIT(1), nullable=False)
    is_imprecise: Mapped[int] = mapped_column(BIT(1), nullable=False)
    nhsbt_transplant_type: Mapped[Optional[str]] = mapped_column(String(4))
    transfer_out: Mapped[Optional[int]] = mapped_column(BIT(1))


class SatelliteMap(Base):
    __tablename__ = "vwe_satellite_map"

    satellite_code: Mapped[str] = mapped_column(String(10), primary_key=True)
    main_unit_code: Mapped[str] = mapped_column(String(10), primary_key=True)

    # attributes for backwards compatability
    @property
    def creation_date(self) -> bool:
        return False

    @property
    def update_date(self) -> bool:
        return False


class FacilityRelationship(Base):
    __tablename__ = "vwe_facility_relationship"

    parentfacilitycode: Mapped[str] = mapped_column(String(100), primary_key=True)
    parentfacilitycodestd: Mapped[str] = mapped_column(String(100), primary_key=True)
    childfacilitycode: Mapped[str] = mapped_column(String(100), primary_key=True)
    childfacilitycodestd: Mapped[str] = mapped_column(String(100), primary_key=True)
    relationshiptype: Mapped[Optional[str]] = mapped_column(String(50))


class ValueExclusion(Base):
    __tablename__ = "value_exclusion"

    system: Mapped[str] = mapped_column(String(20), primary_key=True)
    norm_value: Mapped[str] = mapped_column(String(100), primary_key=True)


class File(Base):
    __tablename__ = "file"

    sendingfacility: Mapped[str] = mapped_column(String(7), primary_key=True)
    sendingextract: Mapped[str] = mapped_column(String(6), primary_key=True)
    ni: Mapped[str] = mapped_column(String(50), primary_key=True)

    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    checksum: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    received_on: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    creation_date: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=text("now()"),
    )
    update_date: Mapped[Optional[datetime]] = mapped_column(DateTime)
