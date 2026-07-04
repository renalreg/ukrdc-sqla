from __future__ import annotations

from datetime import datetime
from typing import Optional

import pytest
from sqlalchemy import (
    create_engine,
    String,
    DateTime,
    ForeignKey,
    Boolean,
    Float,
    Numeric,
    cast,
    select,
    update,
)
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    Session,
    relationship,
    QueryableAttribute,
)

from ukrdc_sqla.utils.post_calculations import example_prepost
from ukrdc_sqla.utils.structure import (
    computed_field,
    session_computed_field,
    ComputedField,
    SessionComputedField,
    computed_hybrid,
)


class Base(DeclarativeBase):
    pass


class MinimalPatientRecord(Base):
    __tablename__ = "patientrecord"

    pid: Mapped[str] = mapped_column(String, primary_key=True)
    sendingfacility: Mapped[str] = mapped_column(String(7), nullable=False)
    sendingextract: Mapped[str] = mapped_column(String(6), nullable=False)
    localpatientid: Mapped[str] = mapped_column(String(17), nullable=False)
    repositorycreationdate: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    repositoryupdatedate: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    migrated: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    creation_date: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.now
    )


class MinimalLabOrder(Base):
    __tablename__ = "laborder"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    pid: Mapped[str] = mapped_column(String, ForeignKey("patientrecord.pid"))
    creation_date: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.now
    )

    result_items: Mapped[list[MinimalResultItem]] = relationship(
        "MinimalResultItem", back_populates="order"
    )


class ServiceMultiplier(Base):
    """Reference table: each service code has a multiplier."""

    __tablename__ = "service_multiplier"

    serviceidcode: Mapped[str] = mapped_column(String(100), primary_key=True)
    multiplier: Mapped[float] = mapped_column(Float, nullable=False)


def calc_plus_five(result_item: MinimalResultItem) -> float | None:
    """Pure Python — add 5 to the numeric result value. No session needed."""
    if result_item.resultvalue is None:
        return None
    return float(result_item.resultvalue) + 5.0


def calc_via_relationship(
    result_item: MinimalResultItem, session: Session
) -> float | None:
    """Multiply result value by a factor looked up via the mapped relationship."""
    if result_item.resultvalue is None:
        return None
    if result_item.service_multiplier_rel is None:
        return float(result_item.resultvalue)
    return (
        float(result_item.resultvalue) * result_item.service_multiplier_rel.multiplier
    )


def calc_via_manual_query(
    result_item: MinimalResultItem, session: Session
) -> float | None:
    """Same multiplication but via raw session.execute — no relationship defined."""
    if result_item.resultvalue is None:
        return None
    row = session.execute(
        select(ServiceMultiplier.multiplier).where(
            ServiceMultiplier.serviceidcode == result_item.serviceidcode
        )
    ).scalar_one_or_none()
    if row is None:
        return float(result_item.resultvalue)
    return float(result_item.resultvalue) * row


def _hybrid_plus_ten_py(self) -> float | None:
    """Python side of the hybrid: add 10 to result value."""
    if self.resultvalue is None:
        return None
    return float(self.resultvalue) + 10.0


def _hybrid_plus_ten_expr(cls):
    """SQL side of the hybrid: cast resultvalue to Numeric and add 10."""
    return cast(cls.resultvalue, Numeric) + 10.0


class MinimalResultItem(Base):
    __tablename__ = "resultitem"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    orderid: Mapped[str] = mapped_column(String, ForeignKey("laborder.id"))
    creation_date: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.now
    )
    resultvalue: Mapped[str] = mapped_column(String(20), nullable=True)
    serviceidcode: Mapped[Optional[None]] = mapped_column(String(100), nullable=True)

    service_multiplier_rel: Mapped[ServiceMultiplier | None] = relationship(
        "ServiceMultiplier",
        primaryjoin="MinimalResultItem.serviceidcode == ServiceMultiplier.serviceidcode",
        foreign_keys="[MinimalResultItem.serviceidcode]",
    )
    order: Mapped[MinimalLabOrder] = relationship(
        "MinimalLabOrder", back_populates="result_items"
    )

    @property
    def value(self) -> float | None:
        return float(self.resultvalue) if self.resultvalue is not None else None

    # Pure Python — no session, cache survives expiry
    value_plus_five: float | None = computed_field(calc_plus_five)

    # Hybrid — no cache, usable in queries
    value_plus_ten = computed_hybrid(_hybrid_plus_ten_py, _hybrid_plus_ten_expr)

    # Session-aware — cache cleared on expiry/commit
    prepost_example: str = session_computed_field(example_prepost)
    value_by_relationship: float | None = session_computed_field(calc_via_relationship)
    value_by_manual_query: float | None = session_computed_field(calc_via_manual_query)


@pytest.fixture(scope="function")
def session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as s:
        s.add_all(
            [
                MinimalPatientRecord(
                    pid="TEST_PID",
                    sendingfacility="TST001",
                    sendingextract="PV",
                    localpatientid="LOCAL123",
                    repositorycreationdate=datetime.now(),
                    repositoryupdatedate=datetime.now(),
                    migrated=False,
                    creation_date=datetime.now(),
                ),
                MinimalLabOrder(
                    id="ORDER_1", pid="TEST_PID", creation_date=datetime.now()
                ),
                ServiceMultiplier(serviceidcode="HB", multiplier=2.0),
                ServiceMultiplier(serviceidcode="CREAT", multiplier=0.5),
            ]
        )
        s.commit()
        yield s


def make_result(
    session: Session,
    id: str,
    value: Optional[None],
    serviceidcode: Optional[None] = None,
) -> MinimalResultItem:
    item = MinimalResultItem(
        id=id,
        orderid="ORDER_1",
        creation_date=datetime.now(),
        resultvalue=value,
        serviceidcode=serviceidcode,
    )
    session.add(item)
    session.commit()
    return item


class TestComputedFieldCaching:
    def test_cache_populated_on_first_access(self, session):
        item = make_result(session, "P1", "10")
        assert "_cf_value_plus_five" not in item.__dict__
        _ = item.value_plus_five
        assert "_cf_value_plus_five" in item.__dict__

    def test_cached_value_returned_on_second_access(self, session):
        item = make_result(session, "P2", "10")
        _ = item.value_plus_five
        item.__dict__["_cf_value_plus_five"] = 999.0
        assert item.value_plus_five == 999.0

    def test_cache_survives_session_expire(self, session):
        """
        Pure-Python fields don't need the DB — their cache should remain
        intact after session.expire() so no unnecessary recalculation occurs.
        """
        item = make_result(session, "P3", "10")
        _ = item.value_plus_five
        assert "_cf_value_plus_five" in item.__dict__

        session.expire(item)

        assert "_cf_value_plus_five" in item.__dict__

    def test_cache_survives_commit(self, session):
        """commit() expires SQLAlchemy columns but should leave pure-Python cache alone."""
        item = make_result(session, "P4", "10")
        _ = item.value_plus_five
        assert "_cf_value_plus_five" in item.__dict__

        session.commit()

        assert "_cf_value_plus_five" in item.__dict__

    def test_value_correct_after_expire(self, session):
        """Even after expire the cached value is still the original calculation."""
        item = make_result(session, "P5", "10")
        assert item.value_plus_five == 15.0
        session.expire(item)
        assert item.value_plus_five == 15.0


class TestSessionComputedFieldCaching:
    def test_cache_populated_on_first_access(self, session):
        item = make_result(session, "S1", "75")
        assert "_cf_prepost_example" not in item.__dict__
        _ = item.prepost_example
        assert "_cf_prepost_example" in item.__dict__

    def test_cached_value_returned_on_second_access(self, session):
        item = make_result(session, "S2", "75")
        _ = item.prepost_example
        item.__dict__["_cf_prepost_example"] = "POISONED"
        assert item.prepost_example == "POISONED"

    def test_cache_cleared_after_session_expire(self, session):
        item = make_result(session, "S3", "75")
        _ = item.prepost_example
        assert "_cf_prepost_example" in item.__dict__

        session.expire(item)

        assert "_cf_prepost_example" not in item.__dict__

    def test_cache_cleared_after_commit(self, session):
        item = make_result(session, "S4", "75")
        _ = item.prepost_example
        assert "_cf_prepost_example" in item.__dict__

        session.commit()

        assert "_cf_prepost_example" not in item.__dict__

    def test_recalculates_after_expire_with_new_db_value(self, session):
        """After expiry, the next access queries the DB and reflects updated data."""
        item = make_result(session, "S5", "75")
        assert item.prepost_example == "greater"

        session.execute(
            MinimalResultItem.__table__.update()
            .where(MinimalResultItem.id == "S5")
            .values(resultvalue="10")
        )
        session.expire(item)

        assert item.prepost_example == "less"

    def test_expire_only_clears_session_computed_keys(self, session):
        """
        Key isolation: expiring an instance should clear session_computed_field
        caches but leave computed_field caches untouched.
        """
        item = make_result(session, "S6", "10")
        _ = item.value_plus_five  # computed_field
        _ = item.prepost_example  # session_computed_field

        session.expire(item)

        assert "_cf_value_plus_five" in item.__dict__  # survived
        assert "_cf_prepost_example" not in item.__dict__  # cleared

    def test_multiple_session_fields_all_cleared(self, session):
        item = make_result(session, "S7", "10", serviceidcode="HB")
        _ = item.prepost_example
        _ = item.value_by_relationship

        session.expire(item)

        assert "_cf_prepost_example" not in item.__dict__
        assert "_cf_value_by_relationship" not in item.__dict__

    def test_raises_without_session(self):
        item = MinimalResultItem(id="DETACHED", orderid="ORDER_1", resultvalue="75")
        with pytest.raises(RuntimeError, match="not bound to a session"):
            _ = item.prepost_example


class TestSimpleCalculations:
    def test_threshold_above(self, session):
        assert make_result(session, "C1", "75").prepost_example == "greater"

    def test_threshold_at_boundary(self, session):
        assert make_result(session, "C2", "50").prepost_example == "greater"

    def test_threshold_below(self, session):
        assert make_result(session, "C3", "25").prepost_example == "less"

    def test_plus_five_positive(self, session):
        assert make_result(session, "C4", "10").value_plus_five == 15.0

    def test_plus_five_zero(self, session):
        assert make_result(session, "C5", "0").value_plus_five == 5.0

    def test_plus_five_negative(self, session):
        assert make_result(session, "C6", "-3").value_plus_five == 2.0

    def test_plus_five_none(self, session):
        assert make_result(session, "C7", None).value_plus_five is None


class TestJoinRelationship:
    def test_known_service_applies_multiplier(self, session):
        assert make_result(session, "J1", "10", "HB").value_by_relationship == 20.0

    def test_different_multiplier(self, session):
        assert make_result(session, "J2", "10", "CREAT").value_by_relationship == 5.0

    def test_unknown_service_returns_value_unchanged(self, session):
        assert make_result(session, "J3", "10", "UNKNOWN").value_by_relationship == 10.0

    def test_no_service_code_returns_value_unchanged(self, session):
        assert make_result(session, "J4", "10", None).value_by_relationship == 10.0

    def test_none_result_value_returns_none(self, session):
        assert make_result(session, "J5", None, "HB").value_by_relationship is None

    def test_result_is_cached(self, session):
        item = make_result(session, "J6", "10", "HB")
        _ = item.value_by_relationship
        assert "_cf_value_by_relationship" in item.__dict__


class TestJoinManual:
    def test_known_service_applies_multiplier(self, session):
        assert make_result(session, "M1", "10", "HB").value_by_manual_query == 20.0

    def test_different_multiplier(self, session):
        assert make_result(session, "M2", "10", "CREAT").value_by_manual_query == 5.0

    def test_unknown_service_returns_value_unchanged(self, session):
        assert make_result(session, "M3", "10", "UNKNOWN").value_by_manual_query == 10.0

    def test_no_service_code_returns_value_unchanged(self, session):
        assert make_result(session, "M4", "10", None).value_by_manual_query == 10.0

    def test_none_result_value_returns_none(self, session):
        assert make_result(session, "M5", None, "HB").value_by_manual_query is None

    def test_result_is_cached(self, session):
        item = make_result(session, "M6", "10", "HB")
        _ = item.value_by_manual_query
        assert "_cf_value_by_manual_query" in item.__dict__

    def test_relationship_and_manual_query_agree(self, session):
        item = make_result(session, "M7", "10", "HB")
        assert item.value_by_relationship == item.value_by_manual_query

    def test_new_multiplier_row_visible_after_expire(self, session):
        item = make_result(session, "M8", "10", "NEW_CODE")
        assert item.value_by_manual_query == 10.0  # no multiplier yet

        session.add(ServiceMultiplier(serviceidcode="NEW_CODE", multiplier=3.0))
        session.commit()
        session.expire(item)

        assert item.value_by_manual_query == 30.0


class TestDescriptorContract:
    def test_computed_field_class_access_returns_descriptor(self):
        assert isinstance(MinimalResultItem.value_plus_five, ComputedField)

    def test_session_computed_field_class_access_returns_descriptor(self):
        assert isinstance(MinimalResultItem.prepost_example, SessionComputedField)

    def test_all_session_fields_are_session_computed_field(self):
        for attr in (
            "prepost_example",
            "value_by_relationship",
            "value_by_manual_query",
        ):
            assert isinstance(getattr(MinimalResultItem, attr), SessionComputedField), (
                attr
            )

    def test_pure_python_field_does_not_require_session(self):
        """computed_field works on a detached instance — no session needed."""
        item = MinimalResultItem(id="DETACHED", orderid="ORDER_1", resultvalue="10")
        assert item.value_plus_five == 15.0

    def test_session_field_raises_when_detached(self):
        item = MinimalResultItem(id="DETACHED", orderid="ORDER_1", resultvalue="75")
        with pytest.raises(RuntimeError, match="not bound to a session"):
            _ = item.prepost_example


class TestMultipleResults:
    def test_each_instance_caches_independently(self, session):
        """
        Two instances with different values should each compute and cache
        their own result — not share a cache at the class level.
        """
        low = make_result(session, "MR1", "10", serviceidcode="HB")
        high = make_result(session, "MR2", "90", serviceidcode="CREAT")

        assert low.value_plus_five == 15.0  # 10 + 5
        assert high.value_plus_five == 95.0  # 90 + 5

        assert low.__dict__["_cf_value_plus_five"] == 15.0
        assert high.__dict__["_cf_value_plus_five"] == 95.0

    def test_session_fields_compute_independently(self, session):
        """Each instance runs its own session query and caches its own result."""
        hb = make_result(session, "MR3", "10", serviceidcode="HB")  # × 2.0 → 20.0
        creat = make_result(session, "MR4", "10", serviceidcode="CREAT")  # × 0.5 → 5.0
        none_ = make_result(
            session, "MR5", "10", serviceidcode=None
        )  # no multiplier → 10.0

        assert hb.value_by_relationship == 20.0
        assert creat.value_by_relationship == 5.0
        assert none_.value_by_relationship == 10.0

    def test_expiring_one_instance_does_not_affect_another(self, session):
        """
        session.expire(item) targets a single instance.
        The sibling's session_computed_field cache should be untouched.
        """
        a = make_result(session, "MR6", "75")
        b = make_result(session, "MR7", "75")

        _ = a.prepost_example
        _ = b.prepost_example

        session.expire(a)

        assert "_cf_prepost_example" not in a.__dict__  # cleared
        assert "_cf_prepost_example" in b.__dict__  # untouched

    def test_mixed_field_types_across_instances(self, session):
        """
        Instances with both computed_field and session_computed_field:
        after expiry the pure-Python cache survives on both,
        and only the session caches are cleared.
        """
        a = make_result(session, "MR8", "10", serviceidcode="HB")
        b = make_result(session, "MR9", "20", serviceidcode="CREAT")

        # Populate all caches on both instances
        _ = a.value_plus_five  # computed_field
        _ = a.value_by_relationship  # session_computed_field
        _ = b.value_plus_five
        _ = b.value_by_relationship

        session.expire(a)
        session.expire(b)

        # Pure-Python caches survived on both
        assert "_cf_value_plus_five" in a.__dict__
        assert "_cf_value_plus_five" in b.__dict__

        # Session caches cleared on both
        assert "_cf_value_by_relationship" not in a.__dict__
        assert "_cf_value_by_relationship" not in b.__dict__

    def test_different_computed_fields_on_same_instance(self, session):
        """
        All four computed fields on a single instance each produce the
        correct result independently and cache under separate keys.
        """
        item = make_result(session, "MR10", "10", serviceidcode="HB")

        assert item.value_plus_five == 15.0  # computed_field:         10 + 5
        assert item.prepost_example == "less"  # session_computed_field: 10 < 50
        assert item.value_by_relationship == 20.0  # session_computed_field: 10 × 2.0
        assert item.value_by_manual_query == 20.0  # session_computed_field: 10 × 2.0

        assert "_cf_value_plus_five" in item.__dict__
        assert "_cf_prepost_example" in item.__dict__
        assert "_cf_value_by_relationship" in item.__dict__
        assert "_cf_value_by_manual_query" in item.__dict__

    def test_stale_cache_after_local_mutation(self, session):
        """
        Documents known behaviour: mutating a column locally does NOT
        invalidate a computed_field cache since no expire event fires.
        If correctness after local mutation matters, use session_computed_field.
        """
        item = make_result(session, "MR11", "10")
        assert item.value_plus_five == 15.0  # cached

        item.resultvalue = "99"  # local mutation — no expire fired

        # Cache is stale — still returns the original value
        assert item.value_plus_five == 15.0  # known limitation, not a bug


class TestComputedHybrid:
    def test_instance_returns_correct_value(self, session):
        item = make_result(session, "H1", "10")
        assert item.value_plus_ten == 20.0

    def test_instance_none_value_returns_none(self, session):
        item = make_result(session, "H2", None)
        assert item.value_plus_ten is None

    def test_not_cached_on_instance(self, session):
        """hybrid_property has no cache — no _cf_ key should appear in __dict__."""
        item = make_result(session, "H3", "10")
        _ = item.value_plus_ten
        assert "_cf_value_plus_ten" not in item.__dict__

    def test_recalculates_after_local_mutation(self, session):
        """
        Unlike computed_field, hybrid_property recalculates every access —
        so a local column mutation is immediately reflected.
        """
        item = make_result(session, "H4", "10")
        assert item.value_plus_ten == 20.0

        item.resultvalue = "90"

        assert item.value_plus_ten == 100.0  # reflects new value, no stale cache

    def test_usable_in_where_clause(self, session):
        """Core hybrid_property benefit: works as a SQL expression in queries."""
        make_result(session, "H5", "5")  # value_plus_ten = 15 — excluded
        make_result(session, "H6", "20")  # value_plus_ten = 30 — included
        make_result(session, "H7", "40")  # value_plus_ten = 50 — included

        results = session.scalars(
            select(MinimalResultItem).where(MinimalResultItem.value_plus_ten > 20)
        ).all()

        ids = {r.id for r in results}
        assert "H6" in ids
        assert "H7" in ids
        assert "H5" not in ids

    def test_usable_in_order_by(self, session):
        make_result(session, "H8", "30")
        make_result(session, "H9", "10")
        make_result(session, "H10", "20")

        results = session.scalars(
            select(MinimalResultItem)
            .where(MinimalResultItem.id.in_(["H8", "H9", "H10"]))
            .order_by(MinimalResultItem.value_plus_ten.asc())
        ).all()

        assert [r.id for r in results] == ["H9", "H10", "H8"]

    def test_class_level_access_returns_hybrid(self, session):
        """Class-level access should return the hybrid property/QueryableAttribute, not a value."""
        assert isinstance(MinimalResultItem.value_plus_ten, QueryableAttribute)

    def test_survives_expire_and_recalculates(self, session):
        """After expire the hybrid still recalculates correctly from the reloaded column."""
        item = make_result(session, "H11", "10")
        assert item.value_plus_ten == 20.0

        session.execute(
            update(MinimalResultItem)
            .where(MinimalResultItem.id == "H11")
            .values(resultvalue="50")
        )
        session.expire(item)

        assert item.value_plus_ten == 60.0
