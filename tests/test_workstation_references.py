"""Tests for the small, pinned workstation reference dataset."""

from __future__ import annotations

import hashlib
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import cast
from unittest import TestCase
from unittest.mock import patch

import cv2
import numpy as np

from app.datasets import DATASET_LICENSE, REFERENCE_IMAGES, ReferenceImage
from app.datasets.workstation_references import (
    prepare_workstation_references,
    validate_reference_payload,
)


def _jpeg() -> bytes:
    image = np.full((12, 20, 3), 127, dtype=np.uint8)
    encoded, payload = cv2.imencode(".jpg", image)
    if not encoded:
        raise AssertionError("fixture JPEG could not be encoded")
    return payload.tobytes()


def _reference_for(payload: bytes) -> ReferenceImage:
    return ReferenceImage(
        filename="fixture.jpg",
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


class WorkstationReferenceTests(TestCase):
    def test_source_contract_is_small_pinned_and_noncommercial(self) -> None:
        self.assertEqual(len(REFERENCE_IMAGES), 3)
        self.assertEqual(len({item.filename for item in REFERENCE_IMAGES}), 3)
        self.assertEqual(DATASET_LICENSE, "CC-BY-NC-SA-4.0")
        for item in REFERENCE_IMAGES:
            self.assertRegex(item.sha256, r"^[0-9a-f]{64}$")
            self.assertTrue(item.source_url.startswith("https://huggingface.co/"))

    def test_validates_hash_and_jpeg_dimensions(self) -> None:
        payload = _jpeg()

        dimensions = validate_reference_payload(payload, _reference_for(payload))

        self.assertEqual(dimensions, (20, 12))

    def test_rejects_payload_with_unexpected_hash(self) -> None:
        payload = _jpeg()
        reference = _reference_for(payload)

        with self.assertRaisesRegex(RuntimeError, "hash inesperado"):
            validate_reference_payload(payload + b"changed", reference)

    def test_prepares_manifest_without_productivity_claims(self) -> None:
        payload = _jpeg()
        reference = _reference_for(payload)
        with TemporaryDirectory() as temporary_directory:
            output = Path(temporary_directory)
            with (
                patch(
                    "app.datasets.workstation_references.REFERENCE_IMAGES",
                    (reference,),
                ),
                patch(
                    "app.datasets.workstation_references.download_reference_bytes",
                    return_value=payload,
                ) as downloader,
            ):
                summary = prepare_workstation_references(output)

            downloader.assert_called_once()
            self.assertEqual(summary["total_images"], 1)
            self.assertFalse(summary["commercial_use_allowed"])
            image_row = cast(list[dict[str, object]], summary["images"])[0]
            self.assertNotIn("productivity_status", image_row)
            self.assertNotIn("activity_label", image_row)
            self.assertTrue((output / "fixture.jpg").is_file())
            self.assertTrue((output / "source-manifest.json").is_file())

    def test_existing_corrupt_file_fails_closed(self) -> None:
        payload = _jpeg()
        reference = _reference_for(payload)
        with TemporaryDirectory() as temporary_directory:
            output = Path(temporary_directory)
            (output / reference.filename).write_bytes(b"corrupt")
            with (
                patch(
                    "app.datasets.workstation_references.REFERENCE_IMAGES",
                    (reference,),
                ),
                patch("app.datasets.workstation_references.download_reference_bytes") as downloader,
            ):
                with self.assertRaisesRegex(RuntimeError, "hash inesperado"):
                    prepare_workstation_references(output)

            downloader.assert_not_called()
