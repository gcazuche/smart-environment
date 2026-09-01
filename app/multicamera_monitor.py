"""Two-camera local monitor exposing only aggregate status to the dashboard."""

from __future__ import annotations

import json
import time
from collections.abc import Callable, Sequence
from dataclasses import asdict, dataclass, replace
from datetime import UTC, datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Event, Lock, Thread
from typing import Protocol, cast
from urllib.parse import urlsplit

import cv2

from app.activity import NormalizedWorkZone, detections_in_work_zone
from app.cameras.opencv_source import Frame
from app.live_detection import annotate_frame
from app.vision import Detection, PersonDetector


class CameraLike(Protocol):
    backend_name: str | None

    def open(self) -> None: ...

    def read(self) -> Frame: ...

    def close(self) -> None: ...


@dataclass(frozen=True, slots=True)
class CameraDefinition:
    camera_id: str
    name: str
    environment: str
    source: str
    work_zone: NormalizedWorkZone | None = None


@dataclass(frozen=True, slots=True)
class CameraStatus:
    camera_id: str
    name: str
    environment: str
    source: str
    status: str = "starting"
    people_count: int = 0
    last_seen_at: str | None = None
    detector: str = "intel_yolo26"
    backend: str = "unknown"
    latency_ms: float | None = None
    error_code: str | None = None
    work_zone: tuple[float, float, float, float] | None = None
    people_in_work_zone: int | None = None


class CameraStatusStore:
    """Keep a bounded, in-memory status record; never accept pixels or camera URLs."""

    def __init__(self, definitions: Sequence[CameraDefinition]) -> None:
        self._lock = Lock()
        self._statuses = {
            item.camera_id: CameraStatus(
                camera_id=item.camera_id,
                name=item.name,
                environment=item.environment,
                source=item.source,
                work_zone=item.work_zone.as_tuple() if item.work_zone is not None else None,
            )
            for item in definitions
        }

    def record_success(
        self,
        camera_id: str,
        *,
        people_count: int,
        backend: str,
        latency_ms: float,
        people_in_work_zone: int | None = None,
    ) -> None:
        if people_count < 0 or latency_ms < 0:
            raise ValueError("métrica de câmera inválida")
        if people_in_work_zone is not None and not 0 <= people_in_work_zone <= people_count:
            raise ValueError("contagem da área de trabalho inválida")
        with self._lock:
            current = self._statuses[camera_id]
            if people_in_work_zone is not None and current.work_zone is None:
                raise ValueError("câmera não possui área de trabalho configurada")
            self._statuses[camera_id] = replace(
                current,
                status="online",
                people_count=people_count,
                last_seen_at=datetime.now(UTC).isoformat(),
                backend=backend,
                latency_ms=round(latency_ms, 1),
                error_code=None,
                people_in_work_zone=people_in_work_zone,
            )

    def record_failure(self, camera_id: str, error_code: str) -> None:
        if error_code not in {"camera_unavailable", "frame_unavailable", "detector_unavailable"}:
            raise ValueError("código de falha não permitido")
        with self._lock:
            current = self._statuses[camera_id]
            self._statuses[camera_id] = replace(
                current,
                status="offline",
                people_count=0,
                latency_ms=None,
                error_code=error_code,
                people_in_work_zone=None,
            )

    def snapshot(self) -> tuple[dict[str, object], ...]:
        with self._lock:
            ordered = sorted(self._statuses.values(), key=lambda item: item.camera_id)
            return tuple(asdict(item) for item in ordered)


class LatestFrameStore:
    """Keep one bounded annotated JPEG per camera in volatile memory only."""

    def __init__(self, definitions: Sequence[CameraDefinition]) -> None:
        self._lock = Lock()
        self._frames: dict[str, bytes | None] = {item.camera_id: None for item in definitions}

    def record(self, camera_id: str, jpeg: bytes) -> None:
        if not jpeg or len(jpeg) > 2_000_000:
            raise ValueError("frame JPEG vazio ou acima do limite")
        with self._lock:
            if camera_id not in self._frames:
                raise KeyError(camera_id)
            self._frames[camera_id] = jpeg

    def clear(self, camera_id: str) -> None:
        with self._lock:
            if camera_id not in self._frames:
                raise KeyError(camera_id)
            self._frames[camera_id] = None

    def latest(self, camera_id: str) -> bytes | None:
        with self._lock:
            if camera_id not in self._frames:
                return None
            return self._frames[camera_id]


def encode_annotated_jpeg(
    frame: Frame,
    detections: tuple[Detection, ...],
    *,
    work_zone: NormalizedWorkZone | None = None,
) -> bytes:
    """Render detection boxes and encode a browser-sized in-memory JPEG."""

    annotated = annotate_frame(
        frame,
        detections,
        work_zone=work_zone,
        include_exit_hint=False,
    )
    height, width = annotated.shape[:2]
    if width > 960:
        target_height = max(1, round(height * (960 / width)))
        annotated = cast(
            Frame,
            cv2.resize(annotated, (960, target_height), interpolation=cv2.INTER_AREA),
        )
    encoded, buffer = cv2.imencode(".jpg", annotated, [cv2.IMWRITE_JPEG_QUALITY, 78])
    if not encoded:
        raise RuntimeError("não foi possível codificar o frame local")
    return bytes(buffer)


CameraFactory = Callable[[], CameraLike]
DetectorFactory = Callable[[], PersonDetector]


class CameraWorker(Thread):
    def __init__(
        self,
        definition: CameraDefinition,
        camera_factory: CameraFactory,
        detector_factory: DetectorFactory,
        store: CameraStatusStore,
        frame_store: LatestFrameStore,
        stop_event: Event,
        *,
        interval_seconds: float,
        retry_seconds: float = 3.0,
    ) -> None:
        super().__init__(name=f"camera-{definition.camera_id}", daemon=True)
        self._definition = definition
        self._camera_factory = camera_factory
        self._detector_factory = detector_factory
        self._store = store
        self._frame_store = frame_store
        self._stop_event = stop_event
        self._interval_seconds = interval_seconds
        self._retry_seconds = retry_seconds

    def run(self) -> None:
        while not self._stop_event.is_set():
            camera = self._camera_factory()
            try:
                detector = self._detector_factory()
                camera.open()
                while not self._stop_event.is_set():
                    frame = camera.read()
                    started = time.perf_counter()
                    detections = detector.detect(frame)
                    latency_ms = (time.perf_counter() - started) * 1000
                    frame_height, frame_width = frame.shape[:2]
                    people_in_work_zone = (
                        len(
                            detections_in_work_zone(
                                detections,
                                self._definition.work_zone,
                                frame_width=frame_width,
                                frame_height=frame_height,
                            )
                        )
                        if self._definition.work_zone is not None
                        else None
                    )
                    self._frame_store.record(
                        self._definition.camera_id,
                        encode_annotated_jpeg(
                            frame,
                            detections,
                            work_zone=self._definition.work_zone,
                        ),
                    )
                    self._store.record_success(
                        self._definition.camera_id,
                        people_count=len(detections),
                        backend=camera.backend_name or "unknown",
                        latency_ms=latency_ms,
                        people_in_work_zone=people_in_work_zone,
                    )
                    self._stop_event.wait(self._interval_seconds)
            except Exception as exc:
                error_code = (
                    "detector_unavailable"
                    if "model" in type(exc).__name__.lower()
                    else "camera_unavailable"
                )
                self._store.record_failure(self._definition.camera_id, error_code)
                self._frame_store.clear(self._definition.camera_id)
            finally:
                camera.close()
            self._stop_event.wait(self._retry_seconds)


_ALLOWED_ORIGINS = {"http://localhost:3000", "http://127.0.0.1:3000"}


def _allowed_frame_request(origin: str | None, referer: str | None) -> bool:
    if origin is not None:
        return origin in _ALLOWED_ORIGINS
    if referer is None:
        return False
    parsed = urlsplit(referer)
    return f"{parsed.scheme}://{parsed.netloc}" in _ALLOWED_ORIGINS


def _frame_camera_id(path: str) -> str | None:
    prefix = "/api/cameras/"
    suffix = "/frame.jpg"
    if not path.startswith(prefix) or not path.endswith(suffix):
        return None
    camera_id = path[len(prefix) : -len(suffix)]
    valid = (
        camera_id
        and len(camera_id) <= 64
        and camera_id.isascii()
        and all(character.isalnum() or character in "_-" for character in camera_id)
    )
    return camera_id if valid else None


def _handler_for(
    store: CameraStatusStore, frame_store: LatestFrameStore
) -> type[BaseHTTPRequestHandler]:
    class CameraStatusHandler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802
            path = urlsplit(self.path).path
            if path == "/health":
                self._write_json({"status": "ok"})
                return
            if path == "/api/cameras":
                self._write_json({"cameras": store.snapshot()})
                return
            camera_id = _frame_camera_id(path)
            if camera_id is not None:
                self._write_frame(camera_id)
                return
            self.send_error(404)

        def do_OPTIONS(self) -> None:  # noqa: N802
            self.send_response(204)
            self._write_security_headers()
            self.end_headers()

        def _write_json(self, payload: object) -> None:
            body = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self._write_security_headers()
            self.end_headers()
            self.wfile.write(body)

        def _write_frame(self, camera_id: str) -> None:
            if not _allowed_frame_request(self.headers.get("Origin"), self.headers.get("Referer")):
                self.send_error(403)
                return
            jpeg = frame_store.latest(camera_id)
            if jpeg is None:
                self.send_error(503)
                return
            self.send_response(200)
            self.send_header("Content-Type", "image/jpeg")
            self.send_header("Content-Length", str(len(jpeg)))
            self._write_security_headers()
            self.end_headers()
            self.wfile.write(jpeg)

        def _write_security_headers(self) -> None:
            origin = self.headers.get("Origin")
            if origin in _ALLOWED_ORIGINS:
                self.send_header("Access-Control-Allow-Origin", origin)
                self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
                self.send_header("Vary", "Origin")
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")

        def log_message(self, format: str, *args: object) -> None:
            del format, args

    return CameraStatusHandler


def serve_monitor(
    definitions: Sequence[CameraDefinition],
    camera_factories: Sequence[CameraFactory],
    detector_factory: DetectorFactory,
    *,
    host: str = "127.0.0.1",
    port: int = 8765,
    interval_seconds: float = 0.25,
) -> None:
    """Run camera workers and a loopback-only aggregate JSON service."""

    if host != "127.0.0.1":
        raise ValueError("o serviço de teste deve usar somente 127.0.0.1")
    if not 1024 <= port <= 65535:
        raise ValueError("porta deve estar entre 1024 e 65535")
    if len(definitions) != len(camera_factories) or not definitions:
        raise ValueError("cada câmera deve possuir exatamente uma fábrica")
    if not 0.1 <= interval_seconds <= 5:
        raise ValueError("intervalo deve estar entre 0,1 e 5 segundos")

    store = CameraStatusStore(definitions)
    frame_store = LatestFrameStore(definitions)
    stop_event = Event()
    workers = [
        CameraWorker(
            definition,
            camera_factory,
            detector_factory,
            store,
            frame_store,
            stop_event,
            interval_seconds=interval_seconds,
        )
        for definition, camera_factory in zip(definitions, camera_factories, strict=True)
    ]
    server = ThreadingHTTPServer((host, port), _handler_for(store, frame_store))
    for worker in workers:
        worker.start()
    try:
        server.serve_forever(poll_interval=0.25)
    finally:
        stop_event.set()
        server.shutdown()
        server.server_close()
        for worker in workers:
            worker.join(timeout=5)
