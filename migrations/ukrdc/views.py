# collection of views for alembic

VWE_FACILITY_RELATIONSHIP = """
CREATE MATERIALIZED VIEW vwe_facility_relationship AS
 SELECT
   f2.facilitycode    AS parentfacilitycode,
   f2.facilitycodestd AS parentfacilitycodestd,
   f1.facilitycode    AS childfacilitycode,
   f1.facilitycodestd AS childfacilitycodestd,
   CASE
     WHEN (
       (f1.facilitycodestd)::text = 'RR1+'::text AND
       (f2.facilitycodestd)::text = 'RR1+'::text AND
       (cm.source_coding_standard)::text = 'RR1+_FEEDSHARE_CHILD'::text AND
       (cm.destination_coding_standard)::text = 'RR1+_FEEDSHARE_PARENT'::text
     ) THEN 'FEED-SHARE'::text
     WHEN (
       (f1.facilitycodestd)::text = 'RR1+'::text AND
       (f2.facilitycodestd)::text = 'RR1+'::text AND
       (cm.source_coding_standard)::text = 'RR1+_SATELLITE'::text AND
       (cm.destination_coding_standard)::text = 'RR1+_MAIN'::text
     ) THEN 'MAIN-SATELLITE'::text
     WHEN (
       (f1.facilitycodestd)::text = 'RR1+'::text AND
       (f2.facilitycodestd)::text = 'RR1+'::text AND
       (cm.source_coding_standard)::text = 'RR1+_CURRENT'::text AND
       (cm.destination_coding_standard)::text = 'RR1+_DEPRECATED'::text
     ) THEN 'DEPRECATED-CURRENT'::text
     ELSE NULL::text
   END AS relationshiptype
 FROM facility_new f1
 JOIN code_map cm
   ON (f1.facilitycode)::text = (cm.source_code)::text
 JOIN facility_new f2
   ON (f2.facilitycode)::text = (cm.destination_code)::text
 WHERE (cm.source_coding_standard)::text = ANY (
   ARRAY[
     ('RR1+_FEEDSHARE_CHILD'::character varying)::text,
     ('RR1+_SATELLITE'::character varying)::text,
     ('RR1+_CURRENT'::character varying)::text
   ]
 )
 WITH NO DATA;
"""

VWE_SATELLITE_MAP = """
CREATE VIEW vwe_satellite_map AS
 SELECT
   parentfacilitycode AS main_unit_code,
   childfacilitycode  AS satellite_code
 FROM vwe_facility_relationship
 WHERE relationshiptype = 'MAIN-SATELLITE'::text;

"""


def set_view_owner(view, owner):
    command = f"""
    DO $$
    BEGIN
      IF EXISTS (SELECT FROM pg_roles WHERE rolname = '{owner}') THEN
        ALTER VIEW {view} OWNER TO {owner};
      END IF;
    END
    $$
    """
    return command


def set_materialized_view_owner(view, owner):
    command = f"""
    DO $$
    BEGIN
      IF EXISTS (SELECT FROM pg_roles WHERE rolname = '{owner}') THEN
        ALTER MATERIALIZED VIEW {view} OWNER TO {owner};
      END IF;
    END
    $$
    """
    return command


def drop_materialized_view(view):
    command = f"DROP MATERIALIZED VIEW IF EXISTS {view}"
    return command


def drop_view(view):
    command = f"DROP VIEW IF EXISTS {view}"
    return command
