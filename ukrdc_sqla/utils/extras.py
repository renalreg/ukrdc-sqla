from typing import Union, Iterable, List
from sqlalchemy import Column as Col
from sqlalchemy.orm import InstrumentedAttribute


def column_name(col: Union[Col, InstrumentedAttribute]) -> str:
    """
    Return the column name for a single SQLAlchemy InstrumentedAttribute.

    Example:
        column_name(User.id) -> "id"
    """
    return col.name


def column_names(
    *items: Union[
        Union[Col, InstrumentedAttribute], Iterable[Union[Col, InstrumentedAttribute]]
    ],
) -> List[str]:
    """
    Return a list of column names for one or more SQLAlchemy InstrumentedAttributes.

    Examples:
        column_names(User.id)-> ["id"]
        column_names(User.id, User.age)-> ["id", "age"]
        column_names([User.id, User.age])-> ["id", "age"]
    """
    names: List[str] = []

    for item in items:
        if isinstance(item, Iterable):
            for x in item:
                names.append(x.name)
        else:
            names.append(item.name)

    return names
