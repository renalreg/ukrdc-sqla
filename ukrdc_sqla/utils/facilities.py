from sqlalchemy import select
from sqlalchemy.orm import Session

from ukrdc_sqla.ukrdc import FacilityRelationship

from .constants import RelationshipType


def get_facility_parent_unit(
    ukrdc3: Session,
    facility_codes: set[str],
) -> dict[str, str]:
    """Find the parent unit of each given facility code

    Facilities that are satellites resolve to their parent unit's code.
    Facilities that are not satellites (i.e. are themselves a main unit)
    are not included in the returned mapping.

    Args:
        ukrdc3 (Session): SQLAlchemy session
        facility_codes (set[str]): Facility codes to resolve

    Returns:
        dict[str, str]: Mapping of facility code -> parent unit code
    """
    if not facility_codes:
        return {}

    relationship_stmt = select(
        FacilityRelationship.childfacilitycode,
        FacilityRelationship.parentfacilitycode,
    ).where(
        FacilityRelationship.relationshiptype == RelationshipType.main_satellite,
        FacilityRelationship.childfacilitycode.in_(facility_codes),
    )
    relationship_rows = ukrdc3.execute(relationship_stmt).all()

    return {row.childfacilitycode: row.parentfacilitycode for row in relationship_rows}
