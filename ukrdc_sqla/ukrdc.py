"""Models which relate to the main UKRDC database"""

import datetime
from typing import List, Optional

from sqlalchemy import (
    Boolean,
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
from sqlalchemy.orm import Mapped, relationship, synonym, declarative_base, mapped_column

metadata = MetaData()
Base = declarative_base(metadata=metadata)

GLOBAL_LAZY = "dynamic"


class PatientRecord(Base):
    __tablename__ = "patientrecord"

    pid = mapped_column(String, primary_key=True)

    sendingfacility = mapped_column(String(7), nullable=False)
    sendingextract = mapped_column(String(6), nullable=False)
    localpatientid = mapped_column(String(17), nullable=False)
    repositorycreationdate = mapped_column(DateTime, nullable=False)
    repositoryupdatedate = mapped_column(DateTime, nullable=False)
    migrated = mapped_column(Boolean, nullable=False, server_default=text("false"))
    creation_date = mapped_column(DateTime, nullable=False, server_default=text("now()"))
    ukrdcid = mapped_column(String(10), index=True)
    channelname = mapped_column(String(50))
    channelid = mapped_column(String(50))
    extracttime = mapped_column(String(50))
    startdate = mapped_column(DateTime)
    stopdate = mapped_column(DateTime)
    schemaversion = mapped_column(String(50))
    update_date = mapped_column(DateTime)

    # Relationships

    patient: Mapped["Patient"] = relationship(
        "Patient", backref="record", uselist=False, cascade="all, delete-orphan"
    )
    lab_orders:Mapped["LabOrder"] = relationship(
        "LabOrder", backref="record", lazy=GLOBAL_LAZY, cascade="all, delete-orphan"
    )
    result_items:Mapped["ResultItem"] = relationship(
        "ResultItem",
        secondary="laborder",
        primaryjoin="LabOrder.pid == PatientRecord.pid",
        secondaryjoin="ResultItem.order_id == LabOrder.id",
        lazy=GLOBAL_LAZY,
        viewonly=True,
    )
    observations:Mapped["Observation"] = relationship(
        "Observation", backref="record", lazy=GLOBAL_LAZY, cascade="all, delete-orphan"
    )
    social_histories:Mapped["SocialHistory"] = relationship(
        "SocialHistory", cascade="all, delete-orphan"
    )
    family_histories:Mapped["FamilyHistory"] = relationship(
        "FamilyHistory", cascade="all, delete-orphan"
    )
    allergies:Mapped["Allergy"] = relationship(
        "Allergy", lazy=GLOBAL_LAZY, cascade="all, delete-orphan"
    )
    diagnoses:Mapped["Diagnosis"] = relationship(
        "Diagnosis", lazy=GLOBAL_LAZY, cascade="all, delete-orphan"
    )
    cause_of_death:Mapped["CauseOfDeath"] = relationship(
        "CauseOfDeath", lazy=GLOBAL_LAZY, cascade="all, delete-orphan"
    )
    renaldiagnoses:Mapped["RenalDiagnosis"] = relationship(
        "RenalDiagnosis", lazy=GLOBAL_LAZY, cascade="all, delete-orphan"
    )
    medications:Mapped["Medication"] = relationship(
        "Medication", lazy=GLOBAL_LAZY, cascade="all, delete-orphan"
    )
    dialysis_sessions:Mapped["DialysisSession"] = relationship(
        "DialysisSession", lazy=GLOBAL_LAZY, cascade="all, delete-orphan"
    )
    vascular_accesses:Mapped["VascularAccess"] = relationship(
        "VascularAccess", lazy=GLOBAL_LAZY, cascade="all, delete-orphan"
    )
    procedures:Mapped["Procedure"] = relationship(
        "Procedure", lazy=GLOBAL_LAZY, cascade="all, delete-orphan"
    )
    documents:Mapped["Document"] = relationship(
        "Document", lazy=GLOBAL_LAZY, cascade="all, delete-orphan"
    )
    encounters:Mapped["Encounter"] = relationship(
        "Encounter", lazy=GLOBAL_LAZY, cascade="all, delete-orphan"
    )
    transplantlists:Mapped["TransplantList"] = relationship(
        "TransplantList", lazy=GLOBAL_LAZY, cascade="all, delete-orphan"
    )
    treatments:Mapped["Treatment"] = relationship(
        "Treatment", lazy=GLOBAL_LAZY, cascade="all, delete-orphan"
    )
    program_memberships:Mapped["ProgramMembership"] = relationship(
        "ProgramMembership", cascade="all, delete-orphan"
    )
    transplants:Mapped["Transplant"] = relationship(
        "Transplant", lazy=GLOBAL_LAZY, cascade="all, delete-orphan"
    )
    opt_outs = relationship("OptOut", lazy=GLOBAL_LAZY, cascade="all, delete-orphan")
    clinical_relationships = relationship(
        "ClinicalRelationship", cascade="all, delete-orphan"
    )
    surveys:Mapped["Survey"] = relationship(
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

    pid = mapped_column(String, ForeignKey("patientrecord.pid"), primary_key=True)

    creation_date = mapped_column(DateTime, nullable=False, server_default=text("now()"))
    birthtime = mapped_column(DateTime)
    deathtime = mapped_column(DateTime)
    gender = mapped_column(String(2))
    countryofbirth = mapped_column(String(3))
    ethnicgroupcode = mapped_column(String(100))
    ethnicgroupcodestd = mapped_column(String(100))
    ethnicgroupdesc = mapped_column(String(100))
    occupationcode = mapped_column(String(100))
    occupationcodestd = mapped_column(String(100))
    occupationdesc = mapped_column(String(100))
    primarylanguagecode = mapped_column(String(100))
    primarylanguagecodestd = mapped_column(String(100))
    primarylanguagedesc = mapped_column(String(100))
    death = mapped_column(Boolean)
    persontocontactname = mapped_column(String(100))
    persontocontact_relationship = mapped_column(String(20))
    persontocontact_contactnumber = mapped_column(String(20))
    persontocontact_contactnumbertype = mapped_column(String(20))
    persontocontact_contactnumbercomments = mapped_column(String(200))
    updatedon = mapped_column(DateTime)
    actioncode = mapped_column(String(3))
    externalid = mapped_column(String(100))
    bloodgroup = mapped_column(String(100))
    bloodrhesus = mapped_column(String(100))
    update_date = mapped_column(DateTime)

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

    numbers:Mapped["PatientNumber"] = relationship(
        "PatientNumber",
        backref="patient",
        lazy=GLOBAL_LAZY,
        cascade="all, delete-orphan",
    )
    names:Mapped["Name"] = relationship(
        "Name", lazy=GLOBAL_LAZY, cascade="all, delete-orphan"
    )
    contact_details:Mapped["ContactDetail"] = relationship(
        "ContactDetail", lazy=GLOBAL_LAZY, cascade="all, delete-orphan"
    )
    addresses:Mapped["Address"] = relationship(
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

    pid = mapped_column(String, ForeignKey("patientrecord.pid"), primary_key=True)

    creation_date = mapped_column(DateTime, nullable=False, server_default=text("now()"))
    diagnosistype = mapped_column(String(50))
    diagnosingcliniciancode = mapped_column(String(100))
    diagnosingcliniciancodestd = mapped_column(String(100))
    diagnosingcliniciandesc = mapped_column(String(100))
    diagnosiscode = mapped_column(String(100))
    diagnosiscodestd = mapped_column(String(100))
    diagnosisdesc = mapped_column(String(255))
    comments = mapped_column(Text)
    enteredon = mapped_column(DateTime)
    updatedon = mapped_column(DateTime)
    actioncode = mapped_column(String(3))
    externalid = mapped_column(String(100))
    update_date = mapped_column(DateTime)

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

    id = mapped_column(String, ForeignKey("patient.pid"), primary_key=True)

    creation_date = mapped_column(DateTime, nullable=False, server_default=text("now()"))
    gpname = mapped_column(String(100))

    gpid = mapped_column(String(20), ForeignKey("ukrdc_ods_gp_codes.code"))
    gppracticeid = mapped_column(String(20), ForeignKey("ukrdc_ods_gp_codes.code"))

    addressuse = mapped_column(String(10))
    fromtime = mapped_column(Date)
    totime = mapped_column(Date)
    street = mapped_column(String(100))
    town = mapped_column(String(100))
    county = mapped_column(String(100))
    postcode = mapped_column(String(10))
    countrycode = mapped_column(String(100))
    countrycodestd = mapped_column(String(100))
    countrydesc = mapped_column(String(100))
    contactuse = mapped_column(String(10))
    contactvalue = mapped_column(String(100))
    email = mapped_column(String(100))
    commenttext = mapped_column(String(100))
    update_date = mapped_column(DateTime)

    # Relationships

    gp_info = relationship("GPInfo", foreign_keys=[gpid], uselist=False)
    gp_practice_info = relationship(
        "GPInfo", foreign_keys=[gppracticeid], uselist=False
    )

    def __str__(self):
        return (
            f"{self.__class__.__name__}({self.id}) <" f"{self.gpname} {self.gpid}" f">"
        )


class GPInfo(Base):
    __tablename__ = "ukrdc_ods_gp_codes"

    code = mapped_column(String(8), primary_key=True)

    creation_date = mapped_column(DateTime, nullable=False, server_default=text("now()"))
    name = mapped_column(String(50))
    address1 = mapped_column(String(35))
    postcode = mapped_column(String(8))
    phone = mapped_column(String(12))
    type = mapped_column(Enum("GP", "PRACTICE", name="gp_type"))
    update_date = mapped_column(DateTime)

    # Synonyms

    gpname: Mapped[str] = synonym("name")
    street: Mapped[str] = synonym("address1")
    contactvalue: Mapped[str] = synonym("phone")


class SocialHistory(Base):
    __tablename__ = "socialhistory"

    id = mapped_column(String, primary_key=True)
    pid = mapped_column(String, ForeignKey("patientrecord.pid"))

    creation_date = mapped_column(DateTime, nullable=False, server_default=text("now()"))
    idx = mapped_column(Integer)
    socialhabitcode = mapped_column(String(100))
    socialhabitcodestd = mapped_column(String(100))
    socialhabitdesc = mapped_column(String(100))
    updatedon = mapped_column(DateTime)
    actioncode = mapped_column(String(3))
    externalid = mapped_column(String(100))
    update_date = mapped_column(DateTime)


class FamilyHistory(Base):
    __tablename__ = "familyhistory"

    id = mapped_column(String, primary_key=True)
    pid = mapped_column(String, ForeignKey("patientrecord.pid"))

    creation_date = mapped_column(DateTime, nullable=False, server_default=text("now()"))
    idx = mapped_column(Integer)
    familymembercode = mapped_column(String(100))
    familymembercodestd = mapped_column(String(100))
    familymemberdesc = mapped_column(String(100))
    diagnosiscode = mapped_column(String(100))
    diagnosiscodestd = mapped_column(String(100))
    diagnosisdesc = mapped_column(String(100))
    notetext = mapped_column(String(100))
    enteredatcode = mapped_column(String(100))
    enteredatcodestd = mapped_column(String(100))
    enteredatdesc = mapped_column(String(100))
    fromtime = mapped_column(DateTime)
    totime = mapped_column(DateTime)
    updatedon = mapped_column(DateTime)
    actioncode = mapped_column(String(3))
    externalid = mapped_column(String(100))
    update_date = mapped_column(DateTime)


class Observation(Base):
    __tablename__ = "observation"

    id = mapped_column(String, primary_key=True)
    pid = mapped_column(String, ForeignKey("patientrecord.pid"))

    creation_date = mapped_column(DateTime, nullable=False, server_default=text("now()"))
    idx = mapped_column(Integer)
    observationtime = mapped_column(DateTime)
    observationcode = mapped_column(String(100))
    observationcodestd = mapped_column(String(100))
    observationdesc = mapped_column(String(100))
    observationvalue = mapped_column(String(100))
    observationunits = mapped_column(String(100))
    prepost = mapped_column(String(4))
    commenttext = mapped_column(String(100))
    cliniciancode = mapped_column(String(100))
    cliniciancodestd = mapped_column(String(100))
    cliniciandesc = mapped_column(String(100))
    enteredatcode = mapped_column(String(100))
    enteredatcodestd = mapped_column(String(100))
    enteredatdesc = mapped_column(String(100))
    enteringorganizationcode = mapped_column(String(100))
    enteringorganizationcodestd = mapped_column(String(100))
    enteringorganizationdesc = mapped_column(String(100))
    updatedon = mapped_column(DateTime)
    actioncode = mapped_column(String(3))
    externalid = mapped_column(String(100))
    update_date = mapped_column(DateTime)

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

    id = mapped_column(String, primary_key=True)
    pid = mapped_column(String, ForeignKey("patientrecord.pid"))

    creation_date = mapped_column(DateTime, nullable=False, server_default=text("now()"))
    idx = mapped_column(Integer)
    programname = mapped_column(String(100))
    programdescription = mapped_column(String(100))
    enteredbycode = mapped_column(String(100))
    enteredbycodestd = mapped_column(String(100))
    enteredbydesc = mapped_column(String(100))
    enteredatcode = mapped_column(String(100))
    enteredatcodestd = mapped_column(String(100))
    enteredatdesc = mapped_column(String(100))
    fromtime = mapped_column(Date)
    totime = mapped_column(Date)
    updatedon = mapped_column(DateTime)
    actioncode = mapped_column(String(3))
    externalid = mapped_column(String(100))
    update_date = mapped_column(DateTime)

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

    id = mapped_column(String, primary_key=True)
    pid = mapped_column(String, ForeignKey("patientrecord.pid"))

    creation_date = mapped_column(DateTime, nullable=False, server_default=text("now()"))
    idx = mapped_column(Integer)
    allergycode = mapped_column(String(100))
    allergycodestd = mapped_column(String(100))
    allergydesc = mapped_column(String(100))
    allergycategorycode = mapped_column(String(100))
    allergycategorycodestd = mapped_column(String(100))
    allergycategorydesc = mapped_column(String(100))
    severitycode = mapped_column(String(100))
    severitycodestd = mapped_column(String(100))
    severitydesc = mapped_column(String(100))
    cliniciancode = mapped_column(String(100))
    cliniciancodestd = mapped_column(String(100))
    cliniciandesc = mapped_column(String(100))
    discoverytime = mapped_column(DateTime)
    confirmedtime = mapped_column(DateTime)
    commenttext = mapped_column(String(500))
    inactivetime = mapped_column(DateTime)
    freetextallergy = mapped_column(String(500))
    qualifyingdetails = mapped_column(String(500))
    updatedon = mapped_column(DateTime)
    actioncode = mapped_column(String(3))
    externalid = mapped_column(String(100))
    update_date = mapped_column(DateTime)


class Diagnosis(Base):
    __tablename__ = "diagnosis"

    id = mapped_column(String, primary_key=True)
    pid = mapped_column(String, ForeignKey("patientrecord.pid"))

    creation_date = mapped_column(DateTime, nullable=False, server_default=text("now()"))
    idx = mapped_column(Integer)
    diagnosistype = mapped_column(String(50))
    diagnosingcliniciancode = mapped_column(String(100))
    diagnosingcliniciancodestd = mapped_column(String(100))
    diagnosingcliniciandesc = mapped_column(String(100))
    diagnosiscode = mapped_column(String(100))
    diagnosiscodestd = mapped_column(String(100))
    diagnosisdesc = mapped_column(String(255))
    comments = mapped_column(Text)
    identificationtime = mapped_column(DateTime)
    onsettime = mapped_column(DateTime)
    enteredon = mapped_column(DateTime)
    updatedon = mapped_column(DateTime)
    actioncode = mapped_column(String(3))
    externalid = mapped_column(String(100))
    update_date = mapped_column(DateTime)
    enteredatcode = mapped_column(String(100))
    enteredatcodestd = mapped_column(String(100))
    enteredatdesc = mapped_column(String(100))
    encounternumber = mapped_column(String(100))
    verificationstatus = mapped_column(String(100))

    # Synonyms

    diagnosis_code: Mapped[str] = synonym("diagnosiscode")
    diagnosis_code_std: Mapped[str] = synonym("diagnosiscodestd")
    diagnosis_desc: Mapped[str] = synonym("diagnosisdesc")
    identification_time: Mapped[datetime.datetime] = synonym("identificationtime")
    onset_time: Mapped[datetime.datetime] = synonym("onsettime")


class RenalDiagnosis(Base):
    __tablename__ = "renaldiagnosis"

    pid = mapped_column(String, ForeignKey("patientrecord.pid"), primary_key=True)

    creation_date = mapped_column(DateTime, nullable=False, server_default=text("now()"))
    diagnosistype = mapped_column(String(50))
    diagnosiscode = mapped_column("diagnosiscode", String)
    diagnosiscodestd = mapped_column("diagnosiscodestd", String)
    diagnosisdesc = mapped_column("diagnosisdesc", String)
    diagnosingcliniciancode = mapped_column(String(100))
    diagnosingcliniciancodestd = mapped_column(String(100))
    diagnosingcliniciandesc = mapped_column(String(100))
    comments = mapped_column(String)
    identificationtime = mapped_column("identificationtime", DateTime)
    onsettime = mapped_column(DateTime)
    enteredon = mapped_column(DateTime)
    updatedon = mapped_column(DateTime)
    actioncode = mapped_column(String(3))
    externalid = mapped_column(String(100))
    update_date = mapped_column(DateTime)

    # Synonyms
    id: Mapped[str] = synonym("pid")  # see comment on cause of death
    diagnosis_code: Mapped[str] = synonym("diagnosiscode")
    diagnosis_code_std: Mapped[str] = synonym("diagnosiscodestd")
    diagnosis_desc: Mapped[str] = synonym("diagnosisdesc")
    identification_time: Mapped[datetime.datetime] = synonym("identificationtime")


class DialysisSession(Base):
    __tablename__ = "dialysissession"

    id = mapped_column(String, primary_key=True)
    pid = mapped_column(String, ForeignKey("patientrecord.pid"))

    creation_date = mapped_column(DateTime, nullable=False, server_default=text("now()"))
    idx = mapped_column(Integer)
    proceduretypecode = mapped_column(String(100))
    proceduretypecodestd = mapped_column(String(100))
    proceduretypedesc = mapped_column(String(100))
    cliniciancode = mapped_column(String(100))
    cliniciancodestd = mapped_column(String(100))
    cliniciandesc = mapped_column(String(100))
    proceduretime = mapped_column(DateTime)
    enteredbycode = mapped_column(String(100))
    enteredbycodestd = mapped_column(String(100))
    enteredbydesc = mapped_column(String(100))
    enteredatcode = mapped_column(String(100))
    enteredatcodestd = mapped_column(String(100))
    enteredatdesc = mapped_column(String(100))
    qhd19 = mapped_column(String(255))
    qhd20 = mapped_column(String(255))
    qhd21 = mapped_column(String(255))
    qhd22 = mapped_column(String(255))
    qhd30 = mapped_column(String(255))
    qhd31 = mapped_column(String(255))
    qhd32 = mapped_column(String(255))
    qhd33 = mapped_column(String(255))

    updatedon = mapped_column(DateTime)
    actioncode = mapped_column(String(3))
    externalid = mapped_column(String(100))
    update_date = mapped_column(DateTime)

    # Synonyms

    procedure_type_code: Mapped[str] = synonym("proceduretypecode")
    procedure_type_code_std: Mapped[str] = synonym("proceduretypecodestd")
    procedure_type_desc: Mapped[str] = synonym("proceduretypedesc")
    procedure_time: Mapped[datetime.datetime] = synonym("proceduretime")


class Transplant(Base):
    __tablename__ = "transplant"

    id = mapped_column(String, primary_key=True)
    pid = mapped_column(String, ForeignKey("patientrecord.pid"))

    creation_date = mapped_column(DateTime, nullable=False, server_default=text("now()"))
    idx = mapped_column(Integer)

    proceduretypecode = mapped_column(String(100))
    proceduretypecodestd = mapped_column(String(100))
    proceduretypedesc = mapped_column(String(100))

    cliniciancode = mapped_column(String(100))
    cliniciancodestd = mapped_column(String(100))
    cliniciandesc = mapped_column(String(100))

    proceduretime = mapped_column(DateTime)

    enteredbycode = mapped_column(String(100))
    enteredbycodestd = mapped_column(String(100))
    enteredbydesc = mapped_column(String(100))

    enteredatcode = mapped_column(String(100))
    enteredatcodestd = mapped_column(String(100))
    enteredatdesc = mapped_column(String(100))

    updatedon = mapped_column(DateTime)
    actioncode = mapped_column(String(3))
    externalid = mapped_column(String(100))

    tra64 = mapped_column(DateTime)
    tra65 = mapped_column(String(255))
    tra66 = mapped_column(String(255))
    tra69 = mapped_column(DateTime)
    tra76 = mapped_column(String(255))
    tra77 = mapped_column(String(255))
    tra78 = mapped_column(String(255))
    tra79 = mapped_column(String(255))
    tra80 = mapped_column(String(255))
    tra8a = mapped_column(String(255))
    tra81 = mapped_column(String(255))
    tra82 = mapped_column(String(255))
    tra83 = mapped_column(String(255))
    tra84 = mapped_column(String(255))
    tra85 = mapped_column(String(255))
    tra86 = mapped_column(String(255))
    tra87 = mapped_column(String(255))
    tra88 = mapped_column(String(255))
    tra89 = mapped_column(String(255))
    tra90 = mapped_column(String(255))
    tra91 = mapped_column(String(255))
    tra92 = mapped_column(String(255))
    tra93 = mapped_column(String(255))
    tra94 = mapped_column(String(255))
    tra95 = mapped_column(String(255))
    tra96 = mapped_column(String(255))
    tra97 = mapped_column(String(255))
    tra98 = mapped_column(String(255))

    update_date = mapped_column(DateTime)

    # Synonyms

    procedure_type_code: Mapped[str] = synonym("proceduretypecode")
    procedure_type_code_std: Mapped[str] = synonym("proceduretypecodestd")
    procedure_type_desc: Mapped[str] = synonym("proceduretypedesc")
    procedure_time: Mapped[datetime.datetime] = synonym("proceduretime")


class VascularAccess(Base):
    __tablename__ = "vascularaccess"

    id = mapped_column(String, primary_key=True)
    pid = mapped_column(String, ForeignKey("patientrecord.pid"))
    idx = mapped_column(Integer)

    creation_date = mapped_column(DateTime, nullable=False, server_default=text("now()"))
    proceduretypecode = mapped_column(String(100))
    proceduretypecodestd = mapped_column(String(100))
    proceduretypedesc = mapped_column(String(100))
    cliniciancode = mapped_column(String(100))
    cliniciancodestd = mapped_column(String(100))
    cliniciandesc = mapped_column(String(100))
    proceduretime = mapped_column(DateTime)
    enteredbycode = mapped_column(String(100))
    enteredbycodestd = mapped_column(String(100))
    enteredbydesc = mapped_column(String(100))
    enteredatcode = mapped_column(String(100))
    enteredatcodestd = mapped_column(String(100))
    enteredatdesc = mapped_column(String(100))
    updatedon = mapped_column(DateTime)
    actioncode = mapped_column(String(3))
    externalid = mapped_column(String(100))

    acc19 = mapped_column(String(255))
    acc20 = mapped_column(String(255))
    acc21 = mapped_column(String(255))
    acc22 = mapped_column(String(255))
    acc30 = mapped_column(String(255))
    acc40 = mapped_column(String(255))

    update_date = mapped_column(DateTime)


class Procedure(Base):
    __tablename__ = "procedure"

    id = mapped_column(String, primary_key=True)
    pid = mapped_column(String, ForeignKey("patientrecord.pid"))

    creation_date = mapped_column(DateTime, nullable=False, server_default=text("now()"))
    idx = mapped_column(Integer)
    proceduretypecode = mapped_column(String(100))
    proceduretypecodestd = mapped_column(String(100))
    proceduretypedesc = mapped_column(String(100))
    cliniciancode = mapped_column(String(100))
    cliniciancodestd = mapped_column(String(100))
    cliniciandesc = mapped_column(String(100))
    proceduretime = mapped_column(DateTime)
    enteredbycode = mapped_column(String(100))
    enteredbycodestd = mapped_column(String(100))
    enteredbydesc = mapped_column(String(100))
    enteredatcode = mapped_column(String(100))
    enteredatcodestd = mapped_column(String(100))
    enteredatdesc = mapped_column(String(100))
    updatedon = mapped_column(DateTime)
    actioncode = mapped_column(String(3))
    externalid = mapped_column(String(100))
    update_date = mapped_column(DateTime)


class Encounter(Base):
    __tablename__ = "encounter"

    id = mapped_column(String, primary_key=True)
    pid = mapped_column(String, ForeignKey("patientrecord.pid"))

    creation_date = mapped_column(DateTime, nullable=False, server_default=text("now()"))
    idx = mapped_column(Integer)
    encounternumber = mapped_column(String(100))
    encountertype = mapped_column(String(100))
    fromtime = mapped_column(DateTime)
    totime = mapped_column(DateTime)
    admittingcliniciancode = mapped_column(String(100))
    admittingcliniciancodestd = mapped_column(String(100))
    admittingcliniciandesc = mapped_column(String(100))
    admitreasoncode = mapped_column(String(100))
    admitreasoncodestd = mapped_column(String(100))
    admitreasondesc = mapped_column(String(100))
    admissionsourcecode = mapped_column(String(100))
    admissionsourcecodestd = mapped_column(String(100))
    admissionsourcedesc = mapped_column(String(100))
    dischargereasoncode = mapped_column(String(100))
    dischargereasoncodestd = mapped_column(String(100))
    dischargereasondesc = mapped_column(String(100))
    dischargelocationcode = mapped_column(String(100))
    dischargelocationcodestd = mapped_column(String(100))
    dischargelocationdesc = mapped_column(String(100))
    healthcarefacilitycode = mapped_column(String(100))
    healthcarefacilitycodestd = mapped_column(String(100))
    healthcarefacilitydesc = mapped_column(String(100))
    enteredatcode = mapped_column(String(100))
    enteredatcodestd = mapped_column(String(100))
    enteredatdesc = mapped_column(String(100))
    visitdescription = mapped_column(String(100))
    updatedon = mapped_column(DateTime)
    actioncode = mapped_column(String(3))
    externalid = mapped_column(String(100))
    update_date = mapped_column(DateTime)

    # Synonyms

    from_time: Mapped[datetime.datetime] = synonym("fromtime")
    to_time: Mapped[datetime.datetime] = synonym("totime")


class ProgramMembership(Base):
    __tablename__ = "programmembership"

    id = mapped_column(String, primary_key=True)
    pid = mapped_column(String, ForeignKey("patientrecord.pid"))

    creation_date = mapped_column(DateTime, nullable=False, server_default=text("now()"))
    programname = mapped_column(String(100))
    programdescription = mapped_column(String(100))
    enteredbycode = mapped_column(String(100))
    enteredbycodestd = mapped_column(String(100))
    enteredbydesc = mapped_column(String(100))
    enteredatcode = mapped_column(String(100))
    enteredatcodestd = mapped_column(String(100))
    enteredatdesc = mapped_column(String(100))
    fromtime = mapped_column(Date)
    totime = mapped_column(Date)
    updatedon = mapped_column(DateTime)
    actioncode = mapped_column(String(3))
    externalid = mapped_column(String(100))
    update_date = mapped_column(DateTime)

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

    id = mapped_column(String, primary_key=True)
    pid = mapped_column(String, ForeignKey("patientrecord.pid"))

    creation_date = mapped_column(DateTime, nullable=False, server_default=text("now()"))
    idx = mapped_column(Integer)
    cliniciancode = mapped_column(String(100))
    cliniciancodestd = mapped_column(String(100))
    cliniciandesc = mapped_column(String(100))
    facilitycode = mapped_column(String(100))
    facilitycodestd = mapped_column(String(100))
    facilitydesc = mapped_column(String(100))
    fromtime = mapped_column(Date)
    totime = mapped_column(Date)
    updatedon = mapped_column(DateTime)
    actioncode = mapped_column(String(3))
    externalid = mapped_column(String(100))
    update_date = mapped_column(DateTime)


class Name(Base):
    __tablename__ = "name"

    id = mapped_column(String, primary_key=True)
    pid = mapped_column(String, ForeignKey("patient.pid"))

    creation_date = mapped_column(DateTime, nullable=False, server_default=text("now()"))
    idx = mapped_column(Integer)
    nameuse = mapped_column(String(10))
    prefix = mapped_column(String(10))
    family = mapped_column(String(60))
    given = mapped_column(String(60))
    othergivennames = mapped_column(String(60))
    suffix = mapped_column(String(10))
    update_date = mapped_column(DateTime)

    def __str__(self):
        return (
            f"{self.__class__.__name__}({self.pid}) <"
            f"{self.given} {self.family}"
            f">"
        )


class PatientNumber(Base):
    __tablename__ = "patientnumber"

    id = mapped_column(String, primary_key=True)
    pid = mapped_column(String, ForeignKey("patient.pid"))

    creation_date = mapped_column(DateTime, nullable=False, server_default=text("now()"))
    idx = mapped_column(Integer)
    patientid = mapped_column(String(50), index=True)
    numbertype = mapped_column(String(3))
    organization = mapped_column(String(50))
    updatedon = mapped_column(DateTime)
    actioncode = mapped_column(String(3))
    externalid = mapped_column(String(100))
    update_date = mapped_column(DateTime)

    def __str__(self):
        return (
            f"{self.__class__.__name__}({self.pid}) <"
            f"{self.organization}:{self.numbertype}:{self.patientid}"
            ">"
        )


class Address(Base):
    __tablename__ = "address"

    id = mapped_column(String, primary_key=True)
    pid = mapped_column(String, ForeignKey("patient.pid"))

    creation_date = mapped_column(DateTime, nullable=False, server_default=text("now()"))
    idx = mapped_column(Integer)
    addressuse = mapped_column(String(10))
    fromtime = mapped_column(Date)
    totime = mapped_column(Date)
    street = mapped_column(String(100))
    town = mapped_column(String(100))
    county = mapped_column(String(100))
    postcode = mapped_column(String(10))
    countrycode = mapped_column(String(100))
    countrycodestd = mapped_column(String(100))
    countrydesc = mapped_column(String(100))
    update_date = mapped_column(DateTime)

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

    id = mapped_column(String, primary_key=True)
    pid = mapped_column(String, ForeignKey("patient.pid"))

    creation_date = mapped_column(DateTime, nullable=False, server_default=text("now()"))
    idx = mapped_column(Integer)
    contactuse = mapped_column(String(10))
    contactvalue = mapped_column(String(100))
    commenttext = mapped_column(String(100))
    updatedon = mapped_column(DateTime)
    actioncode = mapped_column(String(3))
    externalid = mapped_column(String(100))
    update_date = mapped_column(DateTime)

    # Synonyms

    use: Mapped[str] = synonym("contactuse")
    value: Mapped[str] = synonym("contactvalue")

    def __str__(self):
        return f"{self.__class__.__name__}({self.pid}) <{self.use}:{self.value}>"


class Medication(Base):
    __tablename__ = "medication"

    id = mapped_column(String, primary_key=True)
    pid = mapped_column(String, ForeignKey("patientrecord.pid"))

    creation_date = mapped_column(DateTime, nullable=False, server_default=text("now()"))

    idx = mapped_column(Integer)
    repositoryupdatedate = mapped_column(DateTime, nullable=False)
    prescriptionnumber = mapped_column(String(100))
    fromtime = mapped_column(DateTime)
    totime = mapped_column(DateTime)

    orderedbycode = mapped_column(String(100))
    orderedbycodestd = mapped_column(String(100))
    orderedbydesc = mapped_column(String(100))

    enteringorganizationcode = mapped_column(String(100))
    enteringorganizationcodestd = mapped_column(String(100))
    enteringorganizationdesc = mapped_column(String(100))

    routecode = mapped_column(String(10))
    routecodestd = mapped_column(String(100))
    routedesc = mapped_column(String(100))

    drugproductidcode = mapped_column(String(100))
    drugproductidcodestd = mapped_column(String(100))
    drugproductiddesc = mapped_column(String(100))

    drugproductgeneric = mapped_column(String(255))
    drugproductlabelname = mapped_column(String(255))

    drugproductformcode = mapped_column(String(100))
    drugproductformcodestd = mapped_column(String(100))
    drugproductformdesc = mapped_column(String(100))

    drugproductstrengthunitscode = mapped_column(String(100))
    drugproductstrengthunitscodestd = mapped_column(String(100))
    drugproductstrengthunitsdesc = mapped_column(String(100))

    frequency = mapped_column(String(255))
    commenttext = mapped_column(String(1000))
    dosequantity = mapped_column(Numeric(19, 2))

    doseuomcode = mapped_column(String(100))
    doseuomcodestd = mapped_column(String(100))
    doseuomdesc = mapped_column(String(100))

    indication = mapped_column(String(100))
    updatedon = mapped_column(DateTime)
    actioncode = mapped_column(String(3))
    externalid = mapped_column(String(100))
    update_date = mapped_column(DateTime)
    encounternumber = mapped_column(String(100))

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

    id = mapped_column(String, primary_key=True)
    pid = mapped_column(String, ForeignKey("patientrecord.pid"))

    creation_date = mapped_column(DateTime, nullable=False, server_default=text("now()"))
    surveytime = mapped_column(DateTime, nullable=False)
    surveytypecode = mapped_column(String(100))
    surveytypecodestd = mapped_column(String(100))
    surveytypedesc = mapped_column(String(100))
    typeoftreatment = mapped_column(String(100))
    hdlocation = mapped_column(String(100))
    template = mapped_column(String(100))
    enteredbycode = mapped_column(String(100))
    enteredbycodestd = mapped_column(String(100))
    enteredbydesc = mapped_column(String(100))
    enteredatcode = mapped_column(String(100))
    enteredatcodestd = mapped_column(String(100))
    enteredatdesc = mapped_column(String(100))
    updatedon = mapped_column(DateTime)
    actioncode = mapped_column(String(3))
    externalid = mapped_column(String(100))
    update_date = mapped_column(DateTime)

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

    id = mapped_column(String, primary_key=True)

    surveyid = mapped_column(String, ForeignKey("survey.id"))
    creation_date = mapped_column(DateTime, nullable=False, server_default=text("now()"))
    idx = mapped_column(Integer)
    questiontypecode = mapped_column(String(100))
    questiontypecodestd = mapped_column(String(100))
    questiontypedesc = mapped_column(String(100))
    response = mapped_column(String(100))
    questiontext = mapped_column(String(100))
    update_date = mapped_column(DateTime)


class Score(Base):
    __tablename__ = "score"

    id = mapped_column(String, primary_key=True)

    surveyid = mapped_column(String, ForeignKey("survey.id"))
    creation_date = mapped_column(DateTime, nullable=False, server_default=text("now()"))
    idx = mapped_column(Integer)
    scorevalue = mapped_column(String(100))
    scoretypecode = mapped_column(String(100))
    scoretypecodestd = mapped_column(String(100))
    scoretypedesc = mapped_column(String(100))
    update_date = mapped_column(DateTime)

    # Synonyms

    value: Mapped[str] = synonym("scorevalue")


class Level(Base):
    __tablename__ = "level"

    id = mapped_column(String, primary_key=True)

    surveyid = mapped_column(String, ForeignKey("survey.id"))
    creation_date = mapped_column(DateTime, nullable=False, server_default=text("now()"))
    idx = mapped_column(Integer)
    levelvalue = mapped_column(String(100))
    leveltypecode = mapped_column(String(100))
    leveltypecodestd = mapped_column(String(100))
    leveltypedesc = mapped_column(String(100))
    update_date = mapped_column(DateTime)

    # Synonyms

    value: Mapped[str] = synonym("levelvalue")


class Document(Base):
    __tablename__ = "document"

    id = mapped_column(String, primary_key=True)
    pid = mapped_column(String, ForeignKey("patientrecord.pid"))

    repositoryupdatedate = mapped_column(DateTime, nullable=False)
    creation_date = mapped_column(DateTime, nullable=False, server_default=text("now()"))
    idx = mapped_column(Integer)
    documenttime = mapped_column(DateTime)
    notetext = mapped_column(Text)
    documenttypecode = mapped_column(String(100))
    documenttypecodestd = mapped_column(String(100))
    documenttypedesc = mapped_column(String(100))
    cliniciancode = mapped_column(String(100))
    cliniciancodestd = mapped_column(String(100))
    cliniciandesc = mapped_column(String(100))
    documentname = mapped_column(String(100))
    statuscode = mapped_column(String(100))
    statuscodestd = mapped_column(String(100))
    statusdesc = mapped_column(String(100))
    enteredbycode = mapped_column(String(100))
    enteredbycodestd = mapped_column(String(100))
    enteredbydesc = mapped_column(String(100))
    enteredatcode = mapped_column(String(100))
    enteredatcodestd = mapped_column(String(100))
    enteredatdesc = mapped_column(String(100))
    filetype = mapped_column(String(100))
    filename = mapped_column(String(100))
    stream = mapped_column(LargeBinary)
    documenturl = mapped_column(String(100))
    updatedon = mapped_column(DateTime)
    actioncode = mapped_column(String(3))
    externalid = mapped_column(String(100))
    update_date = mapped_column(DateTime)

    # Synonyms

    repository_update_date = synonym("repositoryupdatedate")


class LabOrder(Base):
    __tablename__ = "laborder"

    id = mapped_column(String, primary_key=True)
    pid = mapped_column(String, ForeignKey("patientrecord.pid"))

    creation_date = mapped_column(
        DateTime, nullable=False, index=True, server_default=text("now()")
    )
    placerid = mapped_column(String(100))
    fillerid = mapped_column(String(100))
    receivinglocationcode = mapped_column(String(100))
    receivinglocationcodestd = mapped_column(String(100))
    receivinglocationdesc = mapped_column(String(100))
    orderedbycode = mapped_column(String(100))
    orderedbycodestd = mapped_column(String(100))
    orderedbydesc = mapped_column(String(100))
    orderitemcode = mapped_column(String(100))
    orderitemcodestd = mapped_column(String(100))
    orderitemdesc = mapped_column(String(100))
    prioritycode = mapped_column(String(100))
    prioritycodestd = mapped_column(String(100))
    prioritydesc = mapped_column(String(100))
    status = mapped_column(String(100))
    ordercategorycode = mapped_column(String(100))
    ordercategorycodestd = mapped_column(String(100))
    ordercategorydesc = mapped_column(String(100))
    specimensource = mapped_column(String(50))
    specimenreceivedtime = mapped_column(DateTime)
    specimencollectedtime = mapped_column(DateTime)
    duration = mapped_column(String(50))
    patientclasscode = mapped_column(String(100))
    patientclasscodestd = mapped_column(String(100))
    patientclassdesc = mapped_column(String(100))
    enteredon = mapped_column(DateTime)
    enteredatcode = mapped_column(String(100))
    enteredatcodestd = mapped_column(String(100))
    enteredatdesc = mapped_column(String(100))
    enteringorganizationcode = mapped_column(String(100))
    enteringorganizationcodestd = mapped_column(String(100))
    enteringorganizationdesc = mapped_column(String(100))
    updatedon = mapped_column(DateTime)
    actioncode = mapped_column(String(3))
    externalid = mapped_column(String(100))
    update_date = mapped_column(DateTime, index=True)
    repository_update_date = mapped_column(DateTime, index=True)

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

    result_items:Mapped["ResultItem"] = relationship(
        "ResultItem",
        lazy=GLOBAL_LAZY,
        back_populates="order",
        cascade="all, delete-orphan",
    )


class ResultItem(Base):
    __tablename__ = "resultitem"

    id = mapped_column(String, primary_key=True)

    order_id = mapped_column("orderid", String, ForeignKey("laborder.id"))
    creation_date = mapped_column(DateTime, nullable=False, server_default=text("now()"))
    resulttype = mapped_column(String(2))
    serviceidcode = mapped_column(String(100))
    serviceidcodestd = mapped_column(String(100))
    serviceiddesc = mapped_column(String(100))
    subid = mapped_column(String(50))
    resultvalue = mapped_column(String(20))
    resultvalueunits = mapped_column(String(30))
    referencerange = mapped_column(String(30))
    interpretationcodes = mapped_column(String(50))
    status = mapped_column(String(5))
    observationtime = mapped_column(DateTime)
    commenttext = mapped_column(String(1000))
    referencecomment = mapped_column(String(1000))
    prepost = mapped_column(String(4))
    enteredon = mapped_column(DateTime)
    updatedon = mapped_column(DateTime)
    actioncode = mapped_column(String(3))
    externalid = mapped_column(String(100))
    update_date = mapped_column(DateTime)

    # Proxies

    pid = association_proxy("order", "pid")

    # Synonyms

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

    order:Mapped["LabOrder"] = relationship(
        "LabOrder", back_populates="result_items"
    )

    # Relationships

    order: Mapped[List[LabOrder]] = relationship(
        "LabOrder", back_populates="result_items"
    )


class PVData(Base):
    __tablename__ = "pvdata"

    id = mapped_column(String, ForeignKey("patientrecord.pid"), primary_key=True)

    creation_date = mapped_column(DateTime, nullable=False, server_default=text("now()"))
    update_date = mapped_column(DateTime)

    diagnosisdate = mapped_column(Date)

    bloodgroup = mapped_column(String(10))

    rrtstatus = mapped_column(String(100))
    tpstatus = mapped_column(String(100))

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

    did = mapped_column(Integer, primary_key=True)

    pid = mapped_column(String, ForeignKey("patientrecord.pid"))
    creation_date = mapped_column(DateTime, nullable=False, server_default=text("now()"))
    observationtime = mapped_column(DateTime)
    serviceidcode = mapped_column(String(100))
    update_date = mapped_column(DateTime)

    # Synonyms

    observation_time: Mapped[datetime.datetime] = synonym("observationtime")
    service_id: Mapped[str] = synonym("serviceidcode")


class Treatment(Base):
    __tablename__ = "treatment"

    id = mapped_column(String, primary_key=True)
    pid = mapped_column(String, ForeignKey("patientrecord.pid"))

    creation_date = mapped_column(DateTime, nullable=False, server_default=text("now()"))
    idx = mapped_column(Integer)
    encounternumber = mapped_column(String(100))
    encountertype = mapped_column(String(100))
    fromtime = mapped_column(DateTime)
    totime = mapped_column(DateTime)
    admittingcliniciancode = mapped_column(String(100))
    admittingcliniciancodestd = mapped_column(String(100))
    admittingcliniciandesc = mapped_column(String(100))
    admitreasoncode = mapped_column(String(100))
    admitreasoncodestd = mapped_column(String(100))
    admitreasondesc = mapped_column(String(100))
    admissionsourcecode = mapped_column(String(100))
    admissionsourcecodestd = mapped_column(String(100))
    admissionsourcedesc = mapped_column(String(100))
    dischargereasoncode = mapped_column(String(100))
    dischargereasoncodestd = mapped_column(String(100))
    dischargereasondesc = mapped_column(String(100))
    dischargelocationcode = mapped_column(String(100))
    dischargelocationcodestd = mapped_column(String(100))
    dischargelocationdesc = mapped_column(String(100))
    healthcarefacilitycode = mapped_column(String(100))
    healthcarefacilitycodestd = mapped_column(String(100))
    healthcarefacilitydesc = mapped_column(String(100))
    enteredatcode = mapped_column(String(100))
    enteredatcodestd = mapped_column(String(100))
    enteredatdesc = mapped_column(String(100))
    visitdescription = mapped_column(String(100))
    updatedon = mapped_column(DateTime)
    actioncode = mapped_column(String(3))
    externalid = mapped_column(String(100))
    hdp01 = mapped_column(String(255))
    hdp02 = mapped_column(String(255))
    hdp03 = mapped_column(String(255))
    hdp04 = mapped_column(String(255))
    qbl05 = mapped_column(String(255))
    qbl06 = mapped_column(String(255))
    qbl07 = mapped_column(String(255))
    erf61 = mapped_column(String(255))
    pat35 = mapped_column(String(255))
    update_date = mapped_column(DateTime)

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

    id = mapped_column(String, primary_key=True)
    pid = mapped_column(String, ForeignKey("patientrecord.pid"))

    idx = mapped_column(Integer)
    creation_date = mapped_column(DateTime, nullable=False, server_default=text("now()"))
    encounternumber = mapped_column(String(100))
    encountertype = mapped_column(String(100))
    fromtime = mapped_column(DateTime)
    totime = mapped_column(DateTime)
    admittingcliniciancode = mapped_column(String(100))
    admittingcliniciancodestd = mapped_column(String(100))
    admittingcliniciandesc = mapped_column(String(100))
    admitreasoncode = mapped_column(String(100))
    admitreasoncodestd = mapped_column(String(100))
    admitreasondesc = mapped_column(String(100))
    admissionsourcecode = mapped_column(String(100))
    admissionsourcecodestd = mapped_column(String(100))
    admissionsourcedesc = mapped_column(String(100))
    dischargereasoncode = mapped_column(String(100))
    dischargereasoncodestd = mapped_column(String(100))
    dischargereasondesc = mapped_column(String(100))
    dischargelocationcode = mapped_column(String(100))
    dischargelocationcodestd = mapped_column(String(100))
    dischargelocationdesc = mapped_column(String(100))
    healthcarefacilitycode = mapped_column(String(100))
    healthcarefacilitycodestd = mapped_column(String(100))
    healthcarefacilitydesc = mapped_column(String(100))
    enteredatcode = mapped_column(String(100))
    enteredatcodestd = mapped_column(String(100))
    enteredatdesc = mapped_column(String(100))
    visitdescription = mapped_column(String(100))
    updatedon = mapped_column(DateTime)
    actioncode = mapped_column(String(3))
    externalid = mapped_column(String(100))
    update_date = mapped_column(DateTime)


class Code(Base):
    __tablename__ = "code_list"

    coding_standard = mapped_column(String(256), primary_key=True)
    code = mapped_column(String(256), primary_key=True)
    creation_date = mapped_column(DateTime, nullable=False, server_default=text("now()"))
    description = mapped_column(String(256))
    object_type = mapped_column(String(256))
    update_date = mapped_column(DateTime)
    units = mapped_column(String(256))
    pkb_reference_range = mapped_column(String(10))
    pkb_comment = mapped_column(String(365))


class CodeExclusion(Base):
    __tablename__ = "code_exclusion"

    coding_standard = mapped_column(String, primary_key=True)
    code = mapped_column(String, primary_key=True)
    system = mapped_column(String, primary_key=True)


class CodeMap(Base):
    __tablename__ = "code_map"

    source_coding_standard = mapped_column(String(256), primary_key=True)
    source_code = mapped_column(String(256), primary_key=True)
    destination_coding_standard = mapped_column(String(256), primary_key=True)
    destination_code = mapped_column(String(256), primary_key=True)

    creation_date = mapped_column(DateTime, nullable=False, server_default=text("now()"))
    update_date = mapped_column(DateTime)


class Facility(Base):
    __tablename__ = "facility"

    code = mapped_column("code", String, primary_key=True)
    creation_date = mapped_column(DateTime, nullable=False, server_default=text("now()"))
    pkb_out = mapped_column(Boolean, server_default=text("false"))
    pkb_in = mapped_column(Boolean, server_default=text("false"))
    pkb_msg_exclusions = mapped_column(ARRAY(Text()))
    update_date = mapped_column(DateTime)

    # Proxies

    description = association_proxy("code_info", "description")

    # Relationships

    code_info = relationship(
        "Code",
        primaryjoin="and_(remote(Code.coding_standard)=='RR1+', foreign(Facility.code)==remote(Code.code))",
    )


class RRCodes(Base):
    __tablename__ = "rr_codes"

    id = mapped_column(String, primary_key=True)
    rr_code = mapped_column("rr_code", String, primary_key=True)

    description_1 = mapped_column(String(255))
    description_2 = mapped_column(String(70))
    description_3 = mapped_column(String(60))

    old_value = mapped_column(String(10))
    old_value_2 = mapped_column(String(10))
    new_value = mapped_column(String(10))


class Locations(Base):
    __tablename__ = "locations"

    centre_code = mapped_column(String(10), primary_key=True)
    centre_name = mapped_column(String(255))
    country_code = mapped_column(String(6))
    region_code = mapped_column(String(10))
    paed_unit = mapped_column(Integer)


class RRDataDefinition(Base):
    __tablename__ = "rr_data_definition"

    upload_key = mapped_column(String(5), primary_key=True)

    table_name = mapped_column("TABLE_NAME", String(30), nullable=False)
    feild_name = mapped_column(String(30), nullable=False)
    code_id = mapped_column(String(10))
    mandatory = mapped_column(Numeric(1, 0))

    type = mapped_column("TYPE", String(1))

    alt_constraint = mapped_column(String(30))
    alt_desc = mapped_column(String(30))
    extra_val = mapped_column(String(1))
    error_type = mapped_column(Integer)
    paed_mand = mapped_column(Numeric(1, 0))
    ckd5_mand_numeric = mapped_column("ckd5_mand", Numeric(1, 0))
    dependant_field = mapped_column(String(30))
    alt_validation = mapped_column(String(30))

    file_prefix = mapped_column(String(20))

    load_min = mapped_column(Numeric(38, 4))
    load_max = mapped_column(Numeric(38, 4))
    remove_min = mapped_column(Numeric(38, 4))
    remove_max = mapped_column(Numeric(38, 4))
    in_month = mapped_column(Numeric(1, 0))
    aki_mand = mapped_column(Numeric(1, 0))
    rrt_mand = mapped_column(Numeric(1, 0))
    cons_mand = mapped_column(Numeric(1, 0))
    ckd4_mand = mapped_column(Numeric(1, 0))
    valid_before_dob = mapped_column(Numeric(1, 0))
    valid_after_dod = mapped_column(Numeric(1, 0))
    in_quarter = mapped_column(Numeric(1, 0))

    # Synonyms

    code_type: Mapped[str] = synonym("type")


class ModalityCodes(Base):
    __tablename__ = "modality_codes"

    registry_code = mapped_column(String(8), primary_key=True)

    registry_code_desc = mapped_column(String(100))
    registry_code_type = mapped_column(String(3), nullable=False)
    acute = mapped_column(BIT(1), nullable=False)
    transfer_in = mapped_column(BIT(1), nullable=False)
    ckd = mapped_column(BIT(1), nullable=False)
    cons = mapped_column(BIT(1), nullable=False)
    rrt = mapped_column(BIT(1), nullable=False)
    equiv_modality = mapped_column(String(8))
    end_of_care = mapped_column(BIT(1), nullable=False)
    is_imprecise = mapped_column(BIT(1), nullable=False)
    nhsbt_transplant_type = mapped_column(String(4))
    transfer_out = mapped_column(BIT(1))


class SatelliteMap(Base):
    __tablename__ = "satellite_map"

    satellite_code = mapped_column(String(10), primary_key=True)
    main_unit_code = mapped_column(String(10), primary_key=True)

    creation_date = mapped_column(DateTime, nullable=False, server_default=text("now()"))
    update_date = mapped_column(DateTime)
