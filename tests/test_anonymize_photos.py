"""Privacy-profile tests for the local photo anonymizer."""

from __future__ import annotations

import zipfile
from pathlib import Path
from typing import cast

import cv2
import numpy as np
import pytest

from app.cameras.opencv_source import Frame
from app.vision.intel_yolo import IntelYoloDetector, YoloDetection
from scripts.anonymize_photos import (
    AnonymizationError,
    RedactionProfile,
    _decode_image,
    _encode_jpeg,
    _face_regions,
    _image_members,
    _model_regions,
    _safe_member_name,
    anonymize_archive,
)


def _jpeg_with_exif_marker(image: np.ndarray) -> bytes:
    success, encoded = cv2.imencode(".jpg", image)
    if not success:
        raise AssertionError("fixture JPEG could not be encoded")
    clean = encoded.tobytes()
    exif_segment = b"\xff\xe1\x00\x08Exif\x00\x00"
    return clean[:2] + exif_segment + clean[2:]


def test_training_profile_preserves_more_person_and_laptop_area() -> None:
    image = np.zeros((200, 300, 3), dtype=np.uint8)
    detections = (
        YoloDetection(20, 20, 100, 160, 0.90, 0, "person"),
        YoloDetection(150, 50, 100, 100, 0.90, 63, "laptop"),
    )

    publication_screens, _, publication_people, publication_heads = _model_regions(
        image, detections, profile=RedactionProfile.PUBLICATION
    )
    training_screens, _, training_people, training_heads = _model_regions(
        image, detections, profile=RedactionProfile.TRAINING
    )

    assert publication_people == training_people
    assert training_heads[0].height < publication_heads[0].height
    assert training_screens[0].width < publication_screens[0].width
    assert training_screens[0].height < publication_screens[0].height
    assert training_screens[0].x > publication_screens[0].x
    assert training_screens[0].y > publication_screens[0].y


def test_fresh_jpeg_reencode_does_not_copy_metadata_segments() -> None:
    source = np.full((32, 48, 3), (20, 80, 140), dtype=np.uint8)
    metadata_bearing_payload = _jpeg_with_exif_marker(source)
    assert b"Exif\x00\x00" in metadata_bearing_payload

    decoded = _decode_image(metadata_bearing_payload, "authorized-source.jpg")
    reencoded = _encode_jpeg(decoded)

    assert reencoded.startswith(b"\xff\xd8")
    assert b"Exif\x00\x00" not in reencoded
    assert b"http://ns.adobe.com/xap/1.0/" not in reencoded
    for marker in (b"\xff\xe1", b"\xff\xe2", b"\xff\xed", b"\xff\xfe"):
        assert marker not in reencoded
    round_trip = cv2.imdecode(np.frombuffer(reencoded, dtype=np.uint8), cv2.IMREAD_COLOR)
    assert round_trip is not None
    assert round_trip.shape == source.shape


def test_windows_absolute_zip_member_is_rejected() -> None:
    with pytest.raises(AnonymizationError, match="absoluto"):
        _safe_member_name(r"C:\Users\person\private.jpg")


def test_encrypted_zip_member_is_rejected() -> None:
    encrypted = zipfile.ZipInfo("frame.jpg")
    encrypted.flag_bits |= 0x1
    encrypted.file_size = 1

    class ArchiveStub:
        def infolist(self) -> list[zipfile.ZipInfo]:
            return [encrypted]

    with pytest.raises(AnonymizationError, match="criptografado"):
        _image_members(cast(zipfile.ZipFile, ArchiveStub()))


class PhoneOnlyDetector:
    def detect(self, frame: Frame) -> tuple[YoloDetection, ...]:
        del frame
        return (YoloDetection(5, 5, 20, 20, 0.99, 67, "cell_phone"),)


def test_training_manifest_and_readme_do_not_claim_phone_was_blurred(tmp_path: Path) -> None:
    input_zip = tmp_path / "authorized.zip"
    image = np.full((40, 60, 3), 110, dtype=np.uint8)
    success, encoded = cv2.imencode(".jpg", image)
    if not success:
        raise AssertionError("fixture JPEG could not be encoded")
    with zipfile.ZipFile(input_zip, mode="w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("authorized.jpg", encoded.tobytes())

    output_directory = tmp_path / "training-output"
    output_zip = tmp_path / "training-output.zip"
    manifest, _ = anonymize_archive(
        input_zip,
        output_directory,
        output_zip,
        detector=cast(IntelYoloDetector, PhoneOnlyDetector()),
        profile=RedactionProfile.TRAINING,
    )

    privacy = cast(dict[str, object], manifest["privacy"])
    summary = cast(dict[str, object], manifest["summary"])
    assert privacy["phones"] == "training-phone-redaction-disabled-after-human-absence-review"
    assert summary["phones_redacted"] == 0
    readme = (output_directory / "README.txt").read_text(encoding="utf-8")
    assert "redação automática de celular ficou desativada" in readme
    assert "Regiões candidatas de celular também foram redigidas" not in readme
    assert "celulares detectados foram pixelados" not in readme


class CascadeStub:
    def __init__(self, boxes: tuple[tuple[int, int, int, int], ...]) -> None:
        self.boxes = boxes
        self.sources: list[np.ndarray] = []

    def detectMultiScale(self, source: np.ndarray, **kwargs: object) -> np.ndarray:
        del kwargs
        self.sources.append(source.copy())
        return np.asarray(self.boxes, dtype=np.int32).reshape((-1, 4))


def test_profile_cascade_checks_original_and_horizontally_flipped_image() -> None:
    horizontal = np.tile(np.arange(100, dtype=np.uint8), (80, 1))
    image = cv2.cvtColor(horizontal, cv2.COLOR_GRAY2BGR)
    frontal = CascadeStub(())
    alternate = CascadeStub(())
    profile = CascadeStub(((10, 20, 20, 20),))
    cascades = cast(
        tuple[cv2.CascadeClassifier, ...],
        (frontal, alternate, profile),
    )

    regions = _face_regions(image, cascades)

    assert len(profile.sources) == 2
    np.testing.assert_array_equal(profile.sources[1], cv2.flip(profile.sources[0], 1))
    assert len(regions) == 2
    assert regions[0].x < 40
    assert regions[1].x > 60
