from sqlalchemy.orm import InspectionAttr
from sqlalchemy.ext.associationproxy import (
    AssociationProxy,
    ColumnAssociationProxyInstance,
)
from . import ukrdc_v1 as v1
from ukrdc_sqla import ukrdc as v2

COMP = {
    "PatientRecord": v1.PatientRecord,
    "Patient": v1.Patient,
    "CauseOfDeath": v1.CauseOfDeath,
    "FamilyDoctor": v1.FamilyDoctor,
    "GPInfo": v1.GPInfo,
    "SocialHistory": v1.SocialHistory,
    "FamilyHistory": v1.FamilyHistory,
    "Observation": v1.Observation,
    "OptOut": v1.OptOut,
    "Allergy": v1.Allergy,
    "Diagnosis": v1.Diagnosis,
    "RenalDiagnosis": v1.RenalDiagnosis,
    "DialysisSession": v1.DialysisSession,
    "Transplant": v1.Transplant,
    "Procedure": v1.Procedure,
    "Encounter": v1.Encounter,
    "ProgramMembership": v1.ProgramMembership,
    "ClinicalRelationship": v1.ClinicalRelationship,
    "Name": v1.Name,
    "PatientNumber": v1.PatientNumber,
    "Address": v1.Address,
    "ContactDetail": v1.ContactDetail,
    "Medication": v1.Medication,
    "Survey": v1.Survey,
    "Question": v1.Question,
    "Score": v1.Score,
    "Level": v1.Level,
    "Document": v1.Document,
    "LabOrder": v1.LabOrder,
    "ResultItem": v1.ResultItem,
    "PVData": v1.PVData,
    "PVDelete": v1.PVDelete,
    "Treatment": v1.Treatment,
    "Code": v1.Code,
    "CodeExclusion": v1.CodeExclusion,
    "CodeMap": v1.CodeMap,
    "Facility": v1.Facility,
    "RRCodes": v1.RRCodes,
    "Locations": v1.Locations,
    "RRDataDefinition": v1.RRDataDefinition,
    "ModalityCodes": v1.ModalityCodes,
}


def _field_keys(obj):
    return {k for k in obj.__dict__.keys() if not k.startswith("_")}


def test_v1_compat_patientrecord():
    for name, v1_cls in COMP.items():
        print(name)
        v2_cls = getattr(v2, name)
        assert v2_cls
        for k in _field_keys(v1_cls):
            if k == "feild_name":
                assert hasattr(v2_cls, "field_name"), f"{name}.field_name not found in v2"
            else:
                assert hasattr(v2_cls, k), f"{name}.{k} not found in v2"

                assert isinstance(
                    getattr(v2_cls, k),
                    (
                        InspectionAttr,
                        AssociationProxy,
                        ColumnAssociationProxyInstance,
                        property,
                    ),
                ), f"{name}.{k} is not a valid attribute"
