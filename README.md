# UKRDC-SQLA

SQLAlchemy models for the UKRDC and related databases.

## Installation

`pip install ukrdc-sqla`

## Example Usage

```python
from datetime import datetime

from ukrdc_sqla.ukrdc import LabOrder, PatientNumber, PatientRecord, ResultItem

def commit_extra_resultitem(session):
    patient_record = PatientRecord(
        pid="PYTEST01:LABORDERS:00000000L",
        sendingfacility="PATIENT_RECORD_SENDING_FACILITY_1",
        sendingextract="PV",
        localpatientid="00000000L",
        ukrdcid="000000001",
        repository_update_date=datetime(2020, 3, 16),
        repository_creation_date=datetime(2020, 3, 16),
    )
    patient_number = PatientNumber(
        id=2,
        pid="PYTEST01:LABORDERS:00000000L",
        patientid="111111111",
        organization="NHS",
        numbertype="NI",
    )
    laborder = LabOrder(
        id="LABORDER_TEST2_1",
        pid="PYTEST01:LABORDERS:00000000L",
        external_id="EXTERNAL_ID_TEST2_1",
        order_category="ORDER_CATEGORY_TEST2_1",
        specimen_collected_time=datetime(2020, 3, 16),
    )
    resultitem = ResultItem(
        id="RESULTITEM_TEST2_1",
        order_id="LABORDER_TEST2_1",
        service_id_std="SERVICE_ID_STD_TEST2_1",
        service_id="SERVICE_ID_TEST2_1",
        service_id_description="SERVICE_ID_DESCRIPTION_TEST2_1",
        value="VALUE_TEST2_1",
        value_units="VALUE_UNITS_TEST2_1",
        observation_time=datetime(2020, 3, 16),
    )

    session.add(patient_record)
    session.add(patient_number)
    session.add(laborder)
    session.add(resultitem)

    session.commit()
```

## Developer Notes

### Computed Fields

Three field types for deriving values on SQLAlchemy models. All are defined inline on the model and delegate their logic to functions in `post_calculations.py`.

#### `computed_field`
Pure Python. No session required. Cached permanently on the instance — survives `expire()` and `commit()`.

Use when the value is derivable from already-loaded columns only (arithmetic, date calculations, string formatting).

#### `session_computed_field`
Session-aware. Cache is cleared on `expire()` and `commit()` so DB-derived values are never stale.

Use when the calculation requires a DB query — joins, lookups against reference tables, aggregates over related rows.

#### `computed_hybrid`
Wraps `hybrid_property`. Not cached — recalculates on every access. The only type usable in queries (`WHERE`, `ORDER BY`, `filter()`).

Use when you need the value available at the query level, not just on loaded instances.

#### Quick Reference

| | `computed_field` | `session_computed_field` | `computed_hybrid` |
|---|---|---|---|
| Requires session | No | Yes | No |
| Cached | Yes — permanent | Yes — cleared on expiry | No |
| Usable in queries | No | No | Yes |
| Use for | Arithmetic, dates | Joins, DB lookups | Query-level filtering |

#### Example

```python
# post_calculations.py

def _calc_age(self) -> Optional[int]:
    if self.birthtime is None:
        return None
    today = date.today()
    born = self.birthtime.date()
    return today.year - born.year - ((today.month, today.day) < (born.month, born.day))

def _calc_prepost(self, session: Session) -> str:
    # looks up sibling results on the same date to determine PRE/POST dialysis
    ...

def _numeric_value_py(self) -> Optional[float]:
    return float(self.resultvalue) if self.resultvalue else None

def _numeric_value_expr(cls):
    return cast(cls.resultvalue, Numeric)
```

```python
# ukrdc.py

class ResultItem(Base):
    ...

    # No DB query needed — birthtime is already loaded
    age: int = computed_field(_calc_age)

    # Queries sibling rows — cache cleared on expire/commit
    prepost: str = session_computed_field(_calc_prepost)

    # Usable in WHERE/ORDER BY across a patient cohort
    numeric_value: float = computed_hybrid(_numeric_value_py, _numeric_value_expr)
```

```python
# usage

record = session.get(ResultItem, "R1")
print(record.age)      # 47  — from loaded columns, no query
print(record.prepost)  # "PRE" — queried DB, cached until next commit

# computed_hybrid can be used in queries — the other two cannot
high_results = session.scalars(
    select(ResultItem)
    .where(ResultItem.numeric_value > 10.0)
    .order_by(ResultItem.numeric_value.desc())
).all()
```

### Publish Updates

- Iterate the version number (`poetry version major/minor/patch`)
- Push to GitHub repo
- Create a GitHub release
  - GitHub Actions will automatically publish the release to PyPI