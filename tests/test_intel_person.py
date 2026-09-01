"""Tests for Intel YOLO26 person-only inference without loading OpenVINO."""

from __future__ import annotations

import hashlib
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

import numpy as np

from app.vision import IntelPersonDetector, IntelPersonModelError


class IntelPersonTests(TestCase):
    def _detector(
        self,
        directory: str,
        output: np.ndarray,
    ) -> tuple[IntelPersonDetector, list[np.ndarray]]:
        model_path = Path(directory) / "model.xml"
        weights_path = model_path.with_suffix(".bin")
        model_path.write_bytes(b"xml model for test")
        weights_path.write_bytes(b"binary weights for test")
        blobs: list[np.ndarray] = []

        def runner(blob: np.ndarray) -> np.ndarray:
            blobs.append(blob)
            return output

        detector = IntelPersonDetector(
            model_path,
            xml_sha256=hashlib.sha256(model_path.read_bytes()).hexdigest(),
            bin_sha256=hashlib.sha256(weights_path.read_bytes()).hexdigest(),
            runner_factory=lambda _path, _device: runner,
        )
        return detector, blobs

    def test_detects_people_and_prepares_openvino_blob(self) -> None:
        output = np.zeros((1, 300, 6), dtype=np.float32)
        output[0, 0] = (64, 128, 320, 512, 0.9, 0)
        output[0, 1] = (320, 160, 640, 640, 0.7, 0)
        with TemporaryDirectory() as directory:
            detector, blobs = self._detector(directory, output)

            detections = detector.detect(np.zeros((480, 800, 3), dtype=np.uint8))

        self.assertEqual(len(detections), 2)
        self.assertEqual(detections[0].source, "intel_yolo26")
        self.assertEqual(detections[0].x, 80)
        self.assertEqual(detections[0].y, 96)
        self.assertEqual(blobs[0].shape, (1, 3, 640, 640))
        self.assertEqual(blobs[0].dtype, np.float32)

    def test_filters_other_classes_low_scores_and_invalid_boxes(self) -> None:
        output = np.array(
            [
                [10, 10, 100, 100, 0.99, 1],
                [10, 10, 100, 100, 0.2, 0],
                [100, 100, 10, 10, 0.99, 0],
                [np.nan, 10, 100, 100, 0.99, 0],
            ],
            dtype=np.float32,
        )
        with TemporaryDirectory() as directory:
            detector, _ = self._detector(directory, output)
            detections = detector.detect(np.zeros((200, 200, 3), dtype=np.uint8))

        self.assertEqual(detections, ())

    def test_rejects_missing_modified_or_unexpected_model(self) -> None:
        with TemporaryDirectory() as directory:
            missing = Path(directory) / "missing.xml"
            with self.assertRaisesRegex(IntelPersonModelError, "modelo Intel ausente"):
                IntelPersonDetector(missing, runner_factory=lambda _path, _device: lambda x: x)

            model_path = Path(directory) / "model.xml"
            model_path.write_bytes(b"unexpected")
            model_path.with_suffix(".bin").write_bytes(b"unexpected")
            with self.assertRaisesRegex(IntelPersonModelError, "hash do modelo Intel"):
                IntelPersonDetector(model_path, runner_factory=lambda _path, _device: lambda x: x)

            output = np.zeros((1, 3, 5), dtype=np.float32)
            detector, _ = self._detector(directory, output)
            with self.assertRaisesRegex(IntelPersonModelError, "saída inesperada"):
                detector.detect(np.zeros((20, 20, 3), dtype=np.uint8))

    def test_rejects_invalid_configuration_and_frame(self) -> None:
        with self.assertRaises(ValueError):
            IntelPersonDetector(confidence_threshold=0)
        with self.assertRaises(ValueError):
            IntelPersonDetector(device="")

        output = np.zeros((1, 300, 6), dtype=np.float32)
        with TemporaryDirectory() as directory:
            detector, _ = self._detector(directory, output)
            with self.assertRaises(ValueError):
                detector.detect(np.zeros((20, 20), dtype=np.uint8))
