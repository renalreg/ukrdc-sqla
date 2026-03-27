import typing
import pytest
from sqlalchemy.orm import SynonymProperty, ColumnProperty, Synonym
from sqlalchemy.orm.relationships import _RelationshipDeclared

from ukrdc_sqla import ukrdc


def _get_models(module):
    return [
        obj
        for name, obj in vars(module).items()
        if isinstance(obj, type) and hasattr(obj, "__tablename__")
    ]


def _get_type_hints(cls):
    try:
        return typing.get_type_hints(cls, include_extras=True)
    except Exception:
        return getattr(cls, "__annotations__", {})


def test_synonym_type_hints_match():
    errors = []
    for model in _get_models(ukrdc):
        type_hints = _get_type_hints(model)

        for attr_name, descriptor in model.__mapper__.all_orm_descriptors.items():
            prop = getattr(descriptor, "original_property", None)
            if not isinstance(prop, Synonym):
                continue

            target_name = prop.name

            if attr_name not in type_hints:
                errors.append(
                    f"{model.__name__}.{attr_name} -> {target_name} (missing type hint)"
                )
                continue

            if target_name not in type_hints:
                errors.append(
                    f"{model.__name__}.{attr_name} -> {target_name} (target missing type hint)"
                )
                continue

            synonym_type = type_hints[attr_name]
            target_type = type_hints[target_name]

            if synonym_type != target_type:
                errors.append(f"{model.__name__}.{attr_name} -> {target_name}")

    assert not errors, "Synonym type hint mismatches:\n  " + "\n  ".join(errors)
