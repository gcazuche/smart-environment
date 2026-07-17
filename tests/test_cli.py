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
                with self.assertRaises(SystemExit) as raised:
                    main(["doctor", "--json"])

        self.assertEqual(raised.exception.code, 2)
        self.assertIn("erro de configuração", stderr.getvalue())

    def test_version_command_matches_project_metadata(self) -> None:
        stdout = StringIO()
        with redirect_stdout(stdout):
            exit_code = main(["version"])

        metadata = tomllib.loads(
            (Path(__file__).resolve().parents[1] / "pyproject.toml").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(exit_code, 0)
        self.assertEqual(stdout.getvalue().strip(), __version__)
        self.assertEqual(metadata["project"]["version"], __version__)
