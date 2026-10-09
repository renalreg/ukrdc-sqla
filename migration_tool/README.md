# migration_tool
Two command-line tools for keeping the database and the CSV data in step with the SQLAlchemy models.

# installation
- poetry install --extras migration 
- pip install "ukrdc-sqla[migration]"
- uv add "ukrdc-sqla[migration]"
- poetry add "ukrdc-sqla[migration]"


| Tool | What it's for | Needs |
|---|---|---|
| `migrate.py` | Database schema migrations. A thin wrapper that runs **any Alembic command** against a throwaway Postgres (a Docker container, or a server you point it at), so you can autogenerate and test migrations without touching a real database. | alembic, sqlalchemy, click, psycopg, Docker (or `--db-url`) |
| `csv_migrate.py` | CSV data migrations. Numbered step files, each with an `upgrade` and a `downgrade` per model, written with polars. A stamp file records which step every CSV is at, so `upgrade head` brings them all up to date. No database needed. | polars, sqlalchemy, click |

```
migration_tool/
    migrate.py
    csv_migrate.py
    csv_step_template.py.tmpl      # what csv_migrate.py generate writes
    alembic_template/              # copied into a new migrations folder by migrate.py
        alembic.ini
        env.py
        script.py.mako
```

Run everything from the project root (the folder with `pyproject.toml`). Generated files go in `migrations/{module}/`, where `{module}` is the last part of the models module, e.g. `migrations/ukrdc/` for `ukrdc_sqla.ukrdc:Base`:

```
migrations/ukrdc/
    alembic.ini, env.py, script.py.mako
    versions/                      # Alembic revisions
    csv_steps/                     # CSV step files: 0001_baseline.py, 0002_add_facility_region.py, ...
```

The stamp file, `csv_versions.json`, lives in the tables folder next to the CSVs it describes.

Placeholders below are in `{braces}`. `--models` is always required and can go anywhere on the line.

---

## migrate.py: database migrations

```
poetry run python migration_tool/migrate.py {alembic command} --models {module:Base} [options]
```

Everything that isn't one of the options below is passed to Alembic unchanged, so any Alembic command and flag works.

### Options

| Option | Effect |
|---|---|
| `--models {module:Base}` | **Required.** The declarative Base, e.g. `ukrdc_sqla.ukrdc:Base`. Used for autogenerate and to name the migrations folder. |
| `--db-url {postgresql://user:pass@host:port/db}` | Use this Postgres server instead of Docker. The user must be able to `CREATE DATABASE`; a scratch database is created on it and dropped afterwards. |
| `--pg-image {image}` | Docker image for the throwaway Postgres (default `postgres:16`). Match production. |
| `--at {revision}` | Migrate the throwaway database to `{revision}` before running the command (`base` = empty). Default: `base` for `upgrade`, `head` for everything else. |
| `--migrations {dir}` | Use a different migrations folder (default `migrations/{module}`). |

The throwaway database only exists for the one command. It's never your real database.

### Commands

| Command | Effect |
|---|---|
| `revision --autogenerate -m "{message}"` | Builds a throwaway database at `head`, compares it with the models and writes `migrations/{module}/versions/{rev}_{message}.py`. Writes nothing if there are no changes. The first time, it creates the migrations folder from `alembic_template/`. **Check the revision before committing** (a renamed column comes out as drop + add, and type changes may need `postgresql_using=`). |
| `revision -m "{message}"` | Writes an empty revision to fill in by hand (e.g. a data migration). No database. |
| `upgrade head` | Runs every migration from an empty database, to prove they all apply. |
| `upgrade {revision}` | Same, but stops at `{revision}`. |
| `upgrade head --at {revision}` | Starts the throwaway database at `{revision}` and upgrades from there, to test just the newer migrations. |
| `downgrade base` | Starts at `head` and runs every downgrade, to prove they all reverse. |
| `downgrade {revision}` | Starts at `head` and downgrades to `{revision}`. |
| `downgrade -1` | Starts at `head` and undoes the latest migration. |
| `check` | Fails if the models have changes that no migration covers yet. |
| `current` | Prints the revision the throwaway database reaches (useful with `--at`). |
| `upgrade head --sql` | Prints the SQL for every migration without running it. No database. |
| `upgrade {from}:{to} --sql` | Prints the SQL between two revisions. No database. |
| `history` | Lists the revisions. No database. |
| `heads` / `show {revision}` | Alembic's usual output. No database. |
| `merge -m "{message}" {rev1} {rev2}` | Merges two heads (e.g. after two branches both added a revision). |

### Applying migrations to a real database

`migrate.py` never touches a real database. Use plain Alembic with the migrations folder, with the URL your `env.py` reads:

```
poetry run alembic -c migrations/{module}/alembic.ini upgrade head
```

---

## csv_migrate.py: CSV data migrations

```
poetry run python migration_tool/csv_migrate.py {command} {arguments} --models {module:Base}
```

### How it works

- **Step files** (`migrations/{module}/csv_steps/{NNNN}_{message}.py`) are numbered from `0001`. Each one:
  1. **loads** a CSV into a polars DataFrame (every value as a string, empty cells as null),
  2. **transforms** it with that model's `upgrade` or `downgrade` function,
  3. **saves** it back, keeping the file's original line endings (`\r\n` or `\n`).
- In each step file, every model is listed in `UPGRADES` and `DOWNGRADES`, mapped to `None`. **`None` means "nothing to do for this model in this step"**: the CSV isn't loaded or saved, and the tool moves straight on to the next step.
- **The stamp file** `{tables_dir}/csv_versions.json` records each CSV's model and the step it's at, with paths relative to `{tables_dir}`:
  ```json
  {
    "code_list/north.csv": {"model": "CodeList", "step": "0003"}
  }
  ```
  `upgrade` and `downgrade` start every CSV from its own stamped step, and update the stamp after each step, so a failure leaves the CSV and its stamp at the last good step.
- **A step** can be given as `0003` or `3`, `head` (the latest step), or `base` (before the first step).

### Options

| Option | Effect |
|---|---|
| `--models {module:Base}` | **Required.** The declarative Base. Gives the model names and the steps folder. |
| `--steps {dir}` | Use a different steps folder (default `migrations/{module}/csv_steps`). |

### Commands

| Command | Effect |
|---|---|
| `generate -m "{message}"` | Writes the next step, `csv_steps/{NNNN}_{message}.py`, from `csv_step_template.py.tmpl`. It contains a template `upgrade_template` / `downgrade_template` pair, and every model mapped to `None`. Fill it in (see below) and check it before committing. |
| `init {tables_dir}` | Finds every CSV under `{tables_dir}` (subfolders included) and stamps it at `head` in `{tables_dir}/csv_versions.json`. Each CSV's model comes from its **folder name**, then its **file name**, matched against model class and table names (case and `_` ignored): `tables/code_list/x.csv` becomes `CodeList`. CSVs it can't match are listed and left unstamped. Existing stamps for other files are kept. |
| `init {tables_dir} --step {step}` | Same, but stamps them at `{step}` (e.g. when the CSVs match an older step). |
| `stamp {tables_dir} {Model} {csv} [{csv} ...]` | Stamps the given CSVs as `{Model}` at `head` (e.g. files `init` couldn't match, or new CSVs added later). `{Model}` is the class name, e.g. `CodeList`. |
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

Without `{out.csv}` the CSV is changed in place.

### Filling in a step file

`generate` writes this (models abbreviated):

```python
def upgrade_template(df: pl.DataFrame) -> pl.DataFrame:
    return df


def downgrade_template(df: pl.DataFrame) -> pl.DataFrame:
    return df


# None: nothing to do for that model in this step.
UPGRADES = {
    "CodeList": None,
    "Facility": None,
    ...
}

DOWNGRADES = {
    "CodeList": None,
    "Facility": None,
    ...
}
```

For each model the step changes, copy the template pair, name it after the model and point that model's entries at it:

```python
def upgrade_code_list(df: pl.DataFrame) -> pl.DataFrame:
    return df.with_columns(pl.lit(None, pl.String).alias("description"))


def downgrade_code_list(df: pl.DataFrame) -> pl.DataFrame:
    return df.drop("description")


UPGRADES = {
    "CodeList": upgrade_code_list,
    "Facility": None,
    ...
}

DOWNGRADES = {
    "CodeList": downgrade_code_list,
    "Facility": None,
    ...
}
```

You can delete `upgrade_template` / `downgrade_template` once you're done, or leave them. Nothing uses them.

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

### First-time setup

Run once, while the database migrations and the CSVs both match the current models.

```
# 1. Database: the initial revision (creates migrations/{module}/ from alembic_template)
poetry run python migration_tool/migrate.py revision --autogenerate -m "initial" --models {module:Base}
poetry run python migration_tool/migrate.py upgrade head --models {module:Base}      # check it applies

# 2. CSVs: a baseline step (nothing to fill in), then stamp every CSV at it
poetry run python migration_tool/csv_migrate.py generate -m "baseline" --models {module:Base}
poetry run python migration_tool/csv_migrate.py init {tables_dir} --models {module:Base}
poetry run python migration_tool/csv_migrate.py current {tables_dir} --models {module:Base}   # check the models it picked

# 3. Commit migrations/{module}/ and {tables_dir}/csv_versions.json
```

### Adding a column

For example, adding `description` to `CodeList`.

```
# 1. Add the column to the model in ukrdc_sqla.

# 2. Database revision, then test it both ways
poetry run python migration_tool/migrate.py revision --autogenerate -m "add code_list.description" --models {module:Base}
#    -> review migrations/{module}/versions/{rev}_add_code_list_description.py
poetry run python migration_tool/migrate.py upgrade head --models {module:Base}
poetry run python migration_tool/migrate.py downgrade base --models {module:Base}
poetry run python migration_tool/migrate.py check --models {module:Base}             # models and migrations agree

# 3. CSV step
poetry run python migration_tool/csv_migrate.py generate -m "add code_list.description" --models {module:Base}
#    -> in csv_steps/{NNNN}_add_code_list_description.py, add upgrade_code_list (add the column)
#       and downgrade_code_list (drop it), and map "CodeList" to them in UPGRADES / DOWNGRADES

# 4. Migrate the CSVs and check the result
poetry run python migration_tool/csv_migrate.py upgrade {tables_dir} head --models {module:Base}
poetry run python migration_tool/csv_migrate.py current {tables_dir} --models {module:Base}
git diff {tables_dir}                                                                # only the new column should change

# 5. Commit the model, the revision, the step file, the CSVs and csv_versions.json together
```

### Renaming a column

The same as adding one, with two differences:

- **Database revision:** autogenerate writes a rename as `drop_column` + `add_column`, which loses the data. Replace the pair with `op.alter_column("{table}", "{old}", new_column_name="{new}")` in `upgrade()`, and the reverse in `downgrade()`.
- **CSV step:** `df.rename({"{old}": "{new}"})` in `upgrade_{model}`, and the reverse in `downgrade_{model}`.

### Changing several models in one migration

One `generate` per migration. Fill in a function pair for every model it touches, and leave the rest as `None`. `upgrade` runs each CSV through its own model's function and skips the others.

### New CSVs added later

Stamp them at the step whose columns they already match (usually `head`):

```
poetry run python migration_tool/csv_migrate.py stamp {tables_dir} {Model} {tables_dir}/{folder}/{new.csv} --models {module:Base}
```

Or run `init {tables_dir}` again. Be careful: that re-stamps **every** CSV it finds at `head`, so only do it when they're all up to date.

PowerShell doesn't expand `*.csv` for Python, so list the files or use `init`.

### Undoing a migration

```
# CSVs back to the step before the latest one (e.g. 0003 -> 0002)
poetry run python migration_tool/csv_migrate.py downgrade {tables_dir} {NNNN-1} --models {module:Base}

# then delete (or fix) the step file and regenerate if needed
```

For the database, delete the unapplied revision file, or `alembic -c migrations/{module}/alembic.ini downgrade -1` against a real database.

### When a CSV fails to migrate

`upgrade` / `downgrade` print `FAILED {csv} ({Model}) at step {NNNN} ...` and carry on with the other CSVs. The failed CSV and its stamp stay at the last step that worked. Fix the step file (or the CSV), then run the same `upgrade` again: it picks up from the stamped step.

### Two branches both added step {NNNN}

`csv_migrate.py` stops with "Two steps numbered {NNNN}". Rename the newer file to the next free number and set its `step` / `previous` values. For the database, use `migrate.py merge -m "merge" {rev1} {rev2}`, or re-point `down_revision`.