"""Structured logging with conservative redaction and correlation IDs."""

from __future__ import annotations

import json
import logging
import os
import re
import sys
from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
from datetime import UTC, datetime
from hashlib import sha256
from io import TextIOWrapper
from logging.handlers import RotatingFileHandler
from pathlib import Path
from stat import S_IRUSR, S_IWUSR, S_IXUSR
from threading import RLock
from traceback import extract_tb
from typing import TextIO
from uuid import uuid4

_REDACTED = "[REDACTED]"
_MAX_TEXT_LENGTH = 4_096
_MAX_COLLECTION_ITEMS = 64
_MAX_EXCEPTION_FRAMES = 16
_MAX_EXCEPTION_CHAIN = 4
_RESERVED_LOGGER_NAMESPACE = "multicam"
_CONFIGURATION_LOCK = RLock()
_OWNED_HANDLER_ATTRIBUTE = "_multicam_secure_handler"
_CORRELATION_ID = ContextVar[str | None]("multicam_correlation_id", default=None)
_VALID_CORRELATION_ID = re.compile(r"^[A-Za-z0-9._:-]{1,128}$")
_VALID_EVENT_NAME = re.compile(r"^[a-z][a-z0-9_.-]{0,63}$")
_VALID_CONTEXT_IDENTIFIER = re.compile(r"^[A-Za-z0-9._:-]{1,128}$")
_JWT = re.compile(r"(?<![A-Za-z0-9_-])[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}")
_BEARER = re.compile(r"(?i)\bBearer\s+[A-Za-z0-9._~+/=-]+")
_SENSITIVE_HEADER = re.compile(
    r"(?im)\b(authorization|proxy-authorization|cookie|set-cookie)\b"
    r"(\s*[:=]\s*)[^\r\n]*"
)
_URL_CREDENTIALS = re.compile(r"(?i)\b([a-z][a-z0-9+.-]*://)([^/\s:@]+):([^@\s/]+)@")
_LABELED_SECRET = re.compile(
    r"(?i)\b(password|passwd|pwd|secret|token|api[-_]?key|authorization|cookie)\b"
    r"(\s*[:=]\s*)(?:\"[^\"]*\"|'[^']*'|[^\s,;]+)"
)
_SENSITIVE_KEY_PARTS = frozenset(
    {
        "apikey",
        "authorization",
        "biometric",
        "cookie",
        "credential",
        "databaseurl",
        "datanascimento",
        "document",
        "email",
        "endereco",
        "embedding",
        "facecrop",
        "faceencoding",
        "faceimage",
        "facial",
        "frame",
        "fullname",
        "image",
        "jwt",
        "matricula",
        "nome",
        "password",
        "personname",
        "phone",
        "photo",
        "privatekey",
        "rtspurl",
        "secret",
        "snapshot",
        "sobrenome",
        "token",
    }
)
_SENSITIVE_KEYS_EXACT = frozenset({"face", "cpf", "rg"})


def _is_sensitive_key(key: object) -> bool:
    normalized = re.sub(r"[^a-z0-9]", "", str(key).lower())
    return normalized in _SENSITIVE_KEYS_EXACT or any(
        part in normalized for part in _SENSITIVE_KEY_PARTS
    )


def _sanitize_text(value: str) -> str:
    sanitized = _URL_CREDENTIALS.sub(r"\1[REDACTED]@", value)
    sanitized = _SENSITIVE_HEADER.sub(
        lambda match: f"{match.group(1)}{match.group(2)}{_REDACTED}",
        sanitized,
    )
    sanitized = _BEARER.sub("Bearer [REDACTED]", sanitized)
    sanitized = _JWT.sub("[REDACTED_TOKEN]", sanitized)
    sanitized = _LABELED_SECRET.sub(
        lambda match: f"{match.group(1)}{match.group(2)}{_REDACTED}",
        sanitized,
    )
    if len(sanitized) > _MAX_TEXT_LENGTH:
        sanitized = f"{sanitized[:_MAX_TEXT_LENGTH]}…[TRUNCATED]"
    return sanitized


def _safe_log_identifier(value: object) -> str:
    if isinstance(value, str) and _VALID_CONTEXT_IDENTIFIER.fullmatch(value):
        return value
    return _REDACTED


def _normalize_event_name(value: object) -> str:
    candidate = str(value)
    if _VALID_EVENT_NAME.fullmatch(candidate):
        return candidate
    return "invalid_event"


@dataclass(frozen=True, slots=True)
class SecureLogContext:
    """Allowlisted, identifier-only context for one structured log event."""

    operation: str
    camera_id: str | None = None
    device_id: str | None = None
    error_type: str | None = None

    def to_safe_dict(self) -> dict[str, str]:
        values = {
            "operation": self.operation,
            "camera_id": self.camera_id,
            "device_id": self.device_id,
            "error_type": self.error_type,
        }
        return {
            key: _safe_log_identifier(value) for key, value in values.items() if value is not None
        }


def sanitize_for_log(value: object, *, key: object | None = None) -> object:
    """Return a JSON-safe representation with secrets and biometric payloads removed."""

    if key is not None and _is_sensitive_key(key):
        return _REDACTED
    if value is None or isinstance(value, (bool, int, float)):
        return value
    if isinstance(value, str):
        return _sanitize_text(value)
    if isinstance(value, bytes):
        return f"[BINARY_REDACTED:{len(value)} bytes]"
    if isinstance(value, Mapping):
        sanitized: dict[str, object] = {}
        for index, (item_key, item_value) in enumerate(value.items()):
            if index >= _MAX_COLLECTION_ITEMS:
                sanitized["_truncated"] = True
                break
            rendered_key = _sanitize_text(str(item_key))
            sanitized[rendered_key] = sanitize_for_log(item_value, key=item_key)
        return sanitized
    if isinstance(value, (list, tuple, set, frozenset)):
        items = list(value)
        sanitized_items = [sanitize_for_log(item) for item in items[:_MAX_COLLECTION_ITEMS]]
        if len(items) > _MAX_COLLECTION_ITEMS:
            sanitized_items.append("[TRUNCATED]")
        return sanitized_items
    return _sanitize_text(str(value))


def _normalize_correlation_id(candidate: str | None) -> str:
    if isinstance(candidate, str) and _VALID_CORRELATION_ID.fullmatch(candidate):
        return candidate
    return uuid4().hex


def current_correlation_id() -> str:
    """Return the scoped correlation ID or a fresh unbound identifier."""

    correlation_id = _CORRELATION_ID.get()
    if correlation_id is None:
        return _normalize_correlation_id(None)
    return correlation_id


@contextmanager
def correlation_scope(correlation_id: str | None = None) -> Iterator[str]:
    """Bind a validated correlation ID for one operation and restore it afterwards."""

    resolved = _normalize_correlation_id(correlation_id)
    token = _CORRELATION_ID.set(resolved)
    try:
        yield resolved
    finally:
        _CORRELATION_ID.reset(token)


class _JsonFormatter(logging.Formatter):
    def __init__(self, *, include_exception_details: bool) -> None:
        super().__init__()
        self._include_exception_details = include_exception_details

    def format(self, record: logging.LogRecord) -> str:
        event_name = _normalize_event_name(getattr(record, "event_name", "log"))
        correlation_id = _normalize_correlation_id(getattr(record, "correlation_id", None))
        record.correlation_id = correlation_id
        payload: dict[str, object] = {
            "timestamp": datetime.fromtimestamp(record.created, UTC).isoformat(),
            "level": record.levelname,
            "logger": _safe_log_identifier(record.name),
            "event": event_name,
            "message": event_name,
            "correlation_id": correlation_id,
        }
        context = getattr(record, "secure_context", None)
        if isinstance(context, SecureLogContext):
            payload["context"] = context.to_safe_dict()
        elif context is not None:
            payload["context_rejected"] = True
        if record.exc_info:
            exception_type = record.exc_info[0]
            payload["exception_type"] = (
                _safe_log_identifier(exception_type.__name__)
                if exception_type is not None
                else "Exception"
            )
            if self._include_exception_details:
                traceback_object = record.exc_info[2]
                if traceback_object is not None:
                    frames = extract_tb(traceback_object)[-_MAX_EXCEPTION_FRAMES:]
                    payload["exception_frames"] = [
                        {
                            "source_id": sha256(
                                frame.filename.encode("utf-8", errors="replace")
                            ).hexdigest()[:12],
                            "line": frame.lineno,
                            "function": _safe_log_identifier(frame.name),
                        }
                        for frame in frames
                    ]
                exception = record.exc_info[1]
                chain: list[str] = []
                seen: set[int] = set()
                while exception is not None and len(chain) < _MAX_EXCEPTION_CHAIN:
                    marker = id(exception)
                    if marker in seen:
                        break
                    seen.add(marker)
                    chain.append(_safe_log_identifier(type(exception).__name__))
                    if exception.__cause__ is not None:
                        exception = exception.__cause__
                    elif not exception.__suppress_context__:
                        exception = exception.__context__
                    else:
                        exception = None
                payload["exception_chain"] = chain
        return json.dumps(payload, ensure_ascii=False, separators=(",", ":"))


class _SecureRotatingFileHandler(RotatingFileHandler):
    """Rotate JSON logs without emitting raw logging tracebacks on write failure."""

    def __init__(
        self,
        filename: str | Path,
        *,
        max_bytes: int,
        backup_count: int,
        encoding: str,
        fallback_stream: TextIO,
    ) -> None:
        self._fallback_stream = fallback_stream
        super().__init__(
            filename,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding=encoding,
        )

    def _open(self) -> TextIOWrapper:
        stream = super()._open()
        if os.name != "nt":
            try:
                os.chmod(self.baseFilename, S_IRUSR | S_IWUSR)
            except OSError:
                stream.close()
                raise
        return stream

    def handleError(self, record: logging.LogRecord) -> None:
        payload = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": "ERROR",
            "logger": "multicam",
            "event": "log_write_failed",
            "message": "log_write_failed",
            "correlation_id": _normalize_correlation_id(getattr(record, "correlation_id", None)),
        }
        try:
            self._fallback_stream.write(json.dumps(payload, separators=(",", ":")) + "\n")
        except (OSError, ValueError):
            return


def _resolve_level(level: str) -> int:
    resolved = getattr(logging, level.upper(), None)
    if not isinstance(resolved, int):
        raise ValueError(f"nível de log inválido: {level}")
    return resolved


def _is_owned_handler(handler: logging.Handler) -> bool:
    return bool(getattr(handler, _OWNED_HANDLER_ATTRIBUTE, False))


def _mark_owned_handler(handler: logging.Handler) -> None:
    setattr(handler, _OWNED_HANDLER_ATTRIBUTE, True)


def _close_owned_handlers(logger: logging.Logger) -> None:
    for handler in tuple(logger.handlers):
        if _is_owned_handler(handler):
            logger.removeHandler(handler)
            handler.close()


def _detach_foreign_handlers(logger: logging.Logger) -> None:
    for handler in tuple(logger.handlers):
        if not _is_owned_handler(handler):
            logger.removeHandler(handler)


def configure_secure_logging(
    *,
    level: str = "INFO",
    logger_name: str = "multicam",
    stream: TextIO | None = None,
    log_dir: Path | None = None,
    max_bytes: int = 2 * 1024 * 1024,
    backup_count: int = 5,
) -> logging.Logger:
    """Configure isolated JSON logging and optional rotating file output."""

    if not (
        logger_name == _RESERVED_LOGGER_NAMESPACE
        or logger_name.startswith(f"{_RESERVED_LOGGER_NAMESPACE}.")
    ):
        raise ValueError("logger_name deve usar o namespace reservado multicam")
    if max_bytes < 1:
        raise ValueError("max_bytes deve ser positivo")
    if backup_count < 0 or (log_dir is not None and backup_count < 1):
        raise ValueError("backup_count deve ser ao menos 1 para log em arquivo")

    with _CONFIGURATION_LOCK:
        logger = logging.getLogger(logger_name)
        _detach_foreign_handlers(logger)
        logger.setLevel(_resolve_level(level))
        logger.propagate = False
        _close_owned_handlers(logger)

        fallback_stream = stream if stream is not None else sys.stderr
        stream_handler = logging.StreamHandler(fallback_stream)
        _mark_owned_handler(stream_handler)
        stream_handler.setFormatter(_JsonFormatter(include_exception_details=False))
        logger.addHandler(stream_handler)

        if log_dir is not None:
            if os.name == "nt":
                log_event(
                    logger,
                    logging.WARNING,
                    "secure_file_logging_unavailable",
                    context=SecureLogContext(operation="configure-logging"),
                )
                return logger
            file_handler: _SecureRotatingFileHandler | None = None
            try:
                log_dir.mkdir(
                    mode=S_IRUSR | S_IWUSR | S_IXUSR,
                    parents=True,
                    exist_ok=True,
                )
                if os.name != "nt":
                    os.chmod(log_dir, S_IRUSR | S_IWUSR | S_IXUSR)
                log_file = log_dir / "multicam.log"
                file_handler = _SecureRotatingFileHandler(
                    log_file,
                    max_bytes=max_bytes,
                    backup_count=backup_count,
                    encoding="utf-8",
                    fallback_stream=fallback_stream,
                )
                _mark_owned_handler(file_handler)
                file_handler.setFormatter(_JsonFormatter(include_exception_details=True))
                logger.addHandler(file_handler)
            except OSError as exc:
                if file_handler is not None:
                    file_handler.close()
                log_event(
                    logger,
                    logging.WARNING,
                    "log_destination_unavailable",
                    context=SecureLogContext(
                        operation="configure-logging",
                        error_type=type(exc).__name__,
                    ),
                )
        return logger


def log_event(
    logger: logging.Logger,
    level: int,
    event: str,
    *,
    context: SecureLogContext | None = None,
    exc_info: bool = False,
) -> None:
    """Emit one structured event through the configured secure logger."""

    with _CONFIGURATION_LOCK:
        normalized_event = _normalize_event_name(event)
        logger.log(
            level,
            normalized_event,
            extra={
                "event_name": normalized_event,
                "secure_context": context,
                "correlation_id": current_correlation_id(),
            },
            exc_info=exc_info,
        )
