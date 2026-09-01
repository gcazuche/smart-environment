"""Focused contracts for the authorized workstation prelabel pipeline."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import cv2
import numpy as np
import pytest

from app.cameras.opencv_source import Frame
from app.datasets.authorized_workstations import (
    COCO_PRELABEL_CLASSES,
    DATASET_CLASSES,
    AuthorizedDatasetError,
    Prelabel,
    SceneGroup,
    _decode_anonymized_jpeg,
    _source_images,
    _validate_scene_groups,
    _validate_source_manifest,
    prepare_authorized_workstation_prelabels,
    suppress_duplicate_prelabels,
)
from app.vision.intel_yolo import YoloDetection


def _jpeg(*, value: int = 127, width: int = 200, height: int = 100) -> bytes:
    image = np.full((height, width, 3), value, dtype=np.uint8)
    success, encoded = cv2.imencode(".jpg", image)
    if not success:
        raise AssertionError("fixture JPEG could not be encoded")
    return encoded.tobytes()


def _write_source(
    source: Path,
    *,
    profile: str = "training",
    payloads: tuple[bytes, ...] | None = None,
) -> None:
    source.mkdir()
    frames = payloads or (_jpeg(value=40), _jpeg(value=120), _jpeg(value=200))
    image_rows: list[dict[str, object]] = []
    for number, payload in enumerate(frames, start=1):
        filename = f"frame_{number:03d}.jpg"
        (source / filename).write_bytes(payload)
        decoded = cv2.imdecode(np.frombuffer(payload, dtype=np.uint8), cv2.IMREAD_COLOR)
        if decoded is None:
            raise AssertionError("fixture JPEG could not be decoded")
        image_rows.append(
            {
                "file": filename,
                "sha256": hashlib.sha256(payload).hexdigest(),
                "width": int(decoded.shape[1]),
                "height": int(decoded.shape[0]),
            }
        )
    manifest = {
        "redaction_profile": profile,
        "summary": {"images": len(frames)},
        "privacy": {"metadata": "fresh-jpeg-reencode; exif-xmp-icc-not-copied"},
        "images": image_rows,
    }
    (source / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8", newline="\n")


def _three_split_scenes() -> tuple[SceneGroup, ...]:
    return (
        SceneGroup("scene-train", "train", (1,), (1,)),
        SceneGroup("scene-val", "val", (2,), (2,)),
        SceneGroup("scene-test", "test", (3,), (3,)),
    )


class FakeDetector:
    """Return reviewed COCO candidates plus duplicates and an excluded phone."""

    def __init__(self) -> None:
        self.frame_shapes: list[tuple[int, ...]] = []

    def detect(self, frame: Frame) -> tuple[YoloDetection, ...]:
        self.frame_shapes.append(frame.shape)
        return (
            YoloDetection(10, 20, 80, 70, 0.90, 0, "person"),
            YoloDetection(12, 22, 80, 70, 0.80, 0, "person"),
            YoloDetection(100, 30, 80, 50, 0.70, 63, "laptop"),
            YoloDetection(160, 80, 20, 10, 0.40, 64, "mouse"),
            YoloDetection(100, 75, 50, 10, 0.40, 66, "keyboard"),
            YoloDetection(50, 10, 20, 30, 0.99, 67, "cell_phone"),
        )


class EmptyDetector:
    """Represent a valid prelabel pass that finds none of the four classes."""

    def detect(self, frame: Frame) -> tuple[YoloDetection, ...]:
        del frame
        return ()


def test_class_contract_is_exact_and_has_no_cell_phone() -> None:
    assert dict(DATASET_CLASSES) == {
        0: "person",
        1: "laptop",
        2: "mouse",
        3: "keyboard",
    }
    assert dict(COCO_PRELABEL_CLASSES) == {
        0: "person",
        63: "laptop",
        64: "mouse",
        66: "keyboard",
    }
    assert "cell_phone" not in DATASET_CLASSES.values()
    assert "cell_phone" not in COCO_PRELABEL_CLASSES.values()


def test_nms_is_class_aware_and_stable_when_scores_tie() -> None:
    preferred = Prelabel(0, "person", 10, 10, 40, 40, 0.90)
    same_class_duplicate = Prelabel(0, "person", 12, 12, 40, 40, 0.90)
    overlapping_other_class = Prelabel(1, "laptop", 10, 10, 40, 40, 0.90)

    forward = suppress_duplicate_prelabels(
        (same_class_duplicate, overlapping_other_class, preferred)
    )
    reverse = suppress_duplicate_prelabels(
        (preferred, overlapping_other_class, same_class_duplicate)
    )

    assert forward == reverse
    assert preferred in forward
    assert same_class_duplicate not in forward
    assert overlapping_other_class in forward


def test_scene_plan_requires_unique_exact_coverage_across_all_splits() -> None:
    assignment = _validate_scene_groups(_three_split_scenes(), {1, 2, 3})
    assert {number: group.split for number, group in assignment.items()} == {
        1: "train",
        2: "val",
        3: "test",
    }

    overlapping = (
        SceneGroup("scene-train", "train", (1, 2), (1,)),
        SceneGroup("scene-val", "val", (2,), (2,)),
        SceneGroup("scene-test", "test", (3,), (3,)),
    )
    with pytest.raises(ValueError, match="duas cenas"):
        _validate_scene_groups(overlapping, {1, 2, 3})

    with pytest.raises(ValueError, match="exatamente"):
        _validate_scene_groups(_three_split_scenes(), {1, 2, 3, 4})


def test_source_manifest_must_use_training_redaction_profile(tmp_path: Path) -> None:
    source = tmp_path / "source"
    _write_source(source, profile="publication")

    with pytest.raises(AuthorizedDatasetError, match="perfil training"):
        _validate_source_manifest(source, _source_images(source))

    manifest_path = source / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["redaction_profile"] = "training"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8", newline="\n")
    _validate_source_manifest(source, _source_images(source))


def test_pipeline_writes_review_required_yolo_dataset_and_filters_phone(tmp_path: Path) -> None:
    source = tmp_path / "source"
    output = tmp_path / "prelabels"
    _write_source(source)
    detector = FakeDetector()

    manifest = prepare_authorized_workstation_prelabels(
        source,
        output,
        detector,
        scene_groups=_three_split_scenes(),
    )

    assert detector.frame_shapes == [(100, 200, 3)] * 3
    assert manifest["ready_for_training"] is False
    assert manifest["cell_phone_class_included"] is False
    assert manifest["activity_classification_performed"] is False
    assert manifest["classes"] == dict(DATASET_CLASSES)
    assert manifest["prelabel_counts"] == {
        "keyboard": 3,
        "laptop": 3,
        "mouse": 3,
        "person": 3,
    }

    dataset_yaml = (output / "dataset.yaml").read_text(encoding="utf-8")
    assert "cell_phone" not in dataset_yaml
    assert "4:" not in dataset_yaml
    for split, number in (("train", 1), ("val", 2), ("test", 3)):
        label_path = output / "labels" / split / f"frame_{number:03d}.txt"
        class_ids = [line.split(maxsplit=1)[0] for line in label_path.read_text().splitlines()]
        assert len(class_ids) == 4
        assert set(class_ids) == {"0", "1", "2", "3"}
        assert (output / "images" / split / f"frame_{number:03d}.jpg").is_file()
        assert (output / "previews" / split / f"frame_{number:03d}.jpg").is_file()

    stored_manifest = json.loads((output / "manifest.json").read_text(encoding="utf-8"))
    assert stored_manifest["ready_for_training"] is False
    assert stored_manifest["cell_phone_class_included"] is False
    assert all(not row["human_reviewed"] for row in stored_manifest["images"])


def test_metadata_bearing_jpeg_is_rejected_before_dataset_copy(tmp_path: Path) -> None:
    clean = _jpeg()
    exif_segment = b"\xff\xe1\x00\x08Exif\x00\x00"
    path = tmp_path / "frame_001.jpg"
    path.write_bytes(clean[:2] + exif_segment + clean[2:])

    with pytest.raises(AuthorizedDatasetError, match="metadados"):
        _decode_anonymized_jpeg(path)


@pytest.mark.parametrize(
    "tainted_payload",
    (
        pytest.param(
            lambda clean: clean[:-2] + b"\xff\xfe\x00\x09comment" + clean[-2:],
            id="comment-after-scan",
        ),
        pytest.param(
            lambda clean: clean + b"\xff\xe1\x00\x08Exif\x00\x00",
            id="app1-after-eoi-trailer",
        ),
    ),
)
def test_metadata_after_scan_or_eoi_trailer_is_rejected(
    tmp_path: Path,
    tainted_payload: object,
) -> None:
    if not callable(tainted_payload):
        raise AssertionError("invalid test parameter")
    path = tmp_path / "frame_001.jpg"
    path.write_bytes(tainted_payload(_jpeg()))

    with pytest.raises(AuthorizedDatasetError, match="metadados"):
        _decode_anonymized_jpeg(path)


def test_expected_source_fingerprint_mismatch_fails_before_detection(tmp_path: Path) -> None:
    source = tmp_path / "source"
    output = tmp_path / "prelabels"
    _write_source(source)
    detector = FakeDetector()

    with pytest.raises(AuthorizedDatasetError, match="divisão por cenas"):
        prepare_authorized_workstation_prelabels(
            source,
            output,
            detector,
            scene_groups=_three_split_scenes(),
            expected_source_fingerprint="0" * 64,
        )

    assert detector.frame_shapes == []
    assert not output.exists()


def test_zero_prelabels_are_reported_for_every_dataset_class(tmp_path: Path) -> None:
    source = tmp_path / "source"
    output = tmp_path / "prelabels"
    _write_source(source)

    manifest = prepare_authorized_workstation_prelabels(
        source,
        output,
        EmptyDetector(),
        scene_groups=_three_split_scenes(),
    )

    assert manifest["prelabel_counts"] == {
        "person": 0,
        "laptop": 0,
        "mouse": 0,
        "keyboard": 0,
    }
