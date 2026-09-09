"""Synthetic capture/decoder tests: no network, camera, child process or model."""

from __future__ import annotations

import io
import subprocess  # noqa: S404 - only TimeoutExpired and constants, never real subprocesses
import sys
import threading
import time
from collections.abc import Callable
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import numpy as np
import pytest

from app.server import capture

_EXECUTABLE = str(Path.cwd() / "trusted-test-ffmpeg")


class PartialReader:
    def __init__(self, data: bytes, chunk_size: int = 2) -> None:
        self.source = io.BytesIO(data)
        self.chunk_size = chunk_size

    def read(self, size: int) -> bytes:
        return self.source.read(min(size, self.chunk_size))


class BlockingReader:
    def __init__(self, data: bytes = b"") -> None:
        self.source = io.BytesIO(data)
        self.blocked = threading.Event()
        self.released = threading.Event()
        self.closed = False

    def read(self, size: int) -> bytes:
        data = self.source.read(min(size, 2))
        if data:
            return data
        self.blocked.set()
        self.released.wait(5)
        return b""

    def close(self) -> None:
        self.closed = True
        self.released.set()


class FakeProcess:
    def __init__(self, stdout: BlockingReader, *, needs_kill: bool = False) -> None:
        self.stdout = stdout
        self.needs_kill = needs_kill
        self.returncode: int | None = None
        self.terminate_calls = 0
        self.kill_calls = 0

    def poll(self) -> int | None:
        return self.returncode

    def terminate(self) -> None:
        self.terminate_calls += 1
        if not self.needs_kill:
            self.returncode = 0
            self.stdout.released.set()

    def kill(self) -> None:
        self.kill_calls += 1
        self.returncode = -9
        self.stdout.released.set()

    def wait(self, timeout: float) -> int:
        if self.returncode is None:
            raise subprocess.TimeoutExpired("trusted-test-ffmpeg", timeout)
        return self.returncode


def pump(stop_event: threading.Event | None = None) -> capture.FramePump:
    return capture.FramePump(
        "camera-id",
        "camera1",
        stop_event or threading.Event(),
        ffmpeg_executable=_EXECUTABLE,
        width=2,
        height=1,
    )


def eventually(predicate: Callable[[], bool], timeout: float = 2.0) -> None:
    deadline = time.monotonic() + timeout
    while not predicate() and time.monotonic() < deadline:
        threading.Event().wait(0.005)
    assert predicate()


def test_partial_reads_are_assembled_and_eof_discards_partial_frames() -> None:
    assert capture._read_frame_bytes(PartialReader(b"abcdef"), 6, lambda: False) == b"abcdef"
    assert capture._read_frame_bytes(PartialReader(b"abc"), 6, lambda: False) is None
    assert capture._read_frame_bytes(PartialReader(b"abcdef"), 6, lambda: True) is None


@pytest.mark.parametrize(
    "stream_path",
    ["", "../x", "a/b", "a?token=x", "a#b", "a%2fb", "rtsp://other/x", "x\n", "x@other", "x" * 65],
)
def test_rejects_nonlocal_or_ambiguous_paths(stream_path: str) -> None:
    with pytest.raises(ValueError, match="caminho"):
        capture.FramePump("camera", stream_path, threading.Event(), ffmpeg_executable=_EXECUTABLE)


@pytest.mark.parametrize("width,height", [(0, 1), (1, 0), (1921, 1), (1, 1081), (True, 1)])
def test_bounds_frame_memory(width: int, height: int) -> None:
    with pytest.raises(ValueError):
        capture.FramePump(
            "camera",
            "camera1",
            threading.Event(),
            ffmpeg_executable=_EXECUTABLE,
            width=width,
            height=height,
        )


@pytest.mark.parametrize("executable", ["ffmpeg", "", "bad\nexe", str(Path.cwd() / "helper.cmd")])
def test_requires_trusted_absolute_non_shell_executable(executable: str) -> None:
    with pytest.raises(ValueError, match="executável"):
        capture.FramePump("camera", "camera1", threading.Event(), ffmpeg_executable=executable)


def test_child_environment_is_allowlisted() -> None:
    supplied = {
        "PATH": "runtime-path",
        "SystemRoot": "runtime-root",
        "TEMP": "runtime-temp",
        "FFREPORT": "file=leak",
        "SUPABASE_SERVICE_ROLE_KEY": "private",
        "MTX_AUTHINTERNALUSERS": "private",
        "RTSP_PASSWORD": "private",
        "HTTP_PROXY": "private",
        "HTTPS_PROXY": "private",
        "AWS_SESSION_TOKEN": "private",
        "DATABASE_URL": "private",
        "LD_PRELOAD": "untrusted",
        "HOME": "profile-with-netrc",
    }
    assert capture._child_environment(supplied) == {
        "PATH": "runtime-path",
        "SystemRoot": "runtime-root",
        "TEMP": "runtime-temp",
    }


def test_latest_slot_drains_without_inference_and_returns_owned_bgr_copy(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    raw = bytes(range(6)) + bytes(range(6, 12)) + bytes(range(12, 18))
    reader = BlockingReader(raw)
    process = FakeProcess(reader)
    launch = Mock(return_value=process)
    monkeypatch.setattr(capture.subprocess, "Popen", launch)
    instance = pump()
    before = time.time()
    instance.start()
    try:
        assert reader.blocked.wait(2)
        latest = instance.latest()
        assert latest is not None
        sequence, timestamp, frame = latest
        assert sequence == 3
        assert before <= timestamp <= time.time()
        assert frame.shape == (1, 2, 3)
        assert frame.dtype == np.uint8
        assert frame.tolist() == [[[12, 13, 14], [15, 16, 17]]]
        frame[:] = 0
        fresh = instance.latest()
        assert fresh is not None and int(fresh[2][0, 0, 0]) == 12
        command = launch.call_args.args[0]
        assert command[command.index("-i") + 1] == "rtsp://127.0.0.1:8554/camera1"
        assert command[-1] == "pipe:1"
        assert "bgr24" in command and "scale=2:1" in command
        assert "-r" not in command and "-re" not in command
        assert launch.call_args.kwargs["shell"] is False
        assert launch.call_args.kwargs["close_fds"] is True
        assert launch.call_args.kwargs["stderr"] == subprocess.DEVNULL
        with instance._frame_lock:
            instance._last_received -= capture._FRESH_SECONDS + 1
        assert instance.latest() is None
    finally:
        instance.close()
        instance.join(3)
    assert not instance.is_alive()
    assert reader.closed
    assert instance.latest() is None


def test_close_unblocks_read_and_does_not_stop_other_cameras(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    shared_stop = threading.Event()
    reader = BlockingReader()
    process = FakeProcess(reader, needs_kill=True)
    monkeypatch.setattr(capture.subprocess, "Popen", Mock(return_value=process))
    instance = pump(shared_stop)
    instance.start()
    try:
        assert reader.blocked.wait(2)
    finally:
        instance.stop()
        instance.join(3)
    assert not instance.is_alive()
    assert not shared_stop.is_set()
    assert process.terminate_calls == 1
    assert process.kill_calls == 1
    instance.close()  # Idempotent, including after join().
    assert process.kill_calls == 1


def test_global_stop_interrupts_blocked_reader(monkeypatch: pytest.MonkeyPatch) -> None:
    shared_stop = threading.Event()
    reader = BlockingReader()
    process = FakeProcess(reader)
    monkeypatch.setattr(capture.subprocess, "Popen", Mock(return_value=process))
    instance = pump(shared_stop)
    instance.start()
    try:
        assert reader.blocked.wait(2)
        shared_stop.set()
        instance.join(3)
        assert not instance.is_alive()
        assert process.terminate_calls == 1
    finally:
        instance.close()
        instance.join(3)


def test_closed_or_globally_stopped_pump_never_launches(monkeypatch: pytest.MonkeyPatch) -> None:
    launch = Mock()
    monkeypatch.setattr(capture.subprocess, "Popen", launch)
    shared_stop = threading.Event()
    shared_stop.set()
    for instance in (pump(shared_stop), pump()):
        if shared_stop is not instance._global_stop:
            instance.close()
        instance.start()
        instance.join(2)
        assert not instance.is_alive()
    launch.assert_not_called()


def test_failed_launch_reconnects_with_bounded_backoff(monkeypatch: pytest.MonkeyPatch) -> None:
    launch = Mock(side_effect=OSError("synthetic private detail must not be logged"))
    monkeypatch.setattr(capture.subprocess, "Popen", launch)
    instance = pump()
    delays: list[float] = []

    def reconnect(seconds: float) -> bool:
        delays.append(seconds)
        return len(delays) < 6

    monkeypatch.setattr(instance, "_wait_reconnect", reconnect)
    instance.run()
    assert delays == [0.5, 1.0, 2.0, 4.0, 5.0, 5.0]
    assert launch.call_count == 6
    assert instance.latest() is None


def test_stalled_reader_is_reaped_before_reconnect(monkeypatch: pytest.MonkeyPatch) -> None:
    reader = BlockingReader()
    process = FakeProcess(reader)
    monkeypatch.setattr(capture.subprocess, "Popen", Mock(return_value=process))
    monkeypatch.setattr(capture, "_STALL_SECONDS", 0.01)
    instance = pump()
    monkeypatch.setattr(instance, "_wait_reconnect", lambda _seconds: False)
    instance.start()
    try:
        instance.join(3)
        assert not instance.is_alive()
        assert process.terminate_calls == 1
        assert reader.closed
    finally:
        instance.close()
        instance.join(3)


@pytest.mark.parametrize("threads", [0, -1, 65, True])
def test_detector_rejects_unbounded_cpu_configuration(threads: int) -> None:
    with pytest.raises(ValueError, match="cpu_threads"):
        capture.make_detector(threads)


def test_detector_factory_uses_one_cpu_model_with_bounded_properties(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    output = np.zeros((1, 300, 6), dtype=np.float32)
    compiled = Mock(return_value={"output": output})
    compiled.output.return_value = "output"
    core = Mock()
    core.read_model.return_value = "synthetic-model"
    core.compile_model.return_value = compiled
    monkeypatch.setitem(sys.modules, "openvino", SimpleNamespace(Core=Mock(return_value=core)))
    adapter = Mock()
    monkeypatch.setattr(capture, "IntelPersonDetector", adapter)

    assert capture.make_detector(4) is adapter.return_value
    factory = adapter.call_args.kwargs["runner_factory"]
    assert adapter.call_args.kwargs["device"] == "CPU"
    runner = factory(Path("synthetic-not-read.xml"), "CPU")
    blob = np.zeros((1, 3, 640, 640), dtype=np.float32)
    np.testing.assert_array_equal(runner(blob), output)
    np.testing.assert_array_equal(runner(blob), output)
    core.compile_model.assert_called_once_with(
        "synthetic-model",
        "CPU",
        {
            "PERFORMANCE_HINT": "LATENCY",
            "NUM_STREAMS": 1,
            "INFERENCE_NUM_THREADS": 4,
            "ENABLE_CPU_PINNING": False,
        },
    )
    assert compiled.call_count == 2
