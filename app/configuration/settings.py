"""Small, dependency-free settings layer used during the foundation phase."""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

_ENVIRONMENTS = frozenset({"development", "test", "production"})
_LOG_LEVELS = frozenset({"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"})
_RECOGNITION_DEVICES = frozenset({"auto", "cpu", "gpu"})
_TRUE_VALUES = frozenset({"1", "true", "yes", "on"})
_FALSE_VALUES = frozenset({"0", "false", "no", "off"})


class ConfigurationError(ValueError):
    """Raised when an environment value is invalid or unsafe to interpret."""


def _choice(name: str, raw_value: str, allowed: frozenset[str]) -> str:
    value = raw_value.strip()
    if value not in allowed:
        options = ", ".join(sorted(allowed))
        raise ConfigurationError(f"{name} deve ser um de: {options}")
    return value


def _boolean(name: str, raw_value: str) -> bool:
    value = raw_value.strip().lower()
    if value in _TRUE_VALUES:
        return True
    if value in _FALSE_VALUES:
        return False
    raise ConfigurationError(
        f"{name} deve usar true/false, yes/no, on/off ou 1/0"
    )


def _bounded_integer(name: str, raw_value: str, minimum: int, maximum: int) -> int:
    try:
        value = int(raw_value.strip())
    except ValueError as exc:
        raise ConfigurationError(f"{name} deve ser um número inteiro") from exc
    if not minimum <= value <= maximum:
        raise ConfigurationError(f"{name} deve estar entre {minimum} e {maximum}")
    return value


def _detect_source_root() -> Path | None:
    """Return the checkout root, or None when running from an installed wheel."""

    candidate = Path(__file__).resolve().parents[2]
    return candidate if (candidate / "pyproject.toml").is_file() else None


def _default_user_data_dir(environ: Mapping[str, str]) -> Path:
    """Choose a per-user data directory without writing to site-packages."""

    if os.name == "nt":
        base = environ.get("LOCALAPPDATA") or environ.get("APPDATA")
        root = Path(base).expanduser() if base else Path.home() / "AppData" / "Local"
    else:
        base = environ.get("XDG_DATA_HOME")
        root = Path(base).expanduser() if base else Path.home() / ".local" / "share"
    return root / "multicam-inteligente"


@dataclass(frozen=True, slots=True)
class Settings:
    """Validated non-secret settings needed by the foundation diagnostics."""

    project_root: Path | None
    data_dir: Path
    environment: str = "development"
    log_level: str = "INFO"
    recognition_device: str = "auto"
    offline_mode: bool = True
    max_cameras: int = 1

    @classmethod
    def from_env(
        cls,
        environ: Mapping[str, str] | None = None,
        *,
        project_root: Path | None = None,
    ) -> Settings:
        """Build settings from environment variables without reading a secrets file."""

        source = os.environ if environ is None else environ
        root = project_root.resolve() if project_root is not None else _detect_source_root()

        environment = _choice(
            "MULTICAM_ENV",
            source.get("MULTICAM_ENV", "development").lower(),
            _ENVIRONMENTS,
        )
        log_level = _choice(
            "MULTICAM_LOG_LEVEL",
            source.get("MULTICAM_LOG_LEVEL", "INFO").upper(),
            _LOG_LEVELS,
        )
        recognition_device = _choice(
            "MULTICAM_RECOGNITION_DEVICE",
            source.get("MULTICAM_RECOGNITION_DEVICE", "auto").lower(),
            _RECOGNITION_DEVICES,
        )
        offline_mode = _boolean(
            "MULTICAM_OFFLINE_MODE",
            source.get("MULTICAM_OFFLINE_MODE", "true"),
        )
        max_cameras = _bounded_integer(
            "MULTICAM_MAX_CAMERAS",
            source.get("MULTICAM_MAX_CAMERAS", "1"),
            1,
            64,
        )

        raw_data_dir = source.get("MULTICAM_DATA_DIR", "").strip()
        if not raw_data_dir:
            data_dir = root / "data" if root is not None else _default_user_data_dir(source)
            raw_data_dir = str(data_dir)
        if not raw_data_dir:
            raise ConfigurationError("MULTICAM_DATA_DIR não pode ser vazio")
        data_dir = Path(raw_data_dir).expanduser()
        if not data_dir.is_absolute():
            data_dir = (root if root is not None else Path.cwd()) / data_dir

        return cls(
            project_root=root,
            data_dir=data_dir.resolve(),
            environment=environment,
            log_level=log_level,
            recognition_device=recognition_device,
            offline_mode=offline_mode,
            max_cameras=max_cameras,
        )

    def public_summary(self) -> dict[str, object]:
        """Return only non-secret values suitable for diagnostics and logs."""

        return {
            "environment": self.environment,
            "log_level": self.log_level,
            "recognition_device": self.recognition_device,
            "offline_mode": self.offline_mode,
            "max_cameras": self.max_cameras,
            "execution_layout": "source" if self.project_root is not None else "installed",
            "data_dir_exists": self.data_dir.is_dir(),
        }
