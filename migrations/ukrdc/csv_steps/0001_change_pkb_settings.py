"""change pkb settings

Step 0001.
"""

from __future__ import annotations

import sys
from pathlib import Path

import polars as pl

from ukrdc_sqla.utils.constants import StandardCodesType

sys.path.insert(0, str(Path(__file__).resolve().parent))
import csv_helpers as csv  # noqa: E402

step = "0001"
previous = None


def load(path) -> pl.DataFrame:
    return pl.read_csv(path, infer_schema=False)


def save(df: pl.DataFrame, path, line_terminator: str = "\n") -> None:
    df.write_csv(path, line_terminator=line_terminator)


def line_ending(path) -> str:
    with open(path, "rb") as f:
        return "\r\n" if b"\r\n" in f.read(65536) else "\n"


def upgrade_template(df: pl.DataFrame) -> pl.DataFrame:
    return df


def downgrade_template(df: pl.DataFrame) -> pl.DataFrame:
    return df


def upgrade_sendingextractmetadata(df: pl.DataFrame) -> pl.DataFrame:
    return df.with_columns(pl.lit(csv.PG_FALSE).alias("enable_pkb_export"))


def downgrade_sendingextractmetadata(df: pl.DataFrame) -> pl.DataFrame:
    return df.drop("enable_pkb_export")


# Extract name: (old on/off column, old extract-specific exclusions column)
PKB_EXTRACTS = {
    StandardCodesType.ukrdc: ("ukrdcoutpkb", "pkb_ukrdc_msg_exclusions"),
    StandardCodesType.pv: ("pvoutpkb", "pkb_pv_msg_exclusions"),
}
SHARED_EXCLUSIONS = "pkbmsgexclusions"
OLD_FLAGS = {name: flag for name, (flag, _) in PKB_EXTRACTS.items()}
OLD_EXCLUSIONS = [SHARED_EXCLUSIONS, *(col for _, col in PKB_EXTRACTS.values())]


def upgrade_facility(df: pl.DataFrame) -> pl.DataFrame:

    def _merge_exclusions(row: dict) -> str:
        """Old columns -> {"UKRDC": [shared + UKRDC's own], "PV": [shared + PV's own]};
        an extract with no exclusions is left out."""
        shared = csv.parse_array(row[SHARED_EXCLUSIONS])
        out = {}
        for name, (_, col) in PKB_EXTRACTS.items():
            values = csv.unique(shared + csv.parse_array(row[col]))
            if values:
                out[name] = values
        return csv.to_json(out)

    df = df.with_columns(
        csv.flags_to_array(OLD_FLAGS).alias("enabled_pkb_extracts"),
        pl.struct(OLD_EXCLUSIONS)
        .map_elements(_merge_exclusions, return_dtype=pl.String)
        .alias("pkb_extract_msg_exclusions"),
    )
    return df.drop([*OLD_FLAGS.values(), *OLD_EXCLUSIONS])


def downgrade_facility(df: pl.DataFrame) -> pl.DataFrame:

    def _split_exclusions(value: str | None) -> dict:
        data = csv.parse_json(value)
        lists = {name: data.get(name, []) for name in PKB_EXTRACTS}
        first, *rest = lists.values()
        shared = [v for v in first if all(v in other for other in rest)]
        out = {SHARED_EXCLUSIONS: csv.to_array(shared)}
        for name, (_, col) in PKB_EXTRACTS.items():
            out[col] = csv.to_array(v for v in lists[name] if v not in shared)
        return out

    df = df.with_columns(
        *csv.array_to_flags("enabled_pkb_extracts", OLD_FLAGS),
        pl.col("pkb_extract_msg_exclusions")
        .fill_null("")
        .map_elements(
            _split_exclusions,
            return_dtype=pl.Struct({col: pl.String for col in OLD_EXCLUSIONS}),
        )
        .alias("_exclusions"),
    ).unnest("_exclusions")
    return df.drop(["enabled_pkb_extracts", "pkb_extract_msg_exclusions"])


# None: nothing to do for that model in this step.
UPGRADES = {
    "Address": None,
    "Allergy": None,
    "CauseOfDeath": None,
    "ClinicalRelationship": None,
    "Code": None,
    "CodeExclusion": None,
    "CodeMap": None,
    "CodingStandards": None,
    "ContactDetail": None,
    "Diagnosis": None,
    "DialysisSession": None,
    "Document": None,
    "Encounter": None,
    "Facility": upgrade_facility,
    "FacilityRelationship": None,
    "FamilyDoctor": None,
    "FamilyHistory": None,
    "File": None,
    "GPInfo": None,
    "LabOrder": None,
    "Level": None,
    "Locations": None,
    "Medication": None,
    "ModalityCodes": None,
    "Name": None,
    "Observation": None,
    "OptOut": None,
    "PKBLink": None,
    "PVData": None,
    "PVDelete": None,
    "Patient": None,
    "PatientNumber": None,
    "PatientRecord": None,
    "Procedure": None,
    "ProgramMembership": None,
    "Question": None,
    "RRCodes": None,
    "RRDataDefinition": None,
    "RenalDiagnosis": None,
    "ResultItem": None,
    "SatelliteMap": None,
    "Score": None,
    "SendingExtractMetadata": upgrade_sendingextractmetadata,
    "SocialHistory": None,
    "Survey": None,
    "Transplant": None,
    "TransplantList": None,
    "Treatment": None,
    "ValueExclusion": None,
    "VascularAccess": None,
}

DOWNGRADES = {
    "Address": None,
    "Allergy": None,
    "CauseOfDeath": None,
    "ClinicalRelationship": None,
    "Code": None,
    "CodeExclusion": None,
    "CodeMap": None,
    "CodingStandards": None,
    "ContactDetail": None,
    "Diagnosis": None,
    "DialysisSession": None,
    "Document": None,
    "Encounter": None,
    "Facility": downgrade_facility,
    "FacilityRelationship": None,
    "FamilyDoctor": None,
    "FamilyHistory": None,
    "File": None,
    "GPInfo": None,
    "LabOrder": None,
    "Level": None,
    "Locations": None,
    "Medication": None,
    "ModalityCodes": None,
    "Name": None,
    "Observation": None,
    "OptOut": None,
    "PKBLink": None,
    "PVData": None,
    "PVDelete": None,
    "Patient": None,
    "PatientNumber": None,
    "PatientRecord": None,
    "Procedure": None,
    "ProgramMembership": None,
    "Question": None,
    "RRCodes": None,
    "RRDataDefinition": None,
    "RenalDiagnosis": None,
    "ResultItem": None,
    "SatelliteMap": None,
    "Score": None,
    "SendingExtractMetadata": downgrade_sendingextractmetadata,
    "SocialHistory": None,
    "Survey": None,
    "Transplant": None,
    "TransplantList": None,
    "Treatment": None,
    "ValueExclusion": None,
    "VascularAccess": None,
}


def upgrade(model: str, df: pl.DataFrame) -> pl.DataFrame:
    return UPGRADES[model](df)


def downgrade(model: str, df: pl.DataFrame) -> pl.DataFrame:
    return DOWNGRADES[model](df)


def run(direction: str, model: str, source, dest=None) -> bool:
    """Load, transform and save the CSV; False (untouched) when the model has nothing to do."""
    if (UPGRADES if direction == "upgrade" else DOWNGRADES).get(model) is None:
        return False
    ending = line_ending(source)
    df = load(source)
    df = upgrade(model, df) if direction == "upgrade" else downgrade(model, df)
    save(df, dest or source, ending)
    return True


if __name__ == "__main__":
    if len(sys.argv) not in (4, 5) or sys.argv[1] not in ("upgrade", "downgrade"):
        sys.exit(
            f"usage: python {sys.argv[0]} upgrade|downgrade MODEL IN.csv [OUT.csv]"
        )
    if not run(*sys.argv[1:]):
        print(f"step {step} has no {sys.argv[1]} for {sys.argv[2]}: nothing done")
