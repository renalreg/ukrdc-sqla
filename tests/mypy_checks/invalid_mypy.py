"""
Static type-checking fixture - the "invalid" case.

Nothing in this file is executed. Every function below contains exactly one
deliberate type error. This file exists so `mypy` can be run against it (see
../test_relationship_typing.py) to prove mypy is still doing real, precise
type-checking on the fixed relationship annotations - i.e. the fix didn't
just loosen everything into `Any`.

Running `mypy invalid_mypy.py` on this file must exit non-zero, with exactly
one error per function below.
"""

from ukrdc_sqla.ukrdc import LabOrder, PatientRecord, SocialHistory


def plain_relationship_rejects_query_api(record: PatientRecord) -> None:
    # `social_histories` is a plain `Mapped[List[SocialHistory]]`, i.e. a
    # real `list` at runtime - it has no `.filter()` method.
    record.social_histories.filter()


def dynamic_relationship_rejects_wrong_element_type(
    record: PatientRecord, history: SocialHistory
) -> None:
    # `lab_orders` is `DynamicMapped["LabOrder"]`; appending a SocialHistory
    # instance is a type mismatch.
    record.lab_orders.append(history)


def column_assignment_rejects_wrong_type(record: PatientRecord) -> None:
    # `pid` is `Mapped[str]`; assigning an int is a type mismatch.
    record.pid = 123


def relationship_all_returns_wrong_element_type(record: PatientRecord) -> None:
    # `.all()` on a dynamic relationship returns `List[LabOrder]`, not
    # `List[SocialHistory]` - this assignment should be rejected.
    orders: list[SocialHistory] = record.lab_orders.all()