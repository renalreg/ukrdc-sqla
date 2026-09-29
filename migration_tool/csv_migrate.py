"""Migrate CSV data with polars, one step file per migration, per model."""

from __future__ import annotations

import functools
import json
import os
import importlib
import importlib.util
import re
import sys
from pathlib import Path
from string import Template
from types import ModuleType, SimpleNamespace

import click

STEP_FILE = re.compile(r"^(\d{4})_\w*\.py$")

STEP_TEMPLATE = Path(__file__).resolve().parent / "csv_step_template.py.tmpl"


# ----------------------------------------------------------------------------- models

def load_models(target: str) -> dict[str, str]:
    """{model class name: table name} for the declarative Base named by --models."""
    module_name, _, attr = target.partition(":")
    for path in (Path.cwd() / "src", Path.cwd()):
        if str(path) not in sys.path:
            sys.path.insert(0, str(path))
    try:
        base = getattr(importlib.import_module(module_name), attr or "Base")
    except (ImportError, AttributeError) as e:
        raise click.ClickException(f"Can't load --models {target}: {e}") from None
    mappers = getattr(getattr(base, "registry", None), "mappers", None)
    if not mappers:
        raise click.ClickException(f"{target} has no models: point --models at a declarative Base "
                                   "in a module that imports all the models.")
    return dict(sorted((m.class_.__name__, m.local_table.name) for m in mappers))


def guess_model(path: Path, models: dict[str, str]) -> str | None:
    """The model a CSV belongs to, from its folder or file name (class or table name)."""
    def norm(name: str) -> str:
        return re.sub(r"[\W_]+", "", name).lower()
    lookup = {}
    for cls, table in models.items():
        lookup.setdefault(norm(cls), cls)
        lookup.setdefault(norm(table), cls)
    for name in (path.parent.name, path.stem):
        if norm(name) in lookup:
            return lookup[norm(name)]
    return None


# ----------------------------------------------------------------------------- steps

def list_steps(folder: Path) -> list[tuple[str, Path]]:
    """[(step, file)], oldest first."""
    steps: dict[str, Path] = {}
    for path in sorted(folder.glob("*.py")) if folder.exists() else []:
        match = STEP_FILE.match(path.name)
        if match:
            if match[1] in steps:
                raise click.ClickException(f"Two steps numbered {match[1]}: {steps[match[1]].name} "
                                           f"and {path.name}. Renumber the newer one.")
            steps[match[1]] = path
    return sorted(steps.items())


def resolve(steps: list[tuple[str, Path]], step: str) -> int:
    """The index of a step: a number, head, or base (-1, before the first step)."""
    if step == "base":
        return -1
    if not steps:
        raise click.ClickException("No steps yet: run generate first.")
    if step == "head":
        return len(steps) - 1
    for i, (num, _) in enumerate(steps):
        if num == step.zfill(4):
            return i
    raise click.ClickException(f"No step {step}.")


def step_at(steps: list[tuple[str, Path]], index: int) -> str:
    return steps[index][0] if index >= 0 else "base"


def load_step(path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(f"csv_step_{path.stem}", path)
    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
    except Exception as e:
        raise click.ClickException(f"Can't load {path}: {type(e).__name__}: {e}") from None
    if not callable(getattr(module, "run", None)):
        raise click.ClickException(f"{path} has no run(direction, model, source, dest) function.")
    return module


# ----------------------------------------------------------------------------- stamp file

def stamp_key(path: Path, stamp_file: Path) -> str:
    """How a CSV is recorded: relative to the stamp file's folder where possible, with /."""
    try:
        return Path(os.path.relpath(path.resolve(), stamp_file.resolve().parent)).as_posix()
    except ValueError:  # another drive
        return path.resolve().as_posix()


def csv_path(key: str, stamp_file: Path) -> Path:
    return stamp_file.resolve().parent / key  # an absolute key stays absolute


def load_stamps(path: Path) -> dict[str, dict]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def save_stamps(path: Path, stamps: dict[str, dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(dict(sorted(stamps.items())), indent=2) + "\n", encoding="utf-8")


# ----------------------------------------------------------------------------- migrating

def line_ending(path: Path) -> bytes:
    with open(path, "rb") as f:
        return b"\r\n" if b"\r\n" in f.read(65536) else b"\n"


def keep_line_ending(path: Path, ending: bytes) -> None:
    """Rewrite the CSV with ENDING if a step saved it with the other one."""
    if line_ending(path) != ending:
        data = path.read_bytes().replace(b"\r\n", b"\n")
        path.write_bytes(data.replace(b"\n", ending) if ending == b"\r\n" else data)


def migrate(obj, direction: str, target: str, only_models: tuple, only_csvs: tuple) -> None:
    """Move every stamped CSV (or those picked) to TARGET, in place, one step at a time."""
    steps = list_steps(obj.steps)
    goal = resolve(steps, target)
    stamps = load_stamps(obj.stamp_file)
    if not stamps:
        raise click.ClickException(f"No CSVs stamped in {obj.stamp_file}: run init {obj.tables_dir} first.")
    picked = {stamp_key(Path(p), obj.stamp_file) for p in only_csvs}
    unknown = picked - stamps.keys()
    if unknown:
        raise click.ClickException(f"Not stamped: {', '.join(sorted(unknown))}")
    keys = [k for k, e in stamps.items()
            if (not picked or k in picked) and (not only_models or e["model"] in only_models)]
    modules: dict[int, ModuleType] = {}
    failed = moved = 0
    for key in keys:
        entry = stamps[key]
        model, path = entry["model"], csv_path(key, obj.stamp_file)
        try:
            start = resolve(steps, entry["step"])
        except click.ClickException as e:
            click.secho(f"FAILED {key}: stamped at {entry['step']}: {e.format_message()}", fg="red")
            failed += 1
            continue
        if direction == "upgrade":
            chain = [(i, i) for i in range(start + 1, goal + 1)]      # (step run, index after)
        else:
            chain = [(i, i - 1) for i in range(start, goal, -1)]
        if not chain:
            continue
        if not path.exists():
            click.secho(f"FAILED {key}: file not found", fg="red")
            failed += 1
            continue
        for i, _ in chain:
            modules.setdefault(i, load_step(steps[i][1]))
        maps = direction.upper() + "S"
        if not any(model in getattr(modules[i], maps, {}) for i, _ in chain):
            click.secho(f"FAILED {key}: {model} isn't in {maps} in any step it needs: "
                        "check the model name in the stamp file.", fg="red")
            failed += 1
            continue
        before, ran, error = entry["step"], 0, None
        ending = line_ending(path)
        for i, after in chain:
            try:
                if modules[i].run(direction, model, path):
                    ran += 1
                    keep_line_ending(path, ending)
            except Exception as e:
                error = f"step {steps[i][0]} {direction}: {type(e).__name__}: " \
                        f"{(str(e).strip().splitlines() or [''])[0]}"
                break
            entry["step"] = step_at(steps, after)
            save_stamps(obj.stamp_file, stamps)
        if entry["step"] != before:
            moved += 1
            click.echo(f"{key} ({model}): {before} -> {entry['step']} "
                       f"({ran} run, {len(chain) - ran - bool(error)} skipped)")
        if error:
            click.secho(f"FAILED {key} ({model}) at {error}; stamped at {entry['step']}", fg="red")
            failed += 1
    if failed:
        raise click.ClickException(f"{failed} CSV(s) failed and stopped at their last good step "
                                   f"(see {obj.stamp_file}).")
    click.echo(f"Done: {moved} CSV(s) migrated; everything picked is at {step_at(steps, goal)}.")


# ----------------------------------------------------------------------------- CLI

MODELS_HELP = "module:attr of the declarative Base, e.g. ukrdc_sqla.ukrdc:Base (required)."
STEPS_HELP = "Steps folder. Default: migrations/<module>/csv_steps."
STAMP_FILE = "csv_versions.json"  # kept in the tables folder; CSV paths in it are relative to it
TABLES = click.argument("tables_dir", metavar="TABLES_DIR",
                        type=click.Path(file_okay=False, exists=True, path_type=Path))


@click.group(context_settings={"max_content_width": 100})
@click.option("--models", help=MODELS_HELP)
@click.option("--steps", "steps_dir", type=click.Path(file_okay=False, path_type=Path), help=STEPS_HELP)
@click.pass_context
def cli(ctx, models, steps_dir):
    """Migrate CSV data with polars, one step file per migration, per model."""
    ctx.obj = SimpleNamespace(models=models, steps_dir=steps_dir)


def settings(f):
    """--models and --steps after the command too; they override any before it. With a
    TABLES_DIR argument, the stamp file is TABLES_DIR/csv_versions.json."""
    @click.option("--models", help=MODELS_HELP)
    @click.option("--steps", "steps_dir", type=click.Path(file_okay=False, path_type=Path),
                  help=STEPS_HELP)
    @click.pass_obj
    @functools.wraps(f)
    def wrapper(group, models, steps_dir, **kwargs):
        models = models or group.models
        if not models:
            raise click.UsageError("Missing option '--models', e.g. --models ukrdc_sqla.ukrdc:Base")
        folder = Path("migrations") / models.partition(":")[0].rsplit(".", 1)[-1]
        tables_dir = kwargs.pop("tables_dir", None)
        return f(SimpleNamespace(models=models,
                                 steps=steps_dir or group.steps_dir or folder / "csv_steps",
                                 tables_dir=tables_dir,
                                 stamp_file=tables_dir / STAMP_FILE if tables_dir else None),
                 **kwargs)
    return wrapper


@cli.command()
@click.option("-m", "--message", required=True, help="What the step does.")
@settings
def generate(obj, message):
    """Write the next step: every model mapped to None, and a template upgrade/downgrade pair."""
    names = list(load_models(obj.models))
    steps = list_steps(obj.steps)
    previous = steps[-1][0] if steps else None
    step = f"{int(previous or 0) + 1:04d}"
    slug = re.sub(r"\W+", "_", message.lower()).strip("_")[:40] or "step"
    path = obj.steps / f"{step}_{slug}.py"
    if not STEP_TEMPLATE.exists():
        raise click.ClickException(f"{STEP_TEMPLATE} is missing: keep it next to csv_migrate.py.")
    source = Template(STEP_TEMPLATE.read_text(encoding="utf-8")).substitute(
        message=message, step=step, step_q=json.dumps(step),
        previous_q=json.dumps(previous) if previous else "None",
        after=f", after {previous}" if previous else "",
        upgrades="".join(f"    {json.dumps(n)}: None,\n" for n in names),
        downgrades="".join(f"    {json.dumps(n)}: None,\n" for n in names))
    obj.steps.mkdir(parents=True, exist_ok=True)
    path.write_text(source, encoding="utf-8")
    click.echo(f"Wrote {path} ({len(names)} models)")
    click.secho(f"Fill in {path} (copy the template functions for each model that changes) and "
                "check it before committing it.", fg="yellow")


@cli.command()
@TABLES
@click.option("--step", default="head", show_default=True, help="The step the CSVs are at.")
@settings
def init(obj, step):
    """Stamp every CSV under TABLES_DIR at the latest step (or --step), in
    TABLES_DIR/csv_versions.json. The model comes from each CSV's folder or file name (model
    class or table name)."""
    models = load_models(obj.models)
    steps = list_steps(obj.steps)
    num = step_at(steps, resolve(steps, step))
    stamps, unmatched = load_stamps(obj.stamp_file), []
    for path in sorted(obj.tables_dir.rglob("*.csv")):
        model = guess_model(path, models)
        if model is None:
            unmatched.append(path)
            continue
        key = stamp_key(path, obj.stamp_file)
        stamps[key] = {"model": model, "step": num}
        click.echo(f"{key}: {model} at {num}")
    save_stamps(obj.stamp_file, stamps)
    click.echo(f"Wrote {obj.stamp_file}")
    for path in unmatched:
        click.secho(f"not stamped {path}: no model named like it (use: stamp {obj.tables_dir} MODEL {path})", fg="yellow")


@cli.command()
@TABLES
@click.argument("model")
@click.argument("csvs", nargs=-1, required=True, metavar="CSV...",
                type=click.Path(dir_okay=False, exists=True, path_type=Path))
@click.option("--step", default="head", show_default=True, help="The step the CSVs are at.")
@settings
def stamp(obj, model, csvs, step):
    """Record the model and step of CSVs in TABLES_DIR/csv_versions.json."""
    if model not in load_models(obj.models):
        raise click.ClickException(f"Not a model: {model}")
    steps = list_steps(obj.steps)
    num = step_at(steps, resolve(steps, step))
    stamps = load_stamps(obj.stamp_file)
    for path in csvs:
        key = stamp_key(path, obj.stamp_file)
        stamps[key] = {"model": model, "step": num}
        click.echo(f"{key}: {model} at {num}")
    save_stamps(obj.stamp_file, stamps)


@cli.command()
@TABLES
@click.argument("target", default="head")
@click.option("--model", "only_models", multiple=True, help="Only CSVs of this model (repeatable).")
@click.option("--csv", "only_csvs", multiple=True, help="Only this stamped CSV (repeatable).")
@settings
def upgrade(obj, target, only_models, only_csvs):
    """Upgrade the CSVs stamped in TABLES_DIR, in place, from their stamped step to TARGET
    (default head)."""
    migrate(obj, "upgrade", target, only_models, only_csvs)


@cli.command()
@TABLES
@click.argument("target")
@click.option("--model", "only_models", multiple=True, help="Only CSVs of this model (repeatable).")
@click.option("--csv", "only_csvs", multiple=True, help="Only this stamped CSV (repeatable).")
@settings
def downgrade(obj, target, only_models, only_csvs):
    """Downgrade the CSVs stamped in TABLES_DIR, in place, from their stamped step back to
    TARGET (or base)."""
    migrate(obj, "downgrade", target, only_models, only_csvs)


@cli.command()
@TABLES
@settings
def current(obj):
    """The CSVs stamped in TABLES_DIR, their models and steps."""
    steps = list_steps(obj.steps)
    head = step_at(steps, len(steps) - 1)
    for key, entry in load_stamps(obj.stamp_file).items():
        note = "" if entry["step"] == head else f"  (head is {head})"
        click.echo(f"{key}: {entry['model']} at {entry['step']}{note}")


@cli.command()
@settings
def history(obj):
    """List the steps, oldest first."""
    for num, path in list_steps(obj.steps):
        doc = (load_step(path).__doc__ or "").strip().splitlines()
        click.echo(f"{num}  {doc[0] if doc else path.stem}")


if __name__ == "__main__":
    cli()