"""
Confirms, via a real `mypy` subprocess run, that the DynamicMapped typing
fix in ukrdc_sqla/ukrdc.py works as intended:

  * tests/valid_mypy.py contains only correct usage and must type-check
    with zero errors.
  * tests/invalid_mypy.py contains four deliberate type errors and must
    fail type-checking with exactly those four errors - proving mypy is
    still doing precise checking, not just accepting everything.

These fixture files are never imported or executed by pytest - they are
pure static-analysis inputs, run through `python -m mypy` as a subprocess.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

pytest.importorskip("mypy")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
FIXTURES_DIR = Path(__file__).resolve().parent / "mypy_checks"

VALID_FIXTURE = FIXTURES_DIR / "valid_mypy.py"
INVALID_FIXTURE = FIXTURES_DIR / "invalid_mypy.py"


def run_mypy(target: Path) -> subprocess.CompletedProcess[str]:
    """Run `python -m mypy <target>` as a subprocess and return the result.

    Using a subprocess (rather than mypy's in-process API) guarantees this
    test sees exactly what a developer or CI running `mypy` on the command
    line would see.
    """
    if not target.is_file():
        pytest.fail(
            f"Fixture file not found: {target}\n"
            "valid_mypy.py and invalid_mypy.py must live in "
            "'tests/mypy_checks/' alongside test_relationship_typing.py's "
            "'mypy_checks' subfolder."
        )
    return subprocess.run(
        [
            sys.executable,
            "-m",
            "mypy",
            str(target),
            "--ignore-missing-imports",
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
    )


class TestValidFixtureTypeChecksCleanly:
    """tests/valid_mypy.py exercises only correct usage of the relationships."""

    @classmethod
    @pytest.fixture(scope="class")
    def result(cls) -> subprocess.CompletedProcess[str]:
        return run_mypy(VALID_FIXTURE)

    def test_exits_zero(self, result: subprocess.CompletedProcess[str]) -> None:
        assert result.returncode == 0, result.stdout + result.stderr

    def test_reports_success(self, result: subprocess.CompletedProcess[str]) -> None:
        assert "Success: no issues found" in result.stdout, result.stdout

    def test_reports_no_errors(self, result: subprocess.CompletedProcess[str]) -> None:
        # Deliberately case-insensitive and not anchored on "error:" - a
        # mypy usage error (e.g. "Found 1 error... (errors prevented
        # further checking)") must fail this just as much as a real type
        # error would.
        assert "error" not in result.stdout.lower(), result.stdout


class TestInvalidFixtureIsRejected:
    """tests/invalid_mypy.py exercises four deliberately incorrect usages."""

    @classmethod
    @pytest.fixture(scope="class")
    def result(cls) -> subprocess.CompletedProcess[str]:
        return run_mypy(INVALID_FIXTURE)

    def test_exits_non_zero(self, result: subprocess.CompletedProcess[str]) -> None:
        assert result.returncode != 0, result.stdout + result.stderr

    def test_reports_exactly_four_errors(
        self, result: subprocess.CompletedProcess[str]
    ) -> None:
        assert "Found 4 errors in 1 file" in result.stdout, result.stdout

    @pytest.mark.parametrize(
        "expected_substring",
        [
            # plain list relationship has no .filter()
            'has no attribute "filter"',
            # dynamic relationship rejects wrong element type on .append()
            'incompatible type "SocialHistory"; expected "LabOrder"',
            # column assignment rejects wrong scalar type
            "Incompatible types in assignment",
            # .all() on a dynamic relationship returns the wrong list type
            'has type "list[LabOrder]", variable has type "list[SocialHistory]"',
        ],
    )
    def test_reports_expected_error(
        self, result: subprocess.CompletedProcess[str], expected_substring: str
    ) -> None:
        assert expected_substring in result.stdout, result.stdout