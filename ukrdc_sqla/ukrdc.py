"""Models which relate to the main UKRDC database"""
import datetime
from typing import List, Optional

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    LargeBinary,
    MetaData,
    String,
)
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Mapped, relationship, synonym
from sqlalchemy.schema import PrimaryKeyConstraint

metadata = MetaData()
Base = declarative_base(metadata=metadata)

GLOBAL_LAZY = "dynamic"


class PatientRecord(Base):
    __tablename__ = "patientrecord"

    pid = Column(String, primary_key=True)
    localpatientid = Column("localpatientid", String)
    ukrdcid = Column("ukrdcid", String)

    sendingfacility = Column("sendingfacility", String)
    sendingextract = Column("sendingextract", String)

    extracttime = Column("extracttime", DateTime)
    extract_time: Mapped[datetime.datetime] = synonym("extracttime")

    creation_date = Column("creation_date", DateTime)
    update_date = Column("update_date", DateTime)

    repositorycreationdate = Column("repositorycreationdate", DateTime)
    repository_creation_date: Mapped[datetime.datetime] = synonym(
        "repositorycreationdate"
    )

    repositoryupdatedate = Column("repositoryupdatedate", DateTime)
    repository_update_date: Mapped[datetime.datetime] = synonym("repositoryupdatedate")

    patient: Mapped["Patient"] = relationship(
        "Patient", backref="record", uselist=False, cascade="all, delete-orphan"
    )

    lab_orders: Mapped[List["LabOrder"]] = relationship(
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
    observations: Mapped[List["Observation"]] = relationship(
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
    renaldiagnoses: Mapped[List["RenalDiagnosis"]] = relationship(
        "RenalDiagnosis", lazy=GLOBAL_LAZY, cascade="all, delete-orphan"
    )
    medications: Mapped[List["Medication"]] = relationship(
        "Medication", lazy=GLOBAL_LAZY, cascade="all, delete-orphan"
    )
    dialysis_sessions: Mapped[List["DialysisSession"]] = relationship(
        "DialysisSession", lazy=GLOBAL_LAZY, cascade="all, delete-orphan"
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
    pvdata = relationship("PVData", uselist=False, cascade="all, delete-orphan")
    pvdelete = relationship("PVDelete", lazy=GLOBAL_LAZY, cascade="all, delete-orphan")

    def __str__(self):
        return (
            f"{self.__class__.__name__}({self.pid}) <"
            f"UKRDCID:{self.ukrdcid} CREATED:{self.repository_creation_date}"
            f">"
        )


class Patient(Base):
    __tablename__ = "patient"

    pid = Column(String, ForeignKey("patientrecord.pid"), primary_key=True)

    birthtime = Column("birthtime", DateTime)
    birth_time: Mapped[datetime.datetime] = synonym("birthtime")

    deathtime = Column("deathtime", DateTime)
    death_time: Mapped[datetime.datetime] = synonym("deathtime")

    gender = Column("gender", String)

    countryofbirth = Column("countryofbirth", String)
    country_of_birth: Mapped[str] = synonym("countryofbirth")

    ethnicgroupcode = Column("ethnicgroupcode", String)
    ethnic_group_code: Mapped[str] = synonym("ethnicgroupcode")

    ethnicgroupcodestd = Column("ethnicgroupcodestd", String)
    ethnic_group_code_std = synonym("ethnicgroupcodestd")

    ethnicgroupdesc = Column("ethnicgroupdesc", String)
    ethnic_group_description: Mapped[str] = synonym("ethnicgroupdesc")

    persontocontactname = Column("persontocontactname", String)
    person_to_contact_name: Mapped[str] = synonym("persontocontactname")

    persontocontact_contactnumber = Column("persontocontact_contactnumber", String)
    person_to_contact_number: Mapped[str] = synonym("persontocontact_contactnumber")

    persontocontact_relationship = Column("persontocontact_relationship", String)
    person_to_contact_relationship: Mapped[str] = synonym(
        "persontocontact_relationship"
    )

    persontocontact_contactnumbercomments = Column(
        "persontocontact_contactnumbercomments", String
    )
    person_to_contact_number_comments: Mapped[str] = synonym(
        "person_to_contact_number_comments"
    )

    persontocontact_contactnumbertype = Column(
        "persontocontact_contactnumbertype", String
    )
    person_to_contact_number_type: Mapped[str] = synonym(
        "persontocontact_contactnumbertype"
    )

    occupationcode = Column("occupationcode", String)
    occupation_code: Mapped[str] = synonym("occupationcode")

    occupationcodestd = Column("occupationcodestd", String)
    occupation_codestd: Mapped[str] = synonym("occupationcodestd")

    occupationdesc = Column("occupationdesc", String)
    occupation_description: Mapped[str] = synonym("occupationdesc")

    primarylanguagecode = Column("primarylanguagecode", String)
    primary_language: Mapped[str] = synonym("primarylanguagecode")

    primarylanguagecodestd = Column("primarylanguagecodestd", String)
    primary_language_codestd: Mapped[str] = synonym("primarylanguagecodestd")

    primarylanguagedesc = Column("primarylanguagedesc", String)
    primary_language_description: Mapped[str] = synonym("primarylanguagedesc")

    death = Column("death", Boolean)
    dead: Mapped[bool] = synonym("death")

    updatedon = Column("updatedon", DateTime)
    updated_on: Mapped[datetime.datetime] = synonym("updatedon")

    bloodgroup = Column("bloodgroup", String)
    bloodrhesus = Column("bloodrhesus", String)

    numbers: Mapped[List["PatientNumber"]] = relationship(
        "PatientNumber",
        backref="patient",
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

    pid = Column(String, ForeignKey("patientrecord.pid"), primary_key=True)

    diagnosistype = Column("diagnosistype", String)
    diagnosis_type: Mapped[str] = synonym("diagnosistype")

    diagnosingcliniciancode = Column("diagnosingcliniciancode", String)
    diagnosing_clinician_code: Mapped[str] = synonym("diagnosingcliniciancode")

    diagnosingcliniciancodestd = Column("diagnosingcliniciancodestd", String)
    diagnosing_clinician_code_std: Mapped[str] = synonym("diagnosingcliniciancodestd")

    diagnosingcliniciandesc = Column("diagnosingcliniciandesc", String)
    diagnosing_clinician_desc: Mapped[str] = synonym("diagnosingcliniciandesc")

    diagnosiscode = Column("diagnosiscode", String)
    diagnosis_code: Mapped[str] = synonym("diagnosiscode")

    diagnosiscodestd = Column("diagnosiscodestd", String)
    diagnosis_code_std: Mapped[str] = synonym("diagnosiscodestd")

    diagnosisdesc = Column("diagnosisdesc", String)
    diagnosis_desc: Mapped[str] = synonym("diagnosisdesc")

    comments = Column("comments", String)

    enteredon = Column("enteredon", DateTime)
    entered_on: Mapped[datetime.datetime] = synonym("enteredon")

    updatedon = Column("updatedon", DateTime)
    updated_on: Mapped[datetime.datetime] = synonym("updatedon")

    actioncode = Column("actioncode", String)
    action_code: Mapped[str] = synonym("actioncode")

    externalid = Column("externalid", String)
    external_id: Mapped[str] = synonym("externalid")


class FamilyDoctor(Base):
    __tablename__ = "familydoctor"

    id = Column(String, ForeignKey("patient.pid"), primary_key=True)

    gpname = Column("gpname", String)
    gpid = Column("gpid", String, ForeignKey("ukrdc_ods_gp_codes.code"))
    gppracticeid = Column("gppracticeid", String, ForeignKey("ukrdc_ods_gp_codes.code"))

    gp_info = relationship("GPInfo", foreign_keys=[gpid], uselist=False)
    gp_practice_info = relationship(
        "GPInfo", foreign_keys=[gppracticeid], uselist=False
    )

    addressuse = Column("addressuse", String)
    fromtime = Column("fromtime", DateTime)
    totime = Column("totime", DateTime)
    street = Column("street", String)
    town = Column("town", String)
    county = Column("county", String)
    postcode = Column("postcode", String)
    countrycode = Column("countrycode", String)
    countrycodestd = Column("countrycodestd", String)
    countrydesc = Column("countrydesc", String)
    contactuse = Column("contactuse", String)
    contactvalue = Column("contactvalue", String)
    email = Column("email", String)
    commenttext = Column("commenttext", String)

    def __str__(self):
        return (
            f"{self.__class__.__name__}({self.id}) <" f"{self.gpname} {self.gpid}" f">"
        )


class GPInfo(Base):
    __tablename__ = "ukrdc_ods_gp_codes"

    code = Column("code", String, primary_key=True)

    name = Column("name", String)
    gpname: Mapped[str] = synonym("name")

    address1 = Column("address1", String)
    street: Mapped[str] = synonym("address1")

    postcode = Column("postcode", String)

    phone = Column("phone", String)
    contactvalue: Mapped[str] = synonym("phone")

    type = Column("type", String)


class SocialHistory(Base):
    __tablename__ = "socialhistory"
    id = Column(String, primary_key=True)
    pid = Column(String, ForeignKey("patientrecord.pid"))


class FamilyHistory(Base):
    __tablename__ = "familyhistory"
    id = Column(String, primary_key=True)
    pid = Column(String, ForeignKey("patientrecord.pid"))


class Observation(Base):
    __tablename__ = "observation"

    id = Column(String, primary_key=True)
    pid = Column(String, ForeignKey("patientrecord.pid"))
    idx = Column(Integer)

    observationtime = Column("observationtime", DateTime)
    observation_time: Mapped[datetime.datetime] = synonym("observationtime")

    observationcode = Column("observationcode", String)
    observation_code: Mapped[str] = synonym("observationcode")

    observationcodestd = Column("observationcodestd", String)
    observation_code_std: Mapped[str] = synonym("observationcodestd")

    observationdesc = Column("observationdesc", String)
    observation_desc: Mapped[str] = synonym("observationdesc")

    observationvalue = Column("observationvalue", String)
    observation_value: Mapped[str] = synonym("observationvalue")

    observationunits = Column("observationunits", String)
    observation_units: Mapped[str] = synonym("observationunits")

    commenttext = Column("commenttext", String)
    comment_text: Mapped[str] = synonym("commenttext")

    cliniciancode = Column("cliniciancode", String)
    clinician_code: Mapped[str] = synonym("cliniciancode")

    cliniciancodestd = Column("cliniciancodestd", String)
    clinician_code_std: Mapped[str] = synonym("cliniciancodestd")

    cliniciandesc = Column("cliniciandesc", String)
    clinician_desc: Mapped[str] = synonym("cliniciandesc")

    enteredatcode = Column("enteredatcode", String)
    entered_at: Mapped[str] = synonym("enteredatcode")

    enteredatdesc = Column("enteredatdesc", String)
    entered_at_description: Mapped[str] = synonym("enteredatdesc")

    enteringorganizationcode = Column("enteringorganizationcode", String)
    entering_organization_code: Mapped[str] = synonym("enteringorganizationcode")

    enteringorganizationdesc = Column("enteringorganizationdesc", String)
    entering_organization_description: Mapped[str] = synonym("enteringorganizationdesc")

    updatedon = Column("updatedon", DateTime)
    updated_on: Mapped[datetime.datetime] = synonym("updatedon")

    actioncode = Column("actioncode", String)
    action_code: Mapped[str] = synonym("actioncode")

    externalid = Column("externalid", String)
    external_id: Mapped[str] = synonym("externalid")

    prepost = Column("prepost", String)
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
    idx = Column(Integer)

    programname = Column("programname", String)
    program_name: Mapped[str] = synonym("programname")

    programdescription = Column("programdescription", String)
    program_description: Mapped[str] = synonym("programdescription")

    enteredbycode = Column("enteredbycode", String)
    entered_by_code: Mapped[str] = synonym("enteredbycode")

    enteredbycodestd = Column("enteredbycodestd", String)
    entered_by_code_std: Mapped[str] = synonym("enteredbycodestd")

    enteredbydesc = Column("enteredbydesc", String)
    entered_by_desc: Mapped[str] = synonym("enteredbydesc")

    enteredatcode = Column("enteredatcode", String)
    entered_at_code: Mapped[str] = synonym("enteredatcode")

    enteredatcodestd = Column("enteredatcodestd", String)
    entered_at_code_std: Mapped[str] = synonym("enteredatcodestd")

    enteredatdesc = Column("enteredatdesc", String)
    entered_at_desc: Mapped[str] = synonym("enteredatdesc")

    fromtime = Column("fromtime", Date)
    from_time: Mapped[datetime.date] = synonym("fromtime")

    totime = Column("totime", Date)
    to_time: Mapped[datetime.date] = synonym("totime")

    updatedon = Column("updatedon", DateTime)
    updated_on: Mapped[datetime.datetime] = synonym("updatedon")

    actioncode = Column("actioncode", String)
    action_code: Mapped[str] = synonym("actioncode")

    externalid = Column("externalid", String)
    external_id: Mapped[str] = synonym("externalid")


class Allergy(Base):
    __tablename__ = "allergy"

    id = Column(String, primary_key=True)
    pid = Column(String, ForeignKey("patientrecord.pid"))


class Diagnosis(Base):
    __tablename__ = "diagnosis"

    id = Column(String, primary_key=True)
    pid = Column(String, ForeignKey("patientrecord.pid"))

    diagnosiscode = Column("diagnosiscode", String)
    diagnosis_code: Mapped[str] = synonym("diagnosiscode")

    diagnosiscodestd = Column("diagnosiscodestd", String)
    diagnosis_code_std: Mapped[str] = synonym("diagnosiscodestd")

    diagnosisdesc = Column("diagnosisdesc", String)
    diagnosis_desc: Mapped[str] = synonym("diagnosisdesc")

    identificationtime = Column("identificationtime", DateTime)
    identification_time: Mapped[datetime.datetime] = synonym("identificationtime")

    onsettime = Column("onsettime", DateTime)
    onset_time: Mapped[datetime.datetime] = synonym("onsettime")

    comments = Column(String)


class RenalDiagnosis(Base):
    __tablename__ = "renaldiagnosis"

    pid = Column(String, ForeignKey("patientrecord.pid"), primary_key=True)

    diagnosiscode = Column("diagnosiscode", String)
    diagnosis_code: Mapped[str] = synonym("diagnosiscode")

    diagnosiscodestd = Column("diagnosiscodestd", String)
    diagnosis_code_std: Mapped[str] = synonym("diagnosiscodestd")

    diagnosisdesc = Column("diagnosisdesc", String)
    diagnosis_desc: Mapped[str] = synonym("diagnosisdesc")

    identificationtime = Column("identificationtime", DateTime)
    identification_time: Mapped[datetime.datetime] = synonym("identificationtime")

    comments = Column(String)


class DialysisSession(Base):
    __tablename__ = "dialysissession"

    id = Column(String, primary_key=True)
    pid = Column(String, ForeignKey("patientrecord.pid"))

    proceduretypecode = Column("proceduretypecode", String)
    procedure_type_code: Mapped[str] = synonym("proceduretypecode")

    proceduretypecodestd = Column("proceduretypecodestd", String)
    procedure_type_code_std: Mapped[str] = synonym("proceduretypecodestd")

    proceduretypedesc = Column("proceduretypedesc", String)
    procedure_type_desc: Mapped[str] = synonym("proceduretypedesc")

    proceduretime = Column("proceduretime", DateTime)
    procedure_time: Mapped[datetime.datetime] = synonym("proceduretime")

    qhd19 = Column(String)
    qhd20 = Column(String)
    qhd21 = Column(String)
    qhd22 = Column(String)
    qhd30 = Column(String)
    qhd31 = Column(String)
    qhd32 = Column(String)
    qhd33 = Column(String)


class Transplant(Base):

    __tablename__ = "transplant"

    id = Column(String, primary_key=True)
    pid = Column(String, ForeignKey("patientrecord.pid"))

    proceduretypecode = Column("proceduretypecode", String)
    procedure_type_code: Mapped[str] = synonym("proceduretypecode")

    proceduretypecodestd = Column("proceduretypecodestd", String)
    procedure_type_code_std: Mapped[str] = synonym("proceduretypecodestd")

    proceduretypedesc = Column("proceduretypedesc", String)
    procedure_type_desc: Mapped[str] = synonym("proceduretypedesc")

    proceduretime = Column("proceduretime", DateTime)
    procedure_time: Mapped[datetime.datetime] = synonym("proceduretime")

    tra64 = Column(String)
    tra65 = Column(String)
    tra66 = Column(DateTime)
    tra69 = Column(DateTime)
    tra76 = Column(DateTime)
    tra77 = Column(String)
    tra78 = Column(String)
    tra79 = Column(String)
    tra8a = Column(String)
    tra81 = Column(String)
    tra82 = Column(String)
    tra83 = Column(String)
    tra84 = Column(String)
    tra85 = Column(String)


class Procedure(Base):
    __tablename__ = "procedure"

    id = Column(String, primary_key=True)
    pid = Column(String, ForeignKey("patientrecord.pid"))


class Encounter(Base):
    __tablename__ = "encounter"

    id = Column(String, primary_key=True)
    pid = Column(String, ForeignKey("patientrecord.pid"))

    fromtime = Column("fromtime", DateTime)
    from_time: Mapped[datetime.datetime] = synonym("fromtime")

    totime = Column("totime", DateTime)
    to_time: Mapped[datetime.datetime] = synonym("totime")


class ProgramMembership(Base):
    __tablename__ = "programmembership"

    id = Column(String, primary_key=True)
    pid = Column(String, ForeignKey("patientrecord.pid"))

    programname = Column("programname", String)
    program_name: Mapped[str] = synonym("programname")

    fromtime = Column("fromtime", Date)
    from_time: Mapped[datetime.date] = synonym("fromtime")

    totime = Column("totime", Date)
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


class Name(Base):
    __tablename__ = "name"

    id = Column(String, primary_key=True)
    pid = Column(String, ForeignKey("patient.pid"))

    nameuse = Column("nameuse", String)
    prefix = Column("prefix", String)
    family = Column("family", String)
    given = Column("given", String)
    othergivennames = Column("othergivennames", String)
    suffix = Column("suffix", String)

    def __str__(self):
        return (
            f"{self.__class__.__name__}({self.pid}) <"
            f"{self.given} {self.family}"
            f">"
        )


class PatientNumber(Base):
    __tablename__ = "patientnumber"

    id = Column(String, primary_key=True)
    pid = Column(String, ForeignKey("patient.pid"))

    patientid = Column("patientid", String)
    organization = Column("organization", String)
    numbertype = Column("numbertype", String)

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

    addressuse = Column("addressuse", String)

    fromtime = Column("fromtime", Date)
    from_time: Mapped[datetime.date] = synonym("fromtime")

    totime = Column("totime", Date)
    to_time: Mapped[datetime.date] = synonym("totime")

    street = Column(String)
    town = Column(String)
    county = Column(String)
    postcode = Column(String)

    countrycode = Column("countrycode", String)
    country_code: Mapped[str] = synonym("countrycode")

    countrycodestd = Column("countrycodestd", String)
    country_code_std: Mapped[str] = synonym("countrycodestd")

    countrydesc = Column("countrydesc", String)
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

    contactuse = Column("contactuse", String)
    use: Mapped[str] = synonym("contactuse")

    contactvalue = Column("contactvalue", String)
    value: Mapped[str] = synonym("contactvalue")

    commenttext = Column(String)

    def __str__(self):
        return f"{self.__class__.__name__}({self.pid}) <{self.use}:{self.value}>"


class Medication(Base):
    __tablename__ = "medication"

    id = Column(String, primary_key=True)
    pid = Column(String, ForeignKey("patientrecord.pid"))
    idx = Column(Integer)

    fromtime = Column("fromtime", DateTime)
    from_time: Mapped[datetime.datetime] = synonym("fromtime")

    totime = Column("totime", DateTime)
    to_time: Mapped[datetime.datetime] = synonym("totime")

    doseuomcode = Column("doseuomcode", String)
    dose_uom_code: Mapped[str] = synonym("doseuomcode")

    doseuomcodestd = Column("doseuomcodestd", String)
    dose_uom_code_std: Mapped[str] = synonym("doseuomcodestd")

    doseuomdesc = Column("doseuomdesc", String)
    dose_uom_description: Mapped[str] = synonym("doseuomdesc")

    dosequantity = Column("dosequantity", String)
    dose_quantity: Mapped[str] = synonym("dosequantity")

    drugproductidcode = Column("drugproductidcode", String)
    drug_product_id_code: Mapped[str] = synonym("drugproductidcode")

    drugproductiddesc = Column("drugproductiddesc", String)
    drug_product_id_description: Mapped[str] = synonym("drugproductiddesc")

    drugproductgeneric = Column("drugproductgeneric", String)
    drug_product_generic: Mapped[str] = synonym("drugproductgeneric")

    enteringorganizationcode = Column("enteringorganizationcode", String)
    entering_organization_code: Mapped[str] = synonym("enteringorganizationcode")

    enteringorganizationdesc = Column("enteringorganizationdesc", String)
    entering_organization_description: Mapped[str] = synonym("enteringorganizationdesc")

    frequency = Column(String)

    commenttext = Column("commenttext", String)
    comment: Mapped[str] = synonym("commenttext")

    routecode = Column("routecode", String)
    route_code: Mapped[str] = synonym("routecode")

    routecodestd = Column("routecodestd", String)
    route_code_std: Mapped[str] = synonym("routecodestd")

    routedesc = Column("routedesc", String)
    route_desc: Mapped[str] = synonym("routedesc")

    externalid = Column("externalid", String)
    external_id: Mapped[str] = synonym("externalid")

    updatedon = Column("updatedon", DateTime)
    updated_on: Mapped[datetime.datetime] = synonym("updatedon")

    repositoryupdatedate = Column("repositoryupdatedate", DateTime)
    repository_update_date: Mapped[datetime.datetime] = synonym("repositoryupdatedate")

    def __str__(self):
        return f"{self.__class__.__name__}({self.pid})"


class Survey(Base):
    __tablename__ = "survey"

    id = Column(String, primary_key=True)
    pid = Column(String, ForeignKey("patientrecord.pid"))
    surveytime = Column(DateTime)
    surveytypecode = Column(String)
    surveytypecodestd = Column(String)
    surveytypedesc = Column(String)
    enteredbycode = Column(String)
    enteredbycodestd = Column(String)
    enteredatcode = Column(String)
    enteredatcodestd = Column(String)
    enteredatdesc = Column(String)
    updatedon = Column(DateTime)
    externalid = Column(String)

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

    questiontypecode = Column(String)
    questiontypecodestd = Column(String)
    questiontypedesc = Column(String)
    response = Column(String)


class Score(Base):
    __tablename__ = "score"

    id = Column(String, primary_key=True)
    surveyid = Column(String, ForeignKey("survey.id"))

    scorevalue = Column("scorevalue", String)
    value: Mapped[str] = synonym("scorevalue")

    scoretypecode = Column(String)
    scoretypecodestd = Column(String)
    scoretypedesc = Column(String)


class Level(Base):
    __tablename__ = "level"

    id = Column(String, primary_key=True)
    surveyid = Column(String, ForeignKey("survey.id"))

    levelvalue = Column("levelvalue", String)
    value: Mapped[str] = synonym("levelvalue")

    leveltypecode = Column(String)
    leveltypecodestd = Column(String)
    leveltypedesc = Column(String)


class Document(Base):
    __tablename__ = "document"

    id = Column(String, primary_key=True)
    pid = Column(String, ForeignKey("patientrecord.pid"))
    idx = Column(Integer)
    documenttime = Column(DateTime)
    notetext = Column(String)
    documenttypecode = Column(String)
    documenttypecodestd = Column(String)
    documenttypedesc = Column(String)

    cliniciancode = Column(String)
    cliniciancodestd = Column(String)
    cliniciandesc = Column(String)
    documentname = Column(String)
    statuscode = Column(String)
    statuscodestd = Column(String)
    statusdesc = Column(String)
    enteredbycode = Column(String)
    enteredbycodestd = Column(String)
    enteredbydesc = Column(String)
    enteredatcode = Column(String)
    enteredatcodestd = Column(String)
    enteredatdesc = Column(String)
    filetype = Column(String)
    filename = Column(String)
    stream = Column(LargeBinary)
    documenturl = Column(String)
    updatedon = Column(DateTime)
    actioncode = Column(String)
    externalid = Column(String)

    update_date = Column(DateTime)
    creation_date = Column(DateTime)

    repositoryupdatedate = Column("repositoryupdatedate", DateTime)
    repository_update_date = synonym("repositoryupdatedate")


class LabOrder(Base):
    __tablename__ = "laborder"

    id = Column(String, primary_key=True)
    pid = Column(String, ForeignKey("patientrecord.pid"))

    receivinglocationcode = Column("receivinglocationcode", String)
    receiving_location: Mapped[str] = synonym("receivinglocationcode")

    receivinglocationdesc = Column("receivinglocationdesc", String)
    receiving_location_description: Mapped[str] = synonym("receivinglocationdesc")

    receivinglocationcodestd = Column("receivinglocationcodestd", String)
    receiving_location_code_std: Mapped[str] = synonym("receivinglocationcodestd")

    placerid = Column("placerid", String)
    placer_id: Mapped[str] = synonym("placerid")

    fillerid = Column("fillerid", String)
    filler_id: Mapped[str] = synonym("fillerid")

    orderedbycode = Column("orderedbycode", String)
    ordered_by: Mapped[str] = synonym("orderedbycode")

    orderedbydesc = Column("orderedbydesc", String)
    ordered_by_description: Mapped[str] = synonym("orderedbydesc")

    orderedbycodestd = Column("orderedbycodestd", String)
    ordered_by_code_std: Mapped[str] = synonym("orderedbycodestd")

    orderitemcode = Column("orderitemcode", String)
    order_item: Mapped[str] = synonym("orderitemcode")

    orderitemdesc = Column("orderitemdesc", String)
    order_item_description: Mapped[str] = synonym("orderitemdesc")

    orderitemcodestd = Column("orderitemcodestd", String)
    order_item_code_std: Mapped[str] = synonym("orderitemcodestd")

    ordercategorycode = Column("ordercategorycode", String)
    order_category: Mapped[str] = synonym("ordercategorycode")

    ordercategorydesc = Column("ordercategorydesc", String)
    order_category_description: Mapped[str] = synonym("ordercategorydesc")

    ordercategorycodestd = Column("ordercategorycodestd", String)
    order_category_code_std: Mapped[str] = synonym("ordercategorycodestd")

    specimencollectedtime = Column("specimencollectedtime", DateTime)
    specimen_collected_time: Mapped[datetime.datetime] = synonym(
        "specimencollectedtime"
    )

    specimenreceivedtime = Column("specimenreceivedtime", DateTime)
    specimen_received_time: Mapped[datetime.datetime] = synonym("specimenreceivedtime")

    status = Column(String)

    prioritycode = Column("prioritycode", String)
    priority: Mapped[str] = synonym("prioritycode")

    prioritydesc = Column("prioritydesc", String)
    priority_description: Mapped[str] = synonym("prioritydesc")

    prioritycodestd = Column("prioritycodestd", String)
    priority_code_std: Mapped[str] = synonym("prioritycodestd")

    specimensource = Column("specimensource", String)
    specimen_source: Mapped[str] = synonym("specimensource")

    duration = Column(String)

    patientclasscode = Column("patientclasscode", String)
    patient_class: Mapped[str] = synonym("patientclasscode")

    patientclassdesc = Column("patientclassdesc", String)
    patient_class_description: Mapped[str] = synonym("patientclassdesc")

    patientclasscodestd = Column("patientclasscodestd", String)
    patient_class_code_std: Mapped[str] = synonym("patientclasscodestd")

    enteredon = Column("enteredon", DateTime)
    entered_on: Mapped[datetime.datetime] = synonym("enteredon")

    enteredatcode = Column("enteredatcode", String)
    entered_at: Mapped[str] = synonym("enteredatcode")

    enteredatdesc = Column("enteredatdesc", String)
    entered_at_description: Mapped[str] = synonym("enteredatdesc")

    externalid = Column("externalid", String)
    external_id: Mapped[str] = synonym("externalid")

    enteringorganizationcode = Column("enteringorganizationcode", String)
    entering_organization_code: Mapped[str] = synonym("enteringorganizationcode")

    enteringorganizationdesc = Column("enteringorganizationdesc", String)
    entering_organization_description: Mapped[str] = synonym("enteringorganizationdesc")

    enteringorganizationcodestd = Column("enteringorganizationcodestd", String)
    entering_organization_code_std: Mapped[str] = synonym("enteringorganizationcodestd")

    updatedon = Column("updatedon", DateTime)

    creation_date = Column("creation_date", DateTime)
    update_date = Column("update_date", DateTime)
    repository_update_date = Column("repository_update_date", DateTime)

    result_items: Mapped[List["ResultItem"]] = relationship(
        "ResultItem",
        lazy=GLOBAL_LAZY,
        back_populates="order",
        cascade="all, delete-orphan",
    )


class ResultItem(Base):
    __tablename__ = "resultitem"

    id = Column(String, primary_key=True)
    order_id = Column("orderid", String, ForeignKey("laborder.id"))

    resulttype = Column("resulttype", String)
    result_type: Mapped[str] = synonym("resulttype")

    enteredon = Column("enteredon", DateTime)
    entered_on: Mapped[datetime.datetime] = synonym("enteredon")

    prepost = Column("prepost", String)
    pre_post: Mapped[str] = synonym("prepost")

    serviceidcode = Column("serviceidcode", String)
    service_id: Mapped[str] = synonym("serviceidcode")

    serviceidcodestd = Column("serviceidcodestd", String)
    service_id_std: Mapped[str] = synonym("serviceidcodestd")

    serviceiddesc = Column("serviceiddesc", String)
    service_id_description: Mapped[str] = synonym("serviceiddesc")

    subid = Column("subid", String)
    sub_id: Mapped[str] = synonym("subid")

    resultvalue = Column("resultvalue", String)
    value: Mapped[str] = synonym("resultvalue")

    resultvalueunits = Column("resultvalueunits", String)
    value_units: Mapped[str] = synonym("resultvalueunits")

    referencerange = Column("referencerange", String)
    reference_range: Mapped[str] = synonym("referencerange")

    interpretationcodes = Column("interpretationcodes", String)
    interpretation_codes: Mapped[str] = synonym("interpretationcodes")

    status = Column(String)

    observationtime = Column("observationtime", DateTime)
    observation_time: Mapped[datetime.datetime] = synonym("observationtime")

    commenttext = Column("commenttext", String)
    comments: Mapped[str] = synonym("commenttext")

    referencecomment = Column("referencecomment", String)
    reference_comment: Mapped[str] = synonym("referencecomment")

    order: LabOrder = relationship("LabOrder", back_populates="result_items")

    pid = association_proxy("order", "pid")


class PVData(Base):
    __tablename__ = "pvdata"

    id = Column(String, ForeignKey("patientrecord.pid"), primary_key=True)
    rrtstatus = Column(String)
    tpstatus = Column(String)
    diagnosisdate = Column(Date)
    bloodgroup = Column(String)
    update_date = Column(DateTime)
    creation_date = Column(DateTime)

    def __str__(self):
        return f"{self.__class__.__name__}({self.id})"


class PVDelete(Base):
    __tablename__ = "pvdelete"

    did = Column(Integer, primary_key=True)
    pid = Column(String, ForeignKey("patientrecord.pid"))

    observationtime = Column("observationtime", DateTime)
    observation_time: Mapped[datetime.datetime] = synonym("observationtime")

    serviceidcode = Column("serviceidcode", String)
    service_id: Mapped[str] = synonym("serviceidcode")


class Treatment(Base):
    __tablename__ = "treatment"

    id = Column(String, primary_key=True)
    pid = Column(String, ForeignKey("patientrecord.pid"))
    idx = Column(Integer)

    encounternumber = Column("encounternumber", String)
    encounter_number: Mapped[str] = synonym("encounternumber")

    encountertype = Column("encountertype", String)
    encounter_type: Mapped[str] = synonym("encountertype")

    fromtime = Column("fromtime", DateTime)
    from_time: Mapped[datetime.datetime] = synonym("fromtime")

    totime = Column("totime", DateTime)
    to_time: Mapped[datetime.datetime] = synonym("totime")

    admittingcliniciancode = Column("admittingcliniciancode", String)
    admitting_clinician_code: Mapped[str] = synonym("admittingcliniciancode")

    admittingcliniciancodestd = Column("admittingcliniciancodestd", String)
    admitting_clinician_code_std: Mapped[str] = synonym("admittingcliniciancodestd")

    admittingcliniciandesc = Column("admittingcliniciandesc", String)
    admitting_clinician_desc: Mapped[str] = synonym("admittingcliniciandesc")

    admissionsourcecode = Column("admissionsourcecode", String)
    admission_source_code: Mapped[str] = synonym("admissionsourcecode")

    admissionsourcecodestd = Column("admissionsourcecodestd", String)
    admission_source_code_std: Mapped[str] = synonym("admissionsourcecodestd")

    admissionsourcedesc = Column("admissionsourcedesc", String)
    admission_source_desc: Mapped[str] = synonym("admissionsourcedesc")

    admitreasoncode = Column("admitreasoncode", String)
    admit_reason_code: Mapped[str] = synonym("admitreasoncode")

    admitreasoncodestd = Column("admitreasoncodestd", String)
    admit_reason_code_std: Mapped[str] = synonym("admitreasoncodestd")

    admit_reason_code_item = relationship(
        "Code",
        primaryjoin="and_(foreign(Treatment.admit_reason_code_std)==remote(Code.coding_standard), foreign(Treatment.admit_reason_code)==remote(Code.code))",
    )
    admit_reason_desc = association_proxy("admit_reason_code_item", "description")

    dischargereasoncode = Column("dischargereasoncode", String)
    discharge_reason_code: Mapped[str] = synonym("dischargereasoncode")

    dischargereasoncodestd = Column("dischargereasoncodestd", String)
    discharge_reason_code_std: Mapped[str] = synonym("dischargereasoncodestd")

    discharge_reason_code_item = relationship(
        "Code",
        primaryjoin="and_(foreign(Treatment.discharge_reason_code_std)==remote(Code.coding_standard), foreign(Treatment.discharge_reason_code)==remote(Code.code))",
    )
    discharge_reason_desc = association_proxy(
        "discharge_reason_code_item", "description"
    )

    dischargelocationcode = Column("dischargelocationcode", String)
    discharge_location_code: Mapped[str] = synonym("dischargelocationcode")

    dischargelocationcodestd = Column("dischargelocationcodestd", String)
    discharge_location_code_std: Mapped[str] = synonym("dischargelocationcodestd")

    dischargelocationdesc = Column("dischargelocationdesc", String)
    discharge_location_desc: Mapped[str] = synonym("dischargelocationdesc")

    healthcarefacilitycode = Column("healthcarefacilitycode", String)
    health_care_facility_code: Mapped[str] = synonym("healthcarefacilitycode")

    healthcarefacilitycodestd = Column("healthcarefacilitycodestd", String)
    health_care_facility_code_std: Mapped[str] = synonym("healthcarefacilitycodestd")

    healthcarefacilitydesc = Column("healthcarefacilitydesc", String)
    health_care_facility_desc: Mapped[str] = synonym("healthcarefacilitydesc")

    enteredatcode = Column("enteredatcode", String)
    entered_at_code: Mapped[str] = synonym("enteredatcode")

    visitdescription = Column("visitdescription", String)
    visit_description: Mapped[str] = synonym("visitdescription")

    updatedon = Column("updatedon", DateTime)
    updated_on: Mapped[datetime.datetime] = synonym("updatedon")

    actioncode = Column("actioncode", String)
    action_code: Mapped[str] = synonym("actioncode")

    externalid = Column("externalid", String)
    external_id: Mapped[str] = synonym("externalid")

    hdp01 = Column("hdp01", String)
    hdp02 = Column("hdp02", String)
    hdp03 = Column("hdp03", String)
    hdp04 = Column("hdp04", String)
    qbl05 = Column("qbl05", String)
    qbl06 = Column("qbl06", String)
    qbl07 = Column("qbl07", String)
    erf61 = Column("erf61", String)
    pat35 = Column("pat35", String)


class Code(Base):
    __tablename__ = "code_list"

    coding_standard = Column("coding_standard", String, primary_key=True)
    code = Column("code", String, primary_key=True)
    description = Column("description", String)
    object_type = Column("object_type", String)
    creation_date = Column("creation_date", DateTime)
    update_date = Column("update_date", DateTime)
    units = Column("units", String)


class CodeExclusion(Base):
    __tablename__ = "code_exclusion"

    coding_standard = Column("coding_standard", String, primary_key=True)
    code = Column("code", String, primary_key=True)
    system = Column("system", String, primary_key=True)


class CodeMap(Base):
    __tablename__ = "code_map"

    source_coding_standard = Column("source_coding_standard", String, primary_key=True)
    source_code = Column("source_code", String, primary_key=True)
    destination_coding_standard = Column(
        "destination_coding_standard", String, primary_key=True
    )
    destination_code = Column("destination_code", String, primary_key=True)

    creation_date = Column("creation_date", DateTime)
    update_date = Column("update_date", DateTime)


class Facility(Base):
    __tablename__ = "facility"

    code = Column("code", String, primary_key=True)
    pkb_out = Column("pkb_out", Boolean)
    pkb_in = Column("pkb_in", Boolean)
    pkb_msg_exclusions = Column("pkb_msg_exclusions", ARRAY(String))

    code_info = relationship(
        "Code",
        primaryjoin="and_(remote(Code.coding_standard)=='RR1+', foreign(Facility.code)==remote(Code.code))",
    )
    description = association_proxy("code_info", "description")


class RRCodes(Base):
    __tablename__ = "rr_codes"
    id = Column(String, primary_key=True)
    rr_code = Column("rr_code", String, primary_key=True)
    description_1 = Column("description_1", String)
    description_2 = Column("description_2", String)
    description_3 = Column("description_3", String)
    old_value = Column("old_value", String)
    old_value_2 = Column("old_value_2", String)
    new_value = Column("new_value", String)
    __table_args__ = (PrimaryKeyConstraint(id, rr_code), {})


class Locations(Base):
    __tablename__ = "locations"
    centre_code = Column("centre_code", String, primary_key=True)
    centre_name = Column("centre_name", String)
    country_code = Column("country_code", String)
    region_code = Column("region_code", String)
    paed_unit = Column("paed_unit", String)


class RRDataDefinition(Base):
    __tablename__ = "rr_data_definition"
    upload_key = Column("upload_key", String, primary_key=True)
    table_name = Column("table_name", String)
    feild_name = Column("feild_name", String)
    code_id = Column("code_id", String)
    mandatory = Column("mandatory", Float)

    type = Column("type", String)
    code_type: Mapped[str] = synonym("type")

    alt_constraint = Column("alt_constraint", String)
    alt_desc = Column("alt_desc", String)
    extra_val = Column("extra_val", String)
    error_type = Column("error_type", Integer)
    paed_mand = Column("paed_mand", Float)
    ckd5_mand_numeric = Column("ckd5_mand_numeric", Float)
    dependant_field = Column("dependant_field", String)
    alt_validation = Column("alt_validation", String)

    file_prefix = Column("file_prefix", String)

    load_min = Column("load_min", Float)
    load_max = Column("load_max", Float)
    remove_min = Column("remove_min", Float)
    remove_max = Column("remove_max", Float)
    in_month = Column("in_month", Float)
    aki_mand = Column("aki_mand", Float)
    rrt_mand = Column("rrt_mand", Float)
    cons_mand = Column("cons_mand", Float)
    ckd4_mand = Column("ckd4_mand", Float)
    valid_before_dob = Column("valid_before_dob", Float)
    valid_after_dod = Column("valid_after_dod", Float)
    in_quarter = Column("in_quarter", Float)


class ModalityCodes(Base):
    __tablename__ = "modality_codes"
    registry_code = Column("registry_code", String, primary_key=True)
    registry_code_desc = Column("registry_code_desc", String)
    registry_code_type = Column("registry_code_type", String)
    acute = Column("acute", Boolean)
    transfer_in = Column("transfer_in", Boolean)
    ckd = Column("ckd", Boolean)
    cons = Column("cons", Boolean)
    rrt = Column("rrt", Boolean)
    equiv_modality = Column("equiv_modality", String)
    end_of_care = Column("end_of_care", Boolean)
    is_imprecise = Column("is_imprecise", Boolean)
    nhsbt_transplant_type = Column("nhsbt_transplant_type", String)
    transfer_out = Column("transfer_out", Boolean)
