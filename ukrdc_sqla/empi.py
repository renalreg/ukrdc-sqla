"""Models which relate to the EMPI (JTRACE) database"""

import datetime
from typing import List

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    MetaData,
    String,
)

from sqlalchemy.orm import Mapped, relationship, synonym, declarative_base

metadata = MetaData()
Base = declarative_base(metadata=metadata)


class MasterRecord(Base):
    __tablename__ = "masterrecord"

    id = Column(Integer, primary_key=True)

    lastupdated = Column("lastupdated", DateTime, nullable=False)
    last_updated: Mapped[datetime.datetime] = synonym("lastupdated")

    dateofbirth = Column("dateofbirth", Date, nullable=False)
    date_of_birth: Mapped[datetime.date] = synonym("dateofbirth")

    gender = Column("gender", String)
    givenname = Column("givenname", String)
    surname = Column("surname", String)
    nationalid = Column("nationalid", String, nullable=False)

    nationalidtype = Column("nationalidtype", String, nullable=False)
    nationalid_type: Mapped[str] = synonym("nationalidtype")

    status = Column("status", Integer, nullable=False)

    effectivedate = Column("effectivedate", DateTime, nullable=False)
    effective_date: Mapped[datetime.datetime] = synonym("effectivedate")

    creationdate = Column("creationdate", DateTime)
    creation_date: Mapped[datetime.datetime] = synonym("creationdate")

    link_records: Mapped[List["LinkRecord"]] = relationship(
        "LinkRecord", back_populates="master_record", cascade="all, delete-orphan"
    )
    work_items: Mapped[List["WorkItem"]] = relationship(
        "WorkItem", back_populates="master_record", cascade="all, delete-orphan"
    )

    def __str__(self):
        return (
            f"MasterRecord({self.id}) <"
            f"{self.givenname} {self.surname} {self.date_of_birth} "
            f"{self.nationalid_type.strip()}:{self.nationalid}"
            f">"
        )


class LinkRecord(Base):
    __tablename__ = "linkrecord"

    id = Column(Integer, primary_key=True)

    personid = Column("personid", Integer, ForeignKey("person.id"), nullable=False)
    person_id: Mapped[int] = synonym("personid")

    masterid = Column(
        "masterid", Integer, ForeignKey("masterrecord.id"), nullable=False
    )
    master_id: Mapped[int] = synonym("masterid")

    linktype = Column("linktype", Integer, nullable=False)
    link_type: Mapped[int] = synonym("linktype")

    linkcode = Column("linkcode", Integer, nullable=False)
    link_code: Mapped[int] = synonym("linkcode")

    linkdesc = Column("linkdesc", String)
    link_desc: Mapped[str] = synonym("linkdesc")

    updatedby = Column("updatedby", String)
    updated_by: Mapped[str] = synonym("updatedby")

    lastupdated = Column("lastupdated", DateTime, nullable=False)
    last_updated: Mapped[datetime.datetime] = synonym("lastupdated")

    person: Mapped["Person"] = relationship("Person", back_populates="link_records")
    master_record: Mapped["MasterRecord"] = relationship(
        "MasterRecord", back_populates="link_records"
    )

    def __str__(self):
        return (
            f"LinkRecord({self.id}) <"
            f"Person({self.person_id}), "
            f"Master({self.master_id})"
            ">"
        )


class Person(Base):
    __tablename__ = "person"

    id = Column(Integer, primary_key=True)
    originator = Column(String, nullable=False)

    # Person.localid must be unique for PidXRef relationship to work
    localid = Column(String, nullable=False, unique=True)

    localidtype = Column("localidtype", String, nullable=False)
    localid_type: Mapped[str] = synonym("localidtype")

    nationalid = Column("nationalid", String)

    nationalidtype = Column("nationalidtype", String)
    nationalid_type: Mapped[str] = synonym("nationalidtype")

    dateofbirth = Column("dateofbirth", Date, nullable=False)
    date_of_birth: Mapped[datetime.date] = synonym("dateofbirth")

    gender = Column("gender", String, nullable=False)

    dateofdeath = Column("dateofdeath", Date)
    date_of_death: Mapped[datetime.date] = synonym("dateofdeath")

    givenname = Column("givenname", String)
    surname = Column("surname", String)

    prevsurname = Column("prevsurname", String)
    prev_surname: Mapped[str] = synonym("prevsurname")

    othergivennames = Column("othergivennames", String)
    other_given_names: Mapped[str] = synonym("othergivennames")

    title = Column("title", String)
    postcode = Column("postcode", String)
    street = Column("street", String)

    stdsurname = Column("stdsurname", String)
    std_surname: Mapped[str] = synonym("stdsurname")

    stdprevsurname = Column("stdprevsurname", String)
    std_prev_surname: Mapped[str] = synonym("stdprevsurname")

    stdgivenname = Column("stdgivenname", String)
    std_given_name: Mapped[str] = synonym("stdgivenname")

    stdpostcode = Column("stdpostcode", String)
    std_postcode: Mapped[str] = synonym("stdpostcode")

    skipduplicatecheck = Column("skipduplicatecheck", Boolean)
    skip_duplicate_check: Mapped[bool] = synonym("skipduplicatecheck")

    link_records: Mapped[List["LinkRecord"]] = relationship(
        "LinkRecord", back_populates="person", cascade="all, delete-orphan"
    )
    work_items: Mapped[List["WorkItem"]] = relationship(
        "WorkItem", back_populates="person", cascade="all, delete-orphan"
    )
    xref_entries: Mapped[List["PidXRef"]] = relationship(
        "PidXRef", back_populates="person", cascade="all, delete-orphan"
    )

    def __str__(self):
        return (
            f"Person({self.id}) <"
            f"{self.givenname} {self.surname} {self.date_of_birth} "
            f"{self.localid_type.strip()}:{self.localid.strip()}"
            ">"
        )


class WorkItem(Base):
    __tablename__ = "workitem"

    id = Column(Integer, primary_key=True)

    personid = Column("personid", Integer, ForeignKey("person.id"), nullable=False)
    person_id: Mapped[int] = synonym("personid")

    masterid = Column(
        "masterid", Integer, ForeignKey("masterrecord.id"), nullable=False
    )
    master_id: Mapped[int] = synonym("masterid")

    type = Column("type", Integer, nullable=False)
    description = Column("description", String, nullable=False)
    status = Column("status", Integer, nullable=False)

    creationdate = Column("creationdate", DateTime)
    creation_date: Mapped[datetime.datetime] = synonym("creationdate")

    lastupdated = Column("lastupdated", DateTime, nullable=False)
    last_updated: Mapped[datetime.datetime] = synonym("lastupdated")

    updatedby = Column("updatedby", String)
    updated_by: Mapped[str] = synonym("updatedby")

    updatedesc = Column("updatedesc", String)
    update_description: Mapped[str] = synonym("updatedesc")

    attributes = Column("attributes", String)

    person: Mapped["Person"] = relationship("Person", back_populates="work_items")
    master_record: Mapped["MasterRecord"] = relationship(
        "MasterRecord", back_populates="work_items"
    )

    def __str__(self):
        return f"WorkItem({self.id}) <{self.person_id}, {self.master_id}>"


class Audit(Base):
    __tablename__ = "audit"

    id = Column(Integer, primary_key=True)

    # Can't use relations here, otherwise on delete sqla would try to
    # set null for these fields and it would fail, because DB doesn't
    # allow nulls for these fields
    personid = Column("personid", Integer, nullable=False)
    person_id: Mapped[int] = synonym("personid")

    masterid = Column("masterid", Integer, nullable=False)
    master_id: Mapped[int] = synonym("masterid")

    type = Column("type", Integer, nullable=False)
    description = Column("description", String, nullable=False)

    mainnationalid = Column("mainnationalid", String)
    main_nationalid: Mapped[str] = synonym("mainnationalid")

    mainnationalidtype = Column("mainnationalidtype", String)
    main_nationalid_type: Mapped[str] = synonym("mainnationalidtype")

    lastupdated = Column("lastupdated", DateTime, nullable=False)
    last_updated: Mapped[datetime.datetime] = synonym("lastupdated")

    updatedby = Column("updatedby", String)
    updated_by: Mapped[str] = synonym("updatedby")


class PidXRef(Base):
    __tablename__ = "pidxref"

    id = Column(Integer, primary_key=True)
    pid = Column(String, ForeignKey("person.localid"), nullable=False)

    sendingfacility = Column("sendingfacility", String, nullable=False)
    sending_facility: Mapped[str] = synonym("sendingfacility")

    sendingextract = Column("sendingextract", String, nullable=False)
    sending_extract: Mapped[str] = synonym("sendingextract")

    localid = Column("localid", String, nullable=False)

    person = relationship("Person", back_populates="xref_entries")

    def __str__(self):
        return (
            f"PidXRef({self.id}) <"
            f"{self.pid} {self.sending_facility} {self.sending_extract} "
            f"{self.localid.strip()}"
            f">"
        )


Index(
    "ix_person_mrn", Person.originator, Person.localid, Person.localid_type, unique=True
)
Index("person_id_key", Person.id, unique=True)

Index(
    "pidxref_compound",
    PidXRef.sending_facility,
    PidXRef.sending_extract,
    PidXRef.localid,
    unique=True,
)
