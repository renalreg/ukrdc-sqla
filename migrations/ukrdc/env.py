"""Alembic environment for these migrations (copied here by migrate.py).

Apply them to a database with plain Alembic, after setting sqlalchemy.url in alembic.ini
(or DATABASE_URL):

    alembic -c migrations/ukrdc/alembic.ini upgrade head
    alembic -c migrations/ukrdc/alembic.ini downgrade -1
    alembic -c migrations/ukrdc/alembic.ini upgrade head --sql     # print the SQL instead

New revisions come from `python migrate.py generate -m "..."`, which passes in a connection
to its throwaway database and the models' metadata.
"""

import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy import create_engine, pool

config = context.config
connection = config.attributes.get("connection")  # from migrate.py
target_metadata = config.attributes.get("target_metadata")  # from migrate.py generate


# ----------------------------------------------------------------------------- ORM-only FKs
# Foreign keys the models flag as ORM-only aren't written into migrations:
#
#     ForeignKey("patientrecord.pid", info={ORM_ONLY: True})
#
# The ORM still uses them for joins and relationships, but autogenerate won't create them in
# the database: neither as create_foreign_key on an existing table, nor inside create_table
# for a new one. If the database already has a matching FK, Alembic sees no difference and
# leaves it alone. Remove the flag and autogenerate again to have a migration add the FK.


def is_orm_only(fk_constraint) -> bool:
    # Imported here so applying migrations with plain Alembic doesn't need ukrdc_sqla.
    from ukrdc_sqla.utils.structure import ORM_ONLY

    return any(fk.info.get(ORM_ONLY) for fk in fk_constraint.elements)


def include_object(obj, name, type_, reflected, compare_to):
    # Views mapped as models
    if type_ == "table" and name.startswith("vwe_"):
        return False
    # FKs that exist only for SQLAlchemy relationships, not in the DB
    if type_ == "foreign_key_constraint" and not reflected and is_orm_only(obj):
        return False
    return True


def strip_orm_only_fks(context_, revision, directives):
    """Skip ORM-only FKs in create_table (include_object isn't consulted there)."""
    from alembic.operations import ops
    from sqlalchemy import ForeignKeyConstraint

    def walk(op):
        if isinstance(op, ops.CreateTableOp):
            op.columns = [
                c
                for c in op.columns
                if not (isinstance(c, ForeignKeyConstraint) and is_orm_only(c))
            ]
        for child in getattr(op, "ops", ()):
            walk(child)

    for directive in directives:
        for ops_ in directive.upgrade_ops_list:
            walk(ops_)


def run_migrations(conn):
    context.configure(
        connection=conn,
        target_metadata=target_metadata,
        include_object=include_object,
        process_revision_directives=strip_orm_only_fks,
    )
    with context.begin_transaction():
        context.run_migrations()


if connection is not None:
    run_migrations(connection)
else:
    if config.config_file_name:
        fileConfig(config.config_file_name)
    url = os.environ.get("DATABASE_URL") or config.get_main_option("sqlalchemy.url")
    if context.is_offline_mode():
        context.configure(
            url=url or None, dialect_name="postgresql", literal_binds=True
        )
        with context.begin_transaction():
            context.run_migrations()
    elif not url:
        raise SystemExit("Set sqlalchemy.url in alembic.ini, or DATABASE_URL.")
    else:
        with create_engine(url, poolclass=pool.NullPool).connect() as conn:
            run_migrations(conn)
