from collections.abc import Iterable

from sqlalchemy import Column as Col
from sqlalchemy import MetaData
from sqlalchemy.orm import InstrumentedAttribute

from ukrdc_sqla.utils.structure import ORM_ONLY


def column_name(col: Col | InstrumentedAttribute) -> str:
    """
    Return the column name for a single SQLAlchemy InstrumentedAttribute.

    Example:
        column_name(User.id) -> "id"
    """
    return col.name


def column_names(
    *items: Col | InstrumentedAttribute | Iterable[Col | InstrumentedAttribute],
) -> list[str]:
    """
    Return a list of column names for one or more SQLAlchemy InstrumentedAttributes.

    Examples:
        column_names(User.id)-> ["id"]
        column_names(User.id, User.age)-> ["id", "age"]
        column_names([User.id, User.age])-> ["id", "age"]
    """
    names: list[str] = []

    for item in items:
        if isinstance(item, Iterable):
            for x in item:
                names.append(x.name)
        else:
            names.append(item.name)

    return names


def db_metadata(metadata: MetaData) -> MetaData:
    """A copy of METADATA without the ORM_ONLY foreign keys, for create_all."""
    copy = MetaData(
        schema=metadata.schema, naming_convention=metadata.naming_convention
    )
    for table in metadata.sorted_tables:
        t = table.to_metadata(copy)
        for fkc in list(t.foreign_key_constraints):
            if any(fk.info.get(ORM_ONLY) for fk in fkc.elements):
                t.constraints.discard(fkc)
                for fk in fkc.elements:
                    fk.parent.foreign_keys.discard(fk)
    return copy
