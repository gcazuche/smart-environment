"""Read-only startup diagnostics for the foundation phase."""

from __future__ import annotations

import platform
import sys
from dataclasses import asdict, dataclass
from enum import StrEnum
from pathlib import Path
from typing import Final

from app import __version__
from app.configuration import Settings

MINIMUM_PYTHON: Final[tuple[int, int]] = (3, 11)
VALIDATED_PYTHON_MAX_EXCLUSIVE: Final[tuple[int, int]] = (3, 13)


class CheckStatus(StrEnum):
    """Severity of one diagnostic check."""

    PASS = "pass"
    WARN = "warn"
    FAIL = "fail"


@dataclass(frozen=True, slots=True)
class DiagnosticCheck:
    """One immutable and serializable diagnostic observation."""

    name: str
    status: CheckStatus
    detail: str


@dataclass(frozen=True, slots=True)
class DiagnosticReport:
    """Sanitized diagnostic result returned to CLI and future health endpoints."""

    application: str
    version: str
    platform: str
    settings: dict[str, object]
    checks: tuple[DiagnosticCheck, ...]

    @property
    def has_failures(self) -> bool:
        """Whether a check prevents a safe startup."""

        return any(check.status is CheckStatus.FAIL for check in self.checks)

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-ready representation without secrets or raw credentials."""

        return {
            "application": self.application,
            "version": self.version,
            "platform": self.platform,
            "settings": self.settings,
            "checks": [asdict(check) for check in self.checks],
            "has_failures": self.has_failures,
        }


def _python_check(version_info: tuple[int, int, int]) -> DiagnosticCheck:
    current = version_info[:2]
    printable = ".".join(str(part) for part in version_info)
    if current < MINIMUM_PYTHON:
        return DiagnosticCheck(
            "python",
            CheckStatus.FAIL,
            f"Python {printable}; mínimo suportado é 3.11",
        )
    if current >= VALIDATED_PYTHON_MAX_EXCLUSIVE:
        return DiagnosticCheck(
            "python",
            CheckStatus.WARN,
            f"Python {printable}; dependências de visão ainda não foram validadas nesta versão",
        )
    return DiagnosticCheck(
        "python",
        CheckStatus.PASS,
        f"Python {printable} dentro da matriz inicial 3.11–3.12",
    )


def _directory_check(name: str, path: Path, *, required: bool) -> DiagnosticCheck:
    if path.is_dir():
        return DiagnosticCheck(name, CheckStatus.PASS, "diretório disponível")
    status = CheckStatus.FAIL if required else CheckStatus.WARN
    return DiagnosticCheck(name, status, "diretório ausente; diagnóstico não o criou")


def collect_diagnostics(
    settings: Settings | None = None,
    *,
    version_info: tuple[int, int, int] | None = None,
) -> DiagnosticReport:
    """Collect deterministic checks without modifying files or external services."""

    resolved_settings = settings if settings is not None else Settings.from_env()
    runtime = version_info if version_info is not None else sys.version_info[:3]
    checks: list[DiagnosticCheck] = [_python_check(runtime)]
    if resolved_settings.project_root is not None:
        checks.extend(
            (
                _directory_check(
                    "app_directory", resolved_settings.project_root / "app", required=True
                ),
                _directory_check(
                    "tests_directory", resolved_settings.project_root / "tests", required=True
                ),
                _directory_check(
                    "planning_directory",
                    resolved_settings.project_root / ".planning",
                    required=True,
                ),
            )
        )
    else:
        checks.append(
            DiagnosticCheck(
                "installation_layout",
                CheckStatus.PASS,
                "pacote instalado; artefatos do checkout não são exigidos",
            )
        )
    checks.append(
        _directory_check("data_directory", resolved_settings.data_dir, required=False)
    )
    return DiagnosticReport(
        application="Multicam Inteligente",
        version=__version__,
        platform=platform.system() or "unknown",
        settings=resolved_settings.public_summary(),
        checks=tuple(checks),
    )
