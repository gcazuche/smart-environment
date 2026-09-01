"""Tests for the local, volatile multicamera monitor."""

from __future__ import annotations

from typing import cast
from unittest import TestCase

import numpy as np

from app.activity import NormalizedWorkZone
from app.multicamera_monitor import (
    CameraDefinition,
    CameraStatusStore,
    LatestFrameStore,
    _allowed_frame_request,
    _frame_camera_id,
    encode_annotated_jpeg,
    serve_monitor,
)
from app.vision import Detection, PersonDetector


class MulticameraMonitorTests(TestCase):
    def setUp(self) -> None:
        self.definitions = (
            CameraDefinition("pc", "Webcam do computador", "Escritório", "webcam"),
            CameraDefinition("phone", "Câmera do celular", "Escritório", "mjpeg"),
        )

    def test_snapshot_contains_only_aggregate_camera_fields(self) -> None:
        store = CameraStatusStore(self.definitions)
        store.record_success("pc", people_count=2, backend="dshow", latency_ms=32.14)

        snapshot = store.snapshot()

        self.assertEqual(len(snapshot), 2)
        self.assertEqual(snapshot[0]["people_count"], 2)
        self.assertEqual(snapshot[0]["latency_ms"], 32.1)
        serialized = repr(snapshot)
        self.assertNotIn("frame", serialized)
        self.assertNotIn("192.168", serialized)
        self.assertNotIn("url", serialized.lower())

    def test_snapshot_exposes_only_zone_geometry_and_aggregate_count(self) -> None:
        definitions = (
            CameraDefinition(
                "pc",
                "Webcam do computador",
                "Escritório",
                "webcam",
                NormalizedWorkZone(0.1, 0.2, 0.9, 1.0),
            ),
        )
        store = CameraStatusStore(definitions)
        store.record_success(
            "pc",
            people_count=2,
            people_in_work_zone=1,
            backend="dshow",
            latency_ms=12.0,
        )

        status = store.snapshot()[0]

        self.assertEqual(status["work_zone"], (0.1, 0.2, 0.9, 1.0))
        self.assertEqual(status["people_in_work_zone"], 1)
        self.assertNotIn("person_id", status)
        with self.assertRaises(ValueError):
            store.record_success(
                "pc",
                people_count=1,
                people_in_work_zone=2,
                backend="dshow",
                latency_ms=12.0,
            )
        without_zone = CameraStatusStore(self.definitions)
        with self.assertRaisesRegex(ValueError, "não possui área"):
            without_zone.record_success(
                "pc",
                people_count=1,
                people_in_work_zone=1,
                backend="dshow",
                latency_ms=12.0,
            )

    def test_failure_is_allowlisted_and_drops_stale_count(self) -> None:
        store = CameraStatusStore(self.definitions)
        store.record_success("phone", people_count=1, backend="network", latency_ms=40)
        store.record_failure("phone", "camera_unavailable")

        phone = store.snapshot()[1]

        self.assertEqual(phone["status"], "offline")
        self.assertEqual(phone["people_count"], 0)
        self.assertEqual(phone["error_code"], "camera_unavailable")
        with self.assertRaises(ValueError):
            store.record_failure("phone", "http://secret-camera/video")

    def test_annotated_frame_is_bounded_and_kept_only_in_memory(self) -> None:
        frame = np.zeros((80, 120, 3), dtype=np.uint8)
        jpeg = encode_annotated_jpeg(
            frame,
            (Detection(10, 10, 30, 40, 0.9),),
            work_zone=NormalizedWorkZone(0.1, 0.1, 0.9, 0.9),
        )
        frames = LatestFrameStore(self.definitions)

        frames.record("pc", jpeg)

        self.assertEqual(frames.latest("pc"), jpeg)
        self.assertTrue(jpeg.startswith(b"\xff\xd8"))
        self.assertTrue(jpeg.endswith(b"\xff\xd9"))
        self.assertEqual(int(frame.sum()), 0)
        frames.clear("pc")
        self.assertIsNone(frames.latest("pc"))

    def test_frame_route_requires_local_dashboard_origin(self) -> None:
        self.assertTrue(_allowed_frame_request("http://localhost:3000", None))
        self.assertTrue(_allowed_frame_request(None, "http://127.0.0.1:3000/cameras?selected=pc"))
        self.assertFalse(_allowed_frame_request("https://example.com", None))
        self.assertFalse(_allowed_frame_request(None, None))
        self.assertEqual(_frame_camera_id("/api/cameras/phone/frame.jpg"), "phone")
        self.assertIsNone(_frame_camera_id("/api/cameras/../frame.jpg"))

    def test_server_rejects_public_binding_and_mismatched_factories(self) -> None:
        with self.assertRaisesRegex(ValueError, "127.0.0.1"):
            serve_monitor(
                self.definitions,
                (),
                lambda: cast(PersonDetector, object()),
                host="0.0.0.0",  # noqa: S104 - verifies the fail-closed guard
            )
        with self.assertRaisesRegex(ValueError, "exatamente uma"):
            serve_monitor(self.definitions, (), lambda: cast(PersonDetector, object()))
