"""Shared helpers for CSV step files."""

from __future__ import annotations

import json
from typing import Iterable

import polars as pl

# How booleans are written back to CSV (Postgres CSV exports use t/f).
PG_TRUE, PG_FALSE = "t", "f"
TRUTHY = ["t", "true", "1", "y", "yes"]


# ----------------------------------------------------------------------------- booleans


def is_true(col: str) -> pl.Expr:
    """A CSV boolean column as a real boolean: t/true/1/y/yes, any case; blank -> False."""
    return pl.col(col).fill_null("").str.strip_chars().str.to_lowercase().is_in(TRUTHY)


def pg_bool(condition: pl.Expr) -> pl.Expr:
    """A boolean expression as the CSV's t/f text."""
    return pl.when(condition).then(pl.lit(PG_TRUE)).otherwise(pl.lit(PG_FALSE))


# ----------------------------------------------------------------------------- Postgres arrays


def parse_array(value: str | None) -> list[str]:
    """A Postgres array literal ('{A,"B C"}'), or plain 'A,B', or blank -> ['A', 'B C']."""
    s = (value or "").strip()
    if s.startswith("{") and s.endswith("}"):
        s = s[1:-1]
    if not s.strip():
        return []
    out: list[str] = []
    cur: list[str] = []
    quoted = was_quoted = False
    i = 0

    def finish() -> None:
        item = "".join(cur)
        if not was_quoted:
            item = item.strip()
            if item == "" or item.upper() == "NULL":
                return
        out.append(item)

    while i < len(s):
        c = s[i]
        if quoted:
            if c == "\\" and i + 1 < len(s):
                i += 1
                cur.append(s[i])
            elif c == '"':
                quoted = False
            else:
                cur.append(c)
        elif c == '"':
            quoted = was_quoted = True
        elif c == ",":
            finish()
            cur, was_quoted = [], False
        else:
            cur.append(c)
        i += 1
    finish()
    return out


def to_array(values: Iterable[str]) -> str:
    """['A', 'B C'] -> '{A,"B C"}', quoting values a Postgres array literal needs quoted."""

    def q(v: str) -> str:
        if v == "" or v.upper() == "NULL" or any(c in v for c in ',{}"\\ '):
            return '"' + v.replace("\\", "\\\\").replace('"', '\\"') + '"'
        return v

    return "{" + ",".join(q(v) for v in values) + "}"


def array_col(col: str) -> pl.Expr:
    """A Postgres array column as a polars list of strings (blank -> [])."""
    return (
        pl.col(col)
        .fill_null("")
        .map_elements(parse_array, return_dtype=pl.List(pl.String))
    )


def flags_to_array(flags: dict[str, str]) -> pl.Expr:
    """{value: boolean column} -> an array literal of the values whose column is true.

    flags_to_array({"UKRDC": "ukrdcoutpkb", "PV": "pvoutpkb"}) -> {UKRDC,PV}, {PV}, {}...
    """
    return pl.concat_str(
        pl.lit("{"),
        pl.concat_str(
            *(
                pl.when(is_true(col)).then(pl.lit(value))
                for value, col in flags.items()
            ),
            separator=",",
            ignore_nulls=True,
        ),
        pl.lit("}"),
    )


def array_to_flags(col: str, flags: dict[str, str]) -> list[pl.Expr]:
    """The reverse of flags_to_array: one t/f column per value, true if it's in the array."""
    values = array_col(col)
    return [
        pg_bool(values.list.contains(value)).alias(name)
        for value, name in flags.items()
    ]


# ----------------------------------------------------------------------------- JSON


def parse_json(value: str | None, default=None):
    """A JSON cell; blank -> default ({} if not given)."""
    if value is None or not value.strip():
        return {} if default is None else default
    return json.loads(value)


def to_json(value) -> str:
    return json.dumps(value)


# ----------------------------------------------------------------------------- lists


def unique(values: Iterable[str]) -> list[str]:
    """Drop duplicates, keep the first occurrence's order."""
    return list(dict.fromkeys(values))
