"""Migrate CSV data kept outside the project as <tables dir>/<table>/<group>.csv.

CSV headers are the models' attribute names. Each CSV is loaded on its own into a copy
of a database at the CSV's revision, the migrations made by migrate.py are run, and the
table is written back: renamed/dropped/added columns, type changes and data migrations
all apply, headers follow attribute and column renames (via each revision's recorded
attribute names), and values the migrations didn't change keep their original text.
The tables dir's migrate_versions.json records each CSV's revision.

Usage:
    python migrate_csv.py csv-stamp tables/                       # once: record the CSVs' current revision
    python migrate_csv.py csv-migrate tables/ [--out migrated/]   # migrate the data to the latest revision
    python migrate_csv.py csv-migrate tables/ --to <rev>          # ...or to another one (older = back)
    python migrate_csv.py csv-check tables/                       # check headers match their revision

Needs a Postgres for csv-migrate (Docker, or --db-url; see migrate_utils.py).
"""

from __future__ import annotations

import csv as csv_module
import io
import json
import sys
import uuid
from contextlib import contextmanager
from pathlib import Path

import click
from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.exc import DBAPIError
from sqlalchemy.pool import NullPool

sys.path.insert(0, str(Path(__file__).resolve().parent))  # works as a script or with python -m
from migrate_utils import (  # noqa: E402
    _pg_driver, docker_postgres, is_review_error, load_metadata, make_cli, revision_attributes,
    revision_chain, run, run_migrations, script_directory,
)

# --------------------------------------------------------------------------- migrating CSV data
#
# CSVs live outside the project as <tables dir>/<table>/<group>.csv, each loaded on its
# own. To migrate one: copy a template database built at the CSV's revision, load the
# CSV (headers mapped from attribute names to columns using that revision's attribute
# file), run the migrations up to the target revision, and write the table back out
# (columns mapped to the target revision's attribute names). Postgres keeps a column's
# attnum through renames and type changes and a table's oid through renames, which is
# how columns and tables are followed; a temporary serial column keeps rows in order and
# lets values the migrations didn't change be written back with their original text.

CSV_VERSIONS_FILE = "migrate_versions.json"   # in the tables dir: {"<table>/<group>.csv": revision}
ROW_ID = "_migrate_row_id"
_COLUMN_INFO = ("SELECT a.attname, a.attnum, format_type(a.atttypid, a.atttypmod), "
                "t.typcategory = 'A' FROM pg_attribute a JOIN pg_type t ON t.oid = a.atttypid "
                "WHERE a.attrelid = {oid} AND a.attnum > 0 AND NOT a.attisdropped")


class ScratchServer:
    """A Postgres server on which throwaway databases can be created (and are all dropped)."""

    def __init__(self, base_url):
        self.base = base_url
        self.admin = create_engine(base_url, isolation_level="AUTOCOMMIT")
        self.created: list[str] = []

    def create(self, template: str | None = None) -> str:
        name = f"migrate_scratch_{uuid.uuid4().hex[:10]}"
        with self.admin.connect() as conn:
            conn.exec_driver_sql(f'CREATE DATABASE "{name}"' + (f' TEMPLATE "{template}"' if template else ""))
        self.created.append(name)
        return name

    def engine(self, name: str):
        return create_engine(self.base.set(database=name), poolclass=NullPool)

    def drop(self, name: str) -> None:
        with self.admin.connect() as conn:
            try:
                conn.exec_driver_sql(f'DROP DATABASE IF EXISTS "{name}" WITH (FORCE)')
            except DBAPIError:  # Postgres < 13
                conn.exec_driver_sql(f'DROP DATABASE IF EXISTS "{name}"')
        if name in self.created:
            self.created.remove(name)

    def close(self) -> None:
        for name in list(self.created):
            self.drop(name)
        self.admin.dispose()


@contextmanager
def scratch_server(obj):
    if obj["db_url"]:
        base = make_url(obj["db_url"])
        if not base.drivername.startswith("postgresql"):
            raise click.ClickException("--db-url must be a Postgres URL (postgresql://...)")
        if base.drivername == "postgresql":
            base = base.set(drivername=_pg_driver())
        server = ScratchServer(base)
        try:
            with server.admin.connect():
                pass
        except DBAPIError as e:
            server.admin.dispose()
            raise click.ClickException(
                f"Couldn't connect to {base.render_as_string(hide_password=True)}: "
                f"{str(e.orig).strip()}") from None
        try:
            yield server
        finally:
            server.close()
    else:
        with docker_postgres(obj["pg_image"]) as engine:
            server = ScratchServer(engine.url)
            try:
                yield server
            finally:
                server.close()


def _q(name: str) -> str:
    return '"' + name.replace('"', '""') + '"'


def _copy_in(conn, sql: str, text: str) -> None:
    cur = conn.connection.driver_connection.cursor()
    if hasattr(cur, "copy_expert"):  # psycopg2
        cur.copy_expert(sql, io.StringIO(text))
    else:  # psycopg 3
        with cur.copy(sql) as copy:
            copy.write(text)


def _read_csv(path: Path):
    raw = path.read_bytes()
    text = raw.decode("utf-8-sig")
    rows = list(csv_module.reader(io.StringIO(text, newline="")))
    return {"bom": raw.startswith(b"\xef\xbb\xbf"),
            "newline": "\r\n" if b"\r\n" in raw[:65536] else "\n",
            "text": text, "header": rows[0] if rows else [], "rows": rows[1:]}


def _csv_field(value: str | None) -> str:
    """CSV text for one value, as Postgres reads it: empty = NULL, "" = empty string."""
    if value is None:
        return ""
    if value == "" or any(c in value for c in ',"\r\n') or value != value.strip():
        return '"' + value.replace('"', '""') + '"'
    return value


def _bool_style(values) -> tuple[str, str]:
    """How a CSV column wrote booleans (true/false, t/f, 1/0, ...), from its values."""
    styles = [("true", "false"), ("True", "False"), ("TRUE", "FALSE"), ("t", "f"), ("T", "F"),
              ("1", "0"), ("y", "n"), ("Y", "N"), ("yes", "no")]
    seen = {v for v in values if v not in ("", None)}
    for style in styles:
        if seen and seen <= set(style):
            return style
    return "true", "false"


def migrate_csv(server, script, metadata, templates: dict, attrs: dict, table: str, path: Path,
                from_rev: str, target: str, backwards: bool = False) -> dict:
    """Migrate one CSV from `from_rev` to `target` (with the revisions' downgrade() if
    `backwards`). Returns the result (nothing is written)."""
    if from_rev not in attrs:
        raise click.ClickException(f"no attribute names recorded for its revision {from_rev}")
    if target not in attrs:
        raise click.ClickException(f"no attribute names recorded for the target revision {target}")
    columns_at_start = attrs[from_rev].get(table)
    if columns_at_start is None:
        raise click.ClickException(f"there's no table {table!r} at its revision {from_rev}")
    csv_ = _read_csv(path)
    by_attribute = {a: c for c, a in columns_at_start.items()}
    unknown = [h for h in csv_["header"] if h not in by_attribute]
    if unknown:
        raise click.ClickException(f"header(s) {', '.join(unknown)} aren't attributes of {table} at {from_rev}")
    columns = [by_attribute[h] for h in csv_["header"]]

    if from_rev not in templates:  # a database at from_rev, copied for each CSV
        name = server.create()
        engine = server.engine(name)
        try:
            with engine.begin() as conn:
                run_migrations(conn, script, metadata, from_rev)
        finally:
            engine.dispose()
        templates[from_rev] = name

    work = server.create(template=templates[from_rev])
    engine = server.engine(work)
    try:
        with engine.begin() as conn:
            q = conn.exec_driver_sql
            oid = q(f"SELECT to_regclass('public.{_q(table)}')::oid").scalar()
            attnums, types, is_array_at_load = {}, {}, {}
            for name, num, type_, is_array in q(_COLUMN_INFO.format(oid=oid)).all():
                attnums[name], types[name], is_array_at_load[name] = num, type_, is_array
            last_attnum = max(attnums.values())
            q(f"ALTER TABLE {_q(table)} ADD COLUMN {ROW_ID} bigserial")
            # A group's CSV doesn't include the rows its foreign keys point at, so turn FK
            # checks (and other triggers) off for the load and the migrations' own
            # INSERT/UPDATEs. Needs a superuser (it is in Docker); otherwise they stay on.
            try:
                with conn.begin_nested():
                    q("SET LOCAL session_replication_role = replica")
            except DBAPIError:
                pass
            # Load as text first, then cast into the table. Array columns also accept
            # JSON-style lists (["A", "B"]), which is how the CSVs write them.
            stage = [f"s{i}" for i in range(len(columns))]
            q(f"CREATE TEMP TABLE _migrate_stage ({', '.join(f'{c} text' for c in stage)}, "
              "rid bigserial) ON COMMIT DROP")
            _copy_in(conn, f"COPY _migrate_stage ({', '.join(stage)}) FROM STDIN "
                           "WITH (FORMAT csv, HEADER true)", csv_["text"])
            casts = []
            for c, st in zip(columns, stage):
                if is_array_at_load[c]:
                    casts.append(f"CASE WHEN left(btrim({st}), 1) = '[' THEN ARRAY(SELECT e FROM "
                                 f"json_array_elements_text({st}::json) WITH ORDINALITY AS x(e, n) "
                                 f"ORDER BY n)::{types[c]} ELSE {st}::{types[c]} END")
                else:
                    casts.append(f"{st}::{types[c]}")
            q(f"INSERT INTO {_q(table)} ({', '.join(map(_q, columns))}, {ROW_ID}) "
              f"SELECT {', '.join(casts)}, rid FROM _migrate_stage ORDER BY rid")
            q(f"SELECT setval(pg_get_serial_sequence('{_q(table)}', '{ROW_ID}'), "
              f"GREATEST((SELECT max(rid) FROM _migrate_stage), 1))")
            q("DROP TABLE _migrate_stage")
            select = ", ".join(f"{_q(c)}::text" for c in columns)
            before = {r[0]: list(r[1:]) for r in q(f"SELECT {ROW_ID}, {select} FROM {_q(table)}").all()}

            run_migrations(conn, script, metadata, target, downgrade=backwards)

            new_table = q(f"SELECT relname FROM pg_class WHERE oid = {oid}").scalar()
            if new_table is None:
                raise click.ClickException(f"the migrations drop table {table}")
            info = [(num, name, type_ == "boolean", is_array)
                    for name, num, type_, is_array in q(_COLUMN_INFO.format(oid=oid)).all()]
            name_of = {n: a for n, a, _, _ in info}
            is_bool = {a: b for _, a, b, _ in info}
            is_array = {a: arr for _, a, _, arr in info}
            has_row_id = ROW_ID in is_bool
            kept = [(i, name_of[attnums[c]]) for i, c in enumerate(columns) if attnums[c] in name_of]
            added = [a for n, a, _, _ in sorted(info) if n > last_attnum and a != ROW_ID]
            out_cols = [c for _, c in kept] + added
            order = f"ORDER BY {ROW_ID}" if has_row_id else ""
            row_id = ROW_ID if has_row_id else "NULL"
            select = ", ".join(f"{_q(c)}::text" for c in out_cols) or "NULL"
            as_json = ", ".join(f"array_to_json({_q(c)})::text" if is_array[c] else "NULL"
                                for c in out_cols) or "NULL"
            rows = q(f"SELECT {row_id}, {select}, {as_json} FROM {_q(new_table)} {order}").all()
            width = max(len(out_cols), 1)
            after = [(r[0], *r[1:1 + width]) for r in rows]
            after_json = [list(r[1 + width:]) for r in rows]
    finally:
        engine.dispose()
        server.drop(work)

    # --- assemble the new CSV
    names_at_target = attrs[target].get(new_table, {})
    header = [names_at_target.get(c, c) for c in out_cols]
    styles = {c: _bool_style(row[i] if i < len(row) else "" for row in csv_["rows"])
              for i, c in kept if is_bool.get(c)}
    default_style = next(iter(styles.values()), ("true", "false"))  # for new boolean columns
    pg_arrays = {c for i, c in kept if is_array.get(c) and any(
        (row[i] if i < len(row) else "").lstrip().startswith("{") for row in csv_["rows"])}
    changed = 0
    lines = [",".join(_csv_field(h) for h in header)]
    for n_row, rec in enumerate(after):
        rid, values = rec[0], list(rec[1:])
        original = csv_["rows"][rid - 1] if rid is not None and 0 < rid <= len(csv_["rows"]) else None
        fields = []
        for j, value in enumerate(values):
            col = out_cols[j]
            if j < len(kept) and original is not None and rid in before:
                i = kept[j][0]
                if before[rid][i] == value:  # unchanged by the migrations: keep the original text
                    fields.append(_csv_field(before[rid][i] if before[rid][i] in ("", None)
                                             else (original[i] if i < len(original) else value)))
                    continue
            if value is not None and is_bool.get(col):
                true, false = styles.get(col, default_style)
                value = true if value == "true" else false
            elif value is not None and is_array.get(col) and col not in pg_arrays:
                value = json.dumps(json.loads(after_json[n_row][j]))  # as the CSVs write lists
            changed += original is not None and j < len(kept)
            fields.append(_csv_field(value))
        lines.append(",".join(fields))
    text = csv_["newline"].join(lines) + csv_["newline"]
    renamed = [f"{csv_['header'][i]} -> {header[j]}" for j, (i, _c) in enumerate(kept)
               if csv_["header"][i] != header[j]]
    dropped = [csv_["header"][i] for i in range(len(columns)) if i not in {k for k, _ in kept}]
    return {"table": new_table, "text": text, "bom": csv_["bom"], "renamed": renamed,
            "dropped": dropped, "added": [names_at_target.get(c, c) for c in added],
            "rows": (len(csv_["rows"]), len(after)), "changed_cells": changed}


def _csv_files(tables_dir: Path, known_tables: set[str]) -> list[tuple[str, str, Path]]:
    """(key, table, path) for every <tables_dir>/<table>/<group>.csv of a known table."""
    out = []
    for folder in sorted(p for p in tables_dir.iterdir() if p.is_dir()):
        if folder.name not in known_tables:
            continue
        for path in sorted(folder.glob("*.csv")):
            out.append((f"{folder.name}/{path.name}", folder.name, path))
    return out


def _load_versions(tables_dir: Path) -> dict:
    path = tables_dir / CSV_VERSIONS_FILE
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def _save_versions(tables_dir: Path, versions: dict) -> None:
    (tables_dir / CSV_VERSIONS_FILE).write_text(json.dumps(dict(sorted(versions.items())), indent=2) + "\n",
                                                encoding="utf-8")


def _header_problems(header: list[str], table: str, tables: dict) -> list[str]:
    if table not in tables:
        return [f"no table {table!r} at this revision"]
    unknown = [h for h in header if h not in tables[table].values()]
    return [f"unknown column(s) {', '.join(unknown)}"] if unknown else []


# --------------------------------------------------------------------------- CLI

cli = make_cli("Migrate CSV data (<tables dir>/<table>/<group>.csv) with the migrations "
               "made by migrate.py. See the top of migrate_csv.py for details.")


def _csv_context(obj, tables_dir: Path):
    script = script_directory(obj["migrations"])
    chain = revision_chain(script)
    if not chain:
        raise click.ClickException("No revisions yet.")
    attrs = revision_attributes(obj["migrations"], chain)
    known = {t for tables in attrs.values() for t in tables}
    return script, chain, attrs, _csv_files(tables_dir, known)


@cli.command("csv-stamp")
@click.argument("tables_dir", type=click.Path(file_okay=False, exists=True, path_type=Path))
@click.option("--revision", "target", default=None,
              help="Revision the CSVs currently match. Default: latest.")
@click.option("--force", is_flag=True, help="Also re-stamp CSVs that already have a revision.")
@click.pass_obj
def csv_stamp(obj, tables_dir, target, force):
    """Record which revision the CSVs in TABLES_DIR/<table>/<group>.csv are at.

    Needed once per CSV (e.g. when you start using this, or add a new group), so
    csv-migrate knows where to start. Headers are checked against that revision first.
    """
    script, chain, attrs, files = _csv_context(obj, tables_dir)
    rev = chain[-1].revision if target is None else script.get_revision(target).revision
    if rev not in attrs:
        raise click.ClickException(f"No attribute names recorded for {rev} (see snapshot-attributes).")
    versions = _load_versions(tables_dir)
    stamped, problems = 0, []
    for key, table, path in files:
        if key in versions and not force:
            continue
        issues = _header_problems(_read_csv(path)["header"], table, attrs[rev])
        if issues:
            problems.append(f"{key}: {'; '.join(issues)}")
            continue
        versions[key] = rev
        stamped += 1
    _save_versions(tables_dir, versions)
    click.echo(f"Stamped {stamped} CSV file(s) at {rev}.")
    for line in problems:
        click.secho(f"  not stamped: {line}", fg="red")
    if problems:
        sys.exit(1)


@cli.command("csv-migrate")
@click.argument("tables_dir", type=click.Path(file_okay=False, exists=True, path_type=Path))
@click.option("--to", "target", default=None,
              help="Revision to migrate to. Default: latest. An older revision migrates the CSVs "
                   "back, using the revisions' downgrade().")
@click.option("--out", "out_dir", type=click.Path(file_okay=False, path_type=Path), default=None,
              help="Write migrated CSVs here (same <table>/<group>.csv layout) instead of "
                   "replacing the originals.")
@click.option("--only", "only", multiple=True,
              help="Only these CSVs, as <table>/<group>.csv or <table> (repeatable).")
@click.pass_obj
def csv_migrate(obj, tables_dir, target, out_dir, only):
    """Migrate the data in TABLES_DIR/<table>/<group>.csv to a revision.

    Each CSV is loaded on its own into a copy of a database at its recorded revision,
    the migrations are run, and the table is written back, with headers following
    attribute and column renames. Values the migrations didn't change keep their
    original text. --to an older revision migrates back with the revisions' downgrade().
    Needs a Postgres (Docker, or --db-url).
    """
    metadata = load_metadata(obj["models"])
    script, chain, attrs, files = _csv_context(obj, tables_dir)
    goal = chain[-1].revision if target is None else script.get_revision(target).revision
    ids = [r.revision for r in chain]
    versions = _load_versions(tables_dir)
    if only:
        files = [f for f in files if f[0] in only or f[1] in only]
    unstamped = [key for key, _, _ in files if key not in versions]
    todo = []
    for key, table, path in files:
        if key not in versions:
            continue
        if versions[key] not in ids:
            raise click.ClickException(f"{key} is at {versions[key]}, which isn't a known revision.")
        if versions[key] != goal:
            todo.append((key, table, path))
    for key in unstamped:
        click.secho(f"skipped {key}: no revision recorded (run csv-stamp)", fg="yellow")
    if not todo:
        click.echo(f"Nothing to migrate: every stamped CSV is at {goal}.")
        sys.exit(1 if unstamped else 0)

    failures = []
    templates: dict = {}
    with scratch_server(obj) as server:
        for key, table, path in todo:
            start = versions[key]
            try:
                backwards = ids.index(start) > ids.index(goal)
                result = migrate_csv(server, script, metadata, templates, attrs, table, path, start,
                                     goal, backwards)
            except (click.ClickException, DBAPIError, RuntimeError) as e:
                if isinstance(e, RuntimeError) and not is_review_error(e):
                    raise
                if isinstance(e, click.ClickException):
                    message = e.format_message()
                else:
                    lines = str(getattr(e, "orig", e)).strip().splitlines()
                    message = " ".join([lines[0], *[ln.strip() for ln in lines[1:] if ln.startswith("DETAIL")]])
                failures.append(key)
                click.secho(f"FAILED {key}: {message}", fg="red")
                continue
            new_key = f"{result['table']}/{path.name}"
            dest = (out_dir or tables_dir) / result["table"] / path.name
            dest.parent.mkdir(parents=True, exist_ok=True)
            data = ("﻿" if result["bom"] else "").encode() + result["text"].encode("utf-8")
            if not (dest == path and path.read_bytes() == data):
                dest.write_bytes(data)
            if out_dir is None:
                if new_key != key:  # the table was renamed: the CSV moved folders
                    path.unlink()
                    versions.pop(key)
                versions[new_key] = goal
                _save_versions(tables_dir, versions)
            before, after = result["rows"]
            details = [f"{before} -> {after} rows" if before != after else f"{after} rows"]
            details += [f"renamed {', '.join(result['renamed'])}"] if result["renamed"] else []
            details += [f"dropped {', '.join(result['dropped'])}"] if result["dropped"] else []
            details += [f"added {', '.join(result['added'])}"] if result["added"] else []
            if result["changed_cells"]:
                details.append(f"{result['changed_cells']} value(s) changed")
            moved = f" -> {new_key}" if new_key != key else ""
            click.echo(f"{key}{moved}: {start} -> {goal}; {'; '.join(details)}")
    if out_dir is not None:
        click.echo(f"Wrote to {out_dir}; the originals and {CSV_VERSIONS_FILE} are unchanged.")
    if failures or unstamped:
        if failures:
            click.secho(f"{len(failures)} CSV file(s) failed and were left as they were.", fg="red")
        sys.exit(1)


@cli.command("csv-check")
@click.argument("tables_dir", type=click.Path(file_okay=False, exists=True, path_type=Path))
@click.pass_obj
def csv_check(obj, tables_dir):
    """Check every CSV's headers against its recorded revision (exit 1 on problems)."""
    _script, chain, attrs, files = _csv_context(obj, tables_dir)
    versions = _load_versions(tables_dir)
    head = chain[-1].revision
    problems, behind = [], 0
    for key, table, path in files:
        rev = versions.get(key)
        if rev is None:
            problems.append(f"{key}: no revision recorded (run csv-stamp)")
            continue
        if rev not in attrs:
            problems.append(f"{key}: no attribute names recorded for {rev}")
            continue
        issues = _header_problems(_read_csv(path)["header"], table, attrs[rev])
        problems += [f"{key}: {i}" for i in issues]
        behind += rev != head
    for line in problems:
        click.echo(f"  {line}")
    if behind:
        click.secho(f"{behind} CSV file(s) are behind the latest revision (run csv-migrate).", fg="yellow")
    if problems:
        click.echo(f"{len(problems)} problem(s).", err=True)
        sys.exit(1)
    click.echo(f"All {len(files)} CSV file(s) match their recorded revision.")


if __name__ == "__main__":
    run(cli)
