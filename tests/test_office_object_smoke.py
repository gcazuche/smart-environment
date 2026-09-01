"""Tests for the offline smoke report and local annotated previews."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

import cv2
import numpy as np

from app.datasets import ReferenceImage
from app.vision import OfficeObjectDetection
from app.vision.office_object_smoke import run_office_object_smoke


def _jpeg() -> bytes:
    image = np.full((24, 40, 3), 180, dtype=np.uint8)
    encoded, payload = cv2.imencode(".jpg", image)
    if not encoded:
        raise AssertionError("fixture JPEG could not be encoded")
    return payload.tobytes()


def _reference(payload: bytes) -> ReferenceImage:
    return ReferenceImage(
        filename="office.jpg",
        sha256=hashlib.sha256(payload).hexdigest(),
        occupancy_status="occupied",
        number_of_people=1,
        desk_count="1",
        lighting_condition="bright",
        seating_arrangement="single",
        equipment_count="1",
        personal_items_count="few",
        noise_level="unknown",
    )


class _FakeDetector:
    confidence_threshold = 0.25
    target_labels: tuple[str, ...] = ("laptop", "mouse", "keyboard", "cell_phone")

    def detect(self, _frame: np.ndarray) -> tuple[OfficeObjectDetection, ...]:
        return (OfficeObjectDetection(2, 3, 10, 8, 0.9, "laptop"),)


class OfficeObjectSmokeTests(TestCase):
    def test_writes_honest_report_and_preview(self) -> None:
        payload = _jpeg()
        reference = _reference(payload)
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            input_directory = root / "input"
            output_directory = root / "output"
            input_directory.mkdir()
            (input_directory / reference.filename).write_bytes(payload)

            report = run_office_object_smoke(
                input_directory,
                output_directory,
                _FakeDetector(),
                references=(reference,),
            )

            saved = json.loads((output_directory / "report.json").read_text("utf-8"))
            self.assertEqual(report["totals_by_label"], saved["totals_by_label"])
            self.assertEqual(saved["totals_by_label"]["laptop"], 1)
            self.assertEqual(saved["dataset_kind"], "public_real_reference")
            self.assertEqual(saved["dataset_license"], "CC-BY-NC-SA-4.0")
            self.assertFalse(saved["activity_classification_performed"])
            self.assertFalse(saved["webcam_opened"])
            self.assertTrue((output_directory / "previews" / "office-objects.jpg").is_file())

    def test_rejects_missing_reference_and_unexpected_label(self) -> None:
        payload = _jpeg()
        reference = _reference(payload)
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            with self.assertRaisesRegex(FileNotFoundError, "referência ausente"):
                run_office_object_smoke(
                    root,
                    root / "output",
                    _FakeDetector(),
                    references=(reference,),
                )

            (root / reference.filename).write_bytes(payload)

            class UnexpectedDetector(_FakeDetector):
                def detect(self, _frame: np.ndarray) -> tuple[OfficeObjectDetection, ...]:
                    return (OfficeObjectDetection(1, 1, 2, 2, 0.9, "person"),)

            with self.assertRaisesRegex(RuntimeError, "fora da lista"):
                run_office_object_smoke(
                    root,
                    root / "output",
                    UnexpectedDetector(),
                    references=(reference,),
                )
