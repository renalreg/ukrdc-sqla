"""Compare the schema the Alembic migrations build with an existing database's schema."""

from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

import click
from alembic import command
from alembic.config import Config
from alembic.util import CommandError
from sqlalchemy import create_engine, inspect
from sqlalchemy.engine import make_url
from sqlalchemy.exc import DBAPIError
from sqlalchemy.pool import NullPool

sys.path.insert(0, str(Path(__file__).resolve().parent))
from migrate import pg_driver, scratch_database  # noqa: E402

SKIP_SCHEMAS = {"information_schema", "pg_toast"}
SKIP_TABLES = {"alembic_version"}


def snapshot(engine, schemas: tuple[str, ...]) -> dict:
    """{(schema, table): {columns, pk, fks, indexes, uniques}} for the chosen schemas (or all)."""
    insp = inspect(engine)
    found = [
        s
        for s in insp.get_schema_names()
        if s not in SKIP_SCHEMAS and not s.startswith("pg_")
    ]
    out = {}
    for schema in [s for s in found if not schemas or s in schemas]:
        for table in insp.get_table_names(schema=schema):
            if table in SKIP_TABLES:
                continue
            out[(schema, table)] = {
                "columns": {
                    c["name"]: {
                        "type": str(c["type"]),
                        "nullable": c["nullable"],
                        "default": c.get("default"),
                    }
                    for c in insp.get_columns(table, schema=schema)
                },
                "pk": tuple(
                    insp.get_pk_constraint(table, schema=schema)["constrained_columns"]
                    or ()
                ),
                "fks": {
                    (
                        tuple(f["constrained_columns"]),
                        f.get("referred_schema") or schema,
                        f["referred_table"],
                        tuple(f["referred_columns"]),
                    )
                    for f in insp.get_foreign_keys(table, schema=schema)
                },
                "indexes": {
                    (tuple(i["column_names"]), bool(i["unique"]))
                    for i in insp.get_indexes(table, schema=schema)
                },
                "uniques": {
                    tuple(u["column_names"])
                    for u in insp.get_unique_constraints(table, schema=schema)
                },
            }
    return out


def rename_schema(tables: dict, old: str, new: str) -> dict:
    """The snapshot with schema OLD called NEW (tables and foreign key targets)."""
    out = {}
    for (schema, table), info in tables.items():
        info = dict(
            info, fks={(c, new if s == old else s, t, r) for c, s, t, r in info["fks"]}
        )
        out[(new if schema == old else schema, table)] = info
    return out


def fmt_fk(fk) -> str:
    cols, schema, table, ref = fk
    return f"({', '.join(cols)}) -> {schema}.{table}({', '.join(ref)})"


def fmt_index(ix) -> str:
    return f"{'UNIQUE ' if ix[1] else ''}({', '.join(c or '<expr>' for c in ix[0])})"


def compare(migrated: dict, local: dict, check_defaults: bool) -> list[str]:
    lines = []
    for key in sorted(migrated.keys() - local.keys()):
        lines.append(f"{key[0]}.{key[1]}: only in the migrations")
    for key in sorted(local.keys() - migrated.keys()):
        lines.append(f"{key[0]}.{key[1]}: only in the local database")
    for key in sorted(migrated.keys() & local.keys()):
        m, l, diffs = migrated[key], local[key], []
        for col in m["columns"].keys() - l["columns"].keys():
            diffs.append(
                f"column {col}: only in the migrations ({m['columns'][col]['type']})"
            )
        for col in l["columns"].keys() - m["columns"].keys():
            diffs.append(
                f"column {col}: only in the local database ({l['columns'][col]['type']})"
            )
        for col in sorted(m["columns"].keys() & l["columns"].keys()):
            mc, lc = m["columns"][col], l["columns"][col]
            for attr in ("type", "nullable") + (("default",) if check_defaults else ()):
                if mc[attr] != lc[attr]:
                    diffs.append(
                        f"column {col}: {attr} {mc[attr]!r} (migrations) vs "
                        f"{lc[attr]!r} (local)"
                    )
        if m["pk"] != l["pk"]:
            diffs.append(f"primary key: {m['pk']} (migrations) vs {l['pk']} (local)")
        for label, attr, fmt in (
            ("foreign key", "fks", fmt_fk),
            ("index", "indexes", fmt_index),
            ("unique constraint", "uniques", lambda u: f"({', '.join(u)})"),
        ):
            for item in sorted(m[attr] - l[attr], key=str):
                diffs.append(f"{label} {fmt(item)}: only in the migrations")
            for item in sorted(l[attr] - m[attr], key=str):
                diffs.append(f"{label} {fmt(item)}: only in the local database")
        if diffs:
            lines.append(f"{key[0]}.{key[1]}:")
            lines += [f"  {d}" for d in sorted(diffs)]
    return lines


@click.command(context_settings={"max_content_width": 100})
@click.option(
    "--db-url",
    required=True,
    help="The local database to compare with, e.g. postgresql://user:pass@localhost:5432/ukrdc_test.",
)
@click.option(
    "--migrations",
    required=True,
    type=click.Path(file_okay=False, exists=True, path_type=Path),
    help="Migrations folder, e.g. migrations/ukrdc.",
)
@click.option(
    "--revision",
    default="head",
    show_default=True,
    help="Revision to build the migrations to.",
)
@click.option(
    "--schema",
    "schemas",
    multiple=True,
    help="Only this schema (repeatable). Default: all.",
)
@click.option(
    "--local-schema",
    help="Compare this schema of the local database with --schema of the "
    "migrations (e.g. local extract vs migrated public).",
)
@click.option(
    "--scratch-url",
    help="Server to build the migrations on (needs CREATE DATABASE). "
    "Default: the server of --db-url.",
)
@click.option(
    "--defaults/--no-defaults",
    default=False,
    show_default=True,
    help="Also compare column defaults (noisy: sequence names, casts).",
)
def cli(db_url, migrations, revision, schemas, local_schema, scratch_url, defaults):
    """Build the migrations in a scratch database and list how its schema differs from --db-url's."""
    local_url = make_url(db_url)
    if local_url.drivername == "postgresql":
        local_url = local_url.set(drivername=pg_driver())
    ini = migrations / "alembic.ini"
    if not ini.exists():
        raise click.ClickException(f"No {ini}.")

    if local_schema and len(schemas) != 1:
        raise click.UsageError(
            "--local-schema needs exactly one --schema (the migrations' schema)."
        )
    local = snapshot(
        create_engine(local_url, poolclass=NullPool),
        (local_schema,) if local_schema else schemas,
    )
    if local_schema:
        local = rename_schema(local, local_schema, schemas[0])
    obj = SimpleNamespace(
        db_url=scratch_url or local_url.render_as_string(hide_password=False),
        pg_image="postgres:16",
    )
    with scratch_database(obj) as engine:
        with engine.begin() as conn:
            cfg = Config(str(ini))
            cfg.set_main_option(
                "sqlalchemy.url",
                engine.url.render_as_string(hide_password=False).replace("%", "%%"),
            )
            cfg.attributes["connection"] = conn
            try:
                command.upgrade(cfg, revision)
            except (CommandError, DBAPIError) as e:
                raise click.ClickException(
                    f"Running the migrations failed: "
                    f"{str(getattr(e, 'orig', e)).strip()}"
                ) from None
        migrated = snapshot(engine, schemas)

    lines = compare(migrated, local, defaults)
    click.echo(
        f"{len(migrated)} tables from the migrations, {len(local)} in the local database."
    )
    if not lines:
        click.secho("No differences.", fg="green")
        return
    click.echo("\n".join(lines))
    sys.exit(1)


if __name__ == "__main__":
    cli()
