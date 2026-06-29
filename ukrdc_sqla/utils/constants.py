from dataclasses import dataclass


@dataclass
class RelationshipType:
    """Links to the vwe_facility_relationship table, relationshiptype column"""
    feedshare: str = "FEED-SHARE"
    main_satellite: str = "MAIN-SATELLITE"


@dataclass
class CodeMapFacilityType:
    """Links to the code_map table, source_coding_standard and destination_coding_standard columns"""
    satellite: str = "RR1+_SATELLITE"
    main: str = "RR1+_MAIN"
    feedshare_child: str = "RR1+_FEEDSHARE_CHILD"
    feedshare_parent: str = "RR1+_FEEDSHARE_PARENT"