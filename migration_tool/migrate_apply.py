"""Apply the migrations made by migrate.py to Postgres, or write them out as SQL.

Usage:
    python migrate_apply.py upgrade postgresql://user@host/db     # apply to a real Postgres
    python migrate_apply.py downgrade postgresql://... --to <rev>
    python migrate_apply.py stamp postgresql://... head           # mark an existing DB as up to date
    python migrate_apply.py current postgresql://...
    python migrate_apply.py sql --from <rev> -o upgrade.sql       # any range as SQL, no database needed

Settings are described in migrate_utils.py.
"""

from __future__ import annotations

import sys
from pathlib import Path

import click
from sqlalchemy import create_engine

sys.path.insert(0, str(Path(__file__).resolve().parent))  # works as a script or with python -m
from migrate_utils import (  # noqa: E402
    load_metadata, make_cli, migration_context, run, run_migrations, script_directory,
)

cli = make_cli("Apply migrations made by migrate.py to Postgres, or write them out as SQL.")


def _on_database(obj, url: str, action):
    metadata = load_metadata(obj["models"])
    script = script_directory(obj["migrations"])
    engine = create_engine(url)
    try:
        with engine.begin() as conn:
            return action(conn, script, metadata)
    finally:
        engine.dispose()


@cli.command()
@click.argument("url")
@click.option("--to", "target", default="heads", show_default=True, help="Target revision.")
@click.pass_obj
def upgrade(obj, url, target):
    """Apply migrations to the Postgres database at URL."""
    _on_database(obj, url, lambda c, s, m: run_migrations(c, s, m, target))
    click.echo(f"Upgraded to {target}.")


@cli.command()
@click.argument("url")
@click.option("--to", "target", required=True, help="Revision to go back to ('base' for none).")
@click.pass_obj
def downgrade(obj, url, target):
    """Roll the database at URL back to a revision."""
    _on_database(obj, url, lambda c, s, m: run_migrations(c, s, m, target, downgrade=True))
    click.echo(f"Downgraded to {target}.")


@cli.command()
@click.argument("url")
@click.argument("revision", default="heads")
@click.pass_obj
def stamp(obj, url, revision):
    """Record REVISION on the database at URL without running anything."""
    _on_database(obj, url, lambda c, s, m: migration_context(c, s, m).stamp(s, revision))
    click.echo(f"Stamped {revision}.")


@cli.command()
@click.argument("url")
@click.pass_obj
def current(obj, url):
    """Show the revision the database at URL is at."""
    heads = _on_database(obj, url, lambda c, s, m: migration_context(c, s, m).get_current_heads())
    click.echo(", ".join(heads) or "(none)")


@cli.command()
@click.option("--from", "start", default=None,
              help="Revision the database is at. Upgrade default: base (empty DB). "
                   "Required with --downgrade.")
@click.option("--to", "target", default=None,
              help="Revision to end at. Default: heads (upgrade) or base (downgrade).")
@click.option("--downgrade", is_flag=True, help="Write the downgrade SQL instead.")
@click.option("--dialect", default="postgresql", show_default=True,
              help="SQL dialect to write (postgresql, mysql, mssql, oracle...).")
@click.option("-o", "--output", type=click.File("w", encoding="utf-8"), default="-",
              help="File to write to. Default: print to the terminal.")
@click.pass_obj
def sql(obj, start, target, downgrade, dialect, output):
    """Write any range of migrations out as SQL without touching a database.

    \b
    Examples:
      sql                                  everything, from an empty database
      sql --from 39e99353828c              just what's newer than 39e99353828c
      sql --from ed95 --to 39e9            a range (short revision ids work)
      sql --downgrade --from heads --to ed9531736d1c
      sql -o upgrade.sql
    """
    if downgrade and not start:
        raise click.UsageError("--downgrade needs --from (the revision the database is at now)")
    metadata = load_metadata(obj["models"])
    script = script_directory(obj["migrations"])
    if not script.get_heads():
        raise click.ClickException("No revisions yet; run generate first.")
    target = target or ("base" if downgrade else "heads")
    if start in ("head", "heads"):
        start = script.get_current_head()
    elif start and start != "base":
        start = script.get_revision(start).revision  # expand short ids, check it exists
    run_migrations(
        None, script, metadata, target, downgrade=downgrade, dialect_name=dialect,
        as_sql=True, output_buffer=output, starting_rev=start if start != "base" else None,
    )


if __name__ == "__main__":
    run(cli)
