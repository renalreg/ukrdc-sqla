from dataclasses import dataclass
from typing import Any, Optional

from sqlalchemy.orm import MappedColumn, mapped_column as _mapped_column


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
