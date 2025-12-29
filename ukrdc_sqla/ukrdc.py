"""Models which relate to the main UKRDC database"""

import datetime
from dataclasses import dataclass
from typing import List, Optional, Union, Tuple, Any

from sqlalchemy import (
    Boolean,
    ForeignKeyConstraint,
    Column as Col,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    LargeBinary,
    MetaData,
    Numeric,
    String,
    Text,
    text,
    Enum,
)
from sqlalchemy.dialects.postgresql import ARRAY, BIT
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.orm import (
    Mapped,
    relationship,
    synonym,
    declarative_base,
    DynamicMapped,
    mapped_column,
)


@dataclass
class ColumnInfo:
    label: str
    description: str


class Column(Col):
    """A Column subclass that supports typed metadata via a ColumnInfo dataclass.

    When `sqla_info` is set, its `description` field is also applied as the SQL
    comment automatically.
    """

    inherit_cache = True  # this tells sqlalchemy that it can compile like normal

    def __init__(
        self,
        *args: Any,
        sqla_info: Optional[ColumnInfo] = None,
        **kwargs: Any,
    ):
        # Ensure .info dict exists
        info = dict(kwargs.pop("info", {}) or {})
        if sqla_info:
            info["sqla_info"] = sqla_info
            # If no explicit comment is provided, use description this will populate the database with comments
            if "comment" not in kwargs and sqla_info.description:
                kwargs["comment"] = sqla_info.description
        # Call base Column constructor
        super().__init__(*args, info=info, **kwargs)

    # Provide a typed property for easy access
    @property
    def sqla_info(self) -> Optional[ColumnInfo]:
        return self.info.get("sqla_info")


metadata = MetaData()
Base = declarative_base(metadata=metadata)

GLOBAL_LAZY = "dynamic"


class PatientRecord(Base):
    __tablename__ = "patientrecord"

    pid = Column(String, primary_key=True)

    sendingfacility: Mapped[str] = mapped_column(String(7), nullable=False)
    sendingextract = Column(String(6), nullable=False)
    localpatientid = Column(String(17), nullable=False)
    repositorycreationdate = Column(DateTime, nullable=False)
    repositoryupdatedate = Column(DateTime, nullable=False)
    migrated = Column(Boolean, nullable=False, server_default=text("false"))
    creation_date = Column(DateTime, nullable=False, server_default=text("now()"))
    ukrdcid = Column(String(10), index=True)
    channelname = Column(String(50))
    channelid = Column(String(50))
    extracttime = Column(String(50))
    startdate = Column(DateTime)
    stopdate = Column(DateTime)
    schemaversion = Column(String(50))
    update_date = Column(DateTime)

    # Relationships

    patient: Mapped["Patient"] = relationship(
        "Patient", backref="record", uselist=False, cascade="all, delete-orphan"
    )
    lab_orders: DynamicMapped["LabOrder"] = relationship(
        "LabOrder", backref="record", lazy=GLOBAL_LAZY, cascade="all, delete-orphan"
    )
    result_items: Mapped[List["ResultItem"]] = relationship(
        "ResultItem",
        secondary="laborder",
        primaryjoin="LabOrder.pid == PatientRecord.pid",
        secondaryjoin="ResultItem.order_id == LabOrder.id",
        lazy=GLOBAL_LAZY,
        viewonly=True,
    )
    observations: DynamicMapped["Observation"] = relationship(
        "Observation", backref="record", lazy=GLOBAL_LAZY, cascade="all, delete-orphan"
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
    renaldiagnoses: DynamicMapped["RenalDiagnosis"] = relationship(
        "RenalDiagnosis", lazy=GLOBAL_LAZY, cascade="all, delete-orphan"
    )
    medications: DynamicMapped["Medication"] = relationship(
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
    documents: DynamicMapped["Document"] = relationship(
        "Document", lazy=GLOBAL_LAZY, cascade="all, delete-orphan"
    )
    encounters: Mapped[List["Encounter"]] = relationship(
        "Encounter", lazy=GLOBAL_LAZY, cascade="all, delete-orphan"
    )
    transplantlists: Mapped[List["TransplantList"]] = relationship(
        "TransplantList", lazy=GLOBAL_LAZY, cascade="all, delete-orphan"
    )
    treatments: DynamicMapped["Treatment"] = relationship(
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
    pvdata = relationship("PVData", uselist=False, cascade="all, delete-orphan")
    pvdelete = relationship("PVDelete", lazy=GLOBAL_LAZY, cascade="all, delete-orphan")

    # Synonyms
    id: Mapped[str] = synonym("pid")
    extract_time: Mapped[datetime.datetime] = synonym("extracttime")
    repository_creation_date: Mapped[datetime.datetime] = synonym(
        "repositorycreationdate"
    )
    repository_update_date: Mapped[datetime.datetime] = synonym("repositoryupdatedate")

    def __str__(self):
        return (
            f"{self.__class__.__name__}({self.pid}) <"
            f"UKRDCID:{self.ukrdcid} CREATED:{self.repository_creation_date}"
            f">"
        )


class Patient(Base):
    __tablename__ = "patient"

    pid = Column(
        String,
        ForeignKey("patientrecord.pid"),
        primary_key=True,
        sqla_info=ColumnInfo(
            label="Patient ID",
            description="Unique identifier for the patient record, referencing patientrecord.pid.",
        ),
    )
    creation_date = Column(
        DateTime,
        nullable=False,
        server_default=text("now()"),
        sqla_info=ColumnInfo(
            label="Creation Date",
            description="Date and time when the record was created.",
        ),
    )
    birthtime = Column(
        DateTime,
        sqla_info=ColumnInfo(
            label="Date of Birth", description="Patient’s date of birth."
        ),
    )
    deathtime = Column(
        DateTime,
        sqla_info=ColumnInfo(
            label="Date of Death",
            description="Patient’s date of death, if applicable.",
        ),
    )
    gender = Column(
        String(2),
        sqla_info=ColumnInfo(
            label="Gender",
            description="Administrative gender of the patient (1, 2, 9).",
        ),
    )
    countryofbirth = Column(
        String(3),
        sqla_info=ColumnInfo(
            label="Country of Birth",
            description="Country code representing the patient’s country of birth from NHS Data Dictionary ISO 3166-1. Use the 3-char alphabetic code.",
        ),
    )
    ethnicgroupcode = Column(
        String(100),
        sqla_info=ColumnInfo(
            label="Ethnic Group Code",
            description="Code representing the patient’s ethnic group from NHS Data Dictionary: https://www.datadictionary.nhs.uk/data_elements/ethnic_category.html",
        ),
    )
    ethnicgroupcodestd = Column(
        String(100),
        sqla_info=ColumnInfo(
            label="Ethnic Group Code Standard",
            description="Coding standard used for the ethnic group code (NHS_DATA_DICTIONARY).",
        ),
    )
    ethnicgroupdesc = Column(
        String(100),
        sqla_info=ColumnInfo(
            label="Ethnic Group Description",
            description="Text description of the patient’s ethnic group.",
        ),
    )
    occupationcode = Column(
        String(100),
        sqla_info=ColumnInfo(
            label="Occupation Code",
            description="Code representing the patient’s occupation from NHS Data Dictionary.",
        ),
    )
    occupationcodestd = Column(
        String(100),
        sqla_info=ColumnInfo(
            label="Occupation Code Standard",
            description="Coding standard used for the occupation code (NHS_DATA_DICTIONARY_EMPLOYMENT_STATUS).",
        ),
    )
    occupationdesc = Column(
        String(100),
        sqla_info=ColumnInfo(
            label="Occupation Description",
            description="Text description of the patient’s occupation.",
        ),
    )
    primarylanguagecode = Column(
        String(100),
        sqla_info=ColumnInfo(
            label="Primary Language Code",
            description="Code representing the patient’s primary language from NHS Data Dictionary.",
        ),
    )
    primarylanguagecodestd = Column(
        String(100),
        sqla_info=ColumnInfo(
            label="Primary Language Code Standard",
            description="Coding standard used for the primary language code (NHS_DATA_DICTIONARY_LANGUAGE_CODE).",
        ),
    )
    primarylanguagedesc = Column(
        String(100),
        sqla_info=ColumnInfo(
            label="Primary Language Description",
            description="Text description of the patient’s primary language.",
        ),
    )
    death = Column(
        Boolean,
        sqla_info=ColumnInfo(
            label="Deceased",
            description="Indicates whether the patient is deceased.",
        ),
    )
    persontocontactname = Column(
        String(100),
        sqla_info=ColumnInfo(
            label="Contact Person Name",
            description="Name of the person to contact about the patient's care. This element should not be submitted without prior discussion with the UKRR.",
        ),
    )
    persontocontact_relationship = Column(
        String(20),
        sqla_info=ColumnInfo(
            label="Contact Person Relationship",
            description="Relationship of the contact person to the patient.",
        ),
    )
    persontocontact_contactnumber = Column(
        String(20),
        sqla_info=ColumnInfo(
            label="Contact Person Number",
            description="Telephone number of the contact person.",
        ),
    )
    persontocontact_contactnumbertype = Column(
        String(20),
        sqla_info=ColumnInfo(
            label="Contact Number Type", description="Type of contact number."
        ),
    )
    persontocontact_contactnumbercomments = Column(
        String(200),
        sqla_info=ColumnInfo(
            label="Contact Number Comments",
            description="Additional comments related to the contact number.",
        ),
    )
    updatedon = Column(
        DateTime,
        sqla_info=ColumnInfo(label="Updated On", description="Last Modified Date"),
    )
    actioncode = Column(
        String(3),
        sqla_info=ColumnInfo(
            label="Action Code",
            description="Code representing the action performed on the patient record.",
        ),
    )
    externalid = Column(
        String(100),
        sqla_info=ColumnInfo(label="External ID", description="Unique Identifier"),
    )
    bloodgroup = Column(
        String(100),
        sqla_info=ColumnInfo(
            label="Blood Group",
            description="Patient’s blood type, current, from NHS Data Dictionary (A, B, AB, 0).",
        ),
    )
    bloodrhesus = Column(
        String(100),
        sqla_info=ColumnInfo(
            label="Blood Rhesus",
            description="Patient’s blood rhesus, current, from NHS Data Dictionary (POS, NEG).",
        ),
    )
    update_date = Column(
        DateTime,
        sqla_info=ColumnInfo(
            label="Update Date",
            description="Date and time when the record was last updated.",
        ),
    )

    # Synonyms
    id: Mapped[str] = synonym("pid")
    birth_time: Mapped[datetime.datetime] = synonym("birthtime")
    death_time: Mapped[datetime.datetime] = synonym("deathtime")
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
    updated_on: Mapped[datetime.datetime] = synonym("updatedon")

    # Relationships

    numbers: Mapped[List["PatientNumber"]] = relationship(
        "PatientNumber",
        backref="patient",
        lazy=GLOBAL_LAZY,
        cascade="all, delete-orphan",
    )
    names: Mapped[List["Name"]] = relationship(
        "Name", lazy=GLOBAL_LAZY, cascade="all, delete-orphan"
    )
    contact_details: DynamicMapped["ContactDetail"] = relationship(
        "ContactDetail", lazy=GLOBAL_LAZY, cascade="all, delete-orphan"
    )
    addresses: Mapped[List["Address"]] = relationship(
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

    pid = Column(String, ForeignKey("patientrecord.pid"), primary_key=True)

    creation_date = Column(DateTime, nullable=False, server_default=text("now()"))
    diagnosistype = Column(String(50))
    diagnosingcliniciancode = Column(String(100))
    diagnosingcliniciancodestd = Column(String(100))
    diagnosingcliniciandesc = Column(String(100))
    diagnosiscode = Column(String(100))
    diagnosiscodestd = Column(String(100))
    diagnosisdesc = Column(String(255))
    comments = Column(Text)
    enteredon = Column(DateTime)
    updatedon = Column(DateTime)
    actioncode = Column(String(3))
    externalid = Column(String(100))
    update_date = Column(DateTime)

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
    entered_on: Mapped[datetime.datetime] = synonym("enteredon")
    updated_on: Mapped[datetime.datetime] = synonym("updatedon")
    action_code: Mapped[str] = synonym("actioncode")
    external_id: Mapped[str] = synonym("externalid")


class FamilyDoctor(Base):
    __tablename__ = "familydoctor"

    id = Column(String, ForeignKey("patient.pid"), primary_key=True)

    creation_date = Column(DateTime, nullable=False, server_default=text("now()"))
    gpname = Column(String(100))

    gpid = Column(String(20), ForeignKey("ukrdc_ods_gp_codes.code"))
    gppracticeid = Column(String(20), ForeignKey("ukrdc_ods_gp_codes.code"))

    addressuse = Column(String(10))
    fromtime = Column(Date)
    totime = Column(Date)
    street = Column(String(100))
    town = Column(String(100))
    county = Column(String(100))
    postcode = Column(String(10))
    countrycode = Column(String(100))
    countrycodestd = Column(String(100))
    countrydesc = Column(String(100))
    contactuse = Column(String(10))
    contactvalue = Column(String(100))
    email = Column(String(100))
    commenttext = Column(String(100))
    update_date = Column(DateTime)

    # Relationships

    gp_info = relationship("GPInfo", foreign_keys=[gpid], uselist=False)
    gp_practice_info = relationship(
        "GPInfo", foreign_keys=[gppracticeid], uselist=False
    )

    def __str__(self):
        return f"{self.__class__.__name__}({self.id}) <{self.gpname} {self.gpid}>"


class GPInfo(Base):
    __tablename__ = "ukrdc_ods_gp_codes"

    code = Column(String(8), primary_key=True)

    creation_date = Column(DateTime, nullable=False, server_default=text("now()"))
    name = Column(String(50))
    address1 = Column(String(35))
    postcode: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    phone = Column(String(12))
    type = Column(Enum("GP", "PRACTICE", name="gp_type"))
    update_date = Column(DateTime)

    # Synonyms

    gpname: Mapped[str] = synonym("name")
    street: Mapped[str] = synonym("address1")
    contactvalue: Mapped[str] = synonym("phone")


class SocialHistory(Base):
    __tablename__ = "socialhistory"

    id = Column(String, primary_key=True)
    pid = Column(String, ForeignKey("patientrecord.pid"))

    creation_date = Column(DateTime, nullable=False, server_default=text("now()"))
    idx = Column(Integer)
    socialhabitcode = Column(String(100))
    socialhabitcodestd = Column(String(100))
    socialhabitdesc = Column(String(100))
    updatedon = Column(DateTime)
    actioncode = Column(String(3))
    externalid = Column(String(100))
    update_date = Column(DateTime)


class FamilyHistory(Base):
    __tablename__ = "familyhistory"

    id = Column(String, primary_key=True)
    pid = Column(String, ForeignKey("patientrecord.pid"))

    creation_date = Column(DateTime, nullable=False, server_default=text("now()"))
    idx = Column(Integer)
    familymembercode = Column(String(100))
    familymembercodestd = Column(String(100))
    familymemberdesc = Column(String(100))
    diagnosiscode = Column(String(100))
    diagnosiscodestd = Column(String(100))
    diagnosisdesc = Column(String(100))
    notetext = Column(String(100))
    enteredatcode = Column(String(100))
    enteredatcodestd = Column(String(100))
    enteredatdesc = Column(String(100))
    fromtime = Column(DateTime)
    totime = Column(DateTime)
    updatedon = Column(DateTime)
    actioncode = Column(String(3))
    externalid = Column(String(100))
    update_date = Column(DateTime)


class Observation(Base):
    __tablename__ = "observation"

    id = Column(
        String,
        primary_key=True,
        sqla_info=ColumnInfo(
            label="Observation ID",
            description="Unique identifier for the observation record.",
        ),
    )
    pid = Column(
        String,
        ForeignKey("patientrecord.pid"),
        sqla_info=ColumnInfo(
            label="Patient ID",
            description="Identifier of the patient associated with this observation.",
        ),
    )
    creation_date = Column(
        DateTime,
        nullable=False,
        server_default=text("now()"),
        sqla_info=ColumnInfo(
            label="Creation Date",
            description="Date and time when the observation record was created.",
        ),
    )
    idx = Column(
        Integer,
        sqla_info=ColumnInfo(label="Index", description="Index for the observation."),
    )
    observationtime = Column(
        DateTime,
        sqla_info=ColumnInfo(
            label="Observation Time",
            description="Date and time when the observation was made.",
        ),
    )
    observationcode = Column(
        String(100),
        sqla_info=ColumnInfo(
            label="Observation Code",
            description="Code for the observation - UKRR, PV or SNOMED Coding Standards.",
        ),
    )
    observationcodestd = Column(
        String(100),
        sqla_info=ColumnInfo(
            label="Observation Code Standard",
            description="Coding standard used for the observation code (UKRR, PV, SNOMED).",
        ),
    )
    observationdesc = Column(
        String(100),
        sqla_info=ColumnInfo(
            label="Observation Description",
            description="Text description of the observation recorded.",
        ),
    )
    observationvalue = Column(
        String(100),
        sqla_info=ColumnInfo(
            label="Observation Value",
            description="The measured or observed value.",
        ),
    )
    observationunits = Column(
        String(100),
        sqla_info=ColumnInfo(
            label="Observation Units",
            description="Units of measurement for the observation value.",
        ),
    )
    prepost = Column(
        String(4),
        sqla_info=ColumnInfo(
            label="Pre/Post Indicator",
            description="Indicates whether the observation was made PRE or POST dialysis (PRE, POST, UNK, NA).",
        ),
    )
    commenttext = Column(
        String(100),
        sqla_info=ColumnInfo(
            label="Comment Text",
            description="Free-text comment associated with the observation.",
        ),
    )
    cliniciancode = Column(
        String(100),
        sqla_info=ColumnInfo(
            label="Clinician Code",
            description="Code identifying the clinician associated with this observation.",
        ),
    )
    cliniciancodestd = Column(
        String(100),
        sqla_info=ColumnInfo(
            label="Clinician Code Standard",
            description="Coding standard used for the clinician code.",
        ),
    )
    cliniciandesc = Column(
        String(100),
        sqla_info=ColumnInfo(
            label="Clinician Description",
            description="Name or description of the clinician.",
        ),
    )
    enteredatcode = Column(
        String(100),
        sqla_info=ColumnInfo(
            label="Entered At Code",
            description="Code for the location where the observation was entered.",
        ),
    )
    enteredatcodestd = Column(
        String(100),
        sqla_info=ColumnInfo(
            label="Entered At Code Standard",
            description="Coding standard used for the entered-at code.",
        ),
    )
    enteredatdesc = Column(
        String(100),
        sqla_info=ColumnInfo(
            label="Entered At Description",
            description="Text description of the location where the observation was entered.",
        ),
    )
    enteringorganizationcode = Column(
        String(100),
        sqla_info=ColumnInfo(
            label="Entering Organization Code",
            description="Code identifying the organization entering the observation.",
        ),
    )
    enteringorganizationcodestd = Column(
        String(100),
        sqla_info=ColumnInfo(
            label="Entering Organization Code Standard",
            description="Coding standard used for the entering organization code.",
        ),
    )
    enteringorganizationdesc = Column(
        String(100),
        sqla_info=ColumnInfo(
            label="Entering Organization Description",
            description="Text description of the organization entering the observation.",
        ),
    )
    updatedon = Column(
        DateTime,
        sqla_info=ColumnInfo(label="Updated On", description="Last Modified Date"),
    )
    actioncode = Column(
        String(3),
        sqla_info=ColumnInfo(
            label="Action Code",
            description="Code representing the action performed on the observation record.",
        ),
    )
    externalid = Column(
        String(100),
        sqla_info=ColumnInfo(label="External ID", description="Unique Identifier"),
    )
    update_date = Column(
        DateTime,
        sqla_info=ColumnInfo(
            label="Update Date",
            description="Date and time when the record was last updated.",
        ),
    )

    # Synonyms

    observation_time: Mapped[datetime.datetime] = synonym("observationtime")
    observation_code: Mapped[str] = synonym("observationcode")
    observation_code_std: Mapped[str] = synonym("observationcodestd")
    observation_desc: Mapped[str] = synonym("observationdesc")
    observation_value: Mapped[str] = synonym("observationvalue")
    observation_units: Mapped[str] = synonym("observationunits")
    comment_text: Mapped[str] = synonym("commenttext")
    clinician_code: Mapped[str] = synonym("cliniciancode")
    clinician_code_std: Mapped[str] = synonym("cliniciancodestd")
    clinician_desc: Mapped[str] = synonym("cliniciandesc")
    entered_at: Mapped[str] = synonym("enteredatcode")
    entered_at_description: Mapped[str] = synonym("enteredatdesc")
    entering_organization_code: Mapped[str] = synonym("enteringorganizationcode")
    entering_organization_description: Mapped[str] = synonym("enteringorganizationdesc")
    updated_on: Mapped[datetime.datetime] = synonym("updatedon")
    action_code: Mapped[str] = synonym("actioncode")
    external_id: Mapped[str] = synonym("externalid")
    pre_post: Mapped[str] = synonym("prepost")

    def __str__(self):
        return (
            f"{self.__class__.__name__}({self.pid}) <"
            f"{self.observation_code} {self.observation_value}"
            f">"
        )


class OptOut(Base):
    __tablename__ = "optout"

    id = Column(String, primary_key=True)
    pid = Column(String, ForeignKey("patientrecord.pid"))

    creation_date = Column(DateTime, nullable=False, server_default=text("now()"))
    idx = Column(Integer)
    programname = Column(String(100))
    programdescription = Column(String(100))
    enteredbycode = Column(String(100))
    enteredbycodestd = Column(String(100))
    enteredbydesc = Column(String(100))
    enteredatcode = Column(String(100))
    enteredatcodestd = Column(String(100))
    enteredatdesc = Column(String(100))
    fromtime = Column(Date)
    totime = Column(Date)
    updatedon = Column(DateTime)
    actioncode = Column(String(3))
    externalid = Column(String(100))
    update_date = Column(DateTime)

    # Synonyms

    program_name: Mapped[str] = synonym("programname")
    program_description: Mapped[str] = synonym("programdescription")
    entered_by_code: Mapped[str] = synonym("enteredbycode")
    entered_by_code_std: Mapped[str] = synonym("enteredbycodestd")
    entered_by_desc: Mapped[str] = synonym("enteredbydesc")
    entered_at_code: Mapped[str] = synonym("enteredatcode")
    entered_at_code_std: Mapped[str] = synonym("enteredatcodestd")
    entered_at_desc: Mapped[str] = synonym("enteredatdesc")
    from_time: Mapped[datetime.date] = synonym("fromtime")
    to_time: Mapped[datetime.date] = synonym("totime")
    updated_on: Mapped[datetime.datetime] = synonym("updatedon")
    action_code: Mapped[str] = synonym("actioncode")
    external_id: Mapped[str] = synonym("externalid")


class Allergy(Base):
    __tablename__ = "allergy"

    id = Column(String, primary_key=True)
    pid = Column(String, ForeignKey("patientrecord.pid"))

    creation_date = Column(DateTime, nullable=False, server_default=text("now()"))
    idx = Column(Integer)
    allergycode = Column(String(100))
    allergycodestd = Column(String(100))
    allergydesc = Column(String(100))
    allergycategorycode = Column(String(100))
    allergycategorycodestd = Column(String(100))
    allergycategorydesc = Column(String(100))
    severitycode = Column(String(100))
    severitycodestd = Column(String(100))
    severitydesc = Column(String(100))
    cliniciancode = Column(String(100))
    cliniciancodestd = Column(String(100))
    cliniciandesc = Column(String(100))
    discoverytime = Column(DateTime)
    confirmedtime = Column(DateTime)
    commenttext = Column(String(500))
    inactivetime = Column(DateTime)
    freetextallergy = Column(String(500))
    qualifyingdetails = Column(String(500))
    updatedon = Column(DateTime)
    actioncode = Column(String(3))
    externalid = Column(String(100))
    update_date = Column(DateTime)


class Diagnosis(Base):
    __tablename__ = "diagnosis"

    id = Column(String, primary_key=True)
    pid = Column(String, ForeignKey("patientrecord.pid"))

    creation_date = Column(DateTime, nullable=False, server_default=text("now()"))
    idx = Column(Integer)
    diagnosistype = Column(String(50))
    diagnosingcliniciancode = Column(String(100))
    diagnosingcliniciancodestd = Column(String(100))
    diagnosingcliniciandesc = Column(String(100))
    diagnosiscode = Column(String(100))
    diagnosiscodestd = Column(String(100))
    diagnosisdesc = Column(String(255))
    comments: Mapped[Optional[str]] = mapped_column(Text)
    identificationtime = Column(DateTime)
    onsettime = Column(DateTime)
    enteredon = Column(DateTime)
    updatedon = Column(DateTime)
    actioncode = Column(String(3))
    externalid = Column(String(100))
    update_date = Column(DateTime)
    enteredatcode = Column(String(100))
    enteredatcodestd = Column(String(100))
    enteredatdesc = Column(String(100))
    encounternumber = Column(String(100))
    verificationstatus = Column(String(100))

    # Synonyms

    diagnosis_code: Mapped[str] = synonym("diagnosiscode")
    diagnosis_code_std: Mapped[str] = synonym("diagnosiscodestd")
    diagnosis_desc: Mapped[str] = synonym("diagnosisdesc")
    identification_time: Mapped[datetime.datetime] = synonym("identificationtime")
    onset_time: Mapped[datetime.datetime] = synonym("onsettime")


class RenalDiagnosis(Base):
    __tablename__ = "renaldiagnosis"

    pid = Column(String, ForeignKey("patientrecord.pid"), primary_key=True)

    creation_date = Column(DateTime, nullable=False, server_default=text("now()"))
    diagnosistype = Column(String(50))
    diagnosiscode = Column("diagnosiscode", String)
    diagnosiscodestd = Column("diagnosiscodestd", String)
    diagnosisdesc = Column("diagnosisdesc", String)
    diagnosingcliniciancode = Column(String(100))
    diagnosingcliniciancodestd = Column(String(100))
    diagnosingcliniciandesc = Column(String(100))
    comments = Column(String)
    identificationtime = Column("identificationtime", DateTime)
    onsettime = Column(DateTime)
    enteredon = Column(DateTime)
    updatedon = Column(DateTime)
    actioncode = Column(String(3))
    externalid = Column(String(100))
    update_date = Column(DateTime)

    # Synonyms
    id: Mapped[str] = synonym("pid")  # see comment on cause of death
    diagnosis_code: Mapped[str] = synonym("diagnosiscode")
    diagnosis_code_std: Mapped[str] = synonym("diagnosiscodestd")
    diagnosis_desc: Mapped[str] = synonym("diagnosisdesc")
    identification_time: Mapped[datetime.datetime] = synonym("identificationtime")


class DialysisSession(Base):
    __tablename__ = "dialysissession"

    id = Column(String, primary_key=True)
    pid = Column(String, ForeignKey("patientrecord.pid"))

    creation_date = Column(DateTime, nullable=False, server_default=text("now()"))
    idx = Column(Integer)
    proceduretypecode = Column(String(100))
    proceduretypecodestd = Column(String(100))
    proceduretypedesc = Column(String(100))
    cliniciancode = Column(String(100))
    cliniciancodestd = Column(String(100))
    cliniciandesc = Column(String(100))
    proceduretime = Column(DateTime)
    enteredbycode = Column(String(100))
    enteredbycodestd = Column(String(100))
    enteredbydesc = Column(String(100))
    enteredatcode = Column(String(100))
    enteredatcodestd = Column(String(100))
    enteredatdesc = Column(String(100))
    qhd19 = Column(String(255))
    qhd20 = Column(String(255))
    qhd21 = Column(String(255))
    qhd22 = Column(String(255))
    qhd30 = Column(String(255))
    qhd31 = Column(String(255))
    qhd32 = Column(String(255))
    qhd33 = Column(String(255))

    updatedon = Column(DateTime)
    actioncode = Column(String(3))
    externalid = Column(String(100))
    update_date = Column(DateTime)

    # Synonyms

    procedure_type_code: Mapped[str] = synonym("proceduretypecode")
    procedure_type_code_std: Mapped[str] = synonym("proceduretypecodestd")
    procedure_type_desc: Mapped[str] = synonym("proceduretypedesc")
    procedure_time: Mapped[datetime.datetime] = synonym("proceduretime")


class Transplant(Base):
    __tablename__ = "transplant"

    id = Column(String, primary_key=True)
    pid = Column(String, ForeignKey("patientrecord.pid"))

    creation_date = Column(DateTime, nullable=False, server_default=text("now()"))
    idx = Column(Integer)

    proceduretypecode = Column(String(100))
    proceduretypecodestd = Column(String(100))
    proceduretypedesc = Column(String(100))

    cliniciancode = Column(String(100))
    cliniciancodestd = Column(String(100))
    cliniciandesc = Column(String(100))

    proceduretime = Column(DateTime)

    enteredbycode = Column(String(100))
    enteredbycodestd = Column(String(100))
    enteredbydesc = Column(String(100))

    enteredatcode = Column(String(100))
    enteredatcodestd = Column(String(100))
    enteredatdesc = Column(String(100))

    updatedon = Column(DateTime)
    actioncode = Column(String(3))
    externalid = Column(String(100))

    tra64 = Column(DateTime)
    tra65 = Column(String(255))
    tra66 = Column(String(255))
    tra69 = Column(DateTime)
    tra76 = Column(String(255))
    tra77 = Column(String(255))
    tra78 = Column(String(255))
    tra79 = Column(String(255))
    tra80 = Column(String(255))
    tra8a = Column(String(255))
    tra81 = Column(String(255))
    tra82 = Column(String(255))
    tra83 = Column(String(255))
    tra84 = Column(String(255))
    tra85 = Column(String(255))
    tra86 = Column(String(255))
    tra87 = Column(String(255))
    tra88 = Column(String(255))
    tra89 = Column(String(255))
    tra90 = Column(String(255))
    tra91 = Column(String(255))
    tra92 = Column(String(255))
    tra93 = Column(String(255))
    tra94 = Column(String(255))
    tra95 = Column(String(255))
    tra96 = Column(String(255))
    tra97 = Column(String(255))
    tra98 = Column(String(255))

    update_date = Column(DateTime)

    # Synonyms

    procedure_type_code: Mapped[str] = synonym("proceduretypecode")
    procedure_type_code_std: Mapped[str] = synonym("proceduretypecodestd")
    procedure_type_desc: Mapped[str] = synonym("proceduretypedesc")
    procedure_time: Mapped[datetime.datetime] = synonym("proceduretime")


class VascularAccess(Base):
    __tablename__ = "vascularaccess"

    id = Column(String, primary_key=True)
    pid = Column(String, ForeignKey("patientrecord.pid"))
    idx = Column(Integer)

    creation_date = Column(DateTime, nullable=False, server_default=text("now()"))
    proceduretypecode = Column(String(100))
    proceduretypecodestd = Column(String(100))
    proceduretypedesc = Column(String(100))
    cliniciancode = Column(String(100))
    cliniciancodestd = Column(String(100))
    cliniciandesc = Column(String(100))
    proceduretime = Column(DateTime)
    enteredbycode = Column(String(100))
    enteredbycodestd = Column(String(100))
    enteredbydesc = Column(String(100))
    enteredatcode = Column(String(100))
    enteredatcodestd = Column(String(100))
    enteredatdesc = Column(String(100))
    updatedon = Column(DateTime)
    actioncode = Column(String(3))
    externalid = Column(String(100))

    acc19 = Column(String(255))
    acc20 = Column(String(255))
    acc21 = Column(String(255))
    acc22 = Column(String(255))
    acc30 = Column(String(255))
    acc40 = Column(String(255))

    update_date = Column(DateTime)


class Procedure(Base):
    __tablename__ = "procedure"

    id = Column(String, primary_key=True)
    pid = Column(String, ForeignKey("patientrecord.pid"))

    creation_date = Column(DateTime, nullable=False, server_default=text("now()"))
    idx = Column(Integer)
    proceduretypecode = Column(String(100))
    proceduretypecodestd = Column(String(100))
    proceduretypedesc = Column(String(100))
    cliniciancode = Column(String(100))
    cliniciancodestd = Column(String(100))
    cliniciandesc = Column(String(100))
    proceduretime = Column(DateTime)
    enteredbycode = Column(String(100))
    enteredbycodestd = Column(String(100))
    enteredbydesc = Column(String(100))
    enteredatcode = Column(String(100))
    enteredatcodestd = Column(String(100))
    enteredatdesc = Column(String(100))
    updatedon = Column(DateTime)
    actioncode = Column(String(3))
    externalid = Column(String(100))
    update_date = Column(DateTime)


class Encounter(Base):
    __tablename__ = "encounter"

    id = Column(String, primary_key=True)
    pid = Column(String, ForeignKey("patientrecord.pid"))

    creation_date = Column(DateTime, nullable=False, server_default=text("now()"))
    idx = Column(Integer)
    encounternumber = Column(String(100))
    encountertype = Column(String(100))
    fromtime = Column(DateTime)
    totime = Column(DateTime)
    admittingcliniciancode = Column(String(100))
    admittingcliniciancodestd = Column(String(100))
    admittingcliniciandesc = Column(String(100))
    admitreasoncode = Column(String(100))
    admitreasoncodestd = Column(String(100))
    admitreasondesc = Column(String(100))
    admissionsourcecode = Column(String(100))
    admissionsourcecodestd = Column(String(100))
    admissionsourcedesc = Column(String(100))
    dischargereasoncode = Column(String(100))
    dischargereasoncodestd = Column(String(100))
    dischargereasondesc = Column(String(100))
    dischargelocationcode = Column(String(100))
    dischargelocationcodestd = Column(String(100))
    dischargelocationdesc = Column(String(100))
    healthcarefacilitycode = Column(String(100))
    healthcarefacilitycodestd = Column(String(100))
    healthcarefacilitydesc = Column(String(100))
    enteredatcode = Column(String(100))
    enteredatcodestd = Column(String(100))
    enteredatdesc = Column(String(100))
    visitdescription = Column(String(100))
    updatedon = Column(DateTime)
    actioncode = Column(String(3))
    externalid = Column(String(100))
    update_date = Column(DateTime)

    # Synonyms

    from_time: Mapped[datetime.datetime] = synonym("fromtime")
    to_time: Mapped[datetime.datetime] = synonym("totime")


class ProgramMembership(Base):
    __tablename__ = "programmembership"

    id = Column(String, primary_key=True)
    pid = Column(String, ForeignKey("patientrecord.pid"))

    creation_date = Column(DateTime, nullable=False, server_default=text("now()"))
    programname = Column(String(100))
    programdescription = Column(String(100))
    enteredbycode = Column(String(100))
    enteredbycodestd = Column(String(100))
    enteredbydesc = Column(String(100))
    enteredatcode = Column(String(100))
    enteredatcodestd = Column(String(100))
    enteredatdesc = Column(String(100))
    fromtime = Column(Date)
    totime = Column(Date)
    updatedon = Column(DateTime)
    actioncode = Column(String(3))
    externalid = Column(String(100))
    update_date = Column(DateTime)

    # Synonyms

    program_name: Mapped[str] = synonym("programname")
    from_time: Mapped[datetime.date] = synonym("fromtime")
    to_time: Mapped[datetime.date] = synonym("totime")

    def __str__(self):
        return (
            f"{self.__class__.__name__}({self.pid}) <"
            f"{self.program_name} {self.from_time}"
            f">"
        )


class ClinicalRelationship(Base):
    __tablename__ = "clinicalrelationship"

    id = Column(String, primary_key=True)
    pid = Column(String, ForeignKey("patientrecord.pid"))

    creation_date = Column(DateTime, nullable=False, server_default=text("now()"))
    idx = Column(Integer)
    cliniciancode = Column(String(100))
    cliniciancodestd = Column(String(100))
    cliniciandesc = Column(String(100))
    facilitycode = Column(String(100))
    facilitycodestd = Column(String(100))
    facilitydesc = Column(String(100))
    fromtime = Column(Date)
    totime = Column(Date)
    updatedon = Column(DateTime)
    actioncode = Column(String(3))
    externalid = Column(String(100))
    update_date = Column(DateTime)


class Name(Base):
    __tablename__ = "name"

    id = Column(String, primary_key=True)
    pid = Column(String, ForeignKey("patient.pid"))

    creation_date = Column(DateTime, nullable=False, server_default=text("now()"))
    idx = Column(Integer)
    nameuse = Column(String(10))
    prefix = Column(String(10))
    family = Column(String(60))
    given = Column(String(60))
    othergivennames = Column(String(60))
    suffix = Column(String(10))
    update_date = Column(DateTime)

    def __str__(self):
        return f"{self.__class__.__name__}({self.pid}) <{self.given} {self.family}>"


class PatientNumber(Base):
    __tablename__ = "patientnumber"

    id = Column(String, primary_key=True)
    pid = Column(String, ForeignKey("patient.pid"))

    creation_date = Column(DateTime, nullable=False, server_default=text("now()"))
    idx = Column(Integer)
    patientid = Column(String(50), index=True)
    numbertype = Column(String(3))
    organization = Column(String(50))
    updatedon = Column(DateTime)
    actioncode = Column(String(3))
    externalid = Column(String(100))
    update_date = Column(DateTime)

    def __str__(self):
        return (
            f"{self.__class__.__name__}({self.pid}) <"
            f"{self.organization}:{self.numbertype}:{self.patientid}"
            ">"
        )


class Address(Base):
    __tablename__ = "address"

    id = Column(String, primary_key=True)
    pid = Column(String, ForeignKey("patient.pid"))

    creation_date = Column(DateTime, nullable=False, server_default=text("now()"))
    idx = Column(Integer)
    addressuse = Column(String(10))
    fromtime = Column(Date)
    totime = Column(Date)
    street = Column(String(100))
    town = Column(String(100))
    county = Column(String(100))
    postcode: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    countrycode = Column(String(100))
    countrycodestd = Column(String(100))
    countrydesc = Column(String(100))
    update_date = Column(DateTime)

    # Synonyms

    from_time: Mapped[datetime.date] = synonym("fromtime")
    to_time: Mapped[datetime.date] = synonym("totime")
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

    id = Column(String, primary_key=True)
    pid = Column(String, ForeignKey("patient.pid"))

    creation_date = Column(DateTime, nullable=False, server_default=text("now()"))
    idx = Column(Integer)
    contactuse = Column(String(10))
    contactvalue = Column(String(100))
    commenttext = Column(String(100))
    updatedon = Column(DateTime)
    actioncode = Column(String(3))
    externalid = Column(String(100))
    update_date = Column(DateTime)

    # Synonyms

    use: Mapped[str] = synonym("contactuse")
    value: Mapped[str] = synonym("contactvalue")

    def __str__(self):
        return f"{self.__class__.__name__}({self.pid}) <{self.use}:{self.value}>"


class Medication(Base):
    __tablename__ = "medication"

    id = Column(String, primary_key=True)
    pid = Column(String, ForeignKey("patientrecord.pid"))

    creation_date = Column(DateTime, nullable=False, server_default=text("now()"))

    idx = Column(Integer)
    repositoryupdatedate = Column(DateTime, nullable=False)
    prescriptionnumber = Column(String(100))
    fromtime = Column(DateTime)
    totime = Column(DateTime)

    orderedbycode = Column(String(100))
    orderedbycodestd = Column(String(100))
    orderedbydesc = Column(String(100))

    enteringorganizationcode = Column(String(100))
    enteringorganizationcodestd = Column(String(100))
    enteringorganizationdesc = Column(String(100))

    routecode = Column(String(10))
    routecodestd = Column(String(100))
    routedesc = Column(String(100))

    drugproductidcode = Column(String(100))
    drugproductidcodestd = Column(String(100))
    drugproductiddesc = Column(String(100))

    drugproductgeneric = Column(String(255))
    drugproductlabelname = Column(String(255))

    drugproductformcode = Column(String(100))
    drugproductformcodestd = Column(String(100))
    drugproductformdesc = Column(String(100))

    drugproductstrengthunitscode = Column(String(100))
    drugproductstrengthunitscodestd = Column(String(100))
    drugproductstrengthunitsdesc = Column(String(100))

    frequency = Column(String(255))
    commenttext = Column(String(1000))
    dosequantity = Column(Numeric(19, 2))

    doseuomcode = Column(String(100))
    doseuomcodestd = Column(String(100))
    doseuomdesc = Column(String(100))

    indication = Column(String(100))
    updatedon = Column(DateTime)
    actioncode = Column(String(3))
    externalid = Column(String(100))
    update_date = Column(DateTime)
    encounternumber = Column(String(100))

    # Synonyms

    repository_update_date: Mapped[datetime.datetime] = synonym("repositoryupdatedate")
    from_time: Mapped[datetime.datetime] = synonym("fromtime")
    to_time: Mapped[datetime.datetime] = synonym("totime")
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
    updated_on: Mapped[datetime.datetime] = synonym("updatedon")
    external_id: Mapped[str] = synonym("externalid")

    def __str__(self):
        return f"{self.__class__.__name__}({self.pid})"


class Survey(Base):
    __tablename__ = "survey"

    id = Column(String, primary_key=True)
    pid = Column(String, ForeignKey("patientrecord.pid"))

    creation_date = Column(DateTime, nullable=False, server_default=text("now()"))
    surveytime = Column(DateTime, nullable=False)
    surveytypecode = Column(String(100))
    surveytypecodestd = Column(String(100))
    surveytypedesc = Column(String(100))
    typeoftreatment = Column(String(100))
    hdlocation = Column(String(100))
    template = Column(String(100))
    enteredbycode = Column(String(100))
    enteredbycodestd = Column(String(100))
    enteredbydesc = Column(String(100))
    enteredatcode = Column(String(100))
    enteredatcodestd = Column(String(100))
    enteredatdesc = Column(String(100))
    updatedon = Column(DateTime)
    actioncode = Column(String(3))
    externalid = Column(String(100))
    update_date = Column(DateTime)

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

    id = Column(String, primary_key=True)

    surveyid = Column(String, ForeignKey("survey.id"))
    creation_date = Column(DateTime, nullable=False, server_default=text("now()"))
    idx = Column(Integer)
    questiontypecode = Column(String(100))
    questiontypecodestd = Column(String(100))
    questiontypedesc = Column(String(100))
    response = Column(String(100))
    questiontext = Column(String(100))
    update_date = Column(DateTime)


class Score(Base):
    __tablename__ = "score"

    id = Column(String, primary_key=True)

    surveyid = Column(String, ForeignKey("survey.id"))
    creation_date = Column(DateTime, nullable=False, server_default=text("now()"))
    idx = Column(Integer)
    scorevalue = Column(String(100))
    scoretypecode = Column(String(100))
    scoretypecodestd = Column(String(100))
    scoretypedesc = Column(String(100))
    update_date = Column(DateTime)

    # Synonyms

    value: Mapped[str] = synonym("scorevalue")


class Level(Base):
    __tablename__ = "level"

    id = Column(String, primary_key=True)

    surveyid = Column(String, ForeignKey("survey.id"))
    creation_date = Column(DateTime, nullable=False, server_default=text("now()"))
    idx = Column(Integer)
    levelvalue = Column(String(100))
    leveltypecode = Column(String(100))
    leveltypecodestd = Column(String(100))
    leveltypedesc = Column(String(100))
    update_date = Column(DateTime)

    # Synonyms

    value: Mapped[str] = synonym("levelvalue")


class Document(Base):
    __tablename__ = "document"

    id = Column(String, primary_key=True)
    pid = Column(String, ForeignKey("patientrecord.pid"))

    repositoryupdatedate = Column(DateTime, nullable=False)
    creation_date = Column(DateTime, nullable=False, server_default=text("now()"))
    idx = Column(Integer)
    documenttime = Column(DateTime)
    notetext = Column(Text)
    documenttypecode = Column(String(100))
    documenttypecodestd = Column(String(100))
    documenttypedesc = Column(String(100))
    cliniciancode = Column(String(100))
    cliniciancodestd = Column(String(100))
    cliniciandesc = Column(String(100))
    documentname = Column(String(100))
    statuscode = Column(String(100))
    statuscodestd = Column(String(100))
    statusdesc = Column(String(100))
    enteredbycode = Column(String(100))
    enteredbycodestd = Column(String(100))
    enteredbydesc = Column(String(100))
    enteredatcode = Column(String(100))
    enteredatcodestd = Column(String(100))
    enteredatdesc = Column(String(100))
    filetype = Column(String(100))
    filename = Column(String(100))
    stream = Column(LargeBinary)
    documenturl = Column(String(100))
    updatedon = Column(DateTime)
    actioncode = Column(String(3))
    externalid = Column(String(100))
    update_date = Column(DateTime)

    # Synonyms

    repository_update_date = synonym("repositoryupdatedate")


class LabOrder(Base):
    __tablename__ = "laborder"

    id = Column(String, primary_key=True)
    pid = Column(String, ForeignKey("patientrecord.pid"))

    creation_date = Column(
        DateTime, nullable=False, index=True, server_default=text("now()")
    )
    placerid = Column(String(100))
    fillerid = Column(String(100))
    receivinglocationcode = Column(String(100))
    receivinglocationcodestd = Column(String(100))
    receivinglocationdesc = Column(String(100))
    orderedbycode = Column(String(100))
    orderedbycodestd = Column(String(100))
    orderedbydesc = Column(String(100))
    orderitemcode = Column(String(100))
    orderitemcodestd = Column(String(100))
    orderitemdesc = Column(String(100))
    prioritycode = Column(String(100))
    prioritycodestd = Column(String(100))
    prioritydesc = Column(String(100))
    status = Column(String(100))
    ordercategorycode = Column(String(100))
    ordercategorycodestd = Column(String(100))
    ordercategorydesc = Column(String(100))
    specimensource = Column(String(50))
    specimenreceivedtime = Column(DateTime)
    specimencollectedtime = Column(DateTime)
    duration = Column(String(50))
    patientclasscode = Column(String(100))
    patientclasscodestd = Column(String(100))
    patientclassdesc = Column(String(100))
    enteredon = Column(DateTime)
    enteredatcode = Column(String(100))
    enteredatcodestd = Column(String(100))
    enteredatdesc = Column(String(100))
    enteringorganizationcode = Column(String(100))
    enteringorganizationcodestd = Column(String(100))
    enteringorganizationdesc = Column(String(100))
    updatedon = Column(DateTime)
    actioncode = Column(String(3))
    externalid = Column(String(100))
    update_date = Column(DateTime, index=True)
    repository_update_date = Column(DateTime, index=True)

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
    specimen_collected_time: Mapped[datetime.datetime] = synonym(
        "specimencollectedtime"
    )
    specimen_received_time: Mapped[datetime.datetime] = synonym("specimenreceivedtime")
    priority: Mapped[str] = synonym("prioritycode")
    priority_description: Mapped[str] = synonym("prioritydesc")
    priority_code_std: Mapped[str] = synonym("prioritycodestd")
    specimen_source: Mapped[str] = synonym("specimensource")
    patient_class: Mapped[str] = synonym("patientclasscode")
    patient_class_description: Mapped[str] = synonym("patientclassdesc")
    patient_class_code_std: Mapped[str] = synonym("patientclasscodestd")
    entered_on: Mapped[datetime.datetime] = synonym("enteredon")
    entered_at: Mapped[str] = synonym("enteredatcode")
    entered_at_description: Mapped[str] = synonym("enteredatdesc")
    external_id: Mapped[str] = synonym("externalid")
    entering_organization_code: Mapped[str] = synonym("enteringorganizationcode")
    entering_organization_description: Mapped[str] = synonym("enteringorganizationdesc")
    entering_organization_code_std: Mapped[str] = synonym("enteringorganizationcodestd")

    # Relationships

    result_items: Mapped[List["ResultItem"]] = relationship(
        "ResultItem",
        lazy=GLOBAL_LAZY,
        back_populates="order",
        cascade="all, delete-orphan",
    )


class ResultItem(Base):
    __tablename__ = "resultitem"

    id = Column(
        String,
        primary_key=True,
        sqla_info=ColumnInfo(
            label="Result Item ID",
            description="Unique identifier for the result item.",
        ),
    )
    orderid = Column(
        "orderid",
        String,
        ForeignKey("laborder.id"),
        sqla_info=ColumnInfo(
            label="Order ID",
            description="Identifier of the related laboratory order.",
        ),
    )
    creation_date = Column(
        DateTime,
        nullable=False,
        server_default=text("now()"),
        sqla_info=ColumnInfo(
            label="Creation Date",
            description="Date and time when the result item was created.",
        ),
    )
    resulttype = Column(
        String(2),
        sqla_info=ColumnInfo(label="Result Type", description="Type of result."),
    )
    serviceidcode = Column(
        String(100),
        sqla_info=ColumnInfo(
            label="Service ID Code",
            description="Test code identifying the laboratory service or test performed.",
        ),
    )
    serviceidcodestd = Column(
        String(100),
        sqla_info=ColumnInfo(
            label="Service ID Code Standard",
            description="Coding standard used for the service ID (SNOMED, LOINC, UKRR, PV, LOCAL).",
        ),
    )
    serviceiddesc = Column(
        String(100),
        sqla_info=ColumnInfo(
            label="Service ID Description",
            description="Text description of the laboratory service or test performed.",
        ),
    )
    subid = Column(
        String(50), sqla_info=ColumnInfo(label="Sub ID", description="Sub-Test Id.")
    )
    resultvalue = Column(
        String(20),
        sqla_info=ColumnInfo(
            label="Result Value",
            description="The measured or observed value.",
        ),
    )
    resultvalueunits = Column(
        String(30),
        sqla_info=ColumnInfo(
            label="Result Value Units",
            description="Units of measurement for the result value.",
        ),
    )
    referencerange = Column(
        String(30),
        sqla_info=ColumnInfo(
            label="Reference Range",
            description="Reference range for the test result.",
        ),
    )
    interpretationcodes = Column(
        String(50),
        sqla_info=ColumnInfo(
            label="Interpretation Codes",
            description="Code(s) indicating interpretation of the result (POS, NEG, UNK).",
        ),
    )
    status = Column(
        String(5),
        sqla_info=ColumnInfo(
            label="Result Status",
            description="Status of the result (F, P, D).",
        ),
    )
    observationtime = Column(
        DateTime,
        sqla_info=ColumnInfo(
            label="Observation Time",
            description="Date and time when the observation or measurement was made.",
        ),
    )
    commenttext = Column(
        String(1000),
        sqla_info=ColumnInfo(
            label="Comment Text",
            description="Free-text comment associated with the result.",
        ),
    )
    referencecomment = Column(
        String(1000),
        sqla_info=ColumnInfo(
            label="Reference Comment",
            description="Reference comment provided with the result.",
        ),
    )
    prepost = Column(
        String(4),
        sqla_info=ColumnInfo(
            label="Pre/Post Indicator",
            description="Indicates whether the sample was taken PRE or POST dialysis (PRE, POST, UNK, NA).",
        ),
    )
    enteredon = Column(
        DateTime,
        sqla_info=ColumnInfo(
            label="Entered On",
            description="Date and time when the result was entered into the system.",
        ),
    )
    updatedon = Column(
        DateTime,
        sqla_info=ColumnInfo(label="Updated On", description="Last Modified Date"),
    )
    actioncode = Column(
        String(3),
        sqla_info=ColumnInfo(
            label="Action Code",
            description="Code representing the action performed on the result record.",
        ),
    )
    externalid = Column(
        String(100),
        sqla_info=ColumnInfo(label="External ID", description="Unique Identifier"),
    )
    update_date = Column(
        DateTime,
        sqla_info=ColumnInfo(
            label="Update Date",
            description="Date and time when the record was last updated.",
        ),
    )

    # Proxies

    pid = association_proxy("order", "pid")

    # Synonyms
    order_id: Mapped[str] = synonym("orderid")
    result_type: Mapped[str] = synonym("resulttype")
    entered_on: Mapped[datetime.datetime] = synonym("enteredon")
    pre_post: Mapped[str] = synonym("prepost")
    service_id: Mapped[str] = synonym("serviceidcode")
    service_id_std: Mapped[str] = synonym("serviceidcodestd")
    service_id_description: Mapped[str] = synonym("serviceiddesc")
    sub_id: Mapped[str] = synonym("subid")
    value: Mapped[str] = synonym("resultvalue")
    value_units: Mapped[str] = synonym("resultvalueunits")
    reference_range: Mapped[str] = synonym("referencerange")
    interpretation_codes: Mapped[str] = synonym("interpretationcodes")
    observation_time: Mapped[datetime.datetime] = synonym("observationtime")
    comments: Mapped[str] = synonym("commenttext")
    reference_comment: Mapped[str] = synonym("referencecomment")

    order: Mapped["LabOrder"] = relationship("LabOrder", back_populates="result_items")


class PVData(Base):
    __tablename__ = "pvdata"

    id = Column(String, ForeignKey("patientrecord.pid"), primary_key=True)

    creation_date = Column(DateTime, nullable=False, server_default=text("now()"))
    update_date = Column(DateTime)

    diagnosisdate = Column(Date)

    bloodgroup = Column(String(10))

    rrtstatus = Column(String(100))
    tpstatus = Column(String(100))

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

    did = Column(Integer, primary_key=True)

    pid = Column(String, ForeignKey("patientrecord.pid"))
    creation_date = Column(DateTime, nullable=False, server_default=text("now()"))
    observationtime = Column(DateTime)
    serviceidcode = Column(String(100))
    update_date = Column(DateTime)

    # Synonyms

    observation_time: Mapped[datetime.datetime] = synonym("observationtime")
    service_id: Mapped[str] = synonym("serviceidcode")


class Treatment(Base):
    __tablename__ = "treatment"

    id = Column(String, primary_key=True)
    pid = Column(String, ForeignKey("patientrecord.pid"))

    creation_date = Column(DateTime, nullable=False, server_default=text("now()"))
    idx = Column(Integer)
    encounternumber = Column(String(100))
    encountertype = Column(String(100))
    fromtime = Column(DateTime)
    totime = Column(DateTime)
    admittingcliniciancode = Column(String(100))
    admittingcliniciancodestd = Column(String(100))
    admittingcliniciandesc = Column(String(100))
    admitreasoncode = Column(String(100))
    admitreasoncodestd = Column(String(100))
    admitreasondesc = Column(String(100))
    admissionsourcecode = Column(String(100))
    admissionsourcecodestd = Column(String(100))
    admissionsourcedesc = Column(String(100))
    dischargereasoncode = Column(String(100))
    dischargereasoncodestd = Column(String(100))
    dischargereasondesc = Column(String(100))
    dischargelocationcode = Column(String(100))
    dischargelocationcodestd = Column(String(100))
    dischargelocationdesc = Column(String(100))
    healthcarefacilitycode = Column(String(100))
    healthcarefacilitycodestd = Column(String(100))
    healthcarefacilitydesc = Column(String(100))
    enteredatcode = Column(String(100))
    enteredatcodestd = Column(String(100))
    enteredatdesc = Column(String(100))
    visitdescription = Column(String(100))
    updatedon = Column(DateTime)
    actioncode = Column(String(3))
    externalid = Column(String(100))
    hdp01 = Column(String(255))
    hdp02 = Column(String(255))
    hdp03 = Column(String(255))
    hdp04 = Column(String(255))
    qbl05 = Column(String(255))
    qbl06 = Column(String(255))
    qbl07 = Column(String(255))
    erf61 = Column(String(255))
    pat35 = Column(String(255))
    update_date = Column(DateTime)

    # Synonyms

    encounter_number: Mapped[str] = synonym("encounternumber")
    encounter_type: Mapped[str] = synonym("encountertype")
    from_time: Mapped[datetime.datetime] = synonym("fromtime")
    to_time: Mapped[datetime.datetime] = synonym("totime")
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
    updated_on: Mapped[datetime.datetime] = synonym("updatedon")
    action_code: Mapped[str] = synonym("actioncode")
    external_id: Mapped[str] = synonym("externalid")

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


class TransplantList(Base):
    __tablename__ = "transplantlist"

    id = Column(String, primary_key=True)
    pid = Column(String, ForeignKey("patientrecord.pid"))

    idx = Column(Integer)
    creation_date = Column(DateTime, nullable=False, server_default=text("now()"))
    encounternumber = Column(String(100))
    encountertype = Column(String(100))
    fromtime = Column(DateTime)
    totime = Column(DateTime)
    admittingcliniciancode = Column(String(100))
    admittingcliniciancodestd = Column(String(100))
    admittingcliniciandesc = Column(String(100))
    admitreasoncode = Column(String(100))
    admitreasoncodestd = Column(String(100))
    admitreasondesc = Column(String(100))
    admissionsourcecode = Column(String(100))
    admissionsourcecodestd = Column(String(100))
    admissionsourcedesc = Column(String(100))
    dischargereasoncode = Column(String(100))
    dischargereasoncodestd = Column(String(100))
    dischargereasondesc = Column(String(100))
    dischargelocationcode = Column(String(100))
    dischargelocationcodestd = Column(String(100))
    dischargelocationdesc = Column(String(100))
    healthcarefacilitycode = Column(String(100))
    healthcarefacilitycodestd = Column(String(100))
    healthcarefacilitydesc = Column(String(100))
    enteredatcode = Column(String(100))
    enteredatcodestd = Column(String(100))
    enteredatdesc = Column(String(100))
    visitdescription = Column(String(100))
    updatedon = Column(DateTime)
    actioncode = Column(String(3))
    externalid = Column(String(100))
    update_date = Column(DateTime)


class Code(Base):
    __tablename__ = "code_list"

    coding_standard = Column(String(256), primary_key=True)
    code = Column(String(256), primary_key=True)
    creation_date = Column(DateTime, nullable=False, server_default=text("now()"))
    description = Column(String(256))
    object_type = Column(String(256))
    update_date = Column(DateTime)
    units = Column(String(256))
    pkb_reference_range = Column(String(10))
    pkb_comment = Column(String(365))


class CodeExclusion(Base):
    __tablename__ = "code_exclusion"

    coding_standard = Column(String, primary_key=True)
    code = Column(String, primary_key=True)
    system = Column(String, primary_key=True)


class CodeMap(Base):
    __tablename__ = "code_map"

    source_coding_standard = Column(String(256), primary_key=True)
    source_code = Column(String(256), primary_key=True)
    destination_coding_standard = Column(String(256), primary_key=True)
    destination_code = Column(String(256), primary_key=True)

    creation_date = Column(DateTime, nullable=False, server_default=text("now()"))
    update_date = Column(DateTime)


class Facility(Base):
    __tablename__ = "facility_new"

    # New columns matching SQL schema
    facilitycode = Column("facilitycode", String(100), primary_key=True)
    facilitycodestd = Column("facilitycodestd", String(100), primary_key=True)
    facilitytype = Column("facilitytype", String(100), nullable=False)
    pkbout = Column("pkbout", Boolean, nullable=False, server_default=text("false"))
    pkbmsgexclusions = Column("pkbmsgexclusions", ARRAY(Text))
    ukrdcoutpkb = Column(
        "ukrdcoutpkb", Boolean, nullable=False, server_default=text("false")
    )
    pvoutpkb = Column("pvoutpkb", Boolean, nullable=False, server_default=text("false"))
    startdate = Column("startdate", DateTime)
    enddate = Column("enddate", DateTime)
    firstdataquarter = Column("firstdataquarter", Integer)
    pkboutstartdate = Column("pkboutstartdate", DateTime)
    creation_date = Column(
        "creation_date", DateTime, nullable=False, server_default=text("now()")
    )
    update_date = Column(
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
    code = synonym("facilitycode")
    coding_standard = synonym("facilitycodestd")
    pkb_out = synonym("pkbout")
    pkb_msg_exclusions = synonym("pkbmsgexclusions")
    rdastartdate = synonym("startdate")
    rdaenddate = synonym("enddate")
    rdafirstdataquarter = synonym("firstdataquarter")

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

    id = Column(String, primary_key=True)
    rr_code = Column("rr_code", String, primary_key=True)

    description_1 = Column(String(255))
    description_2 = Column(String(70))
    description_3 = Column(String(60))

    old_value = Column(String(10))
    old_value_2 = Column(String(10))
    new_value = Column(String(10))


class Locations(Base):
    __tablename__ = "locations"

    centre_code = Column(String(10), primary_key=True)
    centre_name = Column(String(255))
    country_code = Column(String(6))
    region_code = Column(String(10))
    paed_unit = Column(Integer)


class RRDataDefinition(Base):
    __tablename__ = "rr_data_definition"

    upload_key = Column(String(5), primary_key=True)

    table_name = Column("TABLE_NAME", String(30), nullable=False)
    field_name = Column(String(30), nullable=False)
    code_id = Column(String(10))
    mandatory = Column(Numeric(1, 0))

    code_type = Column("TYPE", String(1))

    alt_constraint = Column(String(30))
    alt_desc = Column(String(30))
    extra_val = Column(String(1))
    error_type = Column(Integer)
    paed_mand = Column(Numeric(1, 0))
    ckd5_mand_numeric = Column("ckd5_mand", Numeric(1, 0))
    dependant_field = Column(String(30))
    alt_validation = Column(String(30))

    file_prefix = Column(String(20))

    load_min = Column(Numeric(38, 4))
    load_max = Column(Numeric(38, 4))
    remove_min = Column(Numeric(38, 4))
    remove_max = Column(Numeric(38, 4))
    in_month = Column(Numeric(1, 0))
    aki_mand = Column(Numeric(1, 0))
    rrt_mand = Column(Numeric(1, 0))
    cons_mand = Column(Numeric(1, 0))
    ckd4_mand = Column(Numeric(1, 0))
    valid_before_dob = Column(Numeric(1, 0))
    valid_after_dod = Column(Numeric(1, 0))
    in_quarter = Column(Numeric(1, 0))

    # Synonyms

    TYPE: Mapped[str] = synonym("code_type")
    ckd5_mand: Mapped[str] = synonym("ckd5_mand_numeric")
    # historical typo for compatibility tests
    feild_name: Mapped[str] = synonym("field_name")


class ModalityCodes(Base):
    __tablename__ = "modality_codes"

    registry_code = Column(String(8), primary_key=True)

    registry_code_desc = Column(String(100))
    registry_code_type = Column(String(3), nullable=False)
    acute = Column(BIT(1), nullable=False)
    transfer_in = Column(BIT(1), nullable=False)
    ckd = Column(BIT(1), nullable=False)
    cons = Column(BIT(1), nullable=False)
    rrt = Column(BIT(1), nullable=False)
    equiv_modality = Column(String(8))
    end_of_care = Column(BIT(1), nullable=False)
    is_imprecise = Column(BIT(1), nullable=False)
    nhsbt_transplant_type = Column(String(4))
    transfer_out = Column(BIT(1))


class SatelliteMap(Base):
    __tablename__ = "vwe_satellite_map"

    satellite_code = Column(String(10), primary_key=True)
    main_unit_code = Column(String(10), primary_key=True)

    # attributes for backwards compatability
    @property
    def creation_date(self) -> bool:
        return False

    @property
    def update_date(self) -> bool:
        return False


class FacilityRelationship(Base):
    __tablename__ = "vwe_facility_relationship"

    parentfacilitycode = Column(String(100), primary_key=True)
    parentfacilitycodestd = Column(String(100), primary_key=True)
    childfacilitycode = Column(String(100), primary_key=True)
    childfacilitycodestd = Column(String(100), primary_key=True)
    relationshiptype = Column(String(50))


class ValueExclusion(Base):
    __tablename__ = "value_exclusion"

    system = Column(String(20), primary_key=True)
    norm_value = Column(String(100), primary_key=True)


class File(Base):
    __tablename__ = "file"

    sendingfacility = Column(String(7), primary_key=True)
    sendingextract = Column(String(6), primary_key=True)
    ni = Column(String(50), primary_key=True)

    filename = Column(String(255), nullable=False)
    checksum = Column(String(64), nullable=False)
    status = Column(String(20), nullable=False)
    received_on = Column(DateTime, nullable=False)

    creation_date = Column(
        DateTime,
        nullable=False,
        server_default=text("now()"),
    )
    update_date = Column(DateTime)
