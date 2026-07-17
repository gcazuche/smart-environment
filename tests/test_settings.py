"""Tests for strict, non-secret foundation settings."""

from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

from app.configuration import ConfigurationError, Settings


class SettingsTests(TestCase):
    def test_safe_defaults_are_relative_to_project_root(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            settings = Settings.from_env({}, project_root=root)

        self.assertEqual(settings.environment, "development")
        self.assertEqual(settings.data_dir, root / "data")
        self.assertTrue(settings.offline_mode)
        self.assertEqual(settings.max_cameras, 1)

    def test_invalid_boolean_is_rejected(self) -> None:
        with self.assertRaisesRegex(ConfigurationError, "MULTICAM_OFFLINE_MODE"):
            Settings.from_env({"MULTICAM_OFFLINE_MODE": "maybe"})

    def test_camera_limit_is_bounded(self) -> None:
        with self.assertRaisesRegex(ConfigurationError, "entre 1 e 64"):
            Settings.from_env({"MULTICAM_MAX_CAMERAS": "0"})

    def test_public_summary_does_not_echo_unrelated_environment_secrets(self) -> None:
        settings = Settings.from_env(
            {
                "MULTICAM_DATABASE_URL": "postgresql://user:secret@example/db",
                "MULTICAM_JWT_SECRET": "never-print-this",
            }
        )
        rendered = repr(settings.public_summary())

        self.assertNotIn("secret", rendered)
        self.assertNotIn("never-print-this", rendered)
