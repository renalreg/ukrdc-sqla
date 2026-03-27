"""Models which relate to the EMPI (JTRACE) database"""

import datetime
from typing import List, Optional

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
)

from sqlalchemy.orm import (
    mapped_column,
    Mapped,
    relationship,
    synonym,
    DeclarativeBase,
)


class Base(DeclarativeBase):
    pass


class MasterRecord(Base):
    __tablename__ = "masterrecord"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    lastupdated: Mapped[datetime.datetime] = mapped_column(DateTime, nullable=False)
    dateofbirth: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    gender: Mapped[Optional[str]] = mapped_column(String)
    givenname: Mapped[Optional[str]] = mapped_column(String)
    surname: Mapped[Optional[str]] = mapped_column(String)
    nationalid: Mapped[str] = mapped_column(String, nullable=False)
    nationalidtype: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[int] = mapped_column(Integer, nullable=False)
    effectivedate: Mapped[datetime.datetime] = mapped_column(DateTime, nullable=False)
    creationdate: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime)

    # --- Relationships ---
    link_records: Mapped[List["LinkRecord"]] = relationship(
        "LinkRecord", back_populates="master_record", cascade="all, delete-orphan"
    )
    work_items: Mapped[List["WorkItem"]] = relationship(
        "WorkItem", back_populates="master_record", cascade="all, delete-orphan"
    )

    # --- Synonyms ---
    last_updated: Mapped[datetime.datetime] = synonym("lastupdated")
    date_of_birth: Mapped[datetime.date] = synonym("dateofbirth")
    nationalid_type: Mapped[str] = synonym("nationalidtype")
    effective_date: Mapped[datetime.datetime] = synonym("effectivedate")
    creation_date: Mapped[Optional[datetime.datetime]] = synonym("creationdate")

    def __str__(self):
        return (
            f"MasterRecord({self.id}) <"
            f"{self.givenname} {self.surname} {self.dateofbirth} "
            f"{self.nationalidtype.strip()}:{self.nationalid}"
            f">"
        )


class LinkRecord(Base):
    __tablename__ = "linkrecord"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    personid: Mapped[int] = mapped_column(
        "personid", Integer, ForeignKey("person.id"), nullable=False
    )
    masterid: Mapped[int] = mapped_column(
        "masterid", Integer, ForeignKey("masterrecord.id"), nullable=False
    )
    linktype: Mapped[int] = mapped_column("linktype", Integer, nullable=False)
    linkcode: Mapped[int] = mapped_column("linkcode", Integer, nullable=False)
    linkdesc: Mapped[Optional[str]] = mapped_column("linkdesc", String)
    updatedby: Mapped[Optional[str]] = mapped_column("updatedby", String)
    lastupdated: Mapped[datetime.datetime] = mapped_column(
        "lastupdated", DateTime, nullable=False
    )

    # --- Relationships ---
    person: Mapped["Person"] = relationship("Person", back_populates="link_records")
    master_record: Mapped["MasterRecord"] = relationship(
        "MasterRecord", back_populates="link_records"
    )

    # --- Synonyms ---
    person_id: Mapped[int] = synonym("personid")
    master_id: Mapped[int] = synonym("masterid")
    link_type: Mapped[int] = synonym("linktype")
    link_code: Mapped[int] = synonym("linkcode")
    link_desc: Mapped[Optional[str]] = synonym("linkdesc")
    updated_by: Mapped[Optional[str]] = synonym("updatedby")
    last_updated: Mapped[datetime.datetime] = synonym("lastupdated")

    def __str__(self):
        return (
            f"LinkRecord({self.id}) <"
            f"Person({self.person_id}), "
            f"Master({self.master_id})"
            ">"
        )


class Person(Base):
    __tablename__ = "person"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    originator: Mapped[str] = mapped_column(String, nullable=False)

    # Person.localid must be unique for PidXRef relationship to work
    localid: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    localidtype: Mapped[str] = mapped_column("localidtype", String, nullable=False)
    nationalid: Mapped[Optional[str]] = mapped_column("nationalid", String)
    nationalidtype: Mapped[Optional[str]] = mapped_column("nationalidtype", String)
    dateofbirth: Mapped[datetime.date] = mapped_column(
        "dateofbirth", Date, nullable=False
    )
    gender: Mapped[str] = mapped_column("gender", String, nullable=False)
    dateofdeath: Mapped[Optional[datetime.date]] = mapped_column("dateofdeath", Date)
    givenname: Mapped[Optional[str]] = mapped_column("givenname", String)
    surname: Mapped[Optional[str]] = mapped_column("surname", String)
    prevsurname: Mapped[Optional[str]] = mapped_column("prevsurname", String)
    othergivennames: Mapped[Optional[str]] = mapped_column("othergivennames", String)
    title: Mapped[Optional[str]] = mapped_column("title", String)
    postcode: Mapped[Optional[str]] = mapped_column("postcode", String)
    street: Mapped[Optional[str]] = mapped_column("street", String)
    stdsurname: Mapped[Optional[str]] = mapped_column("stdsurname", String)
    stdprevsurname: Mapped[Optional[str]] = mapped_column("stdprevsurname", String)
    stdgivenname: Mapped[Optional[str]] = mapped_column("stdgivenname", String)
    stdpostcode: Mapped[Optional[str]] = mapped_column("stdpostcode", String)
    skipduplicatecheck: Mapped[Optional[bool]] = mapped_column(
        "skipduplicatecheck", Boolean
    )

    # --- Relationships ---
    link_records: Mapped[List["LinkRecord"]] = relationship(
        "LinkRecord", back_populates="person", cascade="all, delete-orphan"
    )
    work_items: Mapped[List["WorkItem"]] = relationship(
        "WorkItem", back_populates="person", cascade="all, delete-orphan"
    )
    xref_entries: Mapped[List["PidXRef"]] = relationship(
        "PidXRef", back_populates="person", cascade="all, delete-orphan"
    )
    # --- Synonyms ---
    localid_type: Mapped[str] = synonym("localidtype")
    nationalid_type: Mapped[Optional[str]] = synonym("nationalidtype")
    date_of_birth: Mapped[datetime.date] = synonym("dateofbirth")
    date_of_death: Mapped[Optional[datetime.date]] = synonym("dateofdeath")
    prev_surname: Mapped[Optional[str]] = synonym("prevsurname")
    other_given_names: Mapped[Optional[str]] = synonym("othergivennames")
    std_surname: Mapped[Optional[str]] = synonym("stdsurname")
    std_prev_surname: Mapped[Optional[str]] = synonym("stdprevsurname")
    std_given_name: Mapped[Optional[str]] = synonym("stdgivenname")
    std_postcode: Mapped[Optional[str]] = synonym("stdpostcode")
    skip_duplicate_check: Mapped[Optional[bool]] = synonym("skipduplicatecheck")

    def __str__(self):
        return (
            f"Person({self.id}) <"
            f"{self.givenname} {self.surname} {self.dateofbirth} "
            f"{self.localidtype.strip()}:{self.localid.strip()}"
            ">"
        )


class WorkItem(Base):
    __tablename__ = "workitem"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    personid: Mapped[int] = mapped_column(
        "personid", Integer, ForeignKey("person.id"), nullable=False
    )
    masterid: Mapped[int] = mapped_column(
        "masterid", Integer, ForeignKey("masterrecord.id"), nullable=False
    )
    type: Mapped[int] = mapped_column("type", Integer, nullable=False)
    description: Mapped[str] = mapped_column("description", String, nullable=False)
    status: Mapped[int] = mapped_column("status", Integer, nullable=False)
    creationdate: Mapped[Optional[datetime.datetime]] = mapped_column(
        "creationdate", DateTime
    )
    lastupdated: Mapped[datetime.datetime] = mapped_column(
        "lastupdated", DateTime, nullable=False
    )
    updatedby: Mapped[Optional[str]] = mapped_column("updatedby", String)
    updatedesc: Mapped[Optional[str]] = mapped_column("updatedesc", String)
    attributes: Mapped[Optional[str]] = mapped_column("attributes", String)

    # --- Relationships ---
    person: Mapped["Person"] = relationship("Person", back_populates="work_items")
    master_record: Mapped["MasterRecord"] = relationship(
        "MasterRecord", back_populates="work_items"
    )
    # --- Synonyms ---
    person_id: Mapped[int] = synonym("personid")
    master_id: Mapped[int] = synonym("masterid")
    creation_date: Mapped[Optional[datetime.datetime]] = synonym("creationdate")
    last_updated: Mapped[datetime.datetime] = synonym("lastupdated")
    updated_by: Mapped[Optional[str]] = synonym("updatedby")
    update_description: Mapped[Optional[str]] = synonym("updatedesc")

    def __str__(self):
        return f"WorkItem({self.id}) <{self.person_id}, {self.master_id}>"


class Audit(Base):
    __tablename__ = "audit"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    personid: Mapped[int] = mapped_column("personid", Integer, nullable=False)
    masterid: Mapped[int] = mapped_column("masterid", Integer, nullable=False)
    type: Mapped[int] = mapped_column("type", Integer, nullable=False)
    description: Mapped[str] = mapped_column("description", String, nullable=False)
    mainnationalid: Mapped[Optional[str]] = mapped_column("mainnationalid", String)
    mainnationalidtype: Mapped[Optional[str]] = mapped_column(
        "mainnationalidtype", String
    )
    lastupdated: Mapped[datetime.datetime] = mapped_column(
        "lastupdated", DateTime, nullable=False
    )
    updatedby: Mapped[Optional[str]] = mapped_column("updatedby", String)

    # --- Relationships ---
    # Can't use relations here, otherwise on delete sqla would try to
    # set null for these fields and it would fail, because DB doesn't
    # allow nulls for these fields

    # --- Synonyms ---
    person_id: Mapped[int] = synonym("personid")
    master_id: Mapped[int] = synonym("masterid")
    main_nationalid: Mapped[Optional[str]] = synonym("mainnationalid")
    main_nationalid_type: Mapped[Optional[str]] = synonym("mainnationalidtype")
    last_updated: Mapped[datetime.datetime] = synonym("lastupdated")
    updated_by: Mapped[Optional[str]] = synonym("updatedby")


class PidXRef(Base):
    __tablename__ = "pidxref"

    # --- Attributes ---
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    pid: Mapped[str] = mapped_column(
        String, ForeignKey("person.localid"), nullable=False
    )
    sendingfacility: Mapped[str] = mapped_column(
        "sendingfacility", String, nullable=False
    )
    sendingextract: Mapped[str] = mapped_column(
        "sendingextract", String, nullable=False
    )
    localid: Mapped[str] = mapped_column("localid", String, nullable=False)

    # --- Relationships ---
    person: Mapped["Person"] = relationship("Person", back_populates="xref_entries")

    # --- Synonyms ---
    sending_facility: Mapped[str] = synonym("sendingfacility")
    sending_extract: Mapped[str] = synonym("sendingextract")

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
