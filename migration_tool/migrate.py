"""Run any Alembic command against a throwaway Postgres (Docker, or a server on --db-url)."""

from __future__ import annotations

import configparser
import importlib
import importlib.util
import shutil
import subprocess
import sys
import time
import uuid
from contextlib import contextmanager
from pathlib import Path
from types import SimpleNamespace

import click
from alembic import command
from alembic.config import CommandLine, Config
from alembic.util import CommandError
from sqlalchemy import MetaData, create_engine
from sqlalchemy.engine import URL, make_url
from sqlalchemy.exc import DBAPIError, OperationalError
from sqlalchemy.pool import NullPool

TEMPLATE = Path(__file__).resolve().parent / "alembic_template"
TEMPLATE_FILES = ("alembic.ini", "env.py", "script.py.mako")
NEEDS_DB = {
    command.upgrade,
    command.downgrade,
    command.current,
    command.stamp,
    command.check,
}


# ----------------------------------------------------------------------------- Postgres


def pg_driver() -> str:
    for module in ("psycopg", "psycopg2"):
        if importlib.util.find_spec(module):
            return f"postgresql+{module}"
    raise click.ClickException(
        'No Postgres driver installed: pip install "psycopg[binary]"'
    )


def docker(*args: str, check: bool = True) -> str:
    try:
        res = subprocess.run(["docker", *args], capture_output=True, text=True)
    except FileNotFoundError:
        raise click.ClickException(
            "Docker isn't installed: install it, or pass --db-url."
        ) from None
    if check and res.returncode:
        raise click.ClickException(
            f"docker {args[0]} failed (is Docker running? or pass --db-url): "
            f"{res.stderr.strip()}"
        )
    return res.stdout.strip()


@contextmanager
def postgres_server(obj):
    """A Postgres server URL: --db-url, or a fresh Docker container removed afterwards."""
    if obj.db_url:
        url = make_url(obj.db_url)
        yield url.set(drivername=pg_driver()) if url.drivername == "postgresql" else url
        return
    name = f"migrate-{uuid.uuid4().hex[:8]}"
    click.echo(
        f"Starting a {obj.pg_image} container (the first time downloads the image)...",
        err=True,
    )
    docker(
        "run",
        "-d",
        "--rm",
        "--name",
        name,
        "-e",
        "POSTGRES_PASSWORD=migrate",
        "-p",
        "127.0.0.1::5432",
        obj.pg_image,
    )
    try:
        port = int(docker("port", name, "5432/tcp").splitlines()[0].rsplit(":", 1)[1])
        url = URL.create(
            pg_driver(), "postgres", "migrate", "127.0.0.1", port, "postgres"
        )
        engine, deadline = create_engine(url, poolclass=NullPool), time.monotonic() + 60
        while True:  # wait until it accepts connections
            try:
                with engine.connect():
                    break
            except OperationalError:
                if time.monotonic() > deadline:
                    raise click.ClickException(
                        "The Postgres container didn't start within 60s."
                    )
                time.sleep(0.5)
        yield url
    finally:
        docker("rm", "-f", "-v", name, check=False)


@contextmanager
def scratch_database(obj):
    """An engine for a throwaway database on the server, dropped afterwards."""
    with postgres_server(obj) as server:
        admin = create_engine(server, isolation_level="AUTOCOMMIT", poolclass=NullPool)
        name = f"migrate_scratch_{uuid.uuid4().hex[:8]}"
        try:
            with admin.connect() as conn:
                conn.exec_driver_sql(f'CREATE DATABASE "{name}"')
        except DBAPIError as e:
            raise click.ClickException(
                f"Couldn't create a database on {server.render_as_string()}: "
                f"{str(e.orig).strip()}"
            ) from None
        try:
            yield create_engine(server.set(database=name), poolclass=NullPool)
        finally:
            with admin.connect() as conn:
                conn.exec_driver_sql(f'DROP DATABASE IF EXISTS "{name}"')


# ----------------------------------------------------------------------------- migrations folder


def create_migrations_folder(obj) -> None:
    """The shared migrations folder from alembic_template (alembic.ini, env.py,
    script.py.mako), with no databases in it yet."""
    missing = [n for n in TEMPLATE_FILES if not (TEMPLATE / n).exists()]
    if missing:
        raise click.ClickException(
            f"{TEMPLATE} is missing {', '.join(missing)}: keep the "
            "alembic_template folder next to migrate.py."
        )
    obj.migrations.mkdir(parents=True, exist_ok=True)
    for name in TEMPLATE_FILES:
        if not (obj.migrations / name).exists():
            shutil.copy(TEMPLATE / name, obj.migrations / name)
    click.echo(f"Created {obj.migrations} from {TEMPLATE}.", err=True)


def has_section(ini: Path, section: str) -> bool:
    parser = configparser.ConfigParser(interpolation=None)
    parser.read(ini, encoding="utf-8")
    return parser.has_section(section)


def add_database(ini: Path, section: str) -> None:
    """A section for a new database in the shared alembic.ini, and its versions folder.
    Goes in before the logging sections, so the database sections stay together."""
    (ini.parent / section / "versions").mkdir(parents=True, exist_ok=True)
    block = f"[{section}]\nversion_locations = %(here)s/{section}/versions\n\n"
    text = ini.read_text(encoding="utf-8")
    at = next(
        (i for marker in ("# Logging", "[loggers]") if (i := text.find(marker)) >= 0),
        None,
    )
    if at is None:
        text = text.rstrip("\n") + "\n\n" + block
    else:
        text = text[:at] + block + text[at:]
    ini.write_text(text, encoding="utf-8")
    click.echo(
        f"Added [{section}] to {ini}, with its revisions in {ini.parent / section}"
        "/versions.",
        err=True,
    )


# ----------------------------------------------------------------------------- models


def load_metadata(target: str) -> MetaData:
    """The MetaData of the declarative Base (or MetaData) named by --models."""
    module_name, _, attr = target.partition(":")
    for path in (Path.cwd() / "src", Path.cwd()):
        if str(path) not in sys.path:
            sys.path.insert(0, str(path))
    try:
        base = getattr(importlib.import_module(module_name), attr or "Base")
    except (ImportError, AttributeError) as e:
        raise click.ClickException(f"Can't load --models {target}: {e}") from None
    metadata = base if isinstance(base, MetaData) else base.metadata
    if (
        not metadata.tables
    ):  # carrying on would generate a revision that drops every table
        raise click.ClickException(
            f"{target} has no tables: point --models at a module that "
            "imports all the models."
        )
    return metadata


# ----------------------------------------------------------------------------- check output


def describe_diffs(diffs) -> str:
    """`check` differences, one per line: the operation and what it applies to."""
    lines = []
    for diff in diffs:
        for op, *rest in diff if isinstance(diff, list) else [diff]:
            # schema / table / column / index etc., as names
            names = [
                x if isinstance(x, str) else getattr(x, "name", None) for x in rest[:3]
            ]
            lines.append(f"  {op}: {'.'.join(n for n in names if n)}")
    return "The models have changes that no migration covers:\n" + "\n".join(lines)


# ----------------------------------------------------------------------------- CLI


@click.command(
    context_settings={
        "max_content_width": 100,
        "ignore_unknown_options": True,
        "allow_interspersed_args": True,
    }
)
@click.option(
    "--models",
    required=True,
    help="module:attr of the declarative Base, e.g. ukrdc_sqla.ukrdc:Base.",
)
@click.option(
    "--migrations",
    type=click.Path(file_okay=False, path_type=Path),
    default=Path("migrations"),
    show_default=True,
    help="The shared migrations folder: alembic.ini, env.py and script.py.mako, and a "
    "<database>/versions folder for each database. The database is the --models module "
    "(e.g. ukrdc), or Alembic's -n.",
)
@click.option(
    "--db-url",
    help="Postgres server for the throwaway database. Default: a Docker container.",
)
@click.option(
    "--pg-image",
    default="postgres:16",
    show_default=True,
    help="Docker image for that container (match production).",
)
@click.option(
    "--at",
    "at",
    metavar="REVISION",
    help="Migrate the throwaway database to this revision before the command "
    "(`base` = empty). Default: base for upgrade, head otherwise.",
)
@click.argument("alembic_args", nargs=-1, type=click.UNPROCESSED)
def cli(models, migrations, db_url, pg_image, at, alembic_args):
    """Run an Alembic command (ALEMBIC_ARGS, e.g. `revision --autogenerate -m "..."`) against
    a throwaway Postgres."""
    module = models.partition(":")[0].rsplit(".", 1)[-1]
    obj = SimpleNamespace(
        models=models,
        migrations=migrations,
        db_url=db_url,
        pg_image=pg_image,
    )

    parser = CommandLine(prog="migrate.py [OPTIONS]").parser
    options = parser.parse_args(list(alembic_args))
    if not hasattr(options, "cmd"):
        parser.error("too few arguments")
    fn, positional, kwarg = options.cmd
    args = [getattr(options, k, None) for k in positional]
    kwargs = {k: getattr(options, k, None) for k in kwarg}

    def given(short: str, long: str) -> bool:
        return any(a in (short, long) or a.startswith(f"{long}=") for a in alembic_args)

    explicit_config = given("-c", "--config")
    ini = Path(options.config) if explicit_config else obj.migrations / "alembic.ini"
    # The database's section in the shared alembic.ini: -n if given, else the module.
    section = options.name if given("-n", "--name") else module
    if fn is command.revision and not explicit_config:
        if not ini.exists():
            create_migrations_folder(obj)
        if not has_section(ini, section):
            add_database(ini, section)
    if not ini.exists() and fn is not command.init:
        raise click.ClickException(
            f"No {ini} yet: run `migrate.py revision --autogenerate -m ...` "
            "to create the migrations folder."
        )
    if ini.exists() and fn is not command.init and not has_section(ini, section):
        raise click.ClickException(
            f"{ini} has no [{section}] section: run `migrate.py --models {models} "
            "revision --autogenerate -m ...` to add the database, or pick its "
            "section with -n."
        )
    cfg = Config(str(ini), ini_section=section, cmd_opts=options)

    autogenerate = fn is command.revision and kwargs.get("autogenerate")
    offline = bool(kwargs.get("sql"))
    if autogenerate or fn is command.check:
        cfg.attributes["target_metadata"] = load_metadata(models)
    if autogenerate:

        def process(_context, _revision, directives):
            if directives[0].upgrade_ops.is_empty():
                directives[:] = []  # nothing changed: no revision
                click.echo(
                    "No changes between the models and the migrations: no revision written."
                )

        kwargs["process_revision_directives"] = process

    needs_db = (fn in NEEDS_DB or autogenerate) and not offline
    at = at or ("base" if fn is command.upgrade else "head")
    try:
        if needs_db:
            with scratch_database(obj) as engine, engine.begin() as conn:
                cfg.set_main_option(
                    "sqlalchemy.url",
                    engine.url.render_as_string(hide_password=False).replace("%", "%%"),
                )
                cfg.attributes["connection"] = conn
                if at != "base":
                    try:
                        command.upgrade(cfg, at)
                    except (CommandError, DBAPIError) as e:
                        text = str(getattr(e, "orig", e)).strip()
                        raise click.ClickException(
                            f"Migrating the throwaway database to {at} "
                            f"(--at) failed: {text}"
                        ) from None
                    click.echo(f"(throwaway database migrated to {at})", err=True)
                result = fn(cfg, *args, **kwargs)
        else:
            if not cfg.get_main_option("sqlalchemy.url"):  # offline SQL needs a dialect
                cfg.set_main_option("sqlalchemy.url", f"{pg_driver()}://")
            result = fn(cfg, *args, **kwargs)
    except CommandError as e:
        diffs = getattr(e, "diffs", None)  # set by `check` when the models differ
        raise click.ClickException(describe_diffs(diffs) if diffs else str(e)) from None
    except DBAPIError as e:
        raise click.ClickException(str(e.orig).strip()) from None

    if fn is command.check:
        click.echo("The migrations match the models.")
    if fn is command.revision and result:
        for script in result if isinstance(result, list) else [result]:
            if script is not None:
                click.secho(f"Check {script.path} before committing it.", fg="yellow")


if __name__ == "__main__":
    cli()
