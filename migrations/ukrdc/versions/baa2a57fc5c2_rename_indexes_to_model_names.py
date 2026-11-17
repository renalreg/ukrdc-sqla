"""rename indexes to model names

Revision ID: baa2a57fc5c2
Revises: 55b2defd9a75
Create Date: 2026-11-13 16:07:38.598809

Gives every index the models define the name the models give it (ix_<table>_<column> for
the ones declared with index=True).

- Live has these under older names (e.g. laborder_pid_idx). ALTER INDEX ... RENAME is a
  catalog change only: no rebuild, and on PostgreSQL 12+ it doesn't block reads or writes.
- A database built from the migrations never had most of them, so the missing ones are
  created and it matches the models (what CI's `migrate.py check` compares).
- Local and staging have eight composite idx_* indexes live doesn't. They are now in the
  models and are built here like the others, inside the migration's transaction: on live
  each blocks writes to its table until the migration commits.
- idx_observation_pid_serviceidcode_observationtime is renamed to
  idx_observation_pid_observationcode_observationtime: it indexes observationcode, not
  serviceidcode.

Views and triggers are left as they are: no column changes, and rebuilding them would lock
every table on live for nothing.
"""

from alembic import op

revision = "baa2a57fc5c2"
down_revision = "55b2defd9a75"
branch_labels = None
depends_on = None

# ukrdc_resources_database commit SHA (or release tag) the views are built from.
# None keeps the previous revision's views.
VIEWS_REF = None

# Every index the models define. Run only where the index is missing.
INDEXES = {
    "ix_address_pid": "CREATE INDEX ix_address_pid ON address (pid)",
    "ix_contactdetail_pid": "CREATE INDEX ix_contactdetail_pid ON contactdetail (pid)",
    "ix_diagnosis_pid": "CREATE INDEX ix_diagnosis_pid ON diagnosis (pid)",
    "ix_dialysissession_pid": "CREATE INDEX ix_dialysissession_pid ON dialysissession (pid)",
    "ix_document_pid": "CREATE INDEX ix_document_pid ON document (pid)",
    "ix_laborder_creation_date": "CREATE INDEX ix_laborder_creation_date ON laborder (creation_date)",
    "ix_laborder_pid": "CREATE INDEX ix_laborder_pid ON laborder (pid)",
    "ix_laborder_repository_update_date": "CREATE INDEX ix_laborder_repository_update_date ON laborder (repository_update_date)",
    "ix_laborder_update_date": "CREATE INDEX ix_laborder_update_date ON laborder (update_date)",
    "ix_medication_pid": "CREATE INDEX ix_medication_pid ON medication (pid)",
    "ix_name_pid": "CREATE INDEX ix_name_pid ON name (pid)",
    "ix_observation_pid": "CREATE INDEX ix_observation_pid ON observation (pid)",
    "ix_observation_pid_obstime": "CREATE INDEX ix_observation_pid_obstime ON observation (pid, observationtime)",
    "ix_patientnumber_patientid": "CREATE INDEX ix_patientnumber_patientid ON patientnumber (patientid)",
    "ix_patientnumber_pid": "CREATE INDEX ix_patientnumber_pid ON patientnumber (pid)",
    "ix_patientrecord_ukrdcid": "CREATE INDEX ix_patientrecord_ukrdcid ON patientrecord (ukrdcid)",
    "patientrecord_key2": "CREATE UNIQUE INDEX patientrecord_key2 ON patientrecord (sendingfacility, sendingextract, localpatientid)",
    "ix_programmembership_pid": "CREATE INDEX ix_programmembership_pid ON programmembership (pid)",
    "ix_pvdelete_pid": "CREATE INDEX ix_pvdelete_pid ON pvdelete (pid)",
    "ix_resultitem_orderid": "CREATE INDEX ix_resultitem_orderid ON resultitem (orderid)",
    "ix_resultitem_serviceidcode": "CREATE INDEX ix_resultitem_serviceidcode ON resultitem (serviceidcode)",
    "resultitem_orderid_firstpart": "CREATE INDEX resultitem_orderid_firstpart ON resultitem (left(orderid, -32))",
    "ix_treatment_pid": "CREATE INDEX ix_treatment_pid ON treatment (pid)",
    "ix_treatment_pid_fromtime": "CREATE INDEX ix_treatment_pid_fromtime ON treatment (pid, fromtime)",
    # Composite indexes local and staging have and live doesn't.
    "idx_diagnosis_pid_diagnosiscode": "CREATE INDEX idx_diagnosis_pid_diagnosiscode ON diagnosis (pid, diagnosiscode)",
    "idx_laborder_pid_id": "CREATE INDEX idx_laborder_pid_id ON laborder (pid, id)",
    "idx_medication_pid_fromtime_totime": "CREATE INDEX idx_medication_pid_fromtime_totime ON medication (pid, fromtime, totime)",
    "idx_observation_pid_observationcode_observationtime": "CREATE INDEX idx_observation_pid_observationcode_observationtime ON observation (pid, observationcode, observationtime)",
    "idx_patientnumber_pid_numbertype_organization": "CREATE INDEX idx_patientnumber_pid_numbertype_organization ON patientnumber (pid, numbertype, organization)",
    "idx_renaldiagnosis_pid_diagnosiscodestd": "CREATE INDEX idx_renaldiagnosis_pid_diagnosiscodestd ON renaldiagnosis (pid, diagnosiscodestd)",
    "idx_resultitem_orderid_serviceidcode_observationtime": "CREATE INDEX idx_resultitem_orderid_serviceidcode_observationtime ON resultitem (orderid, serviceidcode, observationtime)",
    "idx_treatment_pid_admitreasoncode": "CREATE INDEX idx_treatment_pid_admitreasoncode ON treatment (pid, admitreasoncode)",
}


def upgrade():
    # Live's names -> the models' names. IF EXISTS: databases built from the migrations
    # don't have the old names.
    op.execute(
        "ALTER INDEX IF EXISTS laborder_creation_date_idx RENAME TO ix_laborder_creation_date"
    )
    op.execute("ALTER INDEX IF EXISTS laborder_pid_idx RENAME TO ix_laborder_pid")
    op.execute(
        "ALTER INDEX IF EXISTS laborder_repository_update_date_idx RENAME TO ix_laborder_repository_update_date"
    )
    op.execute(
        "ALTER INDEX IF EXISTS laborder_update_date_idx RENAME TO ix_laborder_update_date"
    )
    op.execute("ALTER INDEX IF EXISTS medication_pid_idx RENAME TO ix_medication_pid")
    op.execute("ALTER INDEX IF EXISTS name_pid_idx RENAME TO ix_name_pid")
    op.execute("ALTER INDEX IF EXISTS observation_pid_idx RENAME TO ix_observation_pid")
    op.execute(
        "ALTER INDEX IF EXISTS patientnumber_patientid RENAME TO ix_patientnumber_patientid"
    )
    op.execute(
        "ALTER INDEX IF EXISTS patientnumber_pid_idx RENAME TO ix_patientnumber_pid"
    )
    op.execute(
        "ALTER INDEX IF EXISTS resultitem_orderid_idx RENAME TO ix_resultitem_orderid"
    )
    op.execute(
        "ALTER INDEX IF EXISTS resultitem_serviceidcode RENAME TO ix_resultitem_serviceidcode"
    )
    # Local and staging only; the old name said serviceidcode for an observationcode index.
    op.execute(
        "ALTER INDEX IF EXISTS idx_observation_pid_serviceidcode_observationtime"
        " RENAME TO idx_observation_pid_observationcode_observationtime"
    )

    # Create the ones the database doesn't have. Each is looked up first, so a table whose
    # indexes all exist isn't touched (CREATE INDEX IF NOT EXISTS would still lock it
    # against writes until the migration commits).
    for name, create in INDEXES.items():
        op.execute(
            f"DO $$ BEGIN IF to_regclass('{name}') IS NULL THEN {create}; END IF; END $$"
        )


def downgrade():
    # Renames back only; nothing is dropped. ix_laborder_creation_date,
    # ix_laborder_repository_update_date, ix_laborder_update_date and
    # ix_patientnumber_patientid keep their names: the initial revision created them under
    # those names, and its downgrade drops them by those names. The idx_* indexes stay too:
    # local and staging had them before this revision.
    op.execute("ALTER INDEX IF EXISTS ix_laborder_pid RENAME TO laborder_pid_idx")
    op.execute("ALTER INDEX IF EXISTS ix_medication_pid RENAME TO medication_pid_idx")
    op.execute("ALTER INDEX IF EXISTS ix_name_pid RENAME TO name_pid_idx")
    op.execute("ALTER INDEX IF EXISTS ix_observation_pid RENAME TO observation_pid_idx")
    op.execute(
        "ALTER INDEX IF EXISTS ix_patientnumber_pid RENAME TO patientnumber_pid_idx"
    )
    op.execute(
        "ALTER INDEX IF EXISTS ix_resultitem_orderid RENAME TO resultitem_orderid_idx"
    )
    op.execute(
        "ALTER INDEX IF EXISTS ix_resultitem_serviceidcode RENAME TO resultitem_serviceidcode"
    )
    op.execute(
        "ALTER INDEX IF EXISTS idx_observation_pid_observationcode_observationtime"
        " RENAME TO idx_observation_pid_serviceidcode_observationtime"
    )