from datetime import date, datetime, time, timedelta
from typing import TYPE_CHECKING

from sqlalchemy.orm import Session
from sqlalchemy import func

from ukrdc_sqla.ukrdc import ResultItem, LabOrder, PatientRecord, DialysisSession

"""Prepost Dialysis Calculation"""

def _prepost_already_calculated(lab_order: "LabOrder") -> bool:

    for result_item in lab_order.result_items:
        if result_item.calculated_prepost is not None:
            return True

    return False


# Check first if they are a patient that would even need dialysis in the first place
# Probably quicker than getting all DialysisSessions for the patient
# AdmitReasonCode on Treatment record via ModalityCodes, Modality_Type = HD.
def _patient_on_dialysis(patient_record: "PatientRecord") -> bool:

    for treatment in patient_record.treatments:
        # We probably need to include the other HD adjacent modality codes such as 4
        if (
            treatment.admit_reason_code == "1"  # Column maps to string
            and treatment.to_time is None
        ):
            return True

    return False


# Check if the resultitem was relating to a dialysis session
# Is there a risk that with patients on CF_RR7_TREATMENT treatment 4 (dialysis daily) that this might be incorrect?
# There are also some patients that do overnight dialysis at units rather than at home, will these be missed?
# Wondering how broad to be here given patient_on_dialysis checks treatments
# Should we filter by proceduretypecode as well?
def _dialysed_on_result_date(patient_record: "PatientRecord", date: date) -> bool:

    # This doesn't allow us to separate time component
    # sessions = patient_record.dialysis_sessions.filter_by(proceduretime=date).all()

    start = datetime.combine(date, time.min)
    end = start + timedelta(days=1)

    sessions = patient_record.dialysis_sessions.filter(
        DialysisSession.proceduretime >= start,
        DialysisSession.proceduretime < end,
    ).all()

    # As a sanity check should we check that there are not more than one dialysis session on a day
    # This probably already done as part of data validation?
    return len(sessions) > 0


# Set all the resultitems in that laborder to the calculated prepost value
# Will need to be adapted to Oliver's session implementations
def _assign_prepost(lab_order: "LabOrder", value: str) -> str:

    for result_item in lab_order.result_items:
        result_item.calculated_prepost = value

    return


def _get_laborders_for_date(patient_record: "PatientRecord", date: date):

    return [
        lab_order
        for lab_order in patient_record.lab_orders
        if lab_order.specimencollectedtime.date() == date
    ]


# For a specific blood measurement code, check that across laborders that day that the result reduces enough to be considered
# 45% or less urea clearance during treatement is not desirable. This could be a poor dialysis session
def _reduces_within_range(code, min_delta):

    return


# Questions
# - Should we consider both observationtime and enteredon dates for dialysis check?
# - Should we honour existing prepost values or replace them?
# - Should we be checking a single record, or the entire patient?
# - Should we only check in an incoming file for a dialysis session, or across all historical data?
# - Which resultitem codes should be ignored? (i.e which ones are not relevant to dialysis)
# - Will the calculation happen after the record is commited to the database?
# - Should we do this on a table or a single laborder?


# Would it be quicker to do this per dialysis session?
# Effectively this function would be called fewer times as number of DialysisSessions > Laborders
def prepost_calculation(lab_order: "LabOrder", session: Session = None) -> str:

    # Because we are always assign prepost values to an entire day's batch, this should skip all laborders in a day
    if _prepost_already_calculated(lab_order):
        return

    patient_record = lab_order.record

    lab_order_date = lab_order.specimencollectedtime.date()

    days_laborders = _get_laborders_for_date(patient_record, lab_order_date)

    # No way to know if prepost
    if len(days_laborders) == 1:
        _assign_prepost(days_laborders[0], "UNK")

    if not _patient_on_dialysis(patient_record) or not _dialysed_on_result_date(
        patient_record, lab_order_date
    ):
        for lab_order in days_laborders:
            _assign_prepost(lab_order, "NA")

        return

    # A more robust version of the code from Leicester:

    # On the day of dialysis, sort laborders resultitem value provided there are at least 2 entries
    # Weighted ensemble of whether a laborder is pre or post based on each individual result item
    # There should be a minimum difference between pre and post values to consider them valid

    # The idea here is to give each indicating code a 'vote' of what the correct pre/post markings are
    # If most (say 75% of results THAT EXIST) agree on the pre/post designation, we can assign it. Otherwise, it is UNK

    # QBLA1 Creatinine
    # QBLA3 Urea
    # QBLA6 Sodium
    # QBLA9 Potassium - Some patients will have potassium rising in dialysis due to articifial addition (bolimic patients need it added in their dialysate)
    # QBLAC Uric acid
    # QBLB1 Phosphate
    # QBLB3 Calcium
    # Minimum fractional drop for a value to count as "post"
    INDICATING_CODES = {"QBLA1": 0.3, "QBLA3": 0.3, "QBLB1": 0.3}

    for codes, min_delta in INDICATING_CODES.items():
        pass

    # Making lists of sorted laborders based on codes will not work, in the case of some laborders of the day having missing values

    return
