"""rename facility table

Revision ID: 55b2defd9a75
Revises: ce5cf736eff9
Create Date: 2026-10-27 14:52:00.823526

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql
from triggers import create_triggers, drop_triggers
from views import create_views, drop_views

revision = "55b2defd9a75"
down_revision = "ce5cf736eff9"
branch_labels = None
depends_on = None

# ukrdc_resources_database commit SHA (or release tag) the views are built from.
# None keeps the previous revision's views.
VIEWS_REF = "d1396e1a892ec7f2a436d4d0cfb73f1566ecc863"

RADAR_OUT_COMMENT = (
    "Master switch for RADAR export for this facility. If false, nothing exports "
    "for this facility, regardless of enabled_radar_extracts or which extracts are "
    "enabled globally."
)
ENABLED_RADAR_EXTRACTS_COMMENT = (
    "Sending extracts that RADAR should export for this facility. An extract must "
    "ALSO be enabled globally via SendingExtractMetadata.enable_radar_export - this "
    "list only narrows that down per facility, it cannot widen it. A null/empty list "
    "means nothing exports for this facility."
)

# Every column, in table order - used for the data copy in both directions.
FACILITY_COLUMNS = [
    "facilitycode",
    "facilitycodestd",
    "facilitytype",
    "pkbout",
    "pkbmsgexclusions",
    "pkb_pv_msg_exclusions",
    "pkb_ukrdc_msg_exclusions",
    "ukrdcoutpkb",
    "pvoutpkb",
    "radar_out",
    "enabled_radar_extracts",
    "startdate",
    "enddate",
    "firstdataquarter",
    "pkboutstartdate",
    "creation_date",
    "update_date",
]


def _create_facility_table(table_name):
    """Create a facility-shaped table called `table_name`."""
    op.create_table(
        table_name,
        sa.Column("facilitycode", sa.String(length=100), nullable=False),
        sa.Column("facilitycodestd", sa.String(length=256), nullable=False),
        # The facility_type enum already exists (it's used by the table being
        # copied from), so don't try to CREATE TYPE it again.
        sa.Column(
            "facilitytype",
            postgresql.ENUM(
                "Multiple Centre",
                "Adult Renal Centre",
                "Paediatric Renal Centre",
                "Other",
                name="facility_type",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column(
            "pkbout", sa.Boolean(), server_default=sa.text("false"), nullable=False
        ),
        sa.Column("pkbmsgexclusions", postgresql.ARRAY(sa.Text()), nullable=True),
        sa.Column("pkb_pv_msg_exclusions", postgresql.ARRAY(sa.Text()), nullable=True),
        sa.Column(
            "pkb_ukrdc_msg_exclusions", postgresql.ARRAY(sa.Text()), nullable=True
        ),
        sa.Column(
            "ukrdcoutpkb", sa.Boolean(), server_default=sa.text("false"), nullable=False
        ),
        sa.Column(
            "pvoutpkb", sa.Boolean(), server_default=sa.text("false"), nullable=False
        ),
        sa.Column(
            "radar_out",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=False,
            comment=RADAR_OUT_COMMENT,
        ),
        sa.Column(
            "enabled_radar_extracts",
            postgresql.ARRAY(sa.Text()),
            nullable=True,
            comment=ENABLED_RADAR_EXTRACTS_COMMENT,
        ),
        sa.Column("startdate", sa.DateTime(), nullable=True),
        sa.Column("enddate", sa.DateTime(), nullable=True),
        sa.Column("firstdataquarter", sa.Integer(), nullable=True),
        sa.Column("pkboutstartdate", sa.DateTime(), nullable=True),
        sa.Column(
            "creation_date",
            sa.DateTime(),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "update_date",
            sa.DateTime(),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["facilitycode", "facilitycodestd"],
            ["code_list.code", "code_list.coding_standard"],
            name=f"{table_name}_facilitycode_facilitycodestd_fkey",
            onupdate="CASCADE",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint(
            "facilitycode", "facilitycodestd", name=f"{table_name}_pkey"
        ),
    )


def _copy_rows(source, target):
    cols = ", ".join(FACILITY_COLUMNS)
    op.execute(f"INSERT INTO {target} ({cols}) SELECT {cols} FROM {source}")


def upgrade():
    drop_triggers()
    drop_views(down_revision, revision)

    # Remove the old facility table if it is still around.
    op.execute("DROP TABLE IF EXISTS facility")

    # "Rename" facility_new -> facility: create, copy, drop.
    _create_facility_table("facility")
    _copy_rows("facility_new", "facility")
    op.drop_table("facility_new")

    create_views(revision)
    create_triggers()  # update_date trigger on any new table


def downgrade():
    drop_triggers()
    drop_views(revision, down_revision)

    # Reverse: recreate facility_new, copy the data back, drop facility.
    # Note: whatever old facility table existed before upgrade() is not restored.
    _create_facility_table("facility_new")
    _copy_rows("facility", "facility_new")
    op.drop_table("facility")

    create_views(down_revision)
    create_triggers()
