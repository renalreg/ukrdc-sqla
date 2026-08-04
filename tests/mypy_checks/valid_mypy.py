"""
Static type-checking fixture - the "valid" case.

Nothing in this file is executed. It exists purely so `mypy` can be run
against it (see ../test_relationship_typing.py) to prove that the
`DynamicMapped` relationship typing in ukrdc_sqla.ukrdc type-checks cleanly
for realistic usage patterns:

  * "dynamic" relationships (lazy=GLOBAL_LAZY) support Query-style access
    (.filter, .filter_by, .order_by, .all, .first, .one_or_none, .count)
    as well as collection-mutation (.append, .remove).
  * plain (lazy="select") relationships still behave as ordinary lists.

Running `mypy valid_mypy.py` on this file must exit 0 with no errors.
"""

from typing import List, assert_type

from sqlalchemy.orm.dynamic import AppenderQuery

from ukrdc_sqla.ukrdc import (
    LabOrder,
    OptOut,
    Patient,
    PatientNumber,
    PatientRecord,
    ResultItem,
    SocialHistory,
)


def dynamic_relationship_supports_query_api(record: PatientRecord) -> None:
    """This is the exact pattern that originally failed under mypy."""

    filtered = record.lab_orders.filter(LabOrder.status == "closed")
    assert_type(filtered, AppenderQuery[LabOrder])

    filtered_by = record.lab_orders.filter_by(status="closed")
    assert_type(filtered_by, AppenderQuery[LabOrder])

    ordered = record.lab_orders.order_by(LabOrder.enteredon)
    assert_type(ordered, AppenderQuery[LabOrder])

    all_orders = record.lab_orders.all()
    assert_type(all_orders, List[LabOrder])

    first_order = record.lab_orders.first()
    assert_type(first_order, LabOrder | None)

    one_or_none_order = record.lab_orders.one_or_none()
    assert_type(one_or_none_order, LabOrder | None)

    order_count = record.lab_orders.count()
    assert_type(order_count, int)

    chained = (
        record.lab_orders.filter(LabOrder.status == "closed")
        .order_by(LabOrder.enteredon)
        .all()
    )
    assert_type(chained, List[LabOrder])


def dynamic_relationship_supports_collection_mutation(
    record: PatientRecord, order: LabOrder
) -> None:
    """ "dynamic" relationships are still mutable collections, not read-only queries."""
    record.lab_orders.append(order)
    record.lab_orders.remove(order)


def nested_dynamic_relationship(order: LabOrder) -> None:
    """LabOrder.result_items is also dynamic and should behave the same way."""
    closed_items = order.result_items.filter(ResultItem.resultvalue.isnot(None)).all()
    assert_type(closed_items, List[ResultItem])


def dynamic_relationship_on_patient(patient: Patient) -> None:
    """Patient.numbers is dynamic too."""
    ni_numbers = patient.numbers.filter(PatientNumber.numbertype == "NI").all()
    assert_type(ni_numbers, List[PatientNumber])


def previously_untyped_opt_outs(record: PatientRecord) -> None:
    """opt_outs previously had no `Mapped[...]` annotation at all."""
    active = record.opt_outs.filter(OptOut.programname == "PVOptOut").all()
    assert_type(active, List[OptOut])


def plain_relationship_behaves_as_list(
    record: PatientRecord, history: SocialHistory
) -> None:
    """social_histories has no lazy=GLOBAL_LAZY, so it's a normal list."""
    assert_type(record.social_histories, List[SocialHistory])

    record.social_histories.append(history)
    count = len(record.social_histories)
    assert_type(count, int)
    first_item = record.social_histories[0]
    assert_type(first_item, SocialHistory)
