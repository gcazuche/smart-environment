"""Continuously drain local RTSP video; expose one fresh frame for bounded inference.

No camera credentials, remote URLs, recordings or inference run in the decoder.
The UTC timestamp is local frame receipt time, not a camera-synchronized timestamp.
"""

from __future__ import annotations

import os
import re
import subprocess  # noqa: S404 - trusted executable, fixed local input, no shell
import threading
import time
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any, Protocol

import numpy as np
from numpy.typing import NDArray

from app.cameras.opencv_source import Frame
from app.vision.intel_person import IntelPersonDetector, IntelPersonModelError
from app.vision.intel_yolo import InferenceRunner, RunnerFactory

_STREAM_PATH = re.compile(r"[A-Za-z0-9][A-Za-z0-9_-]{0,63}", re.ASCII)
_FRESH_SECONDS = 2.0
_STALL_SECONDS = 8.0
_POLL_SECONDS = 0.1
_RECONNECT_INITIAL_SECONDS = 0.5
_RECONNECT_MAX_SECONDS = 5.0
_PROCESS_STOP_SECONDS = 1.0
_READER_JOIN_SECONDS = 2.0
_SAFE_ENV_KEYS = frozenset(
    {"PATH", "SYSTEMROOT", "WINDIR", "TEMP", "TMP", "TMPDIR", "LANG", "LC_ALL", "LC_CTYPE"}
)


class _ByteReader(Protocol):
    def read(self, size: int, /) -> bytes: ...


def _read_frame_bytes(source: _ByteReader, size: int, stopped: Callable[[], bool]) -> bytes | None:
    """Assemble exactly one raw frame; partial EOF never becomes a valid image."""

    content = bytearray()
    while len(content) < size and not stopped():
        chunk = source.read(size - len(content))
        if not chunk:
            return None
        content.extend(chunk)
    if stopped() or len(content) != size:
        return None
    return bytes(content)


def _child_environment(environment: Mapping[str, str]) -> dict[str, str]:
    """Allow only runtime essentials, excluding FFREPORT and application credentials."""

    return {key: value for key, value in environment.items() if key.upper() in _SAFE_ENV_KEYS}


class FramePump(threading.Thread):
    """One-shot thread with a single latest-frame slot and a cancellable child process.

    ``start()`` returns without opening a stream in the calling thread. ``close()``
    (also available as ``stop()``) affects only this pump, not the shared stop event.
    Call ``join()`` after closing. A global stop also interrupts a blocked pipe read.
    ``latest()`` returns a caller-owned BGR copy, or None after two seconds/stoppage.
    """

    def __init__(
        self,
        camera_id: str,
        stream_path: str,
        stop_event: threading.Event,
        *,
        ffmpeg_executable: str,
        width: int = 640,
        height: int = 360,
    ) -> None:
        if not isinstance(camera_id, str) or not camera_id or len(camera_id) > 128:
            raise ValueError("ID da câmera inválido")
        if not isinstance(stream_path, str) or _STREAM_PATH.fullmatch(stream_path) is None:
            raise ValueError("caminho de stream local inválido")
        for dimension in (width, height):
            if isinstance(dimension, bool) or not isinstance(dimension, int):
                raise ValueError("dimensões de captura inválidas")
        if not 1 <= width <= 1920 or not 1 <= height <= 1080:
            raise ValueError("dimensões de captura fora do limite")
        if (
            not isinstance(ffmpeg_executable, str)
            or any(ord(character) < 32 for character in ffmpeg_executable)
            or not Path(ffmpeg_executable).is_absolute()
            or Path(ffmpeg_executable).suffix.lower() in {".bat", ".cmd", ".ps1"}
        ):
            raise ValueError("use o caminho absoluto do executável FFmpeg confiável")

        super().__init__(name="server-frame-pump", daemon=True)
        self.camera_id = camera_id
        self.stream_path = stream_path
        self.width = width
        self.height = height
        self._executable = ffmpeg_executable
        self._global_stop = stop_event
        self._closed = threading.Event()
        self._frame_lock = threading.Lock()
        self._process_lock = threading.Lock()
        self._reap_lock = threading.Lock()
        self._process: subprocess.Popen[bytes] | None = None
        self._latest: tuple[int, float, Frame] | None = None
        self._last_received = 0.0
        self._sequence = 0

    def _stopped(self) -> bool:
        return self._closed.is_set() or self._global_stop.is_set()

    def _command(self) -> list[str]:
        return [
            self._executable,
            "-hide_banner",
            "-nostdin",
            "-nostats",
            "-loglevel",
            "error",
            "-rtsp_transport",
            "tcp",
            "-timeout",
            "5000000",
            "-fflags",
            "nobuffer",
            "-flags",
            "low_delay",
            "-probesize",
            "32768",
            "-analyzeduration",
            "1000000",
            "-threads",
            "1",
            "-i",
            f"rtsp://127.0.0.1:8554/{self.stream_path}",
            "-map",
            "0:v:0",
            "-an",
            "-sn",
            "-dn",
            "-vf",
            f"scale={self.width}:{self.height}",
            "-filter_threads",
            "1",
            "-threads:v",
            "1",
            "-pix_fmt",
            "bgr24",
            "-fps_mode",
            "passthrough",
            "-f",
            "rawvideo",
            "pipe:1",
        ]

    def latest(self) -> tuple[int, float, Frame] | None:
        """Return fresh local receipt (sequence, UTC epoch seconds, BGR frame)."""

        with self._frame_lock:
            if (
                self._stopped()
                or self._latest is None
                or time.monotonic() - self._last_received > _FRESH_SECONDS
            ):
                return None
            sequence, timestamp, frame = self._latest
            return sequence, timestamp, frame.copy()

    def _clear_latest(self) -> None:
        with self._frame_lock:
            self._latest = None

    def _launch(self) -> subprocess.Popen[bytes] | None:
        with self._process_lock:
            if self._stopped():
                return None
            # No shell, inherited descriptors, stdin, FFREPORT or application secrets.
            self._process = subprocess.Popen(  # noqa: S603
                self._command(),
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                bufsize=0,
                shell=False,
                close_fds=True,
                env=_child_environment(os.environ),
            )
            return self._process

    def _terminate_process(self) -> None:
        # Serialize close(), global stop and EOF cleanup to avoid double reaping.
        with self._reap_lock:
            with self._process_lock:
                process = self._process
            if process is None:
                return
            try:
                if process.poll() is None:
                    try:
                        process.terminate()
                    except OSError:
                        pass  # It may have exited between poll() and terminate().
                try:
                    process.wait(timeout=_PROCESS_STOP_SECONDS)
                except subprocess.TimeoutExpired:
                    try:
                        process.kill()
                    except OSError:
                        pass
                    try:
                        process.wait(timeout=_PROCESS_STOP_SECONDS)
                    except subprocess.TimeoutExpired:
                        # Do not spawn another child if this one cannot be reaped.
                        self._closed.set()
                        return
            except OSError:
                self._closed.set()
                return
            finally:
                with self._process_lock:
                    if self._process is process and process.poll() is not None:
                        self._process = None

    def close(self) -> None:
        """Request this pump's shutdown and terminate/kill its child with timeouts."""

        self._closed.set()
        self._clear_latest()
        self._terminate_process()

    def stop(self) -> None:
        """Alias for close(); deliberately does not set the shared stop event."""

        self.close()

    def _drain(self, process: subprocess.Popen[bytes], finished: threading.Event) -> None:
        try:
            if process.stdout is None:
                return
            while not self._stopped():
                content = _read_frame_bytes(
                    process.stdout, self.width * self.height * 3, self._stopped
                )
                if content is None:
                    return
                frame = np.frombuffer(content, dtype=np.uint8).reshape((self.height, self.width, 3))
                with self._frame_lock:
                    if self._stopped():
                        return
                    self._sequence += 1
                    self._last_received = time.monotonic()
                    self._latest = self._sequence, time.time(), frame
        except (OSError, ValueError):
            # Stream errors are not logged: FFmpeg errors can contain credentials/URLs.
            return
        finally:
            self._clear_latest()
            finished.set()

    def _watch_reader(
        self, process: subprocess.Popen[bytes], finished: threading.Event, started: float
    ) -> None:
        while not finished.wait(_POLL_SECONDS):
            if self._stopped() or process.poll() is not None:
                return
            with self._frame_lock:
                last_received = max(started, self._last_received)
            if time.monotonic() - last_received > _STALL_SECONDS:
                return

    def _wait_reconnect(self, seconds: float) -> bool:
        deadline = time.monotonic() + seconds
        while not self._stopped():
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                return True
            self._closed.wait(min(remaining, _POLL_SECONDS))
        return False

    def run(self) -> None:
        reconnect_delay = _RECONNECT_INITIAL_SECONDS
        try:
            while not self._stopped():
                started = time.monotonic()
                try:
                    process = self._launch()
                except OSError:
                    process = None
                if process is not None:
                    finished = threading.Event()
                    reader = threading.Thread(
                        target=self._drain,
                        args=(process, finished),
                        name="server-frame-reader",
                        daemon=True,
                    )
                    reader.start()
                    try:
                        self._watch_reader(process, finished, started)
                    finally:
                        self._terminate_process()
                        reader.join(_READER_JOIN_SECONDS)
                        if reader.is_alive():
                            # Never stack readers/processes after an abnormal shutdown.
                            self._closed.set()
                        elif process.stdout is not None:
                            process.stdout.close()
                    if time.monotonic() - started >= _STALL_SECONDS:
                        reconnect_delay = _RECONNECT_INITIAL_SECONDS
                self._clear_latest()
                if not self._wait_reconnect(reconnect_delay):
                    break
                reconnect_delay = min(reconnect_delay * 2, _RECONNECT_MAX_SECONDS)
        finally:
            self.close()


def _cpu_runner_factory(cpu_threads: int) -> RunnerFactory:
    def factory(model_path: Path, device: str) -> InferenceRunner:
        try:
            import openvino as ov  # type: ignore[import-untyped]
        except ModuleNotFoundError:
            raise IntelPersonModelError("OpenVINO ausente no ambiente do servidor") from None

        try:
            core = ov.Core()
            compiled = core.compile_model(
                core.read_model(model_path),
                device,
                {
                    "PERFORMANCE_HINT": "LATENCY",
                    "NUM_STREAMS": 1,
                    "INFERENCE_NUM_THREADS": cpu_threads,
                    "ENABLE_CPU_PINNING": False,
                },
            )
            output_port = compiled.output(0)
        except Exception:
            raise IntelPersonModelError("não foi possível carregar o modelo Intel local") from None

        def run(blob: NDArray[Any]) -> NDArray[Any]:
            try:
                return np.asarray(compiled([blob])[output_port])
            except Exception:
                raise IntelPersonModelError("falha local durante a inferência Intel") from None

        return run

    return factory


def make_detector(cpu_threads: int = 4) -> IntelPersonDetector:
    """Compile once for the main sequential inference loop, not once per camera.

    The caller owns cadence/fairness (at most two fresh frames/s/camera) and must
    not invoke this detector concurrently. Existing model integrity checks remain.
    Tests can replace IntelPersonDetector/Core without installing/loading a model.
    """

    if (
        isinstance(cpu_threads, bool)
        or not isinstance(cpu_threads, int)
        or not 1 <= cpu_threads <= 64
    ):
        raise ValueError("cpu_threads deve estar entre 1 e 64")
    return IntelPersonDetector(device="CPU", runner_factory=_cpu_runner_factory(cpu_threads))
