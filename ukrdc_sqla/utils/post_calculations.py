from typing import TYPE_CHECKING

from sqlalchemy.orm import Session

if TYPE_CHECKING:
    from ukrdc_sqla.ukrdc import ResultItem,LabOrder


def example_prepost(result_item: "ResultItem", session: Session) -> str:
    if result_item.value >= 50:
        return "greater"
    return "less"


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
def prepost_calculation(lab_order: "LabOrder", session: Session) -> str:

    # Check first if they are a patient that would even need dialysis in the first place?
    # I.e ignore transplanted patients
    # Save getting all dialysis sessions
    # AdmitReasonCode on Treatment record via ModalityCodes, Modality_Type = HD.
    def _patient_on_dialysis(lab_order: "LabOrder") -> bool:

        for treatment in lab_order.record.treatments:

            # We probably need to include the other HD adjacent modality codes such as 4
            if (treatment.admit_reason_code == 1 and treatment.to_time is None):

                return True
            
        return False

    # Check if the resultitem was relating to a dialysis session
    # Is there a risk that with patients on CF_RR7_TREATMENT treatment 4 (dialysis daily)
    # that this might be incorrect?
    def _dialysed_on_result_date(lab_order: "LabOrder") -> bool:

        date = lab_order.specimencollectedtime.date()

        record = lab_order.record

        sessions = record.dialysis_sessions.filter_by(date=date).all()

        # As a sanity check should we check that there are not more than one dialysis session on a day
        # This probably already done as part of data validation?
        return len(sessions) > 0

    # Set all the resultitems in that laborder to the calculated prepost value
    # Are we assigning in place or returning them?
    def _assign_prepost(lab_order: "LabOrder", value: str) -> str:

        for result_item in lab_order.resultitems:

            # Should we check if some prepost value already exists before overwriting it?
            result_item.prepost = value

        return

    # For a specific blood measurement code, check that across laborders that day that the result reduces enough to be considered 
    def _reduces_within_range(code, min_delta):

        return
    
    if not _patient_on_dialysis(lab_order) or not _dialysed_on_result_date(lab_order):

        _assign_prepost(lab_order, "NA")

        return
    

    # A more robust version of the code from Leicester: 


    # On the day of dialysis, sort laborders resultitem value provided there are at least 2 entries
    # Weighted ensemble of whether a laborder is pre or post based on each individual result item 
    # There should be a minimum difference between pre and post values to consider them valid

    # The idea here is to give each indicating code a 'vote' of what the correct pre/post markings are
    # If most (say 75% of results) agree on the pre/post designation, we can assign it. Otherwise, it is UNK

    # Creatinine, urea, potassium, phosphate
    # Is lab calculated eGFR appropriate?
    indicating_codes = ['QBLA1', 'QBLA3', 'QBLA9', 'QBLB1']

    for code in indicating_codes:

    # Mark the highest value as pre and the lowest value post
        # There should probably be a minimum difference between pre and post values to consider them valid


    # The laborders that contain the QBLA3 pre/post should have all other resultitems on the same laborder marked accordingly
        # Is this misleading if only QBLA3 is used to determine pre/post and other resultitems do not align?

    return prepost_value
