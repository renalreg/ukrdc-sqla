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

## Developer notes

### Publish updates

- Iterate the version number (`poetry version major/minor/patch`)
- Push to GitHub repo
- Create a GitHub release
  - GitHub Actions will automatically publish the release to PyPI
