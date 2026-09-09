"""One shared CPU model, latest frames only, metadata-only durable delivery."""

from __future__ import annotations

import threading
import time
from datetime import UTC, datetime
from typing import Any

from app.server.capture import FramePump, make_detector
from app.server.config import Settings
from app.server.gateway import Gateway, Server
from app.server.supabase import Supabase
from app.server.telemetry import Telemetry


class Runtime:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.backend = Supabase(settings)
        self.stop = threading.Event()
        self.lock = threading.RLock()
        self.catalog: dict[str, dict[str, Any]] = {}
        self.rules: list[dict[str, Any]] = []
        self.catalog_at = 0.0
        self.network_error: str | None = None
        self.readings: dict[str, dict[str, Any]] = {}
        self.telemetry = Telemetry(settings.organization_id, settings.database)
        self.gateway = Gateway(settings, self.backend, self)

    def available(self, camera_id: str) -> bool:
        with self.lock:
            return (
                not self.stop.is_set()
                and time.monotonic() - self.catalog_at < 30
                and camera_id in self.catalog
                and camera_id in self.settings.streams
            )

    def cameras(self) -> list[dict[str, Any]]:
        with self.lock:
            result = []
            for camera in self.catalog.values():
                reading = self.readings.get(camera["id"], {})
                fresh = (
                    self.available(camera["id"]) and time.time() - reading.get("captured_at", 0) < 2
                )
                result.append(
                    {
                        "camera_id": camera["id"],
                        "name": camera["name"],
                        "environment_id": camera["environment_id"],
                        "source": camera["source"],
                        "configured": self.available(camera["id"]),
                        "status": "online" if fresh else "waiting",
                        "people_count": reading.get("people_count") if fresh else None,
                        "boxes": reading.get("boxes", []) if fresh else [],
                        "last_seen_at": reading.get("last_seen_at") if fresh else None,
                        "latency_ms": reading.get("latency_ms") if fresh else None,
                        "inference_fps": reading.get("inference_fps") if fresh else None,
                        "detector": "intel_yolo26",
                        "backend": "servidor CPU",
                    }
                )
            return result

    def health(self) -> dict[str, Any]:
        return {
            "catalog_ready": time.monotonic() - self.catalog_at < 30,
            "analysis_target_fps": self.settings.analysis_fps,
            "network_error": self.network_error,
            "delivery": self.telemetry.stats(),
        }

    def network_loop(self) -> None:
        next_catalog = 0.0
        while not self.stop.is_set():
            if time.monotonic() >= next_catalog:
                try:
                    cameras, rules = self.backend.catalog()
                    with self.lock:
                        fresh_catalog = {item["id"]: item for item in cameras}
                        self.readings = {
                            key: value
                            for key, value in self.readings.items()
                            if fresh_catalog.get(key) == self.catalog.get(key)
                        }
                        self.catalog = fresh_catalog
                        self.rules = rules
                        self.catalog_at = time.monotonic()
                        self.network_error = None
                except Exception:
                    self.network_error = "catalog_unavailable"
                next_catalog = time.monotonic() + 10
            self.stop.wait(1)

    def delivery_loop(self) -> None:
        while not self.stop.is_set():
            try:
                self.telemetry.flush(self.backend.deliver, datetime.now(UTC))
            except Exception:
                self.network_error = "delivery_unavailable"
            self.stop.wait(1)

    def run(self) -> None:
        import imageio_ffmpeg  # type: ignore[import-untyped]

        detector = make_detector(self.settings.cpu_threads)
        ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
        server = Server(self.gateway)
        network = threading.Thread(target=self.network_loop, name="metadata-delivery", daemon=True)
        delivery = threading.Thread(target=self.delivery_loop, name="outbox-delivery", daemon=True)
        http = threading.Thread(target=server.serve_forever, name="authenticated-api", daemon=True)

        def watch_video() -> None:
            while not self.stop.wait(2):
                self.gateway.expire()

        watchdog = threading.Thread(target=watch_video, name="video-authorization", daemon=True)
        network.start()
        delivery.start()
        http.start()
        watchdog.start()
        pumps: dict[str, FramePump] = {}
        sequences: dict[str, int] = {}
        next_analysis: dict[str, float] = {}
        previous_capture: dict[str, float] = {}
        try:
            print("Servidor CPU ativo em loopback:8766; use o proxy HTTPS para acessar.")
            while not self.stop.is_set():
                with self.lock:
                    active = {
                        key: dict(value)
                        for key, value in self.catalog.items()
                        if self.available(key)
                    }
                    rules = list(self.rules)
                for camera_id in list(pumps):
                    if camera_id not in active:
                        pumps.pop(camera_id).close()
                        sequences.pop(camera_id, None)
                        with self.lock:
                            self.readings.pop(camera_id, None)
                for camera_id, camera in active.items():
                    if camera_id not in pumps:
                        pump = FramePump(
                            camera_id,
                            self.settings.streams[camera_id],
                            self.stop,
                            ffmpeg_executable=ffmpeg,
                        )
                        pumps[camera_id] = pump
                        pump.start()
                    if time.monotonic() < next_analysis.get(camera_id, 0):
                        continue
                    next_analysis[camera_id] = time.monotonic() + 1 / self.settings.analysis_fps
                    latest = pumps[camera_id].latest()
                    if latest is None or time.time() - latest[1] > 2:
                        self.telemetry.observe(camera, None, datetime.now(UTC), rules)
                        continue
                    sequence, captured_at, frame = latest
                    if sequences.get(camera_id) == sequence:
                        continue
                    sequences[camera_id] = sequence
                    started = time.perf_counter()
                    try:
                        detections = detector.detect(frame)
                    except Exception:
                        self.telemetry.observe(camera, None, datetime.now(UTC), rules)
                        continue
                    if time.time() - captured_at > 2 or not self.available(camera_id):
                        continue
                    height, width = frame.shape[:2]
                    boxes = [
                        {
                            "x": max(0, item.x / width),
                            "y": max(0, item.y / height),
                            "width": min(item.width, width - max(0, item.x)) / width,
                            "height": min(item.height, height - max(0, item.y)) / height,
                        }
                        for item in detections
                    ]
                    observed = datetime.fromtimestamp(captured_at, UTC)
                    previous = previous_capture.get(camera_id)
                    with self.lock:
                        if self.catalog.get(camera_id) != camera:
                            continue
                        self.readings[camera_id] = {
                            "captured_at": captured_at,
                            "last_seen_at": observed.isoformat(),
                            "people_count": len(detections),
                            "boxes": boxes,
                            "latency_ms": round((time.perf_counter() - started) * 1000, 1),
                            "inference_fps": round(1 / (captured_at - previous), 2)
                            if previous and captured_at > previous
                            else None,
                        }
                    previous_capture[camera_id] = captured_at
                    self.telemetry.observe(camera, len(detections), observed, rules)
                self.telemetry.tick(datetime.now(UTC))
                self.stop.wait(0.02)
        finally:
            self.stop.set()
            server.shutdown()
            for pump in pumps.values():
                pump.close()
            for pump in pumps.values():
                pump.join(timeout=4)
            watchdog.join(timeout=12)
            self.gateway.expire(all_sessions=True)
            server.server_close()
            network.join(timeout=20)
            delivery.join(timeout=20)
            self.telemetry.close()
