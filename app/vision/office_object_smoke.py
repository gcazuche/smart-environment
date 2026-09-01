"""Offline smoke evaluation for office objects on reviewed public references."""

from __future__ import annotations

import json
import time
from collections import Counter
from collections.abc import Sequence
from dataclasses import asdict
from pathlib import Path
from typing import Protocol, cast

import cv2

from app.cameras.opencv_source import Frame
from app.datasets import (
    DATASET_LICENSE,
    DATASET_REPOSITORY,
    REFERENCE_IMAGES,
    PinnedImageReference,
    validate_pinned_image_payload,
)
from app.vision.intel_yolo import MODEL_BIN_SHA256, MODEL_XML_SHA256
from app.vision.office_objects import OfficeObjectDetection

_COLORS = {
    "laptop": (42, 207, 255),
    "mouse": (238, 130, 238),
    "keyboard": (255, 191, 0),
    "cell_phone": (0, 165, 255),
}


class OfficeObjectDetector(Protocol):
    confidence_threshold: float
    target_labels: tuple[str, ...]

    def detect(self, frame: Frame) -> tuple[OfficeObjectDetection, ...]: ...


def _atomic_write(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(f"{path.suffix}.part")
    temporary.write_bytes(payload)
    temporary.replace(path)


def _annotate(frame: Frame, detections: Sequence[OfficeObjectDetection]) -> Frame:
    annotated = frame.copy()
    for detection in detections:
        color = _COLORS[detection.label]
        start = (detection.x, detection.y)
        end = (detection.x + detection.width, detection.y + detection.height)
        cv2.rectangle(annotated, start, end, color, 2)
        caption = f"{detection.label} {detection.score:.2f}"
        text_y = max(18, detection.y - 6)
        cv2.putText(
            annotated,
            caption,
            (detection.x, text_y),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            color,
            1,
            cv2.LINE_AA,
        )
    return annotated


def run_office_object_smoke(
    input_directory: Path,
    output_directory: Path,
    detector: OfficeObjectDetector,
    *,
    references: Sequence[PinnedImageReference] = REFERENCE_IMAGES,
    dataset: str = DATASET_REPOSITORY,
    dataset_usage: str = DATASET_LICENSE,
    dataset_kind: str = "public_real_reference",
) -> dict[str, object]:
    """Run bounded local inference over pinned images and persist only derived previews."""

    if not references:
        raise ValueError("ao menos uma referência deve ser fornecida")
    source = input_directory.resolve()
    output = output_directory.resolve()
    totals: Counter[str] = Counter()
    image_rows: list[dict[str, object]] = []

    for reference in references:
        image_path = source / reference.filename
        if not image_path.is_file():
            raise FileNotFoundError(f"referência ausente: {reference.filename}")
        payload = image_path.read_bytes()
        width, height = validate_pinned_image_payload(payload, reference)
        frame = cv2.imread(str(image_path), cv2.IMREAD_COLOR)
        if frame is None or frame.shape[:2] != (height, width):
            raise RuntimeError(f"não foi possível abrir {reference.filename}")

        started = time.perf_counter()
        detections = detector.detect(cast(Frame, frame))
        elapsed_ms = (time.perf_counter() - started) * 1000
        unexpected = {item.label for item in detections} - set(detector.target_labels)
        if unexpected:
            raise RuntimeError("detector retornou classe fora da lista permitida")
        totals.update(item.label for item in detections)

        annotated = _annotate(cast(Frame, frame), detections)
        encoded, preview = cv2.imencode(
            ".jpg",
            annotated,
            [int(cv2.IMWRITE_JPEG_QUALITY), 90],
        )
        if not encoded:
            raise RuntimeError(f"falha ao gerar prévia de {reference.filename}")
        preview_name = f"{Path(reference.filename).stem}-objects.jpg"
        _atomic_write(output / "previews" / preview_name, preview.tobytes())

        image_rows.append(
            {
                "filename": reference.filename,
                "width": width,
                "height": height,
                "elapsed_ms": round(elapsed_ms, 3),
                "preview": f"previews/{preview_name}",
                "detections": [asdict(item) for item in detections],
            }
        )

    report: dict[str, object] = {
        "evaluation": "office object qualitative smoke",
        "dataset": dataset,
        "dataset_usage": dataset_usage,
        "dataset_license": (dataset_usage if dataset_kind == "public_real_reference" else None),
        "dataset_kind": dataset_kind,
        "model": "Intel reference YOLO26n FP16 OpenVINO",
        "model_xml_sha256": MODEL_XML_SHA256,
        "model_bin_sha256": MODEL_BIN_SHA256,
        "confidence_threshold": detector.confidence_threshold,
        "target_labels": list(detector.target_labels),
        "total_images": len(image_rows),
        "totals_by_label": {label: totals.get(label, 0) for label in detector.target_labels},
        "images": image_rows,
        "activity_classification_performed": False,
        "webcam_opened": False,
        "limitations": [
            "the small reference set is not a representative benchmark",
            "object presence does not establish work, distraction, posture, or intent",
            "derived previews are local and excluded from Git",
        ],
    }
    rendered = json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True).encode("utf-8")
    _atomic_write(output / "report.json", rendered)
    return report
