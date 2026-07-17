"""Tests for deterministic and non-mutating diagnostics."""

import json

from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

from app.configuration import Settings
from app.diagnostics import CheckStatus, collect_diagnostics


def _settings_for(root: Path) -> Settings:
    return Settings.from_env({}, project_root=root)


class DiagnosticsTests(TestCase):
    def test_supported_runtime_and_complete_structure_pass(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            for directory in ("app", "tests", ".planning", "data"):
                (root / directory).mkdir()

            report = collect_diagnostics(_settings_for(root), version_info=(3, 12, 13))

        self.assertFalse(report.has_failures)
        self.assertTrue(all(check.status is CheckStatus.PASS for check in report.checks))

    def test_unsupported_runtime_fails(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            for directory in ("app", "tests", ".planning", "data"):
                (root / directory).mkdir()

            report = collect_diagnostics(_settings_for(root), version_info=(3, 10, 14))

        python_check = next(check for check in report.checks if check.name == "python")
        self.assertEqual(python_check.status, CheckStatus.FAIL)
        self.assertTrue(report.has_failures)

    def test_missing_required_directory_is_reported_without_creation(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            settings = _settings_for(root)

            report = collect_diagnostics(settings, version_info=(3, 12, 1))

            self.assertTrue(report.has_failures)
            self.assertFalse((root / "app").exists())

    def test_json_representation_is_serializable_and_sanitized(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            for directory in ("app", "tests", ".planning", "data"):
                (root / directory).mkdir()

            serialized = json.dumps(
                collect_diagnostics(
                    _settings_for(root), version_info=(3, 12, 1)
                ).to_dict()
            )
            payload = json.loads(serialized)

        self.assertIn("checks", payload)
        self.assertNotIn("project_root", payload["settings"])
        self.assertNotIn("data_dir", payload["settings"])

    def test_installed_layout_does_not_require_checkout_artifacts(self) -> None:
        with TemporaryDirectory() as temp_dir:
            settings = Settings(project_root=None, data_dir=Path(temp_dir) / "data")

            report = collect_diagnostics(settings, version_info=(3, 12, 1))

        names = {check.name for check in report.checks}
        self.assertFalse(report.has_failures)
        self.assertIn("installation_layout", names)
        self.assertNotIn("tests_directory", names)
