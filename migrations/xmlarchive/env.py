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


def run_migrations(conn):
    context.configure(connection=conn, target_metadata=target_metadata)
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
