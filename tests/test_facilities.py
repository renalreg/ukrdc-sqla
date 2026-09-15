import pytest
from sqlalchemy import String, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column

from ukrdc_sqla.utils.constants import RelationshipType
from ukrdc_sqla.utils.facilities import get_facility_parent_unit


class Base(DeclarativeBase):
    pass


class MockFacilityRelationship(Base):
    """A mock table standing in for the vwe_facility_relationship materialized view,
    since materialized views aren't supported by SQLite and aren't needed for this test."""

    __tablename__ = "vwe_facility_relationship"
    parentfacilitycode: Mapped[str] = mapped_column(String(100), primary_key=True)
    parentfacilitycodestd: Mapped[str] = mapped_column(String(10), primary_key=True)
    childfacilitycode: Mapped[str] = mapped_column(String(100), primary_key=True)
    childfacilitycodestd: Mapped[str] = mapped_column(String(10), primary_key=True)
    relationshiptype: Mapped[str | None] = mapped_column(String(50))


@pytest.fixture(scope="function")
def session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as s:
        yield s


def populate_main_satellite_relationship(session: Session):
    relationship = MockFacilityRelationship(
        parentfacilitycode="TSF01",
        parentfacilitycodestd="RR1+",
        childfacilitycode="TSF02",
        childfacilitycodestd="RR1+",
        relationshiptype=RelationshipType.main_satellite,
    )
    session.add(relationship)
    session.commit()


def test_get_facility_parent_unit_satellite(session):
    """Input is a satellite"""
    populate_main_satellite_relationship(session)

    parent_lookup = get_facility_parent_unit(session, {"TSF02"})

    assert parent_lookup == {"TSF02": "TSF01"}


def test_get_facility_parent_unit_main_unit(session):
    """Input is a main unit"""
    populate_main_satellite_relationship(session)

    parent_lookup = get_facility_parent_unit(session, {"TSF01"})

    assert parent_lookup == {}
