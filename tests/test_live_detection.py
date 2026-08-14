"""Tests for the bounded local processing loop."""

from __future__ import annotations

from unittest import TestCase

import numpy as np

from app.cameras.opencv_source import Frame
from app.live_detection import annotate_frame, run_person_detection
from app.vision import Detection


class FakeCamera:
    def __init__(self) -> None:
        self.backend_name: str | None = "fake"
        self.opened = False
        self.closed = False
        self.frame = np.zeros((80, 120, 3), dtype=np.uint8)

    def open(self) -> None:
        self.opened = True

    def read(self) -> Frame:
        return self.frame

    def close(self) -> None:
        self.closed = True


class FakeDetector:
    def __init__(self, detections: tuple[Detection, ...] = ()) -> None:
        self.detections = detections
        self.calls = 0

    def detect(self, frame: Frame) -> tuple[Detection, ...]:
        del frame
        self.calls += 1
        return self.detections


class FakeDisplay:
    def __init__(self, *, stop_on: int | None = None) -> None:
        self.stop_on = stop_on
        self.shown = 0
        self.closed = False

    def show(self, frame: Frame) -> bool:
        del frame
        self.shown += 1
        return self.shown == self.stop_on

    def close(self) -> None:
        self.closed = True


class LiveDetectionTests(TestCase):
    def test_stops_at_frame_limit_and_releases_resources(self) -> None:
        camera = FakeCamera()
        detector = FakeDetector((Detection(1, 2, 10, 20, 0.8),))
        display = FakeDisplay()

        summary = run_person_detection(camera, detector, display, max_frames=3)

        self.assertEqual(summary.frames_processed, 3)
        self.assertEqual(summary.last_count, 1)
        self.assertEqual(summary.max_count, 1)
        self.assertEqual(summary.stopped_by, "frame_limit")
        self.assertTrue(camera.closed)
        self.assertTrue(display.closed)

    def test_operator_can_stop_display(self) -> None:
        camera = FakeCamera()
        display = FakeDisplay(stop_on=2)

        summary = run_person_detection(camera, FakeDetector(), display, max_frames=10)

        self.assertEqual(summary.frames_processed, 2)
        self.assertEqual(summary.stopped_by, "operator")

    def test_releases_resources_when_detector_fails(self) -> None:
        camera = FakeCamera()
        display = FakeDisplay()

        class BrokenDetector:
            def detect(self, frame: Frame) -> tuple[Detection, ...]:
                del frame
                raise RuntimeError("falha simulada")

        with self.assertRaises(RuntimeError):
            run_person_detection(camera, BrokenDetector(), display, max_frames=1)

        self.assertTrue(camera.closed)
        self.assertTrue(display.closed)

    def test_annotation_does_not_modify_original(self) -> None:
        frame = np.zeros((80, 120, 3), dtype=np.uint8)

        annotated = annotate_frame(
            frame,
            (
                Detection(10, 10, 30, 40, 0.8),
                Detection(60, 10, 25, 25, 0.5, "upper_body"),
            ),
        )

        self.assertFalse(np.array_equal(annotated, frame))
        self.assertEqual(int(frame.sum()), 0)

    def test_non_positive_limit_is_rejected_before_opening(self) -> None:
        camera = FakeCamera()

        with self.assertRaises(ValueError):
            run_person_detection(camera, FakeDetector(), FakeDisplay(), max_frames=0)

        self.assertFalse(camera.opened)
