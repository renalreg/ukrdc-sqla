from datetime import datetime
from sqlalchemy import event
import ukrdc_sqla.utils.post_calculations as post_calculations
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from ukrdc_sqla.ukrdc import (
    Base,
    PatientRecord,
    Treatment,
    DialysisSession,
    LabOrder,
    ResultItem,
)
from unittest.mock import Mock


@pytest.fixture
def session():
    engine = create_engine("sqlite:///:memory:")

    # UKRDC models require a now() which is not available in sqlite
    @event.listens_for(engine, "connect")
    def register_now(dbapi_connection, connection_record):
        dbapi_connection.create_function(
            "now", 0, lambda: datetime.now().isoformat(sep=" ")
        )

    tables = [
        PatientRecord.__table__,
        Treatment.__table__,
        DialysisSession.__table__,
        LabOrder.__table__,
        ResultItem.__table__,
    ]
    Base.metadata.create_all(engine, tables=tables)

    with Session(engine) as db_session:
        yield db_session

    engine.dispose()


@pytest.fixture
def patient_record(session):
    now = datetime.now()
    patient_record = PatientRecord(
        pid="TEST_PID",
        sendingfacility="TST001",
        sendingextract="TEST",
        localpatientid="LOCAL123",
        repositorycreationdate=now,
        repositoryupdatedate=now,
    )
    session.add(patient_record)

    return patient_record


@pytest.fixture
def lab_order(session, patient_record):
    lab_order = LabOrder(
        id="TEST_ORDER",
        pid=patient_record.pid,
        specimencollectedtime=datetime(2025, 1, 1, 0, 0),
    )
    session.add(lab_order)

    return lab_order


"""Helper function unit tests"""


def test__prepost_already_calculated(session, lab_order):

    result_item = ResultItem(
        id="TEST_RESULT",
        orderid=lab_order.id,
        calculated_prepost="PRE",
    )
    session.add(result_item)

    assert post_calculations._prepost_already_calculated(lab_order) is True


def test__patient_on_dialysis_true(session, patient_record):

    treatment = Treatment(
        id="TEST_TREATMENT",
        pid=patient_record.pid,
        admit_reason_code="1",
        to_time=None,
    )
    session.add(treatment)

    assert post_calculations._patient_on_dialysis(patient_record) is True


def test__patient_on_dialysis_false(session, patient_record):

    treatment = Treatment(
        id="TEST_TREATMENT",
        pid=patient_record.pid,
        admit_reason_code="1",
        to_time=datetime(2025, 1, 1, 0, 0),
    )
    session.add(treatment)

    assert post_calculations._patient_on_dialysis(patient_record) is False


def test__dialysed_on_result_date_true(session, patient_record):

    dialysis_session = DialysisSession(
        id="TEST_SESSION",
        pid=patient_record.pid,
        proceduretime=datetime(2025, 1, 1, 0, 0),
    )
    session.add(dialysis_session)

    assert (
        post_calculations._dialysed_on_result_date(patient_record, datetime(2025, 1, 1))
        is True
    )


def test__dialysed_on_result_date_false(session, patient_record):

    dialysis_session = DialysisSession(
        id="TEST_SESSION",
        pid=patient_record.pid,
        proceduretime=datetime(2025, 1, 1, 0, 0),
    )
    session.add(dialysis_session)

    assert (
        post_calculations._dialysed_on_result_date(patient_record, datetime(2025, 1, 2))
        is False
    )


def test__assign_prepost(session, lab_order):

    result_item_1 = ResultItem(
        id="TEST_RESULT_1",
        orderid=lab_order.id,
        calculated_prepost=None,
    )
    session.add(result_item_1)

    result_item_2 = ResultItem(
        id="TEST_RESULT_2",
        orderid=lab_order.id,
        calculated_prepost=None,
    )
    session.add(result_item_2)

    post_calculations._assign_prepost(lab_order, "POST")

    assert result_item_1.calculated_prepost == "POST"
    assert result_item_2.calculated_prepost == "POST"


def test__get_laborders_for_date(session, patient_record):

    second_lab_order = LabOrder(
        id="TEST_ORDER_2",
        pid=patient_record.pid,
        specimencollectedtime=datetime(2025, 1, 2, 0, 0),
    )
    session.add(second_lab_order)

    third_lab_order = LabOrder(
        id="TEST_ORDER_3",
        pid=patient_record.pid,
        specimencollectedtime=datetime(2025, 1, 1, 0, 0),
    )
    session.add(third_lab_order)

    days_laborders = post_calculations._get_laborders_for_date(
        patient_record, datetime(2025, 1, 1)
    )

    assert all(
        lab_order.specimencollectedtime.date() == datetime(2025, 1, 1)
        for lab_order in days_laborders
    )


"""Main logic integration tests"""


def test_single_laborder_gets_unk(session, lab_order):

    post_calculations.prepost_calculation(lab_order, session)

    assert all(
        result_item.calculated_prepost == "UNK"
        for result_item in lab_order.result_items
    )


def test_not_on_dialysis_gets_na(session, lab_order):

    result_item = ResultItem(
        id="TEST_RESULT",
        orderid="TEST_ORDER",
        calculated_prepost=None,
    )
    session.add(result_item)

    post_calculations.prepost_calculation(lab_order, session)

    assert result_item.calculated_prepost == "NA"


def test_not_dialysed_on_result_date_gets_na(session, patient_record, lab_order):

    # Already set in fixture but just being explicit
    lab_order.specimencollectedtime = datetime(2025, 1, 1, 0, 0)

    result_item = ResultItem(
        id="TEST_RESULT",
        orderid="TEST_ORDER",
        calculated_prepost=None,
    )
    session.add(result_item)

    # Makes _patient_on_dialysis return True
    treatment = Treatment(
        id="TEST_TREATMENT",
        pid=patient_record.pid,
        admit_reason_code="1",
        to_time=None,
    )
    session.add(treatment)

    dialysis_session = DialysisSession(
        id="TEST_SESSION",
        pid=patient_record.pid,
        proceduretime=datetime(2025, 1, 2, 0, 0),
    )
    session.add(dialysis_session)

    post_calculations.prepost_calculation(lab_order, session)

    assert result_item.calculated_prepost == "NA"


def test_already_calculated_skips_recalculation(session, lab_order, monkeypatch):

    result_item = ResultItem(
        id="TEST_RESULT",
        orderid="TEST_ORDER",
        calculated_prepost="PRE",
    )
    session.add(result_item)

    monkeypatch.setattr(post_calculations, "_assign_prepost", Mock())

    post_calculations.prepost_calculation(lab_order, session)

    assert post_calculations._assign_prepost.call_count == 0


# @pytest.mark.parametrize()
def test_insufficient_drop_gets_unk(session, lab_order):

    pass


# @pytest.mark.parametrize()
def test_sufficient_drop_gets_prepost(session, lab_order):

    pass


# @pytest.mark.parametrize()
def test_middle_laborder_gets_unk(session, lab_order):

    pass
