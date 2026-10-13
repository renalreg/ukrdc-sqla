"""Database views, fetched from renalreg/ukrdc_resources_database at a pinned git ref.

Each revision says which commit of that repo its views come from:

    VIEWS_REF = "4b6133e32e445346a050d6b922b8dad871a222a0"   # full SHA, or a release tag
    VIEWS_REF = None                                          # same as the previous revision

and rebuilds the views around its schema changes (Postgres won't alter a column a view
depends on):

    from views import create_views, drop_views

    def upgrade():
        drop_views(down_revision, revision)   # the views in the db now, then the new set
        ...  # schema changes
        create_views(revision)

    def downgrade():
        drop_views(revision, down_revision)
        ...  # reverse schema changes
        create_views(down_revision)

At a ref, the views are the files listed in schema/UKRDC/scripts/REBUILD_ALL_VIEWS.DDL,
created in that order from schema/UKRDC/views/*.SQL, together with the GRANT / ALTER ...
OWNER statements in each file. The "extract". schema prefix is removed so the views are
built in the same schema as the tables.

Once a revision has been applied anywhere, don't change its VIEWS_REF: dropping works from
the ref, so views only the old ref had would be left behind. Add a new revision instead.

Prefer a full commit SHA to a tag: a tag can be moved to other SQL. Refs are fetched with
`git fetch --depth 1` into a local cache and reused from there. Environment variables:

    UKRDC_VIEWS_REPO   where to fetch from: a URL or a path to a local clone (default GitHub),
                       e.g. for a server without access to GitHub
    UKRDC_VIEWS_CACHE  cache directory (default ~/.cache/ukrdc-views)
"""

from __future__ import annotations

import functools
import os
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

from alembic import context, op

REPO = os.environ.get(
    "UKRDC_VIEWS_REPO", "https://github.com/renalreg/ukrdc_resources_database.git"
)
CACHE = Path(
    os.environ.get("UKRDC_VIEWS_CACHE") or Path.home() / ".cache" / "ukrdc-views"
)
VIEWS_DIR = "schema/UKRDC/views"
BUILD_ORDER = "schema/UKRDC/scripts/REBUILD_ALL_VIEWS.DDL"

# Tables some views use that the migrations don't create: they exist only in databases set
# up from the old DDL. A view that needs a missing one is skipped with a warning (as are
# views built on it) instead of failing the migration.
OPTIONAL_TABLES = ("eventcontrol", "facility", "satellite_map")


@dataclass(frozen=True)
class View:
    name: str
    sql: str  # the SELECT the view is built from
    materialized: bool
    privileges: tuple[tuple[str, str], ...]  # (GRANT/ALTER statement, role it names)
    requires: tuple[str, ...]  # optional tables and other views it selects from

    @property
    def kind(self) -> str:
        return "MATERIALIZED VIEW" if self.materialized else "VIEW"


# ----------------------------------------------------------------------- which ref, when


def views_ref(revision) -> str | None:
    """The VIEWS_REF in effect at `revision`: its own, or the nearest earlier one's."""
    if revision is None:
        return None
    if isinstance(revision, (tuple, list)):  # a merge revision's parents
        refs = {views_ref(r) for r in revision}
        if len(refs) > 1:
            raise ValueError(f"Merged branches have different VIEWS_REF: {sorted(map(str, refs))}")
        return refs.pop() if refs else None
    script = context.script.get_revision(revision)
    try:
        return getattr(script.module, "VIEWS_REF", None) or views_ref(script.down_revision)
    except ValueError as e:
        raise ValueError(f"{e}. Set VIEWS_REF on revision {revision}.") from None


def views_for(revision) -> tuple[View, ...]:
    ref = views_ref(revision)
    return views_at(ref) if ref else ()


# ------------------------------------------------------------------- fetching and parsing


def _git(*args: str, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", "-C", str(CACHE), *args], capture_output=True, text=True, check=check
    )


@functools.cache
def _commit(ref: str) -> str:
    """The commit SHA for `ref`, fetching it into the cache if it isn't there yet."""
    if not (CACHE / "HEAD").exists():
        CACHE.mkdir(parents=True, exist_ok=True)
        subprocess.run(["git", "init", "--bare", "-q", str(CACHE)], check=True)
    pinned = f"refs/pinned/{ref}"

    def resolve():
        return _git("rev-parse", "--verify", "-q", f"{pinned}^{{commit}}", check=False)

    found = resolve()
    if found.returncode:
        if re.fullmatch(r"[0-9a-f]{7,39}", ref):
            raise ValueError(f"VIEWS_REF {ref!r}: use the full 40-character commit SHA")
        fetched = _git(
            "fetch", "--depth=1", "--no-tags", "-q", REPO, f"+{ref}:{pinned}", check=False
        )
        if fetched.returncode:
            raise RuntimeError(
                f"Couldn't fetch VIEWS_REF {ref!r} from {REPO}: {fetched.stderr.strip()}"
            )
        found = resolve()
    return found.stdout.strip()


def _read(commit: str, path: str) -> str:
    return _git("show", f"{commit}:{path}").stdout


_HEADER = re.compile(
    r"CREATE\s+(?:OR\s+REPLACE\s+)?(MATERIALIZED\s+)?VIEW\s+(?:\"?extract\"?\.)?(\w+)\s+AS\b",
    re.I,
)
_TAIL = re.compile(r"^\s*(?:GRANT|ALTER)\b", re.I | re.M)
_SCHEMA = re.compile(r'(?<![\w."])"?extract"?\.\s*', re.I)


def _parse(path: str, text: str) -> tuple[str, str, bool, tuple]:
    header = _HEADER.search(text)
    if not header:
        raise ValueError(f"{path}: no CREATE [MATERIALIZED] VIEW ... AS found")
    rest = text[header.end():]
    tail = _TAIL.search(rest)
    body, tail_sql = (rest[: tail.start()], rest[tail.start():]) if tail else (rest, "")

    body = body.strip().rstrip(";").strip()
    body = re.sub(r"\s*WITH\s+NO\s+DATA$", "", body, flags=re.I).rstrip(";").strip()
    body = _SCHEMA.sub("", body)

    privileges = []
    tail_sql = re.sub(r"--[^\n]*", "", tail_sql)
    for statement in tail_sql.split(";"):
        statement = " ".join(_SCHEMA.sub("", statement).split())
        if not statement:
            continue
        role = re.search(r"\bTO\s+(\w+)$", statement, re.I)
        if not re.match(r"(GRANT|ALTER)\b", statement, re.I) or not role:
            raise ValueError(f"{path}: unexpected statement after the view: {statement}")
        privileges.append((statement, role.group(1)))
    return header.group(2).lower(), body, bool(header.group(1)), tuple(privileges)


@functools.cache
def views_at(ref: str) -> tuple[View, ...]:
    """The views defined at `ref` of the repo, in creation order."""
    commit = _commit(ref)
    files = {
        Path(p).name.lower(): p
        for p in _git("ls-tree", "--name-only", commit, f"{VIEWS_DIR}/").stdout.split()
    }
    order = re.findall(r"^\s*\\i\s+\S*?([^/\s]+\.sql)\s*$", _read(commit, BUILD_ORDER), re.I | re.M)
    if not order:
        raise ValueError(f"{BUILD_ORDER} at {ref} lists no views")

    parsed = []
    for filename in order:
        path = files.get(filename.lower())
        if not path:
            raise ValueError(f"{BUILD_ORDER} at {ref} lists {filename}, not in {VIEWS_DIR}")
        name, sql, materialized, privileges = _parse(path, _read(commit, path))
        if name != Path(filename).stem.lower():
            raise ValueError(f"{path} at {ref} defines {name}, not {Path(filename).stem}")
        if "$view$" in sql:
            raise ValueError(f"{path} at {ref} contains $view$")
        parsed.append((name, sql, materialized, privileges))

    names = [name for name, *_ in parsed]
    return tuple(
        View(
            name,
            sql,
            materialized,
            privileges,
            requires=tuple(
                t
                for t in (*OPTIONAL_TABLES, *names)
                if t != name and re.search(rf"\b{t}\b", sql, re.I)
            ),
        )
        for name, sql, materialized, privileges in parsed
    )


# ------------------------------------------------------------------------------- SQL


def _drop_sql(name: str) -> str:
    """Drop `name` if it's a view or materialized view, whichever it is."""
    return f"""
DO $do$
DECLARE
  kind "char" := (SELECT relkind FROM pg_class WHERE oid = to_regclass('{name}'));
BEGIN
  IF kind = 'v' THEN
    EXECUTE 'DROP VIEW {name}';
  ELSIF kind = 'm' THEN
    EXECUTE 'DROP MATERIALIZED VIEW {name}';
  END IF;
END
$do$"""


def _create_sql(view: View) -> str:
    skip = ""
    if view.requires:
        missing = " OR ".join(f"to_regclass('{t}') IS NULL" for t in view.requires)
        skip = f"""
  IF {missing} THEN
    RAISE WARNING 'Not creating {view.name}: it needs {", ".join(view.requires)}';
    RETURN;
  END IF;"""
    privileges = "".join(
        f"""
  IF EXISTS (SELECT FROM pg_roles WHERE rolname = '{role}') THEN
    EXECUTE $priv${statement}$priv$;
  END IF;"""
        for statement, role in view.privileges
    )
    return f"""
DO $do$
BEGIN{skip}
  EXECUTE $view$
CREATE {view.kind} {view.name} AS
{view.sql}
$view$;{privileges}
END
$do$"""


# ---------------------------------------------------------------------- for migrations


def drop_views(*revisions, also: tuple[str, ...] = ()) -> None:
    """Drop the views in `also`, then each revision's views in turn, dependants first.

    Pass the revision whose views are in the database first. Views that don't exist are
    skipped. A view something else still depends on makes the drop fail rather than
    cascade, so nothing is removed unnoticed.
    """
    names = list(also)
    for revision in revisions:
        for view in reversed(views_for(revision)):
            if view.name not in names:
                names.append(view.name)
    for name in names:
        op.execute(_drop_sql(name))


def create_views(revision) -> None:
    """Create `revision`'s views (materialized views are populated as they're created)."""
    for view in views_for(revision):
        op.execute(_create_sql(view))