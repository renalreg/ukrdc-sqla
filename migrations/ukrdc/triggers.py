"""Triggers that keep the audit timestamps up to date, whoever writes to the database.

- trg_set_update_date: BEFORE UPDATE on every table with an update_date column, sets it to
  now(). Models only set update_date when the ORM writes the row; this covers everything
  else (other services, SQL scripts).
- trg_set_laborder_repository_update_date: on resultitem, sets the parent
  laborder.repository_update_date to now() when a result is added, changed or deleted, so
  extracts see the lab order as changed.

These replace the old generate_triggers.py script, with the same function and trigger
names, so a database that already has them keeps them as they are.

    from triggers import create_triggers, drop_triggers

The revision that adds them calls create_triggers() in upgrade() and drop_triggers() in
downgrade(). Later revisions call create_triggers() at the end of upgrade() and downgrade()
(script.py.mako does), so tables they add get the trigger too, and tables whose update_date
they drop or rename lose it. It only touches tables whose trigger is missing or no longer
fits, so it doesn't lock the others.

Triggers don't need dropping around schema changes the way views do: column type changes,
and adding or dropping tables, work with them in place.

Everything runs in the schema the migrations run in (the first on the search_path).
"""

from __future__ import annotations

from alembic import op

UPDATE_FUNCTION = "trigger_fnc_set_update_date"
UPDATE_TRIGGER = "trg_set_update_date"
LABORDER_FUNCTION = "trigger_fnc_set_laborder_repository_update_date"
LABORDER_TRIGGER = "trg_set_laborder_repository_update_date"


def create_triggers() -> None:
    """Create the functions, and the triggers on any table that should have one and doesn't."""
    op.execute(f"""
CREATE OR REPLACE FUNCTION {UPDATE_FUNCTION}()
RETURNS trigger
LANGUAGE plpgsql
AS $fn$
BEGIN
  NEW.update_date = now();
  RETURN NEW;
END
$fn$""")

    # SET search_path FROM CURRENT pins laborder to this schema, whatever the search_path of
    # the session that fires the trigger.
    op.execute(f"""
CREATE OR REPLACE FUNCTION {LABORDER_FUNCTION}()
RETURNS trigger
LANGUAGE plpgsql
SET search_path FROM CURRENT
AS $fn$
BEGIN
  IF TG_OP = 'DELETE' THEN
    UPDATE laborder SET repository_update_date = now() WHERE id = OLD.orderid;
    RETURN OLD;
  END IF;
  UPDATE laborder SET repository_update_date = now() WHERE id = NEW.orderid;
  RETURN NEW;
END
$fn$""")

    op.execute(f"""
DO $do$
DECLARE
  t regclass;
BEGIN
  -- Remove the trigger from tables whose update_date was dropped or renamed: it would make
  -- every update to them fail with 'record "new" has no field "update_date"'.
  FOR t IN
    SELECT g.tgrelid::regclass
    FROM pg_trigger g
    JOIN pg_class c ON c.oid = g.tgrelid
    WHERE c.relnamespace = current_schema()::regnamespace
      AND g.tgname = '{UPDATE_TRIGGER}'
      AND NOT EXISTS (
        SELECT FROM pg_attribute a
        WHERE a.attrelid = c.oid AND a.attname = 'update_date' AND NOT a.attisdropped
      )
  LOOP
    EXECUTE format('DROP TRIGGER {UPDATE_TRIGGER} ON %s', t);
  END LOOP;

  -- update_date on every table that has the column
  FOR t IN
    SELECT c.oid::regclass
    FROM pg_class c
    JOIN pg_attribute a ON a.attrelid = c.oid AND a.attname = 'update_date' AND NOT a.attisdropped
    WHERE c.relnamespace = current_schema()::regnamespace
      AND c.relkind IN ('r', 'p')
      AND NOT EXISTS (
        SELECT FROM pg_trigger g WHERE g.tgrelid = c.oid AND g.tgname = '{UPDATE_TRIGGER}'
      )
  LOOP
    EXECUTE format(
      'CREATE TRIGGER {UPDATE_TRIGGER} BEFORE UPDATE ON %s '
      'FOR EACH ROW EXECUTE FUNCTION {UPDATE_FUNCTION}()', t);
  END LOOP;

  -- laborder.repository_update_date, from resultitem
  IF to_regclass('resultitem') IS NOT NULL
     AND EXISTS (
       SELECT FROM pg_attribute
       WHERE attrelid = to_regclass('laborder') AND attname = 'repository_update_date'
         AND NOT attisdropped
     )
     AND NOT EXISTS (
       SELECT FROM pg_trigger
       WHERE tgrelid = to_regclass('resultitem') AND tgname = '{LABORDER_TRIGGER}'
     )
  THEN
    CREATE TRIGGER {LABORDER_TRIGGER}
      AFTER INSERT OR UPDATE OR DELETE ON resultitem
      FOR EACH ROW EXECUTE FUNCTION {LABORDER_FUNCTION}();
  END IF;
END
$do$""")


def drop_triggers() -> None:
    """Drop every trigger create_triggers() makes, and their functions."""
    op.execute(f"""
DO $do$
DECLARE
  t regclass;
BEGIN
  FOR t IN
    SELECT g.tgrelid::regclass
    FROM pg_trigger g
    JOIN pg_class c ON c.oid = g.tgrelid
    WHERE c.relnamespace = current_schema()::regnamespace
      AND g.tgname IN ('{UPDATE_TRIGGER}', '{LABORDER_TRIGGER}')
  LOOP
    EXECUTE format('DROP TRIGGER IF EXISTS {UPDATE_TRIGGER} ON %s', t);
    EXECUTE format('DROP TRIGGER IF EXISTS {LABORDER_TRIGGER} ON %s', t);
  END LOOP;
END
$do$""")
    op.execute(f"DROP FUNCTION IF EXISTS {UPDATE_FUNCTION}()")
    op.execute(f"DROP FUNCTION IF EXISTS {LABORDER_FUNCTION}()")
