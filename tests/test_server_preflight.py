"""Offline preflight contracts with fake paths and no external services."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from app.diagnostics import CheckStatus, DiagnosticCheck
from app.server import __main__ as cli
from app.server import preflight
from app.server.config import Settings


@pytest.fixture
def installation(tmp_path, monkeypatch):
    prefix = tmp_path / "smart-environment"
    (prefix / "conda-meta").mkdir(parents=True)
    monkeypatch.setattr(preflight.sys, "prefix", str(prefix))
    monkeypatch.setattr(
        preflight,
        "_dependency",
        lambda distribution, module: DiagnosticCheck(distribution, CheckStatus.PASS, "synthetic"),
    )
    for name in ("_model", "_ffmpeg", "_mediamtx"):
        monkeypatch.setattr(
            preflight, name, lambda: DiagnosticCheck("synthetic", CheckStatus.PASS, "synthetic")
        )
    return prefix


def test_preflight_can_run_before_any_configuration_exists(installation):
    report = preflight.run_preflight()
    assert not report.has_failures
    assert report.settings["configuration_checked"] is False
    assert report.settings["network_checked"] is False
    assert any(
        item.name == "configuration" and item.status is CheckStatus.WARN for item in report.checks
    )


def test_base_or_venv_does_not_pass_conda_check(installation, monkeypatch):
    monkeypatch.setattr(preflight.sys, "prefix", str(installation.parent / "base"))
    assert preflight.run_preflight().has_failures


def test_configuration_exception_never_exposes_values(installation, monkeypatch):
    def invalid(path):
        raise ValueError("synthetic-secret-sb_secret_DO_NOT_PRINT")

    monkeypatch.setattr(preflight.Settings, "read", invalid)
    report = preflight.run_preflight(Path("unused"))
    assert report.has_failures
    assert "DO_NOT_PRINT" not in json.dumps(report.to_dict())


def test_configured_preflight_does_not_create_database(installation, monkeypatch, tmp_path):
    database = tmp_path / "outbox.sqlite3"
    settings = Settings(
        "10000000-0000-4000-8000-000000000001",
        {"camera": "camera1"},
        ("http://localhost:3000",),
        database,
        "https://synthetic.supabase.co",
        "sb_publishable_private_test",
        "sb_secret_private_test",
    )
    monkeypatch.setattr(preflight.Settings, "read", lambda path: settings)
    report = preflight.run_preflight(Path("unused"))
    assert not database.exists()
    assert report.settings["configuration_checked"] is True
    assert "private_test" not in json.dumps(report.to_dict())
    assert not report.has_failures


def test_missing_directory_is_warning_and_not_created(tmp_path):
    parent = tmp_path / "missing"
    assert preflight._storage(parent / "outbox.sqlite3").status is CheckStatus.WARN
    assert not parent.exists()
    assert preflight._storage(tmp_path).status is CheckStatus.FAIL


def test_missing_dependency_reports_generic_failure(monkeypatch):
    monkeypatch.setattr(preflight, "version", Mock(side_effect=RuntimeError("private path")))
    check = preflight._dependency("numpy", "numpy")
    assert check.status is CheckStatus.FAIL and "private path" not in check.detail


def test_ffmpeg_preflight_does_not_execute_discovery_or_environment_override(tmp_path, monkeypatch):
    (tmp_path / "binaries").mkdir()
    executable = tmp_path / "binaries" / "ffmpeg-test.exe"
    executable.write_bytes(b"not executable code")
    executable.chmod(0o700)
    helper = SimpleNamespace(__file__=str(tmp_path / "__init__.py"), get_ffmpeg_exe=Mock())
    monkeypatch.setattr(preflight.importlib, "import_module", lambda module: helper)
    monkeypatch.setenv("IMAGEIO_FFMPEG_EXE", "synthetic-private-override")
    check = preflight._ffmpeg()
    assert check.status is CheckStatus.WARN
    assert "private-override" not in check.detail
    helper.get_ffmpeg_exe.assert_not_called()


def test_missing_mediamtx_has_actionable_instruction(tmp_path, monkeypatch):
    monkeypatch.setattr(preflight, "ROOT", tmp_path)
    check = preflight._mediamtx()
    assert check.status is CheckStatus.FAIL and "scripts/streaming.py setup" in check.detail


def test_inaccessible_mediamtx_is_a_sanitized_check(monkeypatch):
    monkeypatch.setattr(Path, "is_file", Mock(side_effect=PermissionError("private machine path")))
    check = preflight._mediamtx()
    assert check.status is CheckStatus.FAIL and "private machine" not in check.detail


def test_cli_preflight_json_is_machine_readable_without_server_start(installation, capsys):
    assert cli.main(["--preflight", "--json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["settings"]["mode"] == "offline_preflight"
    assert payload["has_failures"] is False


def test_cli_preflight_failure_exit_code_and_human_scope(installation, monkeypatch, capsys):
    monkeypatch.setattr(
        preflight, "_model", lambda: DiagnosticCheck("model", CheckStatus.FAIL, "modelo ausente")
    )
    assert cli.main(["--preflight"]) == 1
    output = capsys.readouterr().out
    assert "[FAIL] model" in output and "não valida conexão" in output


@pytest.mark.parametrize(
    "args",
    [[], ["--check"], ["--json"], ["--preflight", "--check"], ["--preflight", "--env-file", "x"]],
)
def test_cli_rejects_ambiguous_or_incomplete_modes(args):
    with pytest.raises(SystemExit) as error:
        cli.main(args)
    assert error.value.code == 2


def test_cli_check_still_only_validates_configuration(monkeypatch, capsys):
    monkeypatch.setattr(
        cli.Settings, "read", lambda path: SimpleNamespace(streams={"id": "camera1"})
    )
    assert cli.main(["--check", "--config", "unused.toml"]) == 0
    assert "nenhuma conexão iniciada" in capsys.readouterr().out


def test_wrong_toml_types_do_not_escape_as_a_traceback(tmp_path, capsys):
    config = tmp_path / "malformed.toml"
    config.write_text("streams = []\n", encoding="utf-8")
    assert cli.main(["--check", "--config", str(config)]) == 2
    assert "Configuração inválida" in capsys.readouterr().out


def test_startup_failure_is_sanitized_before_runtime_run(monkeypatch, capsys):
    monkeypatch.setattr(cli.Settings, "read", lambda path: SimpleNamespace())
    fake = SimpleNamespace(Runtime=Mock(side_effect=PermissionError("private database path")))
    monkeypatch.setitem(sys.modules, "app.server.runtime", fake)
    assert cli.main(["--config", "unused.toml"]) == 1
    output = capsys.readouterr().out
    assert "falha" in output and "private database path" not in output
