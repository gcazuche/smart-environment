"""Contract tests for the public command-line interface."""

from __future__ import annotations

import json
import tomllib
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch

from app import __version__
from app.__main__ import main
from app.configuration import ConfigurationError, Settings


def _complete_source_settings(root: Path) -> Settings:
    for directory in ("app", "tests", ".planning", "data"):
        (root / directory).mkdir()
    return Settings.from_env({}, project_root=root)


class CliTests(TestCase):
    def test_camera_requires_limit_when_display_is_disabled(self) -> None:
        stderr = StringIO()
        with redirect_stderr(stderr):
            exit_code = main(["camera", "--no-display"])

        self.assertEqual(exit_code, 2)
        self.assertIn("exige --max-frames", stderr.getvalue())

    def test_camera_prints_only_bounded_summary(self) -> None:
        from app.live_detection import RunSummary

        stdout = StringIO()
        summary = RunSummary(3, 1, 2, "dshow", "frame_limit")
        with patch("app.vision.NanoDetPersonDetector"):
            with patch("app.live_detection.run_person_detection", return_value=summary):
                with redirect_stdout(stdout):
                    exit_code = main(["camera", "--no-display", "--max-frames", "3"])

        self.assertEqual(exit_code, 0)
        self.assertIn("frames=3", stdout.getvalue())
        self.assertIn("pessoas_agora=1", stdout.getvalue())
        self.assertNotIn("frame_data", stdout.getvalue())

    def test_camera_reports_missing_model_safely(self) -> None:
        from app.vision import NanoDetModelError

        stderr = StringIO()
        with patch(
            "app.vision.NanoDetPersonDetector",
            side_effect=NanoDetModelError("modelo NanoDet ausente"),
        ):
            with redirect_stderr(stderr):
                exit_code = main(["camera", "--no-display", "--max-frames", "3"])

        self.assertEqual(exit_code, 4)
        self.assertEqual(stderr.getvalue().strip(), "erro de modelo: modelo NanoDet ausente")

    def test_doctor_json_is_parseable_and_returns_zero(self) -> None:
        with TemporaryDirectory() as temp_dir:
            settings = _complete_source_settings(Path(temp_dir))
            stdout = StringIO()
            with patch("app.__main__.Settings.from_env", return_value=settings):
                with redirect_stdout(stdout):
                    exit_code = main(["doctor", "--json"])

        payload = json.loads(stdout.getvalue())
        self.assertEqual(exit_code, 0)
        self.assertFalse(payload["has_failures"])

    def test_doctor_returns_one_when_required_source_artifact_is_missing(self) -> None:
        with TemporaryDirectory() as temp_dir:
            settings = Settings.from_env({}, project_root=Path(temp_dir))
            stdout = StringIO()
            with patch("app.__main__.Settings.from_env", return_value=settings):
                with redirect_stdout(stdout):
                    exit_code = main(["doctor", "--json"])

        self.assertEqual(exit_code, 1)
        self.assertTrue(json.loads(stdout.getvalue())["has_failures"])

    def test_invalid_configuration_uses_stderr_and_exit_two(self) -> None:
        stderr = StringIO()
        with patch(
            "app.__main__.Settings.from_env",
            side_effect=ConfigurationError("valor inválido"),
        ):
            with redirect_stderr(stderr):
                exit_code = main(["doctor", "--json"])

        self.assertEqual(exit_code, 2)
        self.assertIn("erro de configuração", stderr.getvalue())

    def test_version_command_matches_project_metadata(self) -> None:
        stdout = StringIO()
        with redirect_stdout(stdout):
            exit_code = main(["version"])

        metadata = tomllib.loads(
            (Path(__file__).resolve().parents[1] / "pyproject.toml").read_text(encoding="utf-8")
        )
        self.assertEqual(exit_code, 0)
        self.assertEqual(stdout.getvalue().strip(), __version__)
        self.assertEqual(metadata["project"]["version"], __version__)

    def test_unexpected_error_is_sanitized_and_correlated(self) -> None:
        stderr = StringIO()
        with patch(
            "app.__main__.collect_diagnostics",
            side_effect=RuntimeError("Authorization: Bearer do-not-leak"),
        ):
            with redirect_stderr(stderr):
                exit_code = main(["doctor", "--json"])

        lines = stderr.getvalue().splitlines()
        payload = json.loads(lines[0])
        self.assertEqual(exit_code, 1)
        self.assertEqual(payload["event"], "fatal_error")
        self.assertEqual(payload["exception_type"], "RuntimeError")
        self.assertNotIn("do-not-leak", stderr.getvalue())
        self.assertNotIn("Traceback", stderr.getvalue())
        self.assertIn(payload["correlation_id"], lines[-1])

    def test_logging_bootstrap_failure_does_not_escape_global_boundary(self) -> None:
        stderr = StringIO()
        with patch(
            "app.__main__.configure_secure_logging",
            side_effect=RuntimeError("opaque-sensitive-value-456"),
        ):
            with redirect_stderr(stderr):
                exit_code = main(["doctor", "--json"])

        self.assertEqual(exit_code, 1)
        self.assertEqual(
            stderr.getvalue().strip(),
            "erro interno ao iniciar observabilidade",
        )
        self.assertNotIn("opaque-sensitive-value-456", stderr.getvalue())
        self.assertNotIn("Traceback", stderr.getvalue())
