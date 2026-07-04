from typing import TYPE_CHECKING

from sqlalchemy.orm import Session

if TYPE_CHECKING:
    from ukrdc_sqla.ukrdc import ResultItem


def example_prepost(result_item: "ResultItem", session: Session) -> str:
    if result_item.value >= 50:
        return "greater"
    return "less"
