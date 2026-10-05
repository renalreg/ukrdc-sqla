"""Models which relate to the EMPI (JTRACE) database"""

import datetime

from sqlalchemy import (
    CHAR,
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    func,
)
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    relationship,
    synonym,
)

from ukrdc_sqla.utils.structure import ORM_ONLY


class Base(DeclarativeBase):
    pass


class MasterRecord(Base):
    __tablename__ = "masterrecord"

    id: Mapped[int] = mapped_column(Integer, nullable=False)
    __mapper_args__ = {"primary_key": [id]}
    lastupdated: Mapped[datetime.datetime] = mapped_column(DateTime, nullable=False)
    dateofbirth: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    gender: Mapped[str | None] = mapped_column(String(5))
    givenname: Mapped[str | None] = mapped_column(String(60))
    surname: Mapped[str | None] = mapped_column(String(60))
    nationalid: Mapped[str] = mapped_column(CHAR(10), nullable=False)
    nationalidtype: Mapped[str] = mapped_column(CHAR(10), nullable=False)
    status: Mapped[int] = mapped_column(Integer, nullable=False)
    effectivedate: Mapped[datetime.datetime] = mapped_column(DateTime, nullable=False)
    creationdate: Mapped[datetime.datetime] = mapped_column(DateTime, nullable=False)

    # --- Relationships ---
    link_records: Mapped[list["LinkRecord"]] = relationship(
        "LinkRecord", back_populates="master_record", cascade="all, delete-orphan"
    )
    work_items: Mapped[list["WorkItem"]] = relationship(
        "WorkItem", back_populates="master_record", cascade="all, delete-orphan"
    )

    # --- Synonyms ---
    last_updated: Mapped[datetime.datetime] = synonym("lastupdated")
    date_of_birth: Mapped[datetime.date] = synonym("dateofbirth")
    nationalid_type: Mapped[str] = synonym("nationalidtype")
    effective_date: Mapped[datetime.datetime] = synonym("effectivedate")
    creation_date: Mapped[datetime.datetime] = synonym("creationdate")

    def __str__(self):
        return (
            f"MasterRecord({self.id}) <"
            f"{self.givenname} {self.surname} {self.dateofbirth} "
            f"{self.nationalidtype.strip()}:{self.nationalid}"
            f">"
        )


class LinkRecord(Base):
    __tablename__ = "linkrecord"

    id: Mapped[int] = mapped_column(Integer, nullable=False)
    __mapper_args__ = {"primary_key": [id]}
    personid: Mapped[int] = mapped_column(
        "personid",
        Integer,
        ForeignKey("person.id", info={ORM_ONLY: True}),
        nullable=False,
    )
    masterid: Mapped[int] = mapped_column(
        "masterid",
        Integer,
        ForeignKey("masterrecord.id", info={ORM_ONLY: True}),
        nullable=False,
    )
    linktype: Mapped[int] = mapped_column("linktype", Integer, nullable=False)
    linkcode: Mapped[int] = mapped_column("linkcode", Integer, nullable=False)
    linkdesc: Mapped[str | None] = mapped_column("linkdesc", String(200))
    updatedby: Mapped[str | None] = mapped_column("updatedby", String(20))
    creationdate: Mapped[datetime.datetime] = mapped_column(
        "creationdate", DateTime, nullable=False, server_default=func.now()
    )
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
    link_desc: Mapped[str | None] = synonym("linkdesc")
    updated_by: Mapped[str | None] = synonym("updatedby")
    creation_date: Mapped[datetime.datetime] = synonym("creationdate")
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

    id: Mapped[int] = mapped_column(Integer, nullable=False)
    __mapper_args__ = {"primary_key": [id]}
    originator: Mapped[str] = mapped_column(String(50), nullable=False)

    # Not unique on its own in the database (only as part of ix_person_mrn),
    # so the PidXRef -> Person FK is ORM-only
    localid: Mapped[str] = mapped_column(String(17), nullable=False)
    localidtype: Mapped[str] = mapped_column("localidtype", String(10), nullable=False)
    nationalid: Mapped[str | None] = mapped_column("nationalid", String(10))
    nationalidtype: Mapped[str | None] = mapped_column("nationalidtype", String(5))
    dateofbirth: Mapped[datetime.date] = mapped_column(
        "dateofbirth", Date, nullable=False
    )
    gender: Mapped[str] = mapped_column("gender", String(2), nullable=False)
    dateofdeath: Mapped[datetime.date | None] = mapped_column("dateofdeath", Date)
    givenname: Mapped[str | None] = mapped_column("givenname", String(60))
    surname: Mapped[str | None] = mapped_column("surname", String(60))
    prevsurname: Mapped[str | None] = mapped_column("prevsurname", String(60))
    othergivennames: Mapped[str | None] = mapped_column("othergivennames", String(60))
    title: Mapped[str | None] = mapped_column("title", String(20))
    postcode: Mapped[str | None] = mapped_column("postcode", String(10))
    street: Mapped[str | None] = mapped_column("street", String(220))
    stdsurname: Mapped[str | None] = mapped_column("stdsurname", String(4))
    stdprevsurname: Mapped[str | None] = mapped_column("stdprevsurname", String(4))
    stdgivenname: Mapped[str | None] = mapped_column("stdgivenname", String(4))
    stdpostcode: Mapped[str | None] = mapped_column("stdpostcode", String(8))
    skipduplicatecheck: Mapped[bool | None] = mapped_column(
        "skipduplicatecheck", Boolean
    )
    creationdate: Mapped[datetime.datetime] = mapped_column(
        "creationdate", DateTime, nullable=False, server_default=func.now()
    )
    lastupdated: Mapped[datetime.datetime] = mapped_column(
        "lastupdated", DateTime, nullable=False, server_default=func.now()
    )

    # --- Relationships ---
    link_records: Mapped[list["LinkRecord"]] = relationship(
        "LinkRecord", back_populates="person", cascade="all, delete-orphan"
    )
    work_items: Mapped[list["WorkItem"]] = relationship(
        "WorkItem", back_populates="person", cascade="all, delete-orphan"
    )
    xref_entries: Mapped[list["PidXRef"]] = relationship(
        "PidXRef", back_populates="person", cascade="all, delete-orphan"
    )
    # --- Synonyms ---
    localid_type: Mapped[str] = synonym("localidtype")
    nationalid_type: Mapped[str | None] = synonym("nationalidtype")
    date_of_birth: Mapped[datetime.date] = synonym("dateofbirth")
    date_of_death: Mapped[datetime.date | None] = synonym("dateofdeath")
    prev_surname: Mapped[str | None] = synonym("prevsurname")
    other_given_names: Mapped[str | None] = synonym("othergivennames")
    std_surname: Mapped[str | None] = synonym("stdsurname")
    std_prev_surname: Mapped[str | None] = synonym("stdprevsurname")
    std_given_name: Mapped[str | None] = synonym("stdgivenname")
    std_postcode: Mapped[str | None] = synonym("stdpostcode")
    skip_duplicate_check: Mapped[bool | None] = synonym("skipduplicatecheck")
    creation_date: Mapped[datetime.datetime] = synonym("creationdate")
    last_updated: Mapped[datetime.datetime] = synonym("lastupdated")

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
        "personid",
        Integer,
        ForeignKey("person.id", info={ORM_ONLY: True}),
        nullable=False,
    )
    masterid: Mapped[int] = mapped_column(
        "masterid",
        Integer,
        ForeignKey("masterrecord.id", info={ORM_ONLY: True}),
        nullable=False,
    )
    type: Mapped[int] = mapped_column("type", Integer, nullable=False)
    description: Mapped[str] = mapped_column(
        "description", String(100), nullable=False
    )
    status: Mapped[int] = mapped_column("status", Integer, nullable=False)
    creationdate: Mapped[datetime.datetime] = mapped_column(
        "creationdate", DateTime, nullable=False
    )
    lastupdated: Mapped[datetime.datetime] = mapped_column(
        "lastupdated", DateTime, nullable=False
    )
    updatedby: Mapped[str | None] = mapped_column("updatedby", String(20))
    updatedesc: Mapped[str | None] = mapped_column("updatedesc", String(100))
    attributes: Mapped[str | None] = mapped_column("attributes", String(1024))

    # --- Relationships ---
    person: Mapped["Person"] = relationship("Person", back_populates="work_items")
    master_record: Mapped["MasterRecord"] = relationship(
        "MasterRecord", back_populates="work_items"
    )
    # --- Synonyms ---
    person_id: Mapped[int] = synonym("personid")
    master_id: Mapped[int] = synonym("masterid")
    creation_date: Mapped[datetime.datetime] = synonym("creationdate")
    last_updated: Mapped[datetime.datetime] = synonym("lastupdated")
    updated_by: Mapped[str | None] = synonym("updatedby")
    update_description: Mapped[str | None] = synonym("updatedesc")

    def __str__(self):
        return f"WorkItem({self.id}) <{self.person_id}, {self.master_id}>"


class Audit(Base):
    __tablename__ = "audit"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    personid: Mapped[int] = mapped_column("personid", Integer, nullable=False)
    masterid: Mapped[int] = mapped_column("masterid", Integer, nullable=False)
    type: Mapped[int] = mapped_column("type", Integer, nullable=False)
    description: Mapped[str] = mapped_column(
        "description", String(100), nullable=False
    )
    attributes: Mapped[str | None] = mapped_column("attributes", String(1024))
    mainnationalid: Mapped[str | None] = mapped_column("mainnationalid", String(10))
    mainnationalidtype: Mapped[str | None] = mapped_column(
        "mainnationalidtype", String(10)
    )
    lastupdated: Mapped[datetime.datetime] = mapped_column(
        "lastupdated", DateTime, nullable=False
    )
    updatedby: Mapped[str | None] = mapped_column("updatedby", String(20))

    # --- Relationships ---
    # Can't use relations here, otherwise on delete sqla would try to
    # set null for these fields and it would fail, because DB doesn't
    # allow nulls for these fields

    # --- Synonyms ---
    person_id: Mapped[int] = synonym("personid")
    master_id: Mapped[int] = synonym("masterid")
    main_nationalid: Mapped[str | None] = synonym("mainnationalid")
    main_nationalid_type: Mapped[str | None] = synonym("mainnationalidtype")
    last_updated: Mapped[datetime.datetime] = synonym("lastupdated")
    updated_by: Mapped[str | None] = synonym("updatedby")


class PidXRef(Base):
    __tablename__ = "pidxref"

    # --- Attributes ---
    id: Mapped[int] = mapped_column(Integer, nullable=False)
    __mapper_args__ = {"primary_key": [id]}
    pid: Mapped[str] = mapped_column(
        String(10),
        ForeignKey("person.localid", info={ORM_ONLY: True}),
        nullable=False,
    )
    sendingfacility: Mapped[str] = mapped_column(
        "sendingfacility", String(7), nullable=False
    )
    sendingextract: Mapped[str] = mapped_column(
        "sendingextract", String(6), nullable=False
    )
    localid: Mapped[str] = mapped_column("localid", String(17), nullable=False)
    creationdate: Mapped[datetime.datetime] = mapped_column(
        "creationdate", DateTime, nullable=False, server_default=func.now()
    )
    lastupdated: Mapped[datetime.datetime] = mapped_column(
        "lastupdated", DateTime, nullable=False, server_default=func.now()
    )

    # --- Relationships ---
    person: Mapped["Person"] = relationship("Person", back_populates="xref_entries")

    # --- Synonyms ---
    sending_facility: Mapped[str] = synonym("sendingfacility")
    sending_extract: Mapped[str] = synonym("sendingextract")
    creation_date: Mapped[datetime.datetime] = synonym("creationdate")
    last_updated: Mapped[datetime.datetime] = synonym("lastupdated")

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