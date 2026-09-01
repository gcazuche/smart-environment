"""Tests for restricted office-object inference without loading OpenVINO."""

from __future__ import annotations

import hashlib
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

import numpy as np

from app.vision import OFFICE_OBJECT_CLASSES, IntelOfficeObjectDetector


class OfficeObjectTests(TestCase):
    def _detector(
        self,
        directory: str,
        output: np.ndarray,
        *,
        threshold: float = 0.25,
    ) -> IntelOfficeObjectDetector:
        model_path = Path(directory) / "model.xml"
        weights_path = model_path.with_suffix(".bin")
        model_path.write_bytes(b"xml model for test")
        weights_path.write_bytes(b"binary weights for test")
        return IntelOfficeObjectDetector(
            model_path,
            confidence_threshold=threshold,
            xml_sha256=hashlib.sha256(model_path.read_bytes()).hexdigest(),
            bin_sha256=hashlib.sha256(weights_path.read_bytes()).hexdigest(),
            runner_factory=lambda _path, _device: lambda _blob: output,
        )

    def test_detects_only_reviewed_office_classes(self) -> None:
        output = np.array(
            [
                [64, 128, 320, 512, 0.91, 63],
                [320, 160, 640, 640, 0.72, 67],
                [10, 10, 100, 100, 0.99, 0],
                [10, 10, 100, 100, 0.20, 64],
            ],
            dtype=np.float32,
        )
        with TemporaryDirectory() as directory:
            detector = self._detector(directory, output)
            detections = detector.detect(np.zeros((480, 800, 3), dtype=np.uint8))

        self.assertEqual([item.label for item in detections], ["laptop", "cell_phone"])
        self.assertEqual(detections[0].x, 80)
        self.assertEqual(detections[0].y, 96)
        self.assertEqual(detections[0].source, "intel_yolo26")

    def test_contract_contains_only_four_visual_object_labels(self) -> None:
        self.assertEqual(
            OFFICE_OBJECT_CLASSES,
            {63: "laptop", 64: "mouse", 66: "keyboard", 67: "cell_phone"},
        )
        rendered = repr(OFFICE_OBJECT_CLASSES).lower()
        self.assertNotIn("product", rendered)
        self.assertNotIn("distra", rendered)

    def test_rejects_invalid_threshold_and_frame(self) -> None:
        with self.assertRaises(ValueError):
            IntelOfficeObjectDetector(confidence_threshold=float("nan"))

        output = np.zeros((1, 300, 6), dtype=np.float32)
        with TemporaryDirectory() as directory:
            detector = self._detector(directory, output)
            with self.assertRaises(ValueError):
                detector.detect(np.zeros((20, 20), dtype=np.uint8))
