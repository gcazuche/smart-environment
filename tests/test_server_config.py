"""Configuration tests with synthetic environment values and temporary TOML only."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.server.config import Settings, origin, uuid

ORG = "10000000-0000-4000-8000-000000000001"
CAMERA = "20000000-0000-4000-8000-000000000001"


@pytest.fixture(autouse=True)
def synthetic_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SUPABASE_URL", "https://synthetic.supabase.co")
    monkeypatch.setenv("SUPABASE_PUBLISHABLE_KEY", "sb_publishable_synthetic_only")
    monkeypatch.setenv("SUPABASE_SECRET_KEY", "sb_secret_synthetic_only")


def config_file(tmp_path: Path, *, top: str = "", streams: str | None = None) -> Path:
    path = tmp_path / "server.toml"
    path.write_text(
        f'organization_id = "{ORG}"\n'
        'allowed_origins = ["https://dashboard.example", "http://localhost:3000"]\n'
        'database = "outbox.sqlite3"\n'
        + top
        + "\n[streams]\n"
        + (streams if streams is not None else f'"{CAMERA}" = "camera1"\n'),
        encoding="utf-8",
    )
    return path


def test_reads_explicit_defaults_and_hides_keys_from_repr(tmp_path: Path) -> None:
    settings = Settings.read(config_file(tmp_path))
    assert settings.organization_id == ORG
    assert settings.streams == {CAMERA: "camera1"}
    assert settings.analysis_fps == 2.0
    assert settings.cpu_threads == 4
    assert settings.port == 8766
    assert settings.database == (tmp_path / "outbox.sqlite3").resolve()
    assert settings.supabase_url == "https://synthetic.supabase.co"
    assert settings.allowed_origins == ("https://dashboard.example", "http://localhost:3000")
    assert "sb_secret_" not in repr(settings)
    assert "sb_publishable_" not in repr(settings)
    assert not settings.database.exists()


@pytest.mark.parametrize("value", ["", "not-a-uuid", "../../outside", "0" * 35, "-" * 36])
def test_rejects_invalid_organization_uuid(value: str, tmp_path: Path) -> None:
    path = config_file(tmp_path)
    path.write_text(path.read_text(encoding="utf-8").replace(ORG, value), encoding="utf-8")
    with pytest.raises(ValueError):
        Settings.read(path)


def test_uuid_normalizes_case() -> None:
    assert uuid("ABCDEFAB-0000-4000-8000-000000000001") == "abcdefab-0000-4000-8000-000000000001"


@pytest.mark.parametrize(
    "value",
    [
        "",
        "http://public.example",
        "http://192.168.1.50",
        "//dashboard.example",
        "https://user:password@dashboard.example",
        "https://dashboard.example/path",
        "https://dashboard.example?token=synthetic",
        "https://dashboard.example#fragment",
        "https://dashboard.example:bad",
        "https://dashboard.example:70000",
        "https://dash board.example",
        " https://dashboard.example",
        "https://dashboard.example\n",
    ],
)
def test_rejects_unsafe_origins(value: str) -> None:
    with pytest.raises(ValueError):
        origin(value, loopback=True)


def test_http_loopback_is_dashboard_only_opt_in() -> None:
    assert origin("http://127.0.0.1:3000/", loopback=True) == "http://127.0.0.1:3000"
    assert origin("https://dashboard.example/") == "https://dashboard.example"
    with pytest.raises(ValueError):
        origin("http://localhost:3000")


@pytest.mark.parametrize(
    "value", ["http://localhost:54321", "https://host:bad", "https://host/rest/v1"]
)
def test_supabase_origin_must_be_https_without_path(
    value: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("SUPABASE_URL", value)
    with pytest.raises(ValueError):
        Settings.read(config_file(tmp_path))


@pytest.mark.parametrize("origins", [[], ["https://dashboard.example"] * 9, ["*"]])
def test_requires_bounded_explicit_dashboard_origins(origins: list[str], tmp_path: Path) -> None:
    path = config_file(tmp_path)
    content = path.read_text(encoding="utf-8").replace(
        '["https://dashboard.example", "http://localhost:3000"]',
        json.dumps(origins),
    )
    path.write_text(content, encoding="utf-8")
    with pytest.raises(ValueError):
        Settings.read(path)


@pytest.mark.parametrize(
    "top",
    [
        "analysis_fps = 0",
        "analysis_fps = 0.19",
        "analysis_fps = 5.01",
        "analysis_fps = nan",
        "analysis_fps = inf",
        "analysis_fps = true",
        'analysis_fps = "2"',
        "cpu_threads = 0",
        "cpu_threads = 9",
        "cpu_threads = true",
        "cpu_threads = 1.5",
        'cpu_threads = "4"',
    ],
)
def test_rejects_invalid_fps_threads_and_coercions(top: str, tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        Settings.read(config_file(tmp_path, top=top))


@pytest.mark.parametrize("fps,threads", [(0.2, 1), (2, 4), (5, 8)])
def test_accepts_documented_configurable_cpu_limits(
    fps: float, threads: int, tmp_path: Path
) -> None:
    settings = Settings.read(
        config_file(tmp_path, top=f"analysis_fps = {fps}\ncpu_threads = {threads}")
    )
    assert settings.analysis_fps == fps and settings.cpu_threads == threads


@pytest.mark.parametrize(
    "stream", ["", "../outside", "a/b", "a?token=x", "_camera", "-camera", "x" * 65]
)
def test_stream_map_accepts_only_capture_compatible_segments(stream: str, tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        Settings.read(config_file(tmp_path, streams=f'"{CAMERA}" = {json.dumps(stream)}\n'))


@pytest.mark.parametrize(
    "streams",
    [
        "",
        '"bad-camera-id" = "camera1"',
        f'"{CAMERA}" = 123',
        f'"{CAMERA}" = "camera1"\n"20000000-0000-4000-8000-000000000002" = "camera1"',
        "\n".join(f'"20000000-0000-4000-8000-00000000000{i}" = "camera{i}"' for i in range(1, 6)),
    ],
)
def test_rejects_invalid_camera_map(streams: str, tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        Settings.read(config_file(tmp_path, streams=streams))


@pytest.mark.parametrize(
    "key,value",
    [
        ("SUPABASE_PUBLISHABLE_KEY", ""),
        ("SUPABASE_SECRET_KEY", ""),
        ("SUPABASE_PUBLISHABLE_KEY", "sb_secret_wrong-kind"),
        ("SUPABASE_SECRET_KEY", "sb_publishable_wrong-kind"),
        ("SUPABASE_SECRET_KEY", "eyJlegacy-not-supported"),
    ],
)
def test_rejects_missing_or_wrong_key_kind(
    key: str,
    value: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(key, value)
    with pytest.raises(ValueError):
        Settings.read(config_file(tmp_path))
