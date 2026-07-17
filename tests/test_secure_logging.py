"""Security regression tests for structured logging and redaction."""

from __future__ import annotations

import json
import logging
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch

from app.observability import (
    SecureLogContext,
    configure_secure_logging,
    correlation_scope,
    current_correlation_id,
    log_event,
    sanitize_for_log,
)


class SecureLoggingTests(TestCase):
    def test_sensitive_context_and_inline_credentials_are_redacted(self) -> None:
        sanitized = sanitize_for_log(
            {
                "password": "open-sesame",
                "embedding": [0.1, 0.2],
                "message": (
                    "Authorization: Basic YWRtaW46c2VjcmV0\n"
                    "Cookie: session=abc; identity=angel@example.com\n"
                    "Proxy-Authorization: Bearer abc.def.ghi"
                ),
                "database": "postgresql://admin:plain-text@db.example/app",
                "nome": "Angel",
            }
        )
        rendered = json.dumps(sanitized)

        self.assertNotIn("open-sesame", rendered)
        self.assertNotIn("0.1", rendered)
        self.assertNotIn("abc.def.ghi", rendered)
        self.assertNotIn("YWRtaW46c2VjcmV0", rendered)
        self.assertNotIn("session=abc", rendered)
        self.assertNotIn("angel@example.com", rendered)
        self.assertNotIn("Angel", rendered)
        self.assertNotIn("plain-text", rendered)
        self.assertIn("[REDACTED]", rendered)

    def test_structured_event_uses_bound_correlation_id(self) -> None:
        stream = StringIO()
        logger = configure_secure_logging(
            logger_name="multicam.tests.correlation",
            stream=stream,
        )

        with correlation_scope("test-operation-42"):
            log_event(
                logger,
                logging.INFO,
                "camera_probe",
                context=SecureLogContext(
                    camera_id="camera-1",
                    device_id="edge-1",
                    operation="capture-probe",
                ),
            )

        payload = json.loads(stream.getvalue())
        self.assertEqual(payload["correlation_id"], "test-operation-42")
        self.assertEqual(payload["event"], "camera_probe")
        self.assertEqual(payload["context"]["camera_id"], "camera-1")
        self.assertEqual(payload["context"]["device_id"], "edge-1")
        self.assertEqual(payload["context"]["operation"], "capture-probe")

    def test_file_handler_rotates_and_writes_json(self) -> None:
        with TemporaryDirectory() as temp_dir:
            log_dir = Path(temp_dir)
            logger = configure_secure_logging(
                logger_name="multicam.tests.rotation",
                stream=StringIO(),
                log_dir=log_dir,
                max_bytes=256,
                backup_count=1,
            )
            for _ in range(20):
                log_event(
                    logger,
                    logging.INFO,
                    "rotation_probe",
                )
            for handler in logger.handlers:
                handler.flush()

            current = log_dir / "multicam.log"
            rotated = log_dir / "multicam.log.1"
            payload = json.loads(current.read_text(encoding="utf-8").splitlines()[-1])
            rotated_exists = rotated.is_file()
            for handler in tuple(logger.handlers):
                logger.removeHandler(handler)
                handler.close()

        self.assertTrue(rotated_exists)
        self.assertEqual(payload["event"], "rotation_probe")

    def test_protected_log_omits_raw_exception_message_and_absolute_path(self) -> None:
        with TemporaryDirectory() as temp_dir:
            log_dir = Path(temp_dir)
            logger = configure_secure_logging(
                logger_name="multicam.tests.exception-file",
                stream=StringIO(),
                log_dir=log_dir,
            )
            try:
                raise RuntimeError("opaque-sensitive-value-123")
            except RuntimeError:
                log_event(
                    logger,
                    logging.ERROR,
                    "safe_exception_probe",
                    exc_info=True,
                )
            for handler in tuple(logger.handlers):
                handler.flush()
                logger.removeHandler(handler)
                handler.close()

            rendered = (log_dir / "multicam.log").read_text(encoding="utf-8")

        payload = json.loads(rendered)
        self.assertEqual(payload["exception_type"], "RuntimeError")
        self.assertEqual(payload["exception_chain"], ["RuntimeError"])
        self.assertTrue(payload["exception_frames"])
        self.assertNotIn("opaque-sensitive-value-123", rendered)
        self.assertNotIn(str(Path(__file__).resolve().parent), rendered)

    def test_non_sensitive_interface_key_is_not_over_redacted(self) -> None:
        sanitized = sanitize_for_log({"interface": "desktop"})

        self.assertEqual(sanitized, {"interface": "desktop"})

    def test_untyped_context_is_rejected_and_identifiers_are_allowlisted(self) -> None:
        stream = StringIO()
        logger = configure_secure_logging(
            logger_name="multicam.tests.context-policy",
            stream=stream,
        )
        log_event(
            logger,
            logging.INFO,
            "context_probe",
            context={"nome": "Angel"},  # type: ignore[arg-type]
        )
        payload = json.loads(stream.getvalue())

        self.assertTrue(payload["context_rejected"])
        self.assertNotIn("Angel", stream.getvalue())

        stream.seek(0)
        stream.truncate(0)
        log_event(
            logger,
            logging.INFO,
            "context_probe",
            context=SecureLogContext(
                operation="capture",
                camera_id="angel@example.com",
            ),
        )
        payload = json.loads(stream.getvalue())
        self.assertEqual(payload["context"]["camera_id"], "[REDACTED]")

    def test_unscoped_correlation_ids_are_not_reused(self) -> None:
        first = current_correlation_id()
        second = current_correlation_id()

        self.assertNotEqual(first, second)

    def test_configuration_refuses_foreign_handler_without_closing_it(self) -> None:
        logger = logging.getLogger("multicam.tests.foreign-handler")
        foreign_handler = logging.StreamHandler(StringIO())
        logger.addHandler(foreign_handler)
        try:
            with self.assertRaisesRegex(RuntimeError, "handlers externos"):
                configure_secure_logging(logger_name=logger.name, stream=StringIO())

            self.assertIn(foreign_handler, logger.handlers)
        finally:
            logger.removeHandler(foreign_handler)
            foreign_handler.close()

    def test_file_destination_failure_falls_back_without_path_disclosure(self) -> None:
        stream = StringIO()
        with TemporaryDirectory() as temp_dir:
            private_path = Path(temp_dir) / "private-location"
            with patch(
                "app.observability.secure_logging._SecureRotatingFileHandler",
                side_effect=OSError(f"denied: {private_path}"),
            ):
                configure_secure_logging(
                    logger_name="multicam.tests.fallback",
                    stream=stream,
                    log_dir=private_path,
                )

        payload = json.loads(stream.getvalue())
        self.assertEqual(payload["event"], "log_destination_unavailable")
        self.assertNotIn(str(private_path), stream.getvalue())
        self.assertEqual(payload["context"]["error_type"], "OSError")

    def test_file_logging_requires_at_least_one_backup(self) -> None:
        with TemporaryDirectory() as temp_dir:
            with self.assertRaisesRegex(ValueError, "ao menos 1"):
                configure_secure_logging(
                    logger_name="multicam.tests.no-backup",
                    stream=StringIO(),
                    log_dir=Path(temp_dir),
                    backup_count=0,
                )

    def test_posix_permissions_are_reapplied_after_rotation(self) -> None:
        with TemporaryDirectory() as temp_dir:
            log_dir = Path(temp_dir)
            with (
                patch("app.observability.secure_logging.os.name", "posix"),
                patch("app.observability.secure_logging.os.chmod") as chmod,
            ):
                logger = configure_secure_logging(
                    logger_name="multicam.tests.posix-permissions",
                    stream=StringIO(),
                    log_dir=log_dir,
                    max_bytes=256,
                    backup_count=1,
                )
                for _ in range(20):
                    log_event(logger, logging.INFO, "permission_probe")
                for handler in tuple(logger.handlers):
                    handler.flush()
                    logger.removeHandler(handler)
                    handler.close()

        targets = [Path(call.args[0]) for call in chmod.call_args_list]
        self.assertIn(log_dir, targets)
        self.assertGreaterEqual(targets.count(log_dir / "multicam.log"), 2)
