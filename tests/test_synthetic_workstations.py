"""Tests for provisional synthetic workstation provenance."""

from __future__ import annotations

import hashlib
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import cast
from unittest import TestCase

import cv2
import numpy as np

from app.datasets import (
    SYNTHETIC_REFERENCE_IMAGES,
    SyntheticReferenceImage,
    prepare_synthetic_workstation_manifest,
)


def _png() -> bytes:
    image = np.full((18, 30, 3), 110, dtype=np.uint8)
    encoded, payload = cv2.imencode(".png", image)
    if not encoded:
        raise AssertionError("fixture PNG could not be encoded")
    return payload.tobytes()


def _reference(payload: bytes) -> SyntheticReferenceImage:
    return SyntheticReferenceImage(
        filename="synthetic.png",
        sha256=hashlib.sha256(payload).hexdigest(),
        scenario="fixture with laptop visible",
        expected_visible_objects=("laptop",),
        person_visible=True,
    )


class SyntheticWorkstationTests(TestCase):
    def test_manifest_records_provenance_without_activity_labels(self) -> None:
        self.assertEqual(len(SYNTHETIC_REFERENCE_IMAGES), 6)
        self.assertEqual(
            len({item.sha256 for item in SYNTHETIC_REFERENCE_IMAGES}),
            6,
        )
        self.assertFalse(any(item.face_visible for item in SYNTHETIC_REFERENCE_IMAGES))
        payload = _png()
        reference = _reference(payload)
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            (root / reference.filename).write_bytes(payload)

            manifest = prepare_synthetic_workstation_manifest(
                root,
                references=(reference,),
            )

            self.assertEqual(manifest["total_images"], 1)
            self.assertFalse(manifest["contains_real_people"])
            self.assertFalse(manifest["faces_visible"])
            self.assertFalse(manifest["activity_classification_performed"])
            row = cast(list[dict[str, object]], manifest["images"])[0]
            self.assertEqual(row["expected_visible_objects"], ("laptop",))
            self.assertNotIn("productivity_status", row)
            self.assertNotIn("activity_label", row)
            self.assertTrue((root / "source-manifest.json").is_file())

    def test_missing_or_changed_pixels_fail_closed(self) -> None:
        payload = _png()
        reference = _reference(payload)
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            with self.assertRaisesRegex(FileNotFoundError, "sintética ausente"):
                prepare_synthetic_workstation_manifest(root, references=(reference,))

            (root / reference.filename).write_bytes(payload + b"changed")
            with self.assertRaisesRegex(RuntimeError, "hash inesperado"):
                prepare_synthetic_workstation_manifest(root, references=(reference,))
