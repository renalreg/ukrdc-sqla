# migration_tool

Tools for keeping the UKRDC database, its views and its CSV data in step with the SQLAlchemy
models in `ukrdc_sqla`.

| Tool | What it's for |
|---|---|
| `migrate.py` | **Database schema migrations.** A thin wrapper that runs **any Alembic command** against a throwaway Postgres (a Docker container, or a server you point it at). Use it to autogenerate revisions from the models and to test them, without touching a real database. |
| `compare_schema.py` | **Checking migrations against a real database.** Builds the migrations in a scratch database and lists every table, column, key and index that differs from an existing database. |
| `csv_migrate.py` | **CSV data migrations.** Numbered step files, each with an `upgrade` and a `downgrade` per model, written with polars. A stamp file records which step every CSV is at. No database needed. |
| `migrations/ukrdc/views.py` | **Views.** Each revision pins a commit of [ukrdc_resources_database](https://github.com/renalreg/ukrdc_resources_database) and rebuilds the views from it around its schema changes. |

Applying migrations to a real database is plain Alembic. See [Applying migrations to a real database](#applying-migrations-to-a-real-database).

---

## Contents

- [Installation](#installation)
- [Layout](#layout)
- [Quick reference](#quick-reference)
- [Database migrations: migrate.py](#database-migrations-migratepy)
- [Writing and reviewing a revision](#writing-and-reviewing-a-revision)
- [Views](#views)
- [Testing migrations](#testing-migrations)
- [Comparing with an existing database: compare_schema.py](#comparing-with-an-existing-database-compare_schemapy)
- [Applying migrations to a real database](#applying-migrations-to-a-real-database)
- [CSV data migrations: csv_migrate.py](#csv-data-migrations-csv_migratepy)
- [Workflows](#workflows)
- [Troubleshooting](#troubleshooting)
- [CI](#ci)

---

## Installation

The tools run from a checkout of this repository. From the project root (the folder with
`pyproject.toml`):

```
poetry install --extras migration
```

The `migration` extra adds alembic, click, psycopg and polars. `pip install "ukrdc-sqla[migration]"`
(or `uv add` / `poetry add` of the same) installs those dependencies into another project, but not
the scripts in this folder: they aren't part of the package.

You also need:

| For | Needs |
|---|---|
| `migrate.py` (scratch databases) | Docker running, **or** a Postgres server where your user can `CREATE DATABASE` (`--db-url`) |
| `compare_schema.py` | A Postgres server where your user can `CREATE DATABASE` (`--scratch-url`, default the server being compared) |
| Anything that runs the migrations (including autogenerate and `--sql`) | `git` on your PATH and access to GitHub, to fetch the views (or a local clone, see [Views](#views)) |
| `csv_migrate.py` | Nothing else |

**Run every command from the project root.**

**PowerShell:** the commands below work as written. `/` and `\` both work in paths. Use a backtick
(`` ` ``) to continue a line, and set environment variables with `$env:NAME = "value"`
(bash: `export NAME=value`). PowerShell doesn't expand `*.csv` for Python, so list files explicitly.

---

## Layout

```
migration_tool/
    __init__.py
    migrate.py                     # Alembic against a throwaway Postgres
    compare_schema.py              # migrations vs an existing database
    csv_migrate.py                 # CSV data migrations
    csv_step_template.py.tmpl      # what csv_migrate.py generate writes
    alembic_template/              # copied into a NEW migrations folder by migrate.py
        alembic.ini
        env.py
        script.py.mako
    README.md

migrations/ukrdc/                  # one folder per models module: ukrdc_sqla.ukrdc:Base -> migrations/ukrdc
    alembic.ini                    # Alembic settings; sqlalchemy.url is empty (use DATABASE_URL)
    env.py                         # how Alembic connects; skips vwe_* models and ORM-only foreign keys
    script.py.mako                 # template for new revisions (with the view calls and VIEWS_REF)
    views.py                       # fetches and rebuilds the views at each revision's VIEWS_REF
    versions/                      # Alembic revisions
    csv_steps/                     # CSV step files: 0001_baseline.py, 0002_add_code_list_region.py, ...

{tables_dir}/csv_versions.json     # CSV stamp file, next to the CSVs it describes
```

New revisions are written from the migrations folder's own `script.py.mako`. `alembic_template/` is
only used when `migrate.py` creates a migrations folder that doesn't exist yet. It copies
`alembic.ini`, `env.py` and `script.py.mako` and nothing else, so **`views.py` has to be copied in by
hand** (see [First-time setup](#first-time-setup-of-a-migrations-folder)).

Placeholders below are in `{braces}`. For this repo, `{module:Base}` is `ukrdc_sqla.ukrdc:Base` and
`{module}` is `ukrdc`.

---

## Quick reference

```
# New revision from model changes, then test it
poetry run python migration_tool/migrate.py revision --autogenerate -m "{message}" --models ukrdc_sqla.ukrdc:Base
poetry run python migration_tool/migrate.py upgrade head --models ukrdc_sqla.ukrdc:Base
poetry run python migration_tool/migrate.py downgrade base --models ukrdc_sqla.ukrdc:Base
poetry run python migration_tool/migrate.py check --models ukrdc_sqla.ukrdc:Base

# How the migrations differ from an existing database
poetry run python migration_tool/compare_schema.py --db-url {url} --migrations migrations/ukrdc

# Apply to a real database
$env:DATABASE_URL = "postgresql+psycopg://{user}:{pass}@{host}:{port}/{db}"
poetry run alembic -c migrations/ukrdc/alembic.ini upgrade head

# CSVs
poetry run python migration_tool/csv_migrate.py generate -m "{message}" --models ukrdc_sqla.ukrdc:Base
poetry run python migration_tool/csv_migrate.py upgrade {tables_dir} --models ukrdc_sqla.ukrdc:Base
```

---

## Database migrations: migrate.py

```
poetry run python migration_tool/migrate.py {alembic command} --models {module:Base} [options]
```

Everything that isn't one of the options below is passed to Alembic unchanged, so any Alembic
command and flag works. The options can go anywhere on the line.

For each command that needs a database, `migrate.py` creates a scratch database (in a new Docker
container, or on `--db-url`'s server), migrates it to `--at`, runs the command, and drops the
database (and container) afterwards. **It never touches a real database.**

### Options

| Option | Effect |
|---|---|
| `--models {module:Base}` | **Required**, even for commands that don't use it. The declarative Base, e.g. `ukrdc_sqla.ukrdc:Base`. Used for autogenerate and `check`, and to name the migrations folder. |
| `--db-url {postgresql://user:pass@host:port/db}` | Use this Postgres server instead of Docker. The user must be able to `CREATE DATABASE`. A scratch database `migrate_scratch_{random}` is created on it and dropped afterwards; the database named in the URL is only used to connect. |
| `--pg-image {image}` | Docker image for the throwaway Postgres (default `postgres:16`). Match production. |
| `--at {revision}` | Migrate the scratch database to `{revision}` before running the command (`base` = empty). Default: `base` for `upgrade`, `head` for everything else. |
| `--migrations {dir}` | Use a different migrations folder (default `migrations/{module}`). Alembic's own `-c {alembic.ini}` also works. |

### Commands

| Command | Database? | Effect |
|---|---|---|
| `revision --autogenerate -m "{message}"` | scratch at `head` | Compares a database built from every revision with the models and writes `versions/{rev}_{message}.py`. Writes nothing if there are no changes. The first time, creates the migrations folder from `alembic_template/`. **Review the revision before committing** ([checklist](#writing-and-reviewing-a-revision)). |
| `revision -m "{message}"` | none | An empty revision to fill in by hand (a data migration, or a views-only change). |
| `upgrade head` | scratch from empty | Runs every migration, to prove they all apply. |
| `upgrade {revision}` | scratch from empty | Same, stopping at `{revision}`. |
| `upgrade head --at {revision}` | scratch at `{revision}` | Upgrades from `{revision}`, to test just the newer migrations. |
| `downgrade base` | scratch at `head` | Runs every downgrade, to prove they all reverse. |
| `downgrade {revision}` / `downgrade -1` | scratch at `head` | Downgrades to `{revision}` / undoes the latest migration. |
| `check` | scratch at `head` | Fails if the models have changes no migration covers yet. |
| `current` | scratch at `--at` | Prints the revision the scratch database reaches. |
| `upgrade head --sql` | none | Prints the SQL for every migration without running it. |
| `upgrade {from}:{to} --sql` / `downgrade {from}:{to} --sql` | none | The SQL between two revisions. |
| `history` / `heads` / `show {revision}` | none | Alembic's usual output. |
| `merge -m "{message}" {rev1} {rev2}` | none | Merges two heads (two branches each added a revision). |

`stamp` runs against a scratch database too, so it's no use here: stamp a real database with
[plain Alembic](#applying-migrations-to-a-real-database).

---

## Writing and reviewing a revision

Autogenerate gets most of a revision right, but **always read it before committing.** Check:

- **Renamed columns or tables** come out as drop + add, which loses the data. Replace them with
  `op.alter_column("{table}", "{old}", new_column_name="{new}")` (or `op.rename_table`) in
  `upgrade()`, and the reverse in `downgrade()`.
- **Type changes** that Postgres can't cast on its own need `postgresql_using="{col}::{type}"` in
  `op.alter_column`. Narrowing a column (e.g. `VARCHAR(256)` to `VARCHAR(100)`) in a downgrade fails
  if any value is too long.
- **Enum types** (`sa.Enum(..., name="...")`) are created with their table but **not dropped by the
  autogenerated downgrade**. A downgrade then leaves them behind, and upgrading again fails with
  `type "{name}" already exists`. Add, after the `drop_table` calls in `downgrade()`:
  ```python
  op.execute("DROP TYPE IF EXISTS {name}")
  ```
- **New NOT NULL columns** on tables with data need a `server_default`, or a nullable column, a data
  update, then `op.alter_column(..., nullable=False)`.
- **Data changes** (backfills, fixing values) go in by hand with `op.execute(...)`.
- **Views:** the template rebuilds the views around every revision; set `VIEWS_REF` only if the
  views changed (see [Views](#views)).
- **Formatting:** autogenerate writes single quotes and long lines that CI rejects. Run
  `poetry run ruff format migrations` and `poetry run ruff check migrations --fix`.

Things autogenerate leaves out on purpose, set in `env.py`:

- **Models whose table name starts with `vwe_`** are views mapped as models. Autogenerate never
  creates, alters or drops them; they come from [views.py](#views).
- **ORM-only foreign keys.** A foreign key flagged
  `ForeignKey("patientrecord.pid", info={ORM_ONLY: True})` is used by SQLAlchemy for joins and
  relationships but isn't written into migrations, neither on new tables nor on existing ones. If
  the database already has a matching key, it's left alone. Remove the flag and autogenerate again
  to have a migration add the key.

---

## Views

Postgres won't alter or drop a column a view depends on, so every revision drops the views, makes
its changes, and builds the views again. The view definitions aren't copied into this repo: each
revision pins the commit of
[ukrdc_resources_database](https://github.com/renalreg/ukrdc_resources_database) they come from.

```python
from views import create_views, drop_views

# ukrdc_resources_database commit SHA (or release tag) the views are built from.
# None keeps the previous revision's views.
VIEWS_REF = None


def upgrade():
    drop_views(down_revision, revision)    # the views in the database now, then the new set
    ...                                    # schema changes
    create_views(revision)


def downgrade():
    drop_views(revision, down_revision)
    ...                                    # reverse schema changes
    create_views(down_revision)
```

New revisions get this from `script.py.mako`. At a ref, the views are the files listed in
`schema/UKRDC/scripts/REBUILD_ALL_VIEWS.DDL`, created in that order from
`schema/UKRDC/views/*.SQL`, with each file's `GRANT` / `ALTER ... OWNER` statements. A file in the
views folder that the `.DDL` doesn't list is ignored. The `"extract".` schema prefix is removed, so
the views are built in the same schema as the tables.

**Rules:**

- **`VIEWS_REF = None`** keeps the previous revision's views (it's inherited through every earlier
  revision). The first revision must set one, or no views are built.
- **Use the full 40-character commit SHA.** GitHub won't serve a short one (you get a clear error),
  and a tag can be moved to point at different SQL.
- **Never change `VIEWS_REF` on a revision that has been applied anywhere.** Views are dropped by the
  names at the ref; views only the old ref had would be left behind. Add a new revision instead.
- **A view outside the set** (e.g. created by hand) that depends on a changed column makes the
  migration fail with `cannot alter type of a column used by a view`. Drop it explicitly; it won't be
  rebuilt:
  ```python
  drop_views(down_revision, revision, also=("{old_view}",))
  ```
- **Drops never cascade.** If something else depends on a view, the drop fails rather than removing
  it unnoticed.
- **Views that need tables the migrations don't create** (`eventcontrol`, `facility`,
  `satellite_map`, listed as `OPTIONAL_TABLES` in `views.py`) are skipped, as are views built on
  them. Postgres logs `WARNING: Not creating {view}: it needs {table}`, but Alembic doesn't print it.
  On a database built only from the migrations, 11 of the 17 views are created.
- **Materialized views** are created with their data, so `vwe_satellite_map` works straight away.
- Privileges are applied only if the role they name (`ukrdc`) exists.

**Fetching:** the first time a ref is needed, `git fetch --depth 1` gets it into a local cache, and
it's read from there afterwards. Anything that runs the migrations needs this: `upgrade`,
`downgrade`, autogenerate and `--sql`.

| Environment variable | Effect |
|---|---|
| `UKRDC_VIEWS_REPO` | Where to fetch from: a URL or a path to a local clone. Default: the GitHub repo. Use a clone on servers without GitHub access. |
| `UKRDC_VIEWS_CACHE` | Cache folder. Default: `~/.cache/ukrdc-views`. |

---

## Testing migrations

Scratch databases, with `migrate.py` (add `--db-url` if you don't use Docker):

```
poetry run python migration_tool/migrate.py upgrade head --models ukrdc_sqla.ukrdc:Base                  # every revision applies
poetry run python migration_tool/migrate.py downgrade base --models ukrdc_sqla.ukrdc:Base                # every revision reverses
poetry run python migration_tool/migrate.py upgrade head --at {previous_rev} --models ukrdc_sqla.ukrdc:Base   # just the new one
poetry run python migration_tool/migrate.py check --models ukrdc_sqla.ukrdc:Base                         # models and migrations agree
poetry run python migration_tool/migrate.py upgrade head --sql --models ukrdc_sqla.ukrdc:Base            # read the SQL
```

Each command succeeds silently or stops with the error. `migrate.py` can't run a downgrade **and
then** an upgrade again in one go, which is what catches leftovers like enum types. For a full round
trip, use a local database you can throw away:

```
$env:DATABASE_URL = "postgresql+psycopg://{user}:{pass}@localhost:5432/{scratch_db}"
poetry run alembic -c migrations/ukrdc/alembic.ini upgrade head
poetry run alembic -c migrations/ukrdc/alembic.ini downgrade base
poetry run alembic -c migrations/ukrdc/alembic.ini upgrade head
```

To check the migrations build the same tables as an existing database, use
[compare_schema.py](#comparing-with-an-existing-database-compare_schemapy).

---

## Comparing with an existing database: compare_schema.py

```
poetry run python migration_tool/compare_schema.py --db-url {url} --migrations migrations/ukrdc [options]
```

Builds the migrations in a scratch database, then lists how its tables differ from the database at
`--db-url`. **The database at `--db-url` is only read.** The scratch database is created on
`--scratch-url`'s server, or `--db-url`'s by default, and dropped afterwards.

| Option | Effect |
|---|---|
| `--db-url {url}` | **Required.** The existing database to compare with. |
| `--migrations {dir}` | **Required.** The migrations folder, e.g. `migrations/ukrdc`. |
| `--revision {rev}` | Build the migrations to `{rev}` (default `head`). Use it to find the revision an existing database matches before stamping it. |
| `--schema {schema}` | Only this schema (repeatable). Default: every schema. |
| `--local-schema {schema}` | Compare this schema of the existing database with the one `--schema` of the migrations, e.g. live `extract` vs migrated `public`. |
| `--scratch-url {url}` | Build the scratch database on this server instead (its user needs `CREATE DATABASE`). Use it when you can't, or shouldn't, create databases on `--db-url`'s server. |
| `--defaults` | Also compare column defaults. Noisy (sequence names, casts). |

It compares tables, columns (type and nullability), primary keys, foreign keys, indexes and unique
constraints. It doesn't compare views, enum values, check constraints or privileges, and
`alembic_version` is ignored.

Output is a line per difference, e.g. `public.eventcontrol: only in the local database` or
`column id: type 'VARCHAR(100)' (migrations) vs 'VARCHAR(30)' (local)`. It exits with code 1 when
there are differences, so it can gate CI.

```
# The live database (tables in the extract schema), building the scratch copy on a local server
poetry run python migration_tool/compare_schema.py `
  --db-url postgresql://{user}:{pass}@{host}:{port}/{db} `
  --migrations migrations/ukrdc `
  --schema public --local-schema extract `
  --scratch-url postgresql://{user}:{pass}@localhost:5432/postgres
```

---

## Applying migrations to a real database

`migrate.py` never touches a real database. Use plain Alembic with the migrations folder:

```
poetry run alembic -c migrations/ukrdc/alembic.ini {command}
```

### Connecting

The database comes from the `DATABASE_URL` environment variable, or `sqlalchemy.url` in
`alembic.ini` when that isn't set.

```
$env:DATABASE_URL = "postgresql+psycopg://{user}:{pass}@{host}:{port}/{db}"     # PowerShell
export DATABASE_URL="postgresql+psycopg://{user}:{pass}@{host}:{port}/{db}"     # bash
```

- Use `postgresql+psycopg://` (psycopg 3) or `postgresql+psycopg2://`. A bare `postgresql://` means
  psycopg2.
- In `alembic.ini`, write `%` in a password as `%%`. In `DATABASE_URL`, write it as `%25`.
- `ukrdc_sqla` isn't needed to apply migrations, only `alembic`, the driver and `git` (for the views).

### Building into a schema other than public

The migrations don't name a schema, so everything (tables, views, enum types and `alembic_version`)
goes in the first schema on the connection's `search_path`. Create the schema, then set the path
in the URL:

```
psql -h {host} -p {port} -U {user} -d {db} -c "CREATE SCHEMA IF NOT EXISTS {schema}"
$env:DATABASE_URL = "postgresql+psycopg://{user}:{pass}@{host}:{port}/{db}?options=-csearch_path%3D{schema}"
```

Keep that `options=` for **every** later command on that database. Without it, Alembic looks in
`public`, finds no `alembic_version` table, and starts again from the beginning.

### Status

```
poetry run alembic -c migrations/ukrdc/alembic.ini current      # the revision the database is at
poetry run alembic -c migrations/ukrdc/alembic.ini history      # all revisions
```

### An empty database

```
poetry run alembic -c migrations/ukrdc/alembic.ini upgrade head
```

### A database that already has the tables

An existing database (e.g. built from the old DDL) already has what the early revisions create, so
`upgrade head` fails with `relation ... already exists`. Record the revision it matches instead,
then apply only the later ones:

```
# 1. Find the revision it matches (no differences)
poetry run python migration_tool/compare_schema.py --db-url {url} --migrations migrations/ukrdc --revision {rev}
# 2. Record it (writes alembic_version only, changes nothing else)
poetry run alembic -c migrations/ukrdc/alembic.ini stamp {rev}
# 3. Apply the rest
poetry run alembic -c migrations/ukrdc/alembic.ini upgrade head
```

The first `upgrade` after a stamp drops the views of `{rev}`'s `VIEWS_REF` by name, so the views
already in the database need the same names. Views it doesn't know about stay in place, unless
they depend on a changed column (see [Views](#views)).

### Upgrading and downgrading

```
poetry run alembic -c migrations/ukrdc/alembic.ini upgrade head
poetry run alembic -c migrations/ukrdc/alembic.ini upgrade {rev}
poetry run alembic -c migrations/ukrdc/alembic.ini downgrade -1
poetry run alembic -c migrations/ukrdc/alembic.ini downgrade {rev}
```

### SQL for review, or for a DBA to run

```
poetry run alembic -c migrations/ukrdc/alembic.ini upgrade {current_rev}:head --sql > upgrade.sql
poetry run alembic -c migrations/ukrdc/alembic.ini downgrade head:{rev} --sql > downgrade.sql
```

The view SQL is included (as `DO` blocks), so this needs `git` too.

### Before applying to live

- **Back up**, and test the same upgrade on a recent copy first.
- **One transaction.** A run applies all its revisions in one transaction. Postgres rolls back schema
  changes too, so if anything fails, nothing (views included) is left half done.
- **Locks.** Dropping and recreating the views takes exclusive locks on them, and altering a column
  locks its table. Queries and extracts using them wait, or make the migration wait. Run it when
  nothing else is.
- **Time.** Materialized views are repopulated, and changing a column's type can rewrite a large
  table.
- **Skipped views.** If the database lacks `eventcontrol`, `facility` or `satellite_map`, the views
  needing them aren't built. Check the Postgres log for `Not creating`.

---

## CSV data migrations: csv_migrate.py

```
poetry run python migration_tool/csv_migrate.py {command} {arguments} --models {module:Base}
```

### How it works

- **Step files** (`migrations/{module}/csv_steps/{NNNN}_{message}.py`) are numbered from `0001`.
  Each one:
  1. **loads** a CSV into a polars DataFrame (every value as a string, empty cells as null),
  2. **transforms** it with that model's `upgrade` or `downgrade` function,
  3. **saves** it back, keeping the file's original line endings (`\r\n` or `\n`).
- In each step file, every model is listed in `UPGRADES` and `DOWNGRADES`, mapped to `None`.
  **`None` means "nothing to do for this model in this step"**: the CSV isn't loaded or saved, and
  the tool moves straight on to the next step.
- **Models are named by class**, e.g. `Code` for the `code_list` table, `Facility` for
  `facility_new`. `history` and the step files list them.
- **The stamp file** `{tables_dir}/csv_versions.json` records each CSV's model and the step it's at,
  with paths relative to `{tables_dir}`:
  ```json
  {
    "code_list/north.csv": {"model": "Code", "step": "0003"}
  }
  ```
  `upgrade` and `downgrade` start every CSV from its own stamped step, and update the stamp after
  each step, so a failure leaves the CSV and its stamp at the last good step.
- **A step** can be given as `0003` or `3`, `head` (the latest step), or `base` (before the first
  step).

### Options

| Option | Effect |
|---|---|
| `--models {module:Base}` | **Required.** The declarative Base. Gives the model names and the steps folder. |
| `--steps {dir}` | Use a different steps folder (default `migrations/{module}/csv_steps`). |

### Commands

| Command | Effect |
|---|---|
| `generate -m "{message}"` | Writes the next step, `csv_steps/{NNNN}_{message}.py`, from `csv_step_template.py.tmpl`. It contains a template `upgrade_template` / `downgrade_template` pair, and every model mapped to `None`. Fill it in (see below) and check it before committing. |
| `init {tables_dir}` | Finds every CSV under `{tables_dir}` (subfolders included) and stamps it at `head` in `{tables_dir}/csv_versions.json`. Each CSV's model comes from its **folder name**, then its **file name**, matched against model class and table names (case and `_` ignored): `tables/code_list/x.csv` becomes `Code`. CSVs it can't match are listed and left unstamped. Existing stamps for other files are kept. |
| `init {tables_dir} --step {step}` | Same, but stamps them at `{step}` (e.g. when the CSVs match an older step). |
| `stamp {tables_dir} {Model} {csv} [{csv} ...]` | Stamps the given CSVs as `{Model}` at `head` (e.g. files `init` couldn't match, or new CSVs added later). |
| `stamp {tables_dir} {Model} {csv} --step {step}` | Same, at `{step}`. |
| `upgrade {tables_dir}` / `upgrade {tables_dir} head` | Upgrades every stamped CSV, in place, from its stamped step through every later step. |
| `upgrade {tables_dir} {step}` | Same, up to `{step}`. |
| `upgrade {tables_dir} head --model {Model}` | Only the CSVs of `{Model}` (repeatable). |
| `upgrade {tables_dir} head --csv {csv}` | Only that CSV (repeatable). |
| `downgrade {tables_dir} {step}` | Downgrades every stamped CSV, in place, back to `{step}` (running each step's `downgrade`, newest first). |
| `downgrade {tables_dir} base` | All the way back, before step 0001. `--model` and `--csv` work here too. |
| `current {tables_dir}` | Lists each stamped CSV with its model and step, flagging any behind `head`. |
| `history` | Lists the steps, oldest first. |

A step file also runs on its own on one CSV. This doesn't read or update the stamp file:

```
poetry run python migrations/{module}/csv_steps/{NNNN}_{message}.py upgrade {Model} {in.csv} [{out.csv}]
poetry run python migrations/{module}/csv_steps/{NNNN}_{message}.py downgrade {Model} {in.csv} [{out.csv}]
```

Without `{out.csv}` the CSV is changed in place. Use it to try a step on a copy before running it
on everything.

### Filling in a step file

`generate` writes this (models abbreviated):

```python
def upgrade_template(df: pl.DataFrame) -> pl.DataFrame:
    return df


def downgrade_template(df: pl.DataFrame) -> pl.DataFrame:
    return df


# None: nothing to do for that model in this step.
UPGRADES = {
    "Code": None,
    "Facility": None,
    ...
}

DOWNGRADES = {
    "Code": None,
    "Facility": None,
    ...
}
```

For each model the step changes, copy the template pair, name it after the model and point that
model's entries at it:

```python
def upgrade_code(df: pl.DataFrame) -> pl.DataFrame:
    return df.with_columns(pl.lit(None, pl.String).alias("region"))


def downgrade_code(df: pl.DataFrame) -> pl.DataFrame:
    return df.drop("region")


UPGRADES = {
    "Code": upgrade_code,
    "Facility": None,
    ...
}

DOWNGRADES = {
    "Code": downgrade_code,
    "Facility": None,
    ...
}
```

You can delete `upgrade_template` / `downgrade_template` once you're done, or leave them. Nothing
uses them.

Common polars operations (values are strings, so a new column's default is a string too):

| Change | upgrade | downgrade |
|---|---|---|
| Add a column | `df.with_columns(pl.lit("{default}").alias("{col}"))`, or `pl.lit(None, pl.String)` for empty | `df.drop("{col}")` |
| Drop a column | `df.drop("{col}")` | `df.with_columns(pl.lit(None, pl.String).alias("{col}"))` (the values are gone) |
| Rename a column | `df.rename({"{old}": "{new}"})` | `df.rename({"{new}": "{old}"})` |
| Fill empty cells | `df.with_columns(pl.col("{col}").fill_null("{value}"))` | usually `df` (can't tell which were empty) |
| Reformat values | `df.with_columns(pl.col("{col}").str.to_date("%d/%m/%Y").cast(pl.String))` | the reverse, e.g. `.str.to_date().dt.strftime("%d/%m/%Y")` |
| Reorder columns | `df.select(["{col1}", "{col2}", ...])` | the old order |

---

## Workflows

### First-time setup of a migrations folder

`migrations/ukrdc/` already exists in this repo, so this is only needed for another models module,
or to start again. Run it while the database and the CSVs both match the current models.

```
# 1. Database: create the folder, add views.py, then the initial revision
mkdir migrations/{module}
#    -> copy views.py into migrations/{module}/ if the module has views. It must be there before
#       the first revision is generated (migrate.py doesn't copy it).
poetry run python migration_tool/migrate.py revision --autogenerate -m "initial" --models {module:Base}
#    -> in the new revision: set VIEWS_REF to a full SHA, add DROP TYPE for any enums to downgrade(),
#       then ruff format it
poetry run python migration_tool/migrate.py upgrade head --models {module:Base}
poetry run python migration_tool/migrate.py downgrade base --models {module:Base}

# 2. CSVs: a baseline step (nothing to fill in), then stamp every CSV at it
poetry run python migration_tool/csv_migrate.py generate -m "baseline" --models {module:Base}
poetry run python migration_tool/csv_migrate.py init {tables_dir} --models {module:Base}
poetry run python migration_tool/csv_migrate.py current {tables_dir} --models {module:Base}   # check the models it picked

# 3. Commit migrations/{module}/ and {tables_dir}/csv_versions.json
```

`alembic_template/script.py.mako` is what a new folder's revisions are written from. If it includes
the view calls (`from views import ...`), the module needs `views.py`; for a module without views,
remove those lines from the new folder's `script.py.mako`.

### Adding a column

For example, adding `region` to `Code` (`code_list`).

```
# 1. Add the column to the model in ukrdc_sqla.

# 2. Database revision, then test it both ways
poetry run python migration_tool/migrate.py revision --autogenerate -m "add code_list.region" --models ukrdc_sqla.ukrdc:Base
#    -> review migrations/ukrdc/versions/{rev}_add_code_list_region.py, ruff format it
poetry run python migration_tool/migrate.py upgrade head --models ukrdc_sqla.ukrdc:Base
poetry run python migration_tool/migrate.py downgrade base --models ukrdc_sqla.ukrdc:Base
poetry run python migration_tool/migrate.py check --models ukrdc_sqla.ukrdc:Base

# 3. CSV step
poetry run python migration_tool/csv_migrate.py generate -m "add code_list.region" --models ukrdc_sqla.ukrdc:Base
#    -> in csv_steps/{NNNN}_add_code_list_region.py, add upgrade_code (add the column)
#       and downgrade_code (drop it), and map "Code" to them in UPGRADES / DOWNGRADES

# 4. Migrate the CSVs and check the result
poetry run python migration_tool/csv_migrate.py upgrade {tables_dir} head --models ukrdc_sqla.ukrdc:Base
poetry run python migration_tool/csv_migrate.py current {tables_dir} --models ukrdc_sqla.ukrdc:Base
git diff {tables_dir}                                   # only the new column should change

# 5. Commit the model, the revision, the step file, the CSVs and csv_versions.json together
```

### Renaming a column

The same as adding one, with two differences:

- **Database revision:** replace autogenerate's `drop_column` + `add_column` with
  `op.alter_column("{table}", "{old}", new_column_name="{new}")` in `upgrade()`, and the reverse in
  `downgrade()`.
- **CSV step:** `df.rename({"{old}": "{new}"})` in `upgrade_{model}`, and the reverse in
  `downgrade_{model}`.

### Changing a column's type or length

Autogenerate writes `op.alter_column(..., type_=...)`. Add `postgresql_using=` if Postgres can't
cast the old values itself, and make sure the downgrade's narrower type fits the data. The views
are dropped and rebuilt around it automatically. A CSV step is only needed if the values' format
changes.

### Changing the views only

```
# 1. Merge the view change in ukrdc_resources_database and copy the full commit SHA.
# 2. An empty revision (it already drops and rebuilds the views)
poetry run python migration_tool/migrate.py revision -m "views: {what changed}" --models ukrdc_sqla.ukrdc:Base
#    -> set VIEWS_REF = "{sha}" in it
# 3. Test
poetry run python migration_tool/migrate.py upgrade head --models ukrdc_sqla.ukrdc:Base
poetry run python migration_tool/migrate.py downgrade base --models ukrdc_sqla.ukrdc:Base
```

A view that depends on a column the models change needs the new `VIEWS_REF` on the same revision
as the column change, so the old view is dropped first and the new one built afterwards.

### Changing several models in one migration

One revision and one `generate` per migration. Fill in a function pair for every model the step
touches, and leave the rest as `None`. `upgrade` runs each CSV through its own model's function and
skips the others.

### New CSVs added later

Stamp them at the step whose columns they already match (usually `head`):

```
poetry run python migration_tool/csv_migrate.py stamp {tables_dir} {Model} {tables_dir}/{folder}/{new.csv} --models ukrdc_sqla.ukrdc:Base
```

Or run `init {tables_dir}` again. Be careful: that re-stamps **every** CSV it finds at `head`, so
only do it when they're all up to date.

### Deploying to a database

1. `compare_schema.py --revision {rev}` against a copy confirms which revision it's at (or
   `alembic current`, if it's already stamped).
2. `alembic ... upgrade {rev}:head --sql` for review, if needed.
3. `alembic ... upgrade head` on the copy, then on the real database (see
   [Before applying to live](#before-applying-to-live)).
4. `alembic ... current` shows `head`.

### Undoing a migration

```
# CSVs back to the step before the latest one (e.g. 0003 -> 0002)
poetry run python migration_tool/csv_migrate.py downgrade {tables_dir} {NNNN-1} --models ukrdc_sqla.ukrdc:Base
# then delete (or fix) the step file and regenerate if needed
```

For the database: if the revision hasn't been applied anywhere, delete the file. If it has, run
`alembic -c migrations/ukrdc/alembic.ini downgrade -1` against that database first.

### When a CSV fails to migrate

`upgrade` / `downgrade` print `FAILED {csv} ({Model}) at step {NNNN} ...`, carry on with the other
CSVs, and exit with an error. The failed CSV and its stamp stay at the last step that worked. Fix
the step file (or the CSV), then run the same `upgrade` again: it picks up from the stamped step.

### Two branches both added a revision or step

- **Database:** Alembic reports multiple heads. Run
  `migrate.py merge -m "merge" {rev1} {rev2} --models ukrdc_sqla.ukrdc:Base`, or re-point the newer
  revision's `down_revision` at the other one. If the two branches' `VIEWS_REF`s differ, the
  generated merge revision stops with "Merged branches have different VIEWS_REF". Give it its own
  `VIEWS_REF`, drop each parent's views separately with `drop_views(*down_revision, revision)` in
  `upgrade()`, and in `downgrade()` use `drop_views(revision, *down_revision)` and `create_views`
  with the parent whose views should come back.
- **CSV steps:** `csv_migrate.py` stops with "Two steps numbered {NNNN}". Rename the newer file to the
  next free number and set its `step` / `previous` values.

---

## Troubleshooting

| Message | Cause and fix |
|---|---|
| `Docker isn't installed` / `docker run failed (is Docker running?)` | Start Docker, or pass `--db-url` to a Postgres server. |
| `Couldn't create a database on ...` | The user in `--db-url` / `--scratch-url` can't `CREATE DATABASE`. Use a server where it can, e.g. a local one. |
| `Can't load --models ...` / `has no tables` | Run from the project root in the Poetry environment, and point `--models` at the module that defines every model (`ukrdc_sqla.ukrdc:Base`). |
| `No migrations/{module}/alembic.ini yet` | Create the folder with `revision --autogenerate`, or pass `--migrations`. |
| `No module named 'views'` | `views.py` is missing from the migrations folder. Copy it in. |
| `Couldn't fetch VIEWS_REF ...` | No `git`, no access to GitHub, or no such commit or tag. Set `UKRDC_VIEWS_REPO` to a local clone. |
| `use the full 40-character commit SHA` | `VIEWS_REF` is a short SHA. |
| `type "{name}" already exists` | An earlier downgrade left an enum type behind. Add `DROP TYPE IF EXISTS {name}` to that downgrade; drop the type by hand where it's already left over. |
| `relation "{table}" already exists` (real database) | The database already has the tables. [Stamp it](#a-database-that-already-has-the-tables) instead. |
| `cannot alter type of a column used by a view` | A view outside the `VIEWS_REF` set depends on the column. Add it to `drop_views(..., also=(...))`. |
| `cannot drop view ... because other objects depend on it` | Something outside the set depends on the view. Drop it first with `also=`. |
| Some views missing after `upgrade` | Skipped because `eventcontrol`, `facility` or `satellite_map` is missing. Check the Postgres log for `Not creating`. |
| `Multiple head revisions are present` | Two branches each added a revision. [Merge them](#two-branches-both-added-a-revision-or-step). |
| Alembic starts from the first revision on a database that has them all | It's looking in a different schema. Use the same `search_path` as before. |
| `Not a model: {name}` (csv_migrate) | Use the model class name (`Code`), not the table name (`code_list`). |
| `0 run, 1 skipped` (csv_migrate) | The model is mapped to `None` in that step, or the key doesn't match the class name. |
| `Two steps numbered {NNNN}` (csv_migrate) | Two branches added the same step number. [Renumber the newer one](#two-branches-both-added-a-revision-or-step). |

---
