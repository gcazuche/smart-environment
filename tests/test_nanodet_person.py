"""Tests for person-only NanoDet decoding without real model inference."""

from __future__ import annotations

import hashlib
from collections.abc import Sequence
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

import numpy as np

from app.vision import NanoDetModelError, NanoDetPersonDetector


class FakeNet:
    def __init__(self, outputs: Sequence[np.ndarray]) -> None:
        self.outputs = outputs
        self.input_shape: tuple[int, ...] | None = None

    def setInput(self, blob: np.ndarray) -> None:  # noqa: N802
        self.input_shape = blob.shape

    def getUnconnectedOutLayersNames(self) -> Sequence[str]:  # noqa: N802
        return tuple(f"output_{index}" for index in range(len(self.outputs)))

    def forward(self, names: Sequence[str]) -> Sequence[np.ndarray]:
        self.assert_names = names
        return self.outputs


def _outputs(*, people: tuple[tuple[int, int, float], ...] = ()) -> list[np.ndarray]:
    outputs: list[np.ndarray] = []
    for level, stride in enumerate((8, 16, 32)):
        feature_size = 416 // stride
        count = feature_size * feature_size
        classes = np.zeros((1, count, 80), dtype=np.float32)
        boxes = np.zeros((1, count, 32), dtype=np.float32)
        for person_level, index, score in people:
            if person_level == level:
                classes[0, index, 0] = score
        outputs.extend((classes, boxes))
    return outputs


class NanoDetPersonTests(TestCase):
    def _detector(
        self,
        directory: str,
        outputs: Sequence[np.ndarray],
    ) -> tuple[NanoDetPersonDetector, FakeNet]:
        model_path = Path(directory) / "model.onnx"
        model_path.write_bytes(b"model for test")
        expected_hash = hashlib.sha256(model_path.read_bytes()).hexdigest()
        fake_net = FakeNet(outputs)
        detector = NanoDetPersonDetector(
            model_path,
            expected_sha256=expected_hash,
            net_factory=lambda _: fake_net,
        )
        return detector, fake_net

    def test_detects_person_and_prepares_fixed_size_blob(self) -> None:
        center_index = 26 * 52 + 26
        with TemporaryDirectory() as directory:
            detector, fake_net = self._detector(
                directory,
                _outputs(people=((0, center_index, 0.9),)),
            )

            detections = detector.detect(np.zeros((416, 416, 3), dtype=np.uint8))

        self.assertEqual(len(detections), 1)
        self.assertEqual(detections[0].source, "nanodet")
        self.assertAlmostEqual(detections[0].score, 0.9, places=5)
        self.assertEqual(fake_net.input_shape, (1, 3, 416, 416))

    def test_ignores_non_person_classes(self) -> None:
        outputs = _outputs()
        outputs[0][0, 100, 1] = 0.99
        with TemporaryDirectory() as directory:
            detector, _ = self._detector(directory, outputs)

            detections = detector.detect(np.zeros((416, 416, 3), dtype=np.uint8))

        self.assertEqual(detections, ())

    def test_keeps_two_separate_people(self) -> None:
        with TemporaryDirectory() as directory:
            detector, _ = self._detector(
                directory,
                _outputs(people=((0, 530, 0.8), (0, 2170, 0.75))),
            )

            detections = detector.detect(np.zeros((416, 416, 3), dtype=np.uint8))

        self.assertEqual(len(detections), 2)

    def test_rejects_missing_or_modified_model(self) -> None:
        with TemporaryDirectory() as directory:
            missing = Path(directory) / "missing.onnx"
            with self.assertRaisesRegex(NanoDetModelError, "modelo NanoDet ausente"):
                NanoDetPersonDetector(missing, net_factory=lambda _: FakeNet([]))

            modified = Path(directory) / "modified.onnx"
            modified.write_bytes(b"unexpected")
            with self.assertRaisesRegex(NanoDetModelError, "hash do modelo"):
                NanoDetPersonDetector(modified, net_factory=lambda _: FakeNet([]))

    def test_rejects_invalid_thresholds(self) -> None:
        with self.assertRaises(ValueError):
            NanoDetPersonDetector(confidence_threshold=0)
