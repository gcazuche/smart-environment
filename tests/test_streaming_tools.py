"""No camera, network, download or child process is started by these tests."""

import hashlib
import io
import zipfile
from pathlib import Path

import pytest

from scripts import streaming


def test_archive_hash_checked_before_executable_is_read():
    with pytest.raises(ValueError, match="SHA-256"):
        streaming.unpack_verified(b"invalid", "windows.zip", "mediamtx.exe", "0" * 64)


def test_archive_extracts_only_expected_executable():
    data = io.BytesIO()
    with zipfile.ZipFile(data, "w") as archive:
        archive.writestr("mediamtx.exe", b"expected")
        archive.writestr("../../do-not-extract", b"unexpected")
    payload = data.getvalue()
    assert (
        streaming.unpack_verified(
            payload, "windows.zip", "mediamtx.exe", hashlib.sha256(payload).hexdigest()
        )
        == b"expected"
    )


def test_test_pattern_is_video_only_and_loopback(monkeypatch):
    monkeypatch.setattr(streaming, "ffmpeg", lambda: "ffmpeg")
    args = streaming.publish_args(None, 3)
    assert "testsrc=size=1280x720:rate=30" in args
    assert "-an" in args
    assert "-r" not in args  # Do not manufacture 30 FPS by duplicating incoming frames.
    assert args[args.index("-fps_mode") + 1] == "passthrough"
    assert args[-1] == "rtsp://127.0.0.1:8554/camera1"
    assert args[args.index("-bf") + 1] == "0"
    assert args[args.index("-t") + 1] == "3"


def test_windows_webcam_device_remains_one_argument(monkeypatch):
    monkeypatch.setattr(streaming, "ffmpeg", lambda: "ffmpeg")
    monkeypatch.setattr(streaming.platform, "system", lambda: "Windows")
    args = streaming.publish_args("Camera name & symbols", None)
    assert args[args.index("-i") + 1] == "video=Camera name & symbols"
    assert "-re" not in args
    assert "testsrc" not in " ".join(args)


def test_linux_device_and_duration_validation(monkeypatch):
    monkeypatch.setattr(streaming, "ffmpeg", lambda: "ffmpeg")
    monkeypatch.setattr(streaming.platform, "system", lambda: "Linux")
    assert "/dev/video0" in streaming.publish_args("/dev/video0", 5)
    with pytest.raises(ValueError):
        streaming.publish_args("/not-a-camera", 5)
    with pytest.raises(ValueError):
        streaming.publish_args(None, 0)


@pytest.mark.parametrize("name", ["Camera:audio=Microphone", "video=Camera", "", " ", "cam\n"])
def test_directshow_rejects_extra_device_selectors(name):
    with pytest.raises(ValueError):
        streaming.windows_device(name)


def test_server_env_cannot_override_local_profile_or_enable_recording(monkeypatch):
    monkeypatch.setenv("MTX_RTSPADDRESS", "public-listener")
    monkeypatch.setenv("mtx_pathDefaults_record", "true")
    monkeypatch.setenv("RTSP_WEBRTCALLOWORIGINS", "*")
    monkeypatch.setenv("FFREPORT", "file=unexpected.log")
    monkeypatch.setenv("ST_SAFE_TEST", "preserved")
    calls = []

    class Child:
        def wait(self):
            return 0

    def fake_popen(command, **kwargs):
        calls.append(kwargs)
        return Child()

    monkeypatch.setattr(streaming.subprocess, "Popen", fake_popen)
    assert streaming.run(["unused"], local_server=True) == 0
    environment = calls[0]["env"]
    assert not any(key.upper().startswith(("MTX_", "RTSP_")) for key in environment)
    assert "FFREPORT" not in environment
    assert environment["ST_SAFE_TEST"] == "preserved"


def test_local_profile_has_no_public_listeners_recording_or_catch_all():
    config = (
        Path(__file__).resolve().parents[1] / "config/streaming/mediamtx.local.yml"
    ).read_text()
    for required in [
        'rtspAddress: "127.0.0.1:8554"',
        'webrtcAddress: "127.0.0.1:8889"',
        'webrtcLocalUDPAddress: "127.0.0.1:8189"',
        'ips: ["127.0.0.1"]',
        "webrtcIPsFromInterfaces: false",
        "webrtcICEServers2: []",
        "record: false",
        "api: false",
        "metrics: false",
        "pprof: false",
        "rtmp: false",
        "hls: false",
        "srt: false",
        "moq: false",
        "overridePublisher: false",
    ]:
        assert required in config
    assert "all_others" not in config
    assert "0.0.0.0" not in config  # noqa: S104 - regression forbids public binding
