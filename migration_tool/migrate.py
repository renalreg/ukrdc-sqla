"""Generate Alembic migrations (and their SQL files) from the SQLAlchemy models, no env.py needed.

`generate` gets a throwaway Postgres, replays the existing migrations into it,
compares the result with the models, and writes the difference as a new
revision, plus the same revision as plain SQL:

    migrations/versions/<rev>_<slug>.py                    the Alembic revision
    migrations/sql/postgresql/NNNN_<rev>_<slug>.up.sql     upgrade SQL (Postgres)
    migrations/sql/postgresql/NNNN_<rev>_<slug>.down.sql   downgrade SQL (Postgres)

Where the throwaway Postgres comes from:
    --db-url postgresql://user:pw@localhost/postgres   a server you already run: a temporary
                                                        database is created on it and dropped
                                                        afterwards (needs CREATEDB); existing
                                                        databases are never touched
    (no --db-url)                                       a Postgres container is started in
                                                        Docker and removed afterwards

Review markers: every generated file has a "REVIEW STATUS: UNCHECKED" line.
Change it to CHECKED once you've reviewed the file. Files marked CHECKED are
never overwritten; `unchecked` lists what still needs review (exit 1 for CI).

Renames: autogenerate can't detect them; it writes drop + add, which loses the
data. So generate flags a possible rename when a revision
  - drops one column and adds another in the same table with exactly the same
    type, nullability, default and comment, or
  - drops one table and creates another with exactly the same columns (as above),
    primary key and comment.
Anything less is assumed not to be a rename. Each flagged pair gets a one-line
`raise` naming it, and upgrade() starts with one general "REVIEW NEEDED" note
saying how to fix it. Until the raises are removed, the revision fails when run,
no SQL files are written for it, and `generate`/`check` stop.

Attribute renames: renaming a model attribute but not its column
(mapped_column("firstdataquarter") on `firstdataquarters`) changes nothing in the
database, so generate spots it by comparing with the previous revision's recorded
attribute names and writes a revision for it. Each revision records the attribute
names it was generated with (migrations/attributes/NNNN_<rev>_<slug>.json; written
once); migrate_csv.py uses them to map CSV headers.

Usage:
    python migrate.py generate -m "rename facilitycodestd"   # new revision + SQL files
    python migrate.py check                                   # exit 1 if models have unmigrated changes
                                                              # or SQL files are out of date (CI)
    python migrate.py write-sql                               # (re)write SQL files for all revisions
    python migrate.py snapshot-attributes                     # start tracking attribute names
    python migrate.py unchecked                               # list generated files not yet reviewed
    python migrate.py history
    python migrate.py cleanup                                 # remove leftover Docker containers

Applying migrations is in migrate_apply.py and migrating CSV data in migrate_csv.py.
Settings are described in migrate_utils.py.

Needs: alembic, sqlalchemy, click and a Postgres driver (psycopg or psycopg2).
"""

from __future__ import annotations

import io
import re
import shutil
import sys
import textwrap
import tokenize
from datetime import datetime, timezone
from pathlib import Path

import click
from alembic.autogenerate import produce_migrations, renderers
from alembic.autogenerate.api import AutogenContext
from alembic.autogenerate.render import _alter_column as _render_alter_column_default
from alembic.autogenerate.render import _render_cmd_body
from alembic.operations import ops
from alembic.script import ScriptDirectory
from alembic.util import rev_id
from sqlalchemy import Enum, MetaData
from sqlalchemy import types as sqltypes
from sqlalchemy.dialects import postgresql

sys.path.insert(0, str(Path(__file__).resolve().parent))  # works as a script or with python -m
from migrate_utils import (  # noqa: E402
    REVIEW_NEEDED, ReviewPending, _docker, _shown, _without_marker,
    adopt_legacy_snapshot, attribute_renames, attributes_path, baseline_attributes,
    files_with_review_blocks, find_attributes_file, is_review_error, load_metadata, make_cli,
    migration_context, model_attributes, review_status, revision_chain, run, run_migrations,
    scratch_postgres, script_directory, slugify, sql_path, write_attributes, write_generated,
    DOCKER_LABEL, LEGACY_ATTRIBUTES_FILE,
)

_PG_DIALECT = postgresql.dialect()


# --------------------------------------------------------------------------- rendering fixes

@renderers.dispatch_for(ops.AlterColumnOp, replace=True)
def _render_alter_column(autogen_context, op: ops.AlterColumnOp) -> str:
    # Alembic's renderer drops extra kwargs; keep the USING cast added by add_using_casts
    src = _render_alter_column_default(autogen_context, op)
    using = op.kw.get("postgresql_using")
    if using and src.endswith(")"):
        m = re.search(r"\n( *)\S[^\n]*$", src)
        indent = m.group(1) if m else " " * 15
        src = f"{src[:-1]},\n{indent}postgresql_using={using!r})"
    return src


def _qualify_types(src: str) -> str:
    """Alembic writes types nested inside dialect types without a prefix, e.g.
    `postgresql.ARRAY(String())` or `JSONB(astext_type=Text())`, which then fail with
    NameError. Prefix bare SQLAlchemy type names with `sa.` (code only, never inside strings).
    """
    toks = list(tokenize.generate_tokens(io.StringIO(src).readline))
    spots = []
    for i, tok in enumerate(toks[:-1]):
        if (tok.type == tokenize.NAME and tok.string[:1].isupper() and hasattr(sqltypes, tok.string)
                and toks[i + 1].string == "(" and not (i and toks[i - 1].string == ".")):
            spots.append(tok.start)
    lines = src.splitlines(keepends=True)
    for row, col in reversed(spots):
        lines[row - 1] = lines[row - 1][:col] + "sa." + lines[row - 1][col:]
    return "".join(lines)


REVISION_TEMPLATE = '''"""{message}

Revision ID: {revision}
Revises: {down_revision}
Create Date: {create_date}
"""
{imports}

revision = {revision!r}
down_revision = {down_revision!r}
branch_labels = None
depends_on = None
{attributes}

def upgrade():
{upgrade}


def downgrade():
{downgrade}
'''


# --------------------------------------------------------------------------- diffing

class PossibleRenameOp(ops.MigrateOperation):
    """Placeholder rendered as a one-line raise in front of a drop/add pair that looks
    like a renamed column or table, so the revision can't run until someone decides.
    The explanation is one general note at the top of upgrade() (rename_review_note)."""

    def __init__(self, kind, old, new, table_name=None, schema=None):
        self.kind, self.old, self.new, self.table_name, self.schema = kind, old, new, table_name, schema

    def reverse(self):
        return PossibleRenameOp(self.kind, self.new, self.old, self.table_name, self.schema)

    def to_diff_tuple(self):
        return ("possible_rename", self.schema, self.table_name, f"{self.old} -> {self.new}")

    def describe(self) -> str:
        if self.kind == "table":
            return f"table {self.old} (A) -> {self.new} (B)"
        return f"{self.table_name}.{self.old} (A) -> {self.new} (B)"


@renderers.dispatch_for(PossibleRenameOp)
def _render_possible_rename(_autogen_context, op: PossibleRenameOp) -> str:
    msg = f"{REVIEW_NEEDED}: {op.describe()} may be a rename, see the note at the top of upgrade()"
    return f"raise RuntimeError({msg!r})"


def rename_review_note(flagged) -> str:
    """One general note (with A and B, not real names) for all the raises."""
    if not flagged:
        return ""
    kinds = {op.kind for op in flagged}
    lines = [
        f"# {REVIEW_NEEDED}: each raise below marks a possible rename: A is dropped and an identical",
        "# B is added (same type, nullability, default and comment; for a table, the same columns).",
        "# If B is a rename of A, this loses A's data. For each raise, here and in downgrade():",
        "#   - not a rename: delete the raise",
    ]
    if "column" in kinds:
        lines += ["#   - column rename: replace the raise and its add_column/drop_column pair with",
                  "#       op.alter_column('<table>', 'A', new_column_name='B')"]
    if "table" in kinds:
        lines += ["#   - table rename: replace the raise and its create_table/drop_table pair with",
                  "#       op.rename_table('A', 'B') where the create_table was (keep the index lines)"]
    return "\n".join(lines) + "\n"


def _column_signature(col):
    try:
        type_ = _PG_DIALECT.type_compiler_instance.process(col.type).upper()
    except Exception:
        type_ = str(col.type).upper()
    default = col.server_default
    if default is not None:  # the default's SQL text, compared exactly
        arg = getattr(default, "arg", default)
        default = str(getattr(arg, "text", arg)).strip()
        if default.startswith("nextval("):  # a serial column's sequence (named after the table)
            default = None
    return type_, bool(col.nullable), default, col.comment


def _table_signature(table):
    columns = {c.name: _column_signature(c) for c in table.columns}
    primary_key = tuple(sorted(c.name for c in table.primary_key.columns))
    return columns, primary_key, table.comment


def detect_possible_renames(upgrade_ops: ops.UpgradeOps):
    """Flag drop+add pairs that are identical apart from the name. Anything less is
    assumed not to be a rename.

    Columns: dropped and added in the same table with exactly the same type,
    nullability, default and comment. Tables: dropped and created with exactly the
    same columns (names and all of the above), primary key and comment.
    A PossibleRenameOp goes in front of each pair. Returns (notes, flagged ops)."""
    notes, all_flagged = [], []

    # tables
    creates = [o for o in upgrade_ops.ops if isinstance(o, ops.CreateTableOp)]
    drops = [o for o in upgrade_ops.ops if isinstance(o, ops.DropTableOp)]
    used = set()
    for create in creates:
        new_sig = _table_signature(create.to_table())
        for drop in drops:
            if id(drop) in used or drop.schema != create.schema:
                continue
            if _table_signature(drop.to_table()) != new_sig:
                continue
            used.add(id(drop))
            op = PossibleRenameOp("table", drop.table_name, create.table_name, schema=create.schema)
            upgrade_ops.ops.insert(upgrade_ops.ops.index(create), op)
            all_flagged.append(op)
            notes.append(f"POSSIBLE RENAME table {drop.table_name} -> {create.table_name}: "
                         "the revision raises until you review it")
            break

    # columns
    for mod in upgrade_ops.ops:
        if not isinstance(mod, ops.ModifyTableOps):
            continue
        adds = [o for o in mod.ops if isinstance(o, ops.AddColumnOp)]
        drops = [o for o in mod.ops if isinstance(o, ops.DropColumnOp)]
        flagged, used = [], set()
        for add in adds:
            new_sig = _column_signature(add.column)
            for drop in drops:
                if id(drop) in used:
                    continue
                if _column_signature(drop.to_column()) != new_sig:
                    continue
                used.add(id(drop))
                flagged.append(PossibleRenameOp("column", drop.column_name, add.column.name,
                                                mod.table_name, mod.schema))
                notes.append(f"POSSIBLE RENAME {mod.table_name}.{drop.column_name} -> "
                             f"{add.column.name}: the revision raises until you review it")
                break
        mod.ops[:0] = flagged
        all_flagged += flagged
    return notes, all_flagged


def reverse_ops(upgrade_ops: ops.UpgradeOps) -> ops.DowngradeOps:
    """Downgrade ops, with review raises kept in front of each table's changes."""

    def rev(op):
        if isinstance(op, ops.ModifyTableOps):
            reversed_ops = [rev(o) for o in reversed(op.ops)]
            reversed_ops.sort(key=lambda o: not isinstance(o, PossibleRenameOp))  # blocks first
            return ops.ModifyTableOps(op.table_name, reversed_ops, schema=op.schema)
        return op.reverse()

    downgrade = [rev(o) for o in reversed(upgrade_ops.ops)]
    downgrade.sort(key=lambda o: not isinstance(o, PossibleRenameOp))  # table raises first
    return ops.DowngradeOps(ops=downgrade)


def enum_cleanup(op_container, metadata: MetaData) -> str:
    """Source that drops Postgres enum types left behind by drop_table ops.

    Alembic's drop_table leaves the enum type in place, so upgrading again
    fails with 'type already exists'. Only types no other model uses are dropped.
    """
    names = []
    for o in op_container.ops:
        if not isinstance(o, ops.DropTableOp):
            continue
        for col in o.to_table().columns:
            t = col.type
            if isinstance(t, Enum) and t.name and t.native_enum and t.name not in names:
                # still used by a model, or by a table this same function creates
                # (e.g. a downgrade that recreates the table the type came from)
                created = [c.to_table() for c in op_container.ops if isinstance(c, ops.CreateTableOp)]
                used_elsewhere = any(
                    isinstance(c.type, Enum) and c.type.name == t.name
                    for tbl in [*metadata.tables.values(), *created] if tbl.name != o.table_name
                    for c in tbl.columns
                )
                if not used_elsewhere:
                    names.append(t.name)
    if not names:
        return ""
    drops = "\n".join(f'    op.execute("DROP TYPE IF EXISTS {n}")' for n in names)
    return f'\n\nif op.get_context().dialect.name == "postgresql":\n{drops}'


def reuse_existing_enums(op_container, existing: set[str]) -> None:
    """create_table always runs CREATE TYPE for its enum columns, which fails if the type
    already exists (e.g. a table recreated while the old one still uses it). Mark enums
    that exist at that point with create_type=False."""
    seen = set(existing)
    for op in op_container.ops:
        if not isinstance(op, ops.CreateTableOp):
            continue
        for col in op.columns:
            t = getattr(col, "type", None)
            if not (isinstance(t, Enum) and t.name and t.native_enum):
                continue
            if t.name in seen:
                col.type = postgresql.ENUM(*t.enums, name=t.name, create_type=False)
            seen.add(t.name)


def _render_item(type_, obj, autogen_context):
    # Alembic's renderer drops create_type=False; write it out
    if type_ == "type" and isinstance(obj, postgresql.ENUM) and not obj.create_type:
        autogen_context.imports.add("from sqlalchemy.dialects import postgresql")
        values = ", ".join(repr(v) for v in obj.enums)
        return f"postgresql.ENUM({values}, name={obj.name!r}, create_type=False)"
    return False


def add_using_casts(op_container) -> None:
    """Give every generated type change an explicit cast.

    Postgres refuses conversions it has no automatic cast for (e.g. varchar[] ->
    integer[]) unless ALTER ... TYPE has a USING clause.
    """
    for op in op_container.ops:
        for o in op.ops if isinstance(op, ops.ModifyTableOps) else [op]:
            if isinstance(o, ops.AlterColumnOp) and o.modify_type is not None:
                col = o.modify_name or o.column_name
                ident = col if re.fullmatch(r"[a-z_][a-z0-9_]*", col) else '"%s"' % col.replace('"', '""')
                pg_type = _PG_DIALECT.type_compiler_instance.process(o.modify_type)
                o.kw["postgresql_using"] = f"{ident}::{pg_type}"


def compute_diff(engine, metadata: MetaData, script: ScriptDirectory):
    """Replay all migrations into the scratch Postgres, diff against the models."""
    with engine.connect() as conn:
        try:
            run_migrations(conn, script, metadata, "heads")
        except RuntimeError as e:
            if is_review_error(e):
                files = "\n".join(f"  {f}" for f in files_with_review_blocks(Path(script.dir)))
                raise ReviewPending(f"These revisions still have a review block; fix them before "
                                    f"generating again:\n{files}\n  ({e})") from None
            raise
        conn.commit()
        ctx = migration_context(conn, script, metadata)
        upgrade_ops = produce_migrations(ctx, metadata).upgrade_ops
        notes, flagged = detect_possible_renames(upgrade_ops)
        autogen = AutogenContext(ctx, metadata, opts={
            "sqlalchemy_module_prefix": "sa.", "alembic_module_prefix": "op.",
            "user_module_prefix": None, "render_item": _render_item,
        })
        downgrade_ops = reverse_ops(upgrade_ops)
        enums_now = {r[0] for r in conn.exec_driver_sql("SELECT typname FROM pg_type WHERE typtype = 'e'")}
        enums_after = enums_now | {c.type.name for t in metadata.tables.values() for c in t.columns
                                   if isinstance(c.type, Enum) and c.type.name}
        reuse_existing_enums(upgrade_ops, enums_now)
        reuse_existing_enums(downgrade_ops, enums_after)
        add_using_casts(upgrade_ops)
        add_using_casts(downgrade_ops)
        upgrade_src = (rename_review_note(flagged)
                       + _qualify_types(_render_cmd_body(upgrade_ops, autogen))
                       + enum_cleanup(upgrade_ops, metadata))
        downgrade_src = (_qualify_types(_render_cmd_body(downgrade_ops, autogen))
                         + enum_cleanup(downgrade_ops, metadata))
        imports = sorted(autogen.imports)
    return upgrade_ops, notes, upgrade_src, downgrade_src, imports


def describe(upgrade_ops: ops.UpgradeOps) -> list[str]:
    """One short line per change, for printing."""

    def name(x):
        return x if isinstance(x, str) else getattr(x, "name", None)

    lines = []
    for op in upgrade_ops.ops:
        for o in op.ops if isinstance(op, ops.ModifyTableOps) else [op]:
            if isinstance(o, PossibleRenameOp):
                continue  # reported as a note
            diffs = o.to_diff_tuple()
            for d in diffs if isinstance(diffs, list) else [diffs]:
                parts = [n for n in map(name, d[1:4]) if n]
                lines.append(f"{d[0]} {'.'.join(parts)}")
    return lines


# --------------------------------------------------------------------------- SQL files

def revision_sql(script, metadata, rev, downgrade: bool = False) -> str:
    """One revision as Postgres SQL (offline, no database)."""
    buf = io.StringIO()
    try:
        _revision_sql(script, metadata, rev, downgrade, buf)
    except RuntimeError as e:
        if is_review_error(e):
            raise ReviewPending(f"{Path(rev.path).name}: {e}") from None
        raise
    return buf.getvalue()


def _revision_sql(script, metadata, rev, downgrade, buf) -> None:
    if downgrade:
        run_migrations(None, script, metadata, rev.down_revision or "base", downgrade=True,
                       dialect_name="postgresql", as_sql=True, output_buffer=buf,
                       starting_rev=rev.revision)
    else:
        run_migrations(None, script, metadata, rev.revision, dialect_name="postgresql",
                       as_sql=True, output_buffer=buf, starting_rev=rev.down_revision)


def _stale_siblings(path: Path, rev, kind: str):
    """Files for the same revision under an old name (e.g. the message changed)."""
    return [p for p in path.parent.glob(f"*_{rev.revision}_*.{kind}.sql") if p != path]


def write_sql_files(migrations: Path, script, metadata, only=None):
    """Write the Postgres SQL files for every revision, or just `only`. Returns [(path, status)]."""
    results = []
    for index, rev in enumerate(revision_chain(script), start=1):
        if only and rev.revision not in only:
            continue
        try:  # render everything first: a revision with a review block raises
            texts = {"up": revision_sql(script, metadata, rev),
                     "down": revision_sql(script, metadata, rev, True)}
        except ReviewPending:
            results.append((Path(rev.path), "needs-review"))
            continue
        for kind in ("up", "down"):
            path = sql_path(migrations, "postgresql", index, rev, kind)
            results.append((path, write_generated(path, texts[kind], "--")))
            for old in _stale_siblings(path, rev, kind):
                if review_status(old) != "CHECKED":
                    old.unlink()
    return results


def report_files(results) -> None:
    labels = {"created": ("Wrote", None), "updated": ("Updated", None),
              "kept-checked": ("Kept (marked CHECKED, differs from a fresh copy)", "yellow"),
              "needs-review": ("No SQL written yet (it has a review block; fix it, then run write-sql):", "red")}
    for path, status in results:
        if status in labels:
            text, colour = labels[status]
            click.secho(f"{text} {_shown(path)}", fg=colour)


def attributes_block(renames: list[dict]) -> str:
    """A comment recording attribute-only renames (for readers; the CSV tools use the
    per-revision attribute files, not this)."""
    if not renames:
        return ""
    lines = ["", "# Model attribute (CSV header) renames in this revision; the database is unaffected:"]
    lines += [f"#   {r['table']}.{r['old']} -> {r['new']}" for r in renames]
    return "\n".join(lines) + "\n"


# --------------------------------------------------------------------------- CLI

cli = make_cli("Generate Alembic migrations (and their SQL files) from the SQLAlchemy "
               "models, no env.py needed. See the top of migrate.py for details.")


@cli.command()
@click.option("-m", "--message", required=True, help="What this revision does.")
@click.option("--empty", is_flag=True, help="Write an empty revision to fill in by hand.")
@click.pass_obj
def generate(obj, message, empty):
    """Write a new revision (and its SQL files) from the difference between models and migrations."""
    metadata = load_metadata(obj["models"])
    script = script_directory(obj["migrations"])
    chain = revision_chain(script)
    down_revision = chain[-1].revision if chain else None

    snapshot, source = baseline_attributes(obj["migrations"], chain)
    current = model_attributes(metadata)
    renames = attribute_renames(snapshot, current)
    upgrade_ops = None
    if empty:
        upgrade_src = downgrade_src = "pass"
        imports, notes, changes = [], [], []
    else:
        with scratch_postgres(obj) as engine:
            upgrade_ops, notes, upgrade_src, downgrade_src, imports = compute_diff(engine, metadata, script)
        if upgrade_ops.is_empty() and not renames:
            click.echo("No changes between models and migrations.")
            if chain and current is not None and snapshot is None:
                click.secho("note: the latest revision has no attribute names recorded, so attribute "
                            "(CSV header) renames can't be detected. Run snapshot-attributes.", fg="yellow")
            return
        if upgrade_ops.is_empty():  # only attribute (CSV header) renames: nothing for the database
            upgrade_src = downgrade_src = "pass"
        changes = describe(upgrade_ops)
    changes += [f"attribute_rename {r['table']}.{r['old']} -> {r['new']} (CSV headers only)"
                for r in renames]

    revision = rev_id()
    path = obj["migrations"] / "versions" / f"{revision}_{slugify(message)}.py"
    write_generated(path, REVISION_TEMPLATE.format(
        message=message, revision=revision, down_revision=down_revision,
        create_date=datetime.now(timezone.utc).isoformat(timespec="seconds"),
        imports="\n".join(["from alembic import op", "import sqlalchemy as sa", *imports]),
        upgrade=textwrap.indent(upgrade_src, "    "),
        downgrade=textwrap.indent(downgrade_src, "    "),
        attributes=attributes_block(renames),
    ), "#")
    if source == "legacy":
        adopt_legacy_snapshot(obj["migrations"], chain, snapshot)
    if current is not None:
        attrs = attributes_path(obj["migrations"], len(chain) + 1, revision, message)
        write_attributes(attrs, revision, current)
    click.echo(f"Wrote {path}")
    for line in changes:
        click.echo(f"  {line}")
    for note in notes:
        flagged = note.startswith("POSSIBLE RENAME")
        click.secho(f"  {'!!' if flagged else 'note:'} {note}", fg="red" if flagged else "green")

    report_files(write_sql_files(obj["migrations"], script_directory(obj["migrations"]),
                                 metadata, only={revision}))
    click.secho("All files are marked REVIEW STATUS: UNCHECKED. Review them before committing: "
                "autogenerate misses some changes (e.g. new enum values).", fg="yellow")


@cli.command()
@click.option("--skip-db", is_flag=True, help="Only check the SQL files; don't start Postgres.")
@click.pass_obj
def check(obj, skip_db):
    """Exit 1 if the models have unmigrated changes or the SQL files are out of date."""
    metadata = load_metadata(obj["models"])
    script = script_directory(obj["migrations"])
    failed = False

    if not skip_db:
        with scratch_postgres(obj) as engine:
            upgrade_ops, *_ = compute_diff(engine, metadata, script)
        if upgrade_ops.is_empty():
            click.echo("Migrations are up to date with the models.")
        else:
            failed = True
            click.echo("Models have changes without a migration:")
            for line in describe(upgrade_ops):
                click.echo(f"  {line}")

    chain_ = revision_chain(script)
    snapshot, _source = baseline_attributes(obj["migrations"], chain_)
    current = model_attributes(metadata)
    pending = attribute_renames(snapshot, current)
    if pending:
        failed = True
        click.echo("Model attributes renamed without a revision (CSV headers; run generate):")
        for r in pending:
            click.echo(f"  {r['table']}.{r['old']} -> {r['new']}")
    elif current is not None and snapshot is None and chain_:
        click.secho("note: the latest revision has no attribute names recorded, so attribute renames "
                    "can't be detected (run snapshot-attributes).", fg="yellow")
    tracked = [r for r in chain_ if find_attributes_file(obj["migrations"], r.revision)]
    if tracked:
        first = chain_.index(tracked[0])
        missing = [r.revision for r in chain_[first:] if r not in tracked]
        if missing:
            click.secho(f"note: no attribute names recorded for {', '.join(missing)}", fg="yellow")

    stale, edited, blocked = [], [], []
    for index, rev in enumerate(revision_chain(script), start=1):
        wanted = [("postgresql", "up", lambda r=rev: revision_sql(script, metadata, r)),
                  ("postgresql", "down", lambda r=rev: revision_sql(script, metadata, r, True))]
        try:
            revision_sql(script, metadata, rev)
        except ReviewPending:
            blocked.append(_shown(rev.path))
            continue
        for dialect, kind, make in wanted:
            path = sql_path(obj["migrations"], dialect, index, rev, kind)
            if not path.exists():
                stale.append(f"missing  {path}")
            elif _without_marker(path.read_text(encoding="utf-8")) != make():
                if review_status(path) == "CHECKED":  # may be a deliberate reviewed edit
                    edited.append(str(path))
                else:
                    stale.append(f"outdated {path}")
    if blocked:
        failed = True
        click.echo("Revisions with a review block (possible renamed column) to fix:")
        for f in blocked:
            click.echo(f"  {f}")
    if stale:
        failed = True
        click.echo("SQL files don't match the revisions (run write-sql):")
        for line in stale:
            click.echo(f"  {line}")
    else:
        click.echo("SQL files are up to date.")
    for path in edited:
        click.secho(f"note: {path} is marked CHECKED and differs from a fresh copy "
                    "(fine if you edited it on purpose)", fg="yellow")
    if failed:
        sys.exit(1)


@cli.command("write-sql")
@click.pass_obj
def write_sql(obj):
    """(Re)write the Postgres SQL files for every revision.

    Files marked CHECKED are left alone. Unchanged files keep their review status.
    """
    metadata = load_metadata(obj["models"])
    script = script_directory(obj["migrations"])
    if not script.get_heads():
        raise click.ClickException("No revisions yet; run generate first.")
    results = write_sql_files(obj["migrations"], script, metadata)
    report_files(results)
    counts = {s: sum(1 for _, st in results if st == s) for s in ("created", "updated", "unchanged", "kept-checked", "needs-review")}
    click.echo(", ".join(f"{n} {s}" for s, n in counts.items() if n) or "Nothing to do.")


@cli.command("snapshot-attributes")
@click.option("--revision", "target", default=None, help="Revision to record them for. Default: latest.")
@click.option("--force", is_flag=True, help="Replace an existing record.")
@click.pass_obj
def snapshot_attributes(obj, target, force):
    """Record the models' current attribute names for a revision (the baseline for renames).

    generate records them for every new revision; run this only to start tracking, with the
    models as they were at that revision.
    """
    current = model_attributes(load_metadata(obj["models"]))
    if current is None:
        raise click.ClickException("--models is a bare MetaData; attribute names need the declarative Base.")
    script = script_directory(obj["migrations"])
    chain = revision_chain(script)
    if not chain:
        raise click.ClickException("No revisions yet; generate records attribute names from the first one.")
    rev = chain[-1] if target is None else script.get_revision(target)
    existing = find_attributes_file(obj["migrations"], rev.revision)
    if existing and not force:
        raise click.ClickException(f"{_shown(existing)} already exists (use --force to replace it).")
    path = existing or attributes_path(obj["migrations"], chain.index(rev) + 1, rev.revision, rev.doc)
    write_attributes(path, rev.revision, current)
    (obj["migrations"] / LEGACY_ATTRIBUTES_FILE).unlink(missing_ok=True)
    click.echo(f"Wrote {_shown(path)} ({sum(len(c) for c in current.values())} columns "
               f"in {len(current)} tables).")


@cli.command()
@click.pass_obj
def unchecked(obj):
    """List generated files still marked UNCHECKED (exit 1 if there are any)."""
    root = obj["migrations"]
    files = sorted([*root.glob("versions/*.py"), *root.glob("sql/*/*.sql")])
    todo = [p for p in files if review_status(p) == "UNCHECKED"]
    for p in todo:
        click.echo(str(p))
    if todo:
        click.echo(f"{len(todo)} file(s) need review.", err=True)
        sys.exit(1)
    click.echo("Everything generated has been reviewed.")


@cli.command()
@click.pass_obj
def history(obj):
    """List revisions, newest first, with their review status."""
    for rev in script_directory(obj["migrations"]).walk_revisions():
        status = review_status(Path(rev.path)) or "-"
        click.echo(f"{rev.revision}  <- {rev.down_revision or 'base':12}  {status:9}  {(rev.doc or '').strip()}")


@cli.command()
def cleanup():
    """Remove Docker containers left behind by an interrupted run."""
    if shutil.which("docker") is None:
        raise click.ClickException("Docker isn't installed (or not on PATH).")
    ids = _docker("ps", "-aq", "--filter", f"label={DOCKER_LABEL}").split()
    for cid in ids:
        _docker("rm", "-f", cid, check=False)
    click.echo(f"Removed {len(ids)} container(s).")


if __name__ == "__main__":
    run(cli)
