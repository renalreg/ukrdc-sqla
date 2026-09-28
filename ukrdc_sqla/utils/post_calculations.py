from typing import TYPE_CHECKING

from sqlalchemy.orm import Session

if TYPE_CHECKING:
    from ukrdc_sqla.ukrdc import ResultItem, PatientRecord


def example_prepost(result_item: "ResultItem", session: Session) -> str:
    if result_item.value >= 50:
        return "greater"
    return "less"

def prepost_calculation(result_item: "ResultItem", session: Session) -> str:

    # Check if the resultitem was relating to a dialysis session
    def _was_on_dialysis(ukrdcid, result_item_date):

        return False

    # Get the day of the resultitem
    # Observationtime is mandatory, enteredon is not
    dates = [result_item.observationtime.date()]

    # Some logic to check both resultitem days if they are different
    if result_item.enteredon.date() is not None:
        if result_item.observationtime.date() != result_item.enteredon.date():
            dates = [result_item.observationtime.date(), result_item.enteredon.date()]


    # Check for dialysis on both dates (if applicable)
    for date in dates:

        # Check the treatments for dialysis on that day
        if not _was_on_dialysis(id, date):

            result_item.prepost = "UNK"

    return
