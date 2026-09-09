"""Offline installation checks. No network, subprocess, camera, inference or SQLite writes."""

from __future__ import annotations

import importlib
import os
import platform
import sys
from collections.abc import Callable
from importlib.metadata import version
from pathlib import Path

from app import __version__
from app.diagnostics import CheckStatus, DiagnosticCheck, DiagnosticReport
from app.server.config import Settings, load_env

ROOT = Path(__file__).resolve().parents[2]
DEPENDENCIES = (
    ("numpy", "numpy"),
    ("opencv-python", "cv2"),
    ("openvino", "openvino"),
    ("imageio-ffmpeg", "imageio_ffmpeg"),
)
SCOPE = "Somente instalação local; não valida conexão, permissões remotas, vídeo ou FPS."


def _dependency(distribution: str, module: str) -> DiagnosticCheck:
    try:
        installed = version(distribution)
        importlib.import_module(module)
    except Exception:
        return DiagnosticCheck(
            distribution,
            CheckStatus.FAIL,
            "Dependência ausente ou falha ao importar. Recrie o perfil Conda.",
        )
    return DiagnosticCheck(distribution, CheckStatus.PASS, f"Instalada e importável: {installed}.")


def _model() -> DiagnosticCheck:
    try:
        from app.vision.intel_yolo import (
            MODEL_BIN_SHA256,
            MODEL_XML_SHA256,
            _validate_model,
            default_model_path,
        )

        _validate_model(default_model_path(), MODEL_XML_SHA256, MODEL_BIN_SHA256)
    except Exception:
        return DiagnosticCheck(
            "model",
            CheckStatus.FAIL,
            "Modelo ausente, alterado ou inacessível. Copie o XML/BIN aprovado.",
        )
    return DiagnosticCheck(
        "model",
        CheckStatus.PASS,
        "XML e BIN conferem com os SHA-256 do projeto; modelo não executado.",
    )


def _ffmpeg() -> DiagnosticCheck:
    try:
        helper = importlib.import_module("imageio_ffmpeg")
        # imageio's discovery helper may execute FFmpeg to verify it. Locate only the
        # packaged artifact here: preflight must never execute an environment override.
        if helper.__file__ is None:
            raise ValueError("Package location unavailable")
        directory = Path(helper.__file__).parent / "binaries"
        candidates = [
            item
            for item in directory.iterdir()
            if item.name.startswith("ffmpeg-") and item.is_file() and os.access(item, os.X_OK)
        ]
        if not candidates:
            raise ValueError("Packaged FFmpeg missing")
    except Exception:
        return DiagnosticCheck(
            "ffmpeg",
            CheckStatus.FAIL,
            "FFmpeg empacotado ausente/inacessível; reinstale o extra stream.",
        )
    if os.environ.get("IMAGEIO_FFMPEG_EXE"):
        return DiagnosticCheck(
            "ffmpeg",
            CheckStatus.WARN,
            "Há override IMAGEIO_FFMPEG_EXE; removê-lo é recomendado. Não executado.",
        )
    return DiagnosticCheck(
        "ffmpeg", CheckStatus.PASS, "Executável empacotado presente; não executado."
    )


def _mediamtx() -> DiagnosticCheck:
    filename = "mediamtx.exe" if platform.system() == "Windows" else "mediamtx"
    executable = ROOT / "tools" / "streaming" / "1.20.1" / filename
    try:
        present = executable.is_file() and os.access(executable, os.X_OK)
    except OSError:
        present = False
    if not present:
        return DiagnosticCheck(
            "mediamtx",
            CheckStatus.FAIL,
            "MediaMTX ausente/inacessível. Execute python scripts/streaming.py setup.",
        )
    return DiagnosticCheck(
        "mediamtx",
        CheckStatus.PASS,
        "Arquivo presente; versão/integridade dependem do instalador verificado.",
    )


def _storage(database: Path) -> DiagnosticCheck:
    try:
        if database.exists() and not database.is_file():
            raise ValueError("Database path must be a file")
        parent = database.parent
        if not parent.is_dir() or not os.access(parent, os.W_OK | os.X_OK):
            return DiagnosticCheck(
                "outbox_directory",
                CheckStatus.WARN,
                "Diretório da fila ausente/sem permissão aparente; prepare-o antes.",
            )
        if database.exists() and not os.access(database, os.R_OK | os.W_OK):
            raise ValueError("Database not readable/writable")
    except (OSError, ValueError):
        return DiagnosticCheck(
            "outbox_directory",
            CheckStatus.FAIL,
            "Destino da fila inválido ou inacessível. Não foi alterado.",
        )
    return DiagnosticCheck(
        "outbox_directory",
        CheckStatus.PASS,
        "Permissões aparentes adequadas; gravação/SQLite não testados.",
    )


def run_preflight(config: Path | None = None, env_file: Path | None = None) -> DiagnosticReport:
    checks: list[DiagnosticCheck] = []
    prefix = Path(sys.prefix)
    correct_environment = prefix.name == "smart-environment" and (prefix / "conda-meta").is_dir()
    checks.append(
        DiagnosticCheck(
            "conda",
            CheckStatus.PASS if correct_environment else CheckStatus.FAIL,
            "Ambiente Conda smart-environment ativo."
            if correct_environment
            else "Execute com conda run -n smart-environment; não use base nem .venv.",
        )
    )
    supported = (3, 11) <= sys.version_info[:2] < (3, 13)
    checks.append(
        DiagnosticCheck(
            "python",
            CheckStatus.PASS if supported else CheckStatus.FAIL,
            "Python 3.11/3.12 suportado."
            if supported
            else "Este projeto requer Python 3.11 ou 3.12.",
        )
    )
    checks.extend(_dependency(distribution, module) for distribution, module in DEPENDENCIES)
    # Every check reports its own failure: no raw exception/path/credential is serialized.
    for operation in (_model, _ffmpeg, _mediamtx):
        checks.append(operation())
    configured = False
    if config is not None:
        try:
            if env_file is not None:
                load_env(env_file)
            settings = Settings.read(config)
        except Exception:
            checks.append(
                DiagnosticCheck(
                    "configuration",
                    CheckStatus.FAIL,
                    "Configuração inválida. Confira TOML, UUIDs e variáveis; valores omitidos.",
                )
            )
        else:
            configured = True
            checks.append(
                DiagnosticCheck(
                    "configuration",
                    CheckStatus.PASS,
                    f"Formato válido: {len(settings.streams)} câmeras.",
                )
            )
            checks.append(_storage(settings.database))
    else:
        checks.append(
            DiagnosticCheck(
                "configuration",
                CheckStatus.WARN,
                "Não verificada. Informe --config e, se necessário, --env-file.",
            )
        )
    return DiagnosticReport(
        "Smart Environment Server",
        __version__,
        platform.system(),
        {
            "mode": "offline_preflight",
            "configuration_checked": configured,
            "network_checked": False,
            "scope": SCOPE,
        },
        tuple(checks),
    )


def render_report(report: DiagnosticReport, write: Callable[[str], None] = print) -> None:
    write(f"Smart Environment {report.version} — diagnóstico de instalação")
    for check in report.checks:
        write(f"[{check.status.value.upper()}] {check.name}: {check.detail}")
    write(SCOPE)
    write(
        "Resultado: há pendências bloqueantes."
        if report.has_failures
        else "Resultado: sem falhas nos itens verificados; confira os avisos."
    )
