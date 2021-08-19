"""Models which relate to the EMPI (JTRACE) Database"""
from typing import Any, List

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
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Mapped, relationship

metadata = MetaData()
Base: Any = declarative_base(metadata=metadata)


class MasterRecord(Base):
    __tablename__ = "masterrecord"

    id = Column(Integer, primary_key=True)
    last_updated = Column("lastupdated", DateTime, nullable=False)
    date_of_birth = Column("dateofbirth", Date, nullable=False)
    gender = Column(String)
    givenname = Column(String)
    surname = Column(String)
    nationalid = Column(String, nullable=False)
    nationalid_type = Column("nationalidtype", String, nullable=False)
    status = Column(Integer, nullable=False)
    effective_date = Column("effectivedate", DateTime, nullable=False)
    creation_date = Column("creationdate", DateTime)

    link_records: Mapped[List["LinkRecord"]] = relationship(
        "LinkRecord", backref="master_record", cascade="all, delete-orphan"
    )
    work_items: Mapped[List["WorkItem"]] = relationship(
        "WorkItem", backref="master_record", cascade="all, delete-orphan"
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
    person_id = Column("personid", Integer, ForeignKey("person.id"), nullable=False)
    master_id = Column(
        "masterid", Integer, ForeignKey("masterrecord.id"), nullable=False
    )
    link_type = Column("linktype", Integer, nullable=False)
    link_code = Column("linkcode", Integer, nullable=False)
    link_desc = Column("linkdesc", String)
    updated_by = Column("updatedby", String)
    last_updated = Column("lastupdated", DateTime, nullable=False)

    person: "Person"  # Let Person handle backref
    master_record: MasterRecord  # Let MasterRecord handle backref

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
    localid_type = Column("localidtype", String, nullable=False)
    nationalid = Column(String)
    nationalid_type = Column("nationalidtype", String)
    date_of_birth = Column("dateofbirth", Date, nullable=False)
    gender = Column(String, nullable=False)
    date_of_death = Column("dateofdeath", Date)
    givenname = Column(String)
    surname = Column(String)
    prev_surname = Column("prevsurname", String)
    other_given_names = Column("othergivennames", String)
    title = Column(String)
    postcode = Column(String)
    street = Column(String)
    std_surname = Column("stdsurname", String)
    std_prev_surname = Column("stdprevsurname", String)
    std_given_name = Column("stdgivenname", String)
    std_postcode = Column("stdpostcode", String)
    skip_duplicate_check = Column("skipduplicatecheck", Boolean)

    link_records: Mapped[List["LinkRecord"]] = relationship(
        "LinkRecord", backref="person", cascade="all, delete-orphan"
    )
    work_items: Mapped[List["WorkItem"]] = relationship(
        "WorkItem", backref="person", cascade="all, delete-orphan"
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


Index(
    "ix_person_mrn", Person.originator, Person.localid, Person.localid_type, unique=True
)
Index("person_id_key", Person.id, unique=True)


class WorkItem(Base):
    __tablename__ = "workitem"

    id = Column(Integer, primary_key=True)
    person_id = Column("personid", Integer, ForeignKey("person.id"), nullable=False)
    master_id = Column(
        "masterid", Integer, ForeignKey("masterrecord.id"), nullable=False
    )
    type = Column(Integer, nullable=False)
    description = Column(String, nullable=False)
    status = Column(Integer, nullable=False)
    creation_date = Column("creationdate", DateTime)
    last_updated = Column("lastupdated", DateTime, nullable=False)
    updated_by = Column("updatedby", String)
    update_description = Column("updatedesc", String)
    attributes = Column(String)

    person: Person  # Let Person handle backref
    master_record: MasterRecord  # Let MasterRecord handle backref

    def __str__(self):
        return f"WorkItem({self.id}) <{self.person_id}, {self.master_id}>"


class Audit(Base):
    __tablename__ = "audit"

    id = Column(Integer, primary_key=True)
    # Can't use relations here, otherwise on delete sqla would try to
    # set null for these fields and it would fail, because DB doesn't
    # allow nulls for these fields
    person_id = Column("personid", Integer, nullable=False)
    master_id = Column("masterid", Integer, nullable=False)
    type = Column(Integer, nullable=False)
    description = Column(String, nullable=False)
    main_nationalid = Column("mainnationalid", String)
    main_nationalid_type = Column("mainnationalidtype", String)
    last_updated = Column("lastupdated", DateTime, nullable=False)
    updated_by = Column("updatedby", String)


class PidXRef(Base):
    __tablename__ = "pidxref"

    id = Column(Integer, primary_key=True)
    pid = Column(String, ForeignKey("person.localid"), nullable=False)
    sending_facility = Column("sendingfacility", String, nullable=False)
    sending_extract = Column("sendingextract", String, nullable=False)
    localid = Column(String, nullable=False)

    person = relationship("Person", back_populates="xref_entries")

    def __str__(self):
        return (
            f"PidXRef({self.id}) <"
            f"{self.pid} {self.sending_facility} {self.sending_extract} "
            f"{self.localid.strip()}"
            f">"
        )


Index(
    "pidxref_compound",
    PidXRef.sending_facility,
    PidXRef.sending_extract,
    PidXRef.localid,
    unique=True,
)
