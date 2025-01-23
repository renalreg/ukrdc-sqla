"""Models which relate to the EMPI (JTRACE) database"""

import datetime

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    MetaData,
    String,
)

from sqlalchemy.orm import Mapped, relationship, synonym, declarative_base, mapped_column

metadata = MetaData()
Base = declarative_base(metadata=metadata)


class MasterRecord(Base):
    __tablename__ = "masterrecord"

    id = mapped_column(Integer, primary_key=True)

    lastupdated = mapped_column("lastupdated", DateTime, nullable=False)
    last_updated: Mapped[datetime.datetime] = synonym("lastupdated")

    dateofbirth = mapped_column("dateofbirth", Date, nullable=False)
    date_of_birth: Mapped[datetime.date] = synonym("dateofbirth")

    gender = mapped_column("gender", String)
    givenname = mapped_column("givenname", String)
    surname = mapped_column("surname", String)
    nationalid = mapped_column("nationalid", String, nullable=False)

    nationalidtype = mapped_column("nationalidtype", String, nullable=False)
    nationalid_type: Mapped[str] = synonym("nationalidtype")

    status = mapped_column("status", Integer, nullable=False)

    effectivedate = mapped_column("effectivedate", DateTime, nullable=False)
    effective_date: Mapped[datetime.datetime] = synonym("effectivedate")

    creationdate = mapped_column("creationdate", DateTime)
    creation_date: Mapped[datetime.datetime] = synonym("creationdate")

    link_records:Mapped["LinkRecord"] = relationship(
        "LinkRecord", backref="master_record", cascade="all, delete-orphan"
    )
    work_items:Mapped["WorkItem"] = relationship(
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

    id = mapped_column(Integer, primary_key=True)

    personid = mapped_column("personid", Integer, ForeignKey("person.id"), nullable=False)
    person_id: Mapped[int] = synonym("personid")

    masterid = mapped_column(
        "masterid", Integer, ForeignKey("masterrecord.id"), nullable=False
    )
    master_id: Mapped[int] = synonym("masterid")

    linktype = mapped_column("linktype", Integer, nullable=False)
    link_type: Mapped[int] = synonym("linktype")

    linkcode = mapped_column("linkcode", Integer, nullable=False)
    link_code: Mapped[int] = synonym("linkcode")

    linkdesc = mapped_column("linkdesc", String)
    link_desc: Mapped[str] = synonym("linkdesc")

    updatedby = mapped_column("updatedby", String)
    updated_by: Mapped[str] = synonym("updatedby")

    lastupdated = mapped_column("lastupdated", DateTime, nullable=False)
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

    id = mapped_column(Integer, primary_key=True)
    originator = mapped_column(String, nullable=False)

    # Person.localid must be unique for PidXRef relationship to work
    localid = mapped_column(String, nullable=False, unique=True)

    localidtype = mapped_column("localidtype", String, nullable=False)
    localid_type: Mapped[str] = synonym("localidtype")

    nationalid = mapped_column("nationalid", String)

    nationalidtype = mapped_column("nationalidtype", String)
    nationalid_type: Mapped[str] = synonym("nationalidtype")

    dateofbirth = mapped_column("dateofbirth", Date, nullable=False)
    date_of_birth: Mapped[datetime.date] = synonym("dateofbirth")

    gender = mapped_column("gender", String, nullable=False)

    dateofdeath = mapped_column("dateofdeath", Date)
    date_of_death: Mapped[datetime.date] = synonym("dateofdeath")

    givenname = mapped_column("givenname", String)
    surname = mapped_column("surname", String)

    prevsurname = mapped_column("prevsurname", String)
    prev_surname: Mapped[str] = synonym("prevsurname")

    othergivennames = mapped_column("othergivennames", String)
    other_given_names: Mapped[str] = synonym("othergivennames")

    title = mapped_column("title", String)
    postcode = mapped_column("postcode", String)
    street = mapped_column("street", String)

    stdsurname = mapped_column("stdsurname", String)
    std_surname: Mapped[str] = synonym("stdsurname")

    stdprevsurname = mapped_column("stdprevsurname", String)
    std_prev_surname: Mapped[str] = synonym("stdprevsurname")

    stdgivenname = mapped_column("stdgivenname", String)
    std_given_name: Mapped[str] = synonym("stdgivenname")

    stdpostcode = mapped_column("stdpostcode", String)
    std_postcode: Mapped[str] = synonym("stdpostcode")

    skipduplicatecheck = mapped_column("skipduplicatecheck", Boolean)
    skip_duplicate_check: Mapped[bool] = synonym("skipduplicatecheck")

    link_records:Mapped["LinkRecord"] = relationship(
        "LinkRecord", backref="person", cascade="all, delete-orphan"
    )
    work_items:Mapped["WorkItem"] = relationship(
        "WorkItem", backref="person", cascade="all, delete-orphan"
    )
    xref_entries:Mapped["PidXRef"] = relationship(
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

    id = mapped_column(Integer, primary_key=True)

    personid = mapped_column("personid", Integer, ForeignKey("person.id"), nullable=False)
    person_id: Mapped[int] = synonym("personid")

    masterid = mapped_column(
        "masterid", Integer, ForeignKey("masterrecord.id"), nullable=False
    )
    master_id: Mapped[int] = synonym("masterid")

    type = mapped_column("type", Integer, nullable=False)
    description = mapped_column("description", String, nullable=False)
    status = mapped_column("status", Integer, nullable=False)

    creationdate = mapped_column("creationdate", DateTime)
    creation_date: Mapped[datetime.datetime] = synonym("creationdate")

    lastupdated = mapped_column("lastupdated", DateTime, nullable=False)
    last_updated: Mapped[datetime.datetime] = synonym("lastupdated")

    updatedby = mapped_column("updatedby", String)
    updated_by: Mapped[str] = synonym("updatedby")

    updatedesc = mapped_column("updatedesc", String)
    update_description: Mapped[str] = synonym("updatedesc")

    attributes = mapped_column("attributes", String)

    def __str__(self):
        return f"WorkItem({self.id}) <{self.person_id}, {self.master_id}>"


class Audit(Base):
    __tablename__ = "audit"

    id = mapped_column(Integer, primary_key=True)

    # Can't use relations here, otherwise on delete sqla would try to
    # set null for these fields and it would fail, because DB doesn't
    # allow nulls for these fields
    personid = mapped_column("personid", Integer, nullable=False)
    person_id: Mapped[int] = synonym("personid")

    masterid = mapped_column("masterid", Integer, nullable=False)
    master_id: Mapped[int] = synonym("masterid")

    type = mapped_column("type", Integer, nullable=False)
    description = mapped_column("description", String, nullable=False)

    mainnationalid = mapped_column("mainnationalid", String)
    main_nationalid: Mapped[str] = synonym("mainnationalid")

    mainnationalidtype = mapped_column("mainnationalidtype", String)
    main_nationalid_type: Mapped[str] = synonym("mainnationalidtype")

    lastupdated = mapped_column("lastupdated", DateTime, nullable=False)
    last_updated: Mapped[datetime.datetime] = synonym("lastupdated")

    updatedby = mapped_column("updatedby", String)
    updated_by: Mapped[str] = synonym("updatedby")


class PidXRef(Base):
    __tablename__ = "pidxref"

    id = mapped_column(Integer, primary_key=True)
    pid = mapped_column(String, ForeignKey("person.localid"), nullable=False)

    sendingfacility = mapped_column("sendingfacility", String, nullable=False)
    sending_facility: Mapped[str] = synonym("sendingfacility")

    sendingextract = mapped_column("sendingextract", String, nullable=False)
    sending_extract: Mapped[str] = synonym("sendingextract")

    localid = mapped_column("localid", String, nullable=False)

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
