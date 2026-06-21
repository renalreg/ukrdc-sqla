from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional
from typing import Callable, TypeVar

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


class ComputedField:
    """
    Descriptor for a session-aware computed property on a SQLAlchemy model.

    - Calls `fn(instance, session)` on first access
    - Caches in instance.__dict__ under `_cf_<name>`
    - Cache invalidated automatically on SQLAlchemy instance expiry

    Usage:
        class ResultItem(Base):
            prepost_derived = computed_field(calculate_prepost)
    """

    def __init__(self, fn: Callable[[Any, Session], T]) -> None:
        self._fn = fn
        self._attr: str = fn.__name__
        self.__doc__ = fn.__doc__

    def __set_name__(self, owner: type, name: str) -> None:
        self._attr = name

    def __get__(self, obj: Any, objtype: type | None = None) -> Any:
        if obj is None:
            return self  # class-level access

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

    # can add the below if needed to set for tests etc
    # def __set__(self, obj: Any, value: Any) -> None:
    #     # Allow explicit override (e.g. after write-back to stored column)
    #     obj.__dict__[f"_cf_{self._attr}"] = value


def computed_field(fn: Callable[[Any, Session], T]) -> ComputedField:
    """
    Factory/decorator for defining a session-aware computed field.

    Keeps model definitions clean — the calculation function is defined
    elsewhere and attached to the model in one line:

        class ResultItem(Base):
            prepost_derived = computed_field(calculate_prepost)

    Or used as a decorator on a standalone function:

        @computed_field
        def prepost_derived(self, session: Session) -> str:
            ...

    The function signature must be `(instance, session) -> value`.
    """
    return ComputedField(fn)
