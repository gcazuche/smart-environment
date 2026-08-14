"""Tests for person-detection normalization without a model or webcam."""

from __future__ import annotations

from collections.abc import Sequence
from unittest import TestCase

import numpy as np

from app.cameras.opencv_source import Frame
from app.vision import Detection, HogPersonDetector


class FakeHog:
    def __init__(self, boxes: Sequence[Sequence[int]], weights: Sequence[float]) -> None:
        self.boxes = boxes
        self.weights = weights
        self.arguments: tuple[tuple[int, int], tuple[int, int], float] | None = None

    def setSVMDetector(self, detector: object) -> None:  # noqa: N802
        del detector

    def detectMultiScale(  # noqa: N802
        self,
        image: Frame,
        *,
        winStride: tuple[int, int],
        padding: tuple[int, int],
        scale: float,
    ) -> tuple[Sequence[Sequence[int]], Sequence[float]]:
        del image
        self.arguments = winStride, padding, scale
        return self.boxes, self.weights


class PersonDetectionTests(TestCase):
    def test_detects_zero_people(self) -> None:
        fake = FakeHog([], [])
        detector = HogPersonDetector(hog_factory=lambda: fake)

        self.assertEqual(detector.detect(np.zeros((100, 100, 3), dtype=np.uint8)), ())
        self.assertEqual(fake.arguments, ((8, 8), (8, 8), 1.05))

    def test_clips_boxes_and_discards_nested_candidate(self) -> None:
        fake = FakeHog(
            [(-5, -10, 60, 120), (10, 10, 20, 30), (200, 200, 10, 10)],
            [0.7, 0.9, 1.0],
        )
        detector = HogPersonDetector(hog_factory=lambda: fake)

        detections = detector.detect(np.zeros((100, 100, 3), dtype=np.uint8))

        self.assertEqual(detections, (Detection(0, 0, 55, 100, 0.7),))

    def test_orders_multiple_people_by_detector_margin(self) -> None:
        fake = FakeHog([(0, 0, 20, 30), (50, 20, 30, 50)], [0.2, 0.8])
        detector = HogPersonDetector(hog_factory=lambda: fake)

        detections = detector.detect(np.zeros((100, 100, 3), dtype=np.uint8))

        self.assertEqual([item.score for item in detections], [0.8, 0.2])

    def test_rejects_non_color_frame(self) -> None:
        detector = HogPersonDetector(hog_factory=lambda: FakeHog([], []))

        with self.assertRaises(ValueError):
            detector.detect(np.zeros((10, 10), dtype=np.uint8))
