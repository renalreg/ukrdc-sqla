from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional
from typing import Callable, TypeVar

from sqlalchemy import event
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import MappedColumn, mapped_column as _mapped_column
from sqlalchemy.orm import Session, object_session


@dataclass
class ColumnInfo:
    label: str
    description: str


def mapped_column(
    *args: Any,
    sqla_info: Optional[ColumnInfo] = None,
    **kwargs: Any,
) -> MappedColumn:
    """A mapped_column wrapper that supports typed metadata via a ColumnInfo dataclass."""
    info = dict(kwargs.pop("info", {}) or {})
    if sqla_info:
        info["sqla_info"] = sqla_info
        if "comment" not in kwargs and sqla_info.description:
            kwargs["comment"] = sqla_info.description
    return _mapped_column(*args, info=info, **kwargs)


def get_column_info(model, column_name: str) -> Optional[ColumnInfo]:
    """Retrieve ColumnInfo for a given column by name."""
    col = model.__table__.c[column_name]
    return col.info.get("sqla_info")


T = TypeVar("T")
_UNSET = object()

# Registry of cache keys that should be cleared on SQLAlchemy instance expiry.
# Only session_computed_field registers here — computed_field does not.
# Maps class → set of _cf_ cache keys.
_SESSION_CF_KEYS: dict[type, set[str]] = {}


def _clear_session_computed_cache(target: Any, attrs: Any) -> None:
    """
    SQLAlchemy `expire` instance event handler.
    Clears only the session-dependent _cf_ keys, leaving pure-Python
    computed_field caches intact across expiry/commit cycles.
    """
    for key in _SESSION_CF_KEYS.get(type(target), ()):
        target.__dict__.pop(key, None)


class ComputedField:
    """
    Descriptor for a pure-Python computed property.

    - No session required — derives its value from already-loaded columns only
    - Cached permanently on the instance until it is garbage-collected
    - NOT cleared on session.expire() or session.commit() — use this for
      calculations that depend only on column values already in memory
      (e.g. arithmetic, string formatting, date calculations)

    Usage:
        class ResultItem(Base):
            value_plus_five: float = computed_field(calc_plus_five)
    """

    def __init__(self, fn: Callable[[Any], T]) -> None:
        self._fn = fn
        self._attr: str = fn.__name__
        self.__doc__ = fn.__doc__

    def __set_name__(self, owner: type, name: str) -> None:
        self._attr = name

    def __get__(self, obj: Any, objtype: type | None = None) -> Any:
        if obj is None:
            return self

        cache_key = f"_cf_{self._attr}"
        cached = obj.__dict__.get(cache_key, _UNSET)

        if cached is _UNSET:
            cached = self._fn(obj)
            obj.__dict__[cache_key] = cached

        return cached


class SessionComputedField:
    """
    Descriptor for a session-aware computed property.

    - Requires a live SQLAlchemy session — use for calculations that need
      to query related tables (joins, aggregates, lookups)
    - Cached on the instance, but cleared automatically whenever SQLAlchemy
      expires the instance (session.expire(), session.commit(),
      session.rollback()) so DB-derived values are never stale

    Usage:
        class ResultItem(Base):
            prepost_derived: str = session_computed_field(calculate_prepost)
    """

    def __init__(self, fn: Callable[[Any, Session], T]) -> None:
        self._fn = fn
        self._attr: str = fn.__name__
        self.__doc__ = fn.__doc__

    def __set_name__(self, owner: type, name: str) -> None:
        self._attr = name
        cache_key = f"_cf_{name}"

        # Register cache key and attach the expire listener once per class
        if owner not in _SESSION_CF_KEYS:
            _SESSION_CF_KEYS[owner] = set()
            event.listen(owner, "expire", _clear_session_computed_cache)

        _SESSION_CF_KEYS[owner].add(cache_key)

    def __get__(self, obj: Any, objtype: type | None = None) -> Any:
        if obj is None:
            return self

        cache_key = f"_cf_{self._attr}"
        cached = obj.__dict__.get(cache_key, _UNSET)

        if cached is _UNSET:
            session = object_session(obj)
            if session is None:
                raise RuntimeError(
                    f"Cannot compute '{self._attr}': "
                    f"{obj.__class__.__name__} instance is not bound to a session."
                )
            cached = self._fn(obj, session)
            obj.__dict__[cache_key] = cached

        return cached


def computed_field(fn: Callable[[Any], T]) -> ComputedField:
    """
    Pure-Python computed field. No session needed.
    The function signature must be `(instance,) -> value` — no session argument.
    Use for values derivable from already-loaded columns only:

        @computed_field
        def age(self) -> int:
            return (date.today() - self.birthtime.date()).days // 365
    """
    return ComputedField(fn)


def session_computed_field(fn: Callable[[Any, Session], T]) -> SessionComputedField:
    """
    Session-aware computed field. Cache is invalidated on session expiry.

    The function signature must be `(instance, session) -> value`.

    Use for values that require DB queries (joins, lookups, aggregates):

        @session_computed_field
        def prepost_derived(self, session: Session) -> str:
            ...
    """
    return SessionComputedField(fn)


def computed_hybrid(
    fn: Callable[[Any], T],
    expression: Callable[[Any], Any],
) -> hybrid_property:
    """
    Inline hybrid_property. allows a query sided function and a python sided function.

    fn - Python-side: receives the instance, returns the value.
                 Signature: (instance) -> value
    expression - SQL-side: receives the class, returns a SQL expression.
                 Signature: (cls) -> SQLAlchemy column expression

    Example Usage:
        # post_calculations.py
        def _value_plus_five_py(self):
            return float(self.resultvalue) + 5.0 if self.resultvalue else None

        def _value_plus_five_expr(cls):
            return cast(cls.resultvalue, Numeric) + 5.0

        # ukrdc.py
        class ResultItem(Base):
            value_plus_five = computed_hybrid(_value_plus_five_py, _value_plus_five_expr)

    Query usage:
        session.scalars(
            select(ResultItem)
            .where(ResultItem.value_plus_five > 20)
            .order_by(ResultItem.value_plus_five.desc())
        )
    """
    return hybrid_property(fn).expression(classmethod(expression))
