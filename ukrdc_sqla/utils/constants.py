from dataclasses import dataclass


@dataclass
class RelationshipType:
    """Links to the vwe_facility_relationship table, relationshiptype column"""

    feedshare: str = "FEED-SHARE"
    main_satellite: str = "MAIN-SATELLITE"
    deprecated_current: str = "DEPRECATED-CURRENT"


@dataclass
class CodeMapFacilityType:
    """Links to the code_map table, source_coding_standard and destination_coding_standard columns"""

    satellite: str = "RR1+_SATELLITE"
    main: str = "RR1+_MAIN"
    feedshare_child: str = "RR1+_FEEDSHARE_CHILD"
    feedshare_parent: str = "RR1+_FEEDSHARE_PARENT"
    deprecated: str = "RR1+_DEPRECATED"
    current: str = "RR1+_CURRENT"


@dataclass
class FacilityType:
    """Links to the facility table, facilitytype column"""

    multiple_centre: str = "Multiple Centre"
    adult_renal_centre: str = "Adult Renal Centre"
    paediatric_renal_centre: str = "Paediatric Renal Centre"
    other: str = "Other"


@dataclass
class GpType:
    """Links to the gp table, type column"""

    gp: str = "GP"
    practice: str = "PRACTICE"
