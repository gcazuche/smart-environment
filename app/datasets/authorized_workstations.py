"""Prepare a local, review-required YOLO prelabel dataset from authorized photos."""

from __future__ import annotations

import hashlib
import json
import math
import re
import tempfile
from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Protocol, cast

import cv2
import numpy as np

from app.cameras.opencv_source import Frame
from app.vision.intel_yolo import (
    MODEL_BIN_SHA256,
    MODEL_XML_SHA256,
    IntelYoloDetector,
    YoloDetection,
)

DATASET_NAME = "Smart Environment authorized workstation prelabels v1"
DEFAULT_AUTHORIZED_SOURCE_DIRECTORY = Path(
    "data/datasets/workstation-references/user-anonymized-training-20260827-v2"
)
DEFAULT_PRELABEL_OUTPUT_DIRECTORY = Path("data/datasets/workstation-prelabels-v1")
AUTHORIZED_SOURCE_FINGERPRINT_SHA256 = (
    "b2c242109e18987bbfb619c7d0562b251397fd3f2105bf837e5c83c1ef7ad804"
)

DATASET_CLASSES: Mapping[int, str] = MappingProxyType(
    {0: "person", 1: "laptop", 2: "mouse", 3: "keyboard"}
)
COCO_PRELABEL_CLASSES: Mapping[int, str] = MappingProxyType(
    {0: "person", 63: "laptop", 64: "mouse", 66: "keyboard"}
)
COCO_TO_DATASET_CLASS: Mapping[int, int] = MappingProxyType({0: 0, 63: 1, 64: 2, 66: 3})
CLASS_THRESHOLDS: Mapping[str, float] = MappingProxyType(
    {"person": 0.40, "laptop": 0.25, "mouse": 0.25, "keyboard": 0.25}
)

_FRAME_PATTERN = re.compile(r"frame_(\d{3})\.jpg", re.ASCII)
_SCENE_ID_PATTERN = re.compile(r"scene-[a-z0-9][a-z0-9-]{0,31}", re.ASCII)
_SPLITS = frozenset({"train", "val", "test"})
_MAXIMUM_IMAGE_BYTES = 20 * 1024 * 1024
_MAXIMUM_MANIFEST_BYTES = 2 * 1024 * 1024
_MAXIMUM_IMAGE_SIDE = 8192
_TRAINING_INPUT_SIZE = 640
_MINIMUM_TRAINING_OBJECT_SIDE = 8.0
_SHA256_PATTERN = re.compile(r"[0-9a-f]{64}", re.ASCII)


class AuthorizedDatasetError(RuntimeError):
    """Raised when the authorized dataset cannot be prepared safely."""


class PrelabelDetector(Protocol):
    """Minimal object detector contract used by the preparation pipeline."""

    def detect(self, frame: Frame) -> tuple[YoloDetection, ...]: ...


@dataclass(frozen=True, slots=True)
class SceneGroup:
    """A burst kept wholly inside one dataset split."""

    scene_id: str
    split: str
    frame_numbers: tuple[int, ...]
    selected_frame_numbers: tuple[int, ...]

    def __post_init__(self) -> None:
        if _SCENE_ID_PATTERN.fullmatch(self.scene_id) is None:
            raise ValueError("scene_id inválido")
        if self.split not in _SPLITS:
            raise ValueError("split deve ser train, val ou test")
        if not self.frame_numbers or len(set(self.frame_numbers)) != len(self.frame_numbers):
            raise ValueError("cena deve conter frames únicos")
        if any(number < 1 or number > 999 for number in self.frame_numbers):
            raise ValueError("número de frame fora do intervalo")
        if not self.selected_frame_numbers:
            raise ValueError("cena deve selecionar ao menos um frame")
        if len(set(self.selected_frame_numbers)) != len(self.selected_frame_numbers):
            raise ValueError("seleção da cena não pode repetir frames")
        if not set(self.selected_frame_numbers).issubset(self.frame_numbers):
            raise ValueError("seleção deve pertencer à própria cena")


# Visual scene audit of the 62 authorized frames.  Groups are intentionally kept
# intact across splits and a representative subset avoids overweighting near-identical
# frames from the same burst.
AUTHORIZED_SCENE_GROUPS: tuple[SceneGroup, ...] = (
    SceneGroup("scene-001", "train", tuple(range(1, 8)), (1, 4, 6, 7)),
    SceneGroup("scene-002", "val", tuple(range(8, 15)), (8, 11, 14)),
    SceneGroup("scene-003", "test", tuple(range(15, 20)), (15, 17, 18)),
    SceneGroup("scene-004", "train", tuple(range(20, 33)), (20, 21, 22, 24, 26, 28, 31, 32)),
    SceneGroup("scene-005", "train", tuple(range(33, 51)), (33, 36, 38, 41, 43, 46, 50)),
    SceneGroup("scene-006", "train", tuple(range(51, 55)), (51, 53, 54)),
    SceneGroup("scene-007", "test", tuple(range(55, 60)), (55, 57, 59)),
    SceneGroup("scene-008", "val", tuple(range(60, 63)), (60, 62)),
)


@dataclass(frozen=True, slots=True)
class Prelabel:
    """One model-generated candidate that still needs human review."""

    class_id: int
    label: str
    x: int
    y: int
    width: int
    height: int
    score: float

    @property
    def x2(self) -> int:
        return self.x + self.width

    @property
    def y2(self) -> int:
        return self.y + self.height


@dataclass(frozen=True, slots=True)
class _SourceImageRecord:
    sha256: str
    width: int
    height: int


def _validate_scene_groups(
    groups: Sequence[SceneGroup],
    source_frame_numbers: set[int],
) -> dict[int, SceneGroup]:
    if not groups:
        raise ValueError("ao menos uma cena deve ser configurada")
    if {group.split for group in groups} != _SPLITS:
        raise ValueError("o plano deve conter cenas de train, val e test")
    if len({group.scene_id for group in groups}) != len(groups):
        raise ValueError("scene_id deve ser único")
    assignment: dict[int, SceneGroup] = {}
    for group in groups:
        for number in group.frame_numbers:
            if number in assignment:
                raise ValueError("um frame não pode pertencer a duas cenas")
            assignment[number] = group
    if set(assignment) != source_frame_numbers:
        raise ValueError("o plano de cenas deve cobrir exatamente os frames de entrada")
    return assignment


def _source_images(source: Path) -> dict[int, Path]:
    if not source.is_dir():
        raise FileNotFoundError(f"diretório anonimizado ausente: {source}")
    images: dict[int, Path] = {}
    for path in source.iterdir():
        if path.is_symlink():
            raise AuthorizedDatasetError("dataset de entrada não pode conter links simbólicos")
        if not path.is_file() or path.suffix.lower() != ".jpg":
            continue
        match = _FRAME_PATTERN.fullmatch(path.name)
        if match is None:
            raise AuthorizedDatasetError("diretório contém JPEG com nome não permitido")
        number = int(match.group(1))
        if number in images:
            raise AuthorizedDatasetError("diretório contém número de frame duplicado")
        images[number] = path
    if not images:
        raise AuthorizedDatasetError("nenhuma imagem frame_###.jpg foi encontrada")
    if len(images) > 500:
        raise AuthorizedDatasetError("dataset excede o limite de 500 imagens")
    return images


def _validate_source_manifest(
    source: Path,
    images: Mapping[int, Path],
) -> tuple[dict[str, _SourceImageRecord], str]:
    manifest_path = source / "manifest.json"
    if not manifest_path.is_file():
        raise AuthorizedDatasetError("manifest de anonimização ausente")
    if manifest_path.stat().st_size > _MAXIMUM_MANIFEST_BYTES:
        raise AuthorizedDatasetError("manifest de anonimização excede o limite")
    manifest_payload = manifest_path.read_bytes()
    try:
        decoded_manifest = json.loads(manifest_payload.decode("utf-8"))
        if not isinstance(decoded_manifest, dict):
            raise TypeError
        manifest = cast(dict[str, object], decoded_manifest)
        summary_value = manifest["summary"]
        privacy_value = manifest["privacy"]
        manifest_images_value = manifest["images"]
        if (
            not isinstance(summary_value, dict)
            or not isinstance(privacy_value, dict)
            or not isinstance(manifest_images_value, list)
        ):
            raise TypeError
        summary = cast(dict[str, object], summary_value)
        privacy = cast(dict[str, object], privacy_value)
        manifest_images = cast(list[object], manifest_images_value)
    except (json.JSONDecodeError, KeyError, TypeError) as exc:
        raise AuthorizedDatasetError("manifest de anonimização inválido") from exc
    if manifest.get("redaction_profile") != "training":
        raise AuthorizedDatasetError("dataset exige cópia anonimizada com perfil training")
    if summary.get("images") != len(images):
        raise AuthorizedDatasetError("contagem do manifest de anonimização não confere")
    if privacy.get("metadata") != "fresh-jpeg-reencode; exif-xmp-icc-not-copied":
        raise AuthorizedDatasetError("manifest não comprova remoção dos metadados")
    records: dict[str, _SourceImageRecord] = {}
    try:
        for value in manifest_images:
            if not isinstance(value, dict):
                raise TypeError
            filename = value["file"]
            digest = value["sha256"]
            width = value["width"]
            height = value["height"]
            if (
                not isinstance(filename, str)
                or _FRAME_PATTERN.fullmatch(filename) is None
                or not isinstance(digest, str)
                or _SHA256_PATTERN.fullmatch(digest) is None
                or isinstance(width, bool)
                or not isinstance(width, int)
                or isinstance(height, bool)
                or not isinstance(height, int)
                or not 0 < width <= _MAXIMUM_IMAGE_SIDE
                or not 0 < height <= _MAXIMUM_IMAGE_SIDE
                or filename in records
            ):
                raise TypeError
            records[filename] = _SourceImageRecord(digest, width, height)
    except (KeyError, TypeError) as exc:
        raise AuthorizedDatasetError("registros de imagem do manifest são inválidos") from exc
    if set(records) != {path.name for path in images.values()}:
        raise AuthorizedDatasetError("manifest não cobre exatamente as imagens de entrada")
    return records, hashlib.sha256(manifest_payload).hexdigest()


def _source_fingerprint(records: Mapping[str, _SourceImageRecord]) -> str:
    payload = "".join(
        f"{filename}\t{record.sha256}\t{record.width}x{record.height}\n"
        for filename, record in sorted(records.items())
    ).encode()
    return hashlib.sha256(payload).hexdigest()


def _scene_plan_fingerprint(groups: Sequence[SceneGroup]) -> str:
    payload = json.dumps(
        [
            {
                "scene_id": group.scene_id,
                "split": group.split,
                "frame_numbers": group.frame_numbers,
                "selected_frame_numbers": group.selected_frame_numbers,
            }
            for group in groups
        ],
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode()
    return hashlib.sha256(payload).hexdigest()


def _contains_sensitive_jpeg_segments(payload: bytes) -> bool:
    """Detect EXIF/XMP/ICC/IPTC/comment segments before copying a JPEG."""

    if not payload.startswith(b"\xff\xd8"):
        return True
    position = 2
    while position < len(payload):
        if payload[position] != 0xFF:
            return True
        marker_start = position
        while position < len(payload) and payload[position] == 0xFF:
            position += 1
        if position >= len(payload):
            return True
        marker = payload[position]
        position += 1
        if marker == 0xD9:
            return position != len(payload)
        if marker in {0x00, 0xD8}:
            return True
        if marker in {0x01, *range(0xD0, 0xD8)}:
            continue
        if position + 2 > len(payload):
            return True
        segment_length = int.from_bytes(payload[position : position + 2], "big")
        if segment_length < 2 or position + segment_length > len(payload):
            return True
        if marker in {0xE1, 0xE2, 0xED, 0xFE}:
            return True
        position += segment_length
        if marker != 0xDA:
            continue

        # Entropy-coded scan: FF00 is an escaped data byte and restart markers
        # are standalone.  Any other marker resumes the regular parser, allowing
        # progressive JPEGs and metadata between scans to be checked as well.
        while position < len(payload):
            marker_start = payload.find(b"\xff", position)
            if marker_start < 0:
                return True
            position = marker_start + 1
            while position < len(payload) and payload[position] == 0xFF:
                position += 1
            if position >= len(payload):
                return True
            scan_marker = payload[position]
            if scan_marker == 0x00 or 0xD0 <= scan_marker <= 0xD7:
                position += 1
                continue
            position = marker_start
            break
    return True


def _decode_anonymized_jpeg(path: Path) -> tuple[bytes, Frame]:
    file_size = path.stat().st_size
    if not 0 < file_size <= _MAXIMUM_IMAGE_BYTES:
        raise AuthorizedDatasetError(f"imagem fora do limite: {path.name}")
    with path.open("rb") as image_file:
        payload = image_file.read(_MAXIMUM_IMAGE_BYTES + 1)
    if len(payload) != file_size:
        raise AuthorizedDatasetError(f"imagem mudou durante a leitura: {path.name}")
    if _contains_sensitive_jpeg_segments(payload):
        raise AuthorizedDatasetError(f"imagem contém metadados ou JPEG inválido: {path.name}")
    decoded = cv2.imdecode(np.frombuffer(payload, dtype=np.uint8), cv2.IMREAD_COLOR)
    if decoded is None or decoded.ndim != 3 or decoded.shape[2] != 3 or decoded.size == 0:
        raise AuthorizedDatasetError(f"imagem não decodificável: {path.name}")
    height, width = decoded.shape[:2]
    if width > _MAXIMUM_IMAGE_SIDE or height > _MAXIMUM_IMAGE_SIDE:
        raise AuthorizedDatasetError(f"imagem excede a resolução permitida: {path.name}")
    return payload, cast(Frame, decoded)


def _intersection_over_union(first: Prelabel, second: Prelabel) -> float:
    left = max(first.x, second.x)
    top = max(first.y, second.y)
    right = min(first.x2, second.x2)
    bottom = min(first.y2, second.y2)
    intersection = max(0, right - left) * max(0, bottom - top)
    if intersection == 0:
        return 0.0
    union = first.width * first.height + second.width * second.height - intersection
    return intersection / union if union else 0.0


def suppress_duplicate_prelabels(
    candidates: Sequence[Prelabel],
    *,
    iou_threshold: float = 0.50,
) -> tuple[Prelabel, ...]:
    """Apply class-aware NMS to provisional detector output."""

    if not math.isfinite(iou_threshold) or not 0 < iou_threshold < 1:
        raise ValueError("limiar de IoU deve estar entre zero e um")
    kept: list[Prelabel] = []
    for candidate in sorted(
        candidates,
        key=lambda item: (
            -item.score,
            -(item.width * item.height),
            item.class_id,
            item.x,
            item.y,
            item.width,
            item.height,
        ),
    ):
        if any(
            candidate.class_id == existing.class_id
            and _intersection_over_union(candidate, existing) >= iou_threshold
            for existing in kept
        ):
            continue
        kept.append(candidate)
    return tuple(kept)


def _prelabels_for(
    image: Frame,
    detections: Sequence[YoloDetection],
) -> tuple[Prelabel, ...]:
    height, width = image.shape[:2]
    resize_scale = min(_TRAINING_INPUT_SIZE / width, _TRAINING_INPUT_SIZE / height)
    candidates: list[Prelabel] = []
    for detection in detections:
        dataset_class_id = COCO_TO_DATASET_CLASS.get(detection.class_id)
        expected_label = COCO_PRELABEL_CLASSES.get(detection.class_id)
        if dataset_class_id is None or expected_label is None:
            continue
        if detection.label != expected_label:
            raise AuthorizedDatasetError("detector retornou classe e rótulo incompatíveis")
        threshold = CLASS_THRESHOLDS[expected_label]
        if not math.isfinite(detection.score) or detection.score < threshold:
            continue
        x1 = max(0, min(width, detection.x))
        y1 = max(0, min(height, detection.y))
        x2 = max(0, min(width, detection.x + detection.width))
        y2 = max(0, min(height, detection.y + detection.height))
        box_width = x2 - x1
        box_height = y2 - y1
        if box_width <= 0 or box_height <= 0:
            continue
        if min(box_width * resize_scale, box_height * resize_scale) < _MINIMUM_TRAINING_OBJECT_SIDE:
            continue
        candidates.append(
            Prelabel(
                class_id=dataset_class_id,
                label=expected_label,
                x=x1,
                y=y1,
                width=box_width,
                height=box_height,
                score=detection.score,
            )
        )
    return suppress_duplicate_prelabels(candidates)


def _yolo_line(item: Prelabel, image_width: int, image_height: int) -> str:
    center_x = (item.x + item.width / 2) / image_width
    center_y = (item.y + item.height / 2) / image_height
    normalized_width = item.width / image_width
    normalized_height = item.height / image_height
    values = (center_x, center_y, normalized_width, normalized_height)
    if not all(0 <= value <= 1 for value in values):
        raise AuthorizedDatasetError("caixa normalizada fora da imagem")
    return f"{item.class_id} " + " ".join(f"{value:.6f}" for value in values)


def _preview(image: Frame, prelabels: Sequence[Prelabel]) -> bytes:
    rendered = image.copy()
    colors = ((22, 134, 109), (117, 219, 184), (75, 139, 237), (216, 143, 102))
    for item in prelabels:
        color = colors[item.class_id]
        cv2.rectangle(rendered, (item.x, item.y), (item.x2, item.y2), color, 2)
        cv2.putText(
            rendered,
            f"{item.label} {item.score:.2f}",
            (item.x, max(16, item.y - 6)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.45,
            color,
            1,
            cv2.LINE_AA,
        )
    encoded, payload = cv2.imencode(".jpg", rendered, [int(cv2.IMWRITE_JPEG_QUALITY), 90])
    if not encoded:
        raise AuthorizedDatasetError("não foi possível gerar prévia dos pré-rótulos")
    return payload.tobytes()


def _dataset_yaml() -> str:
    names = "\n".join(f"  {class_id}: {label}" for class_id, label in DATASET_CLASSES.items())
    return f"path: .\ntrain: images/train\nval: images/val\ntest: images/test\nnames:\n{names}\n"


def prepare_authorized_workstation_prelabels(
    source_directory: Path,
    output_directory: Path,
    detector: PrelabelDetector,
    *,
    scene_groups: Sequence[SceneGroup],
    expected_source_fingerprint: str | None = None,
) -> dict[str, object]:
    """Create an atomic, local-only prelabel dataset that is not training-ready."""

    source = source_directory.resolve()
    output = output_directory.resolve()
    if source == output or source in output.parents or output in source.parents:
        raise ValueError("entrada e saída do dataset devem ser diretórios separados")
    if output.exists():
        raise FileExistsError(f"saída do dataset já existe: {output}")
    images = _source_images(source)
    source_records, source_manifest_sha256 = _validate_source_manifest(source, images)
    source_fingerprint = _source_fingerprint(source_records)
    if expected_source_fingerprint is not None:
        if _SHA256_PATTERN.fullmatch(expected_source_fingerprint) is None:
            raise ValueError("fingerprint esperado deve ser um SHA-256 minúsculo")
        if source_fingerprint != expected_source_fingerprint:
            raise AuthorizedDatasetError(
                "as imagens não correspondem ao conjunto cuja divisão por cenas foi revisada"
            )
    assignment = _validate_scene_groups(scene_groups, set(images))
    selected_numbers = {number for group in scene_groups for number in group.selected_frame_numbers}
    if not selected_numbers:
        raise ValueError("nenhum frame foi selecionado")

    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="workstation-prelabels-", dir=output.parent) as temp:
        staging = Path(temp) / output.name
        staging.mkdir()
        rows: list[dict[str, object]] = []
        class_counts: Counter[str] = Counter()
        split_counts: Counter[str] = Counter()
        hashes: set[str] = set()

        for number in sorted(selected_numbers):
            group = assignment[number]
            source_path = images[number]
            payload, image = _decode_anonymized_jpeg(source_path)
            digest = hashlib.sha256(payload).hexdigest()
            source_record = source_records[source_path.name]
            if digest != source_record.sha256:
                raise AuthorizedDatasetError(
                    f"hash da imagem diverge do manifest: {source_path.name}"
                )
            if (int(image.shape[1]), int(image.shape[0])) != (
                source_record.width,
                source_record.height,
            ):
                raise AuthorizedDatasetError(
                    f"dimensão da imagem diverge do manifest: {source_path.name}"
                )
            if digest in hashes:
                raise AuthorizedDatasetError("seleção contém imagens exatamente duplicadas")
            hashes.add(digest)
            prelabels = _prelabels_for(image, detector.detect(image))
            split_counts[group.split] += 1
            class_counts.update(item.label for item in prelabels)

            image_directory = staging / "images" / group.split
            label_directory = staging / "labels" / group.split
            preview_directory = staging / "previews" / group.split
            for directory in (image_directory, label_directory, preview_directory):
                directory.mkdir(parents=True, exist_ok=True)
            output_name = f"frame_{number:03d}"
            (image_directory / f"{output_name}.jpg").write_bytes(payload)
            label_text = "\n".join(
                _yolo_line(item, int(image.shape[1]), int(image.shape[0])) for item in prelabels
            )
            if label_text:
                label_text += "\n"
            (label_directory / f"{output_name}.txt").write_text(
                label_text, encoding="ascii", newline="\n"
            )
            (preview_directory / f"{output_name}.jpg").write_bytes(_preview(image, prelabels))
            rows.append(
                {
                    "file": f"{output_name}.jpg",
                    "scene_id": group.scene_id,
                    "split": group.split,
                    "width": int(image.shape[1]),
                    "height": int(image.shape[0]),
                    "sha256": digest,
                    "prelabels": [asdict(item) for item in prelabels],
                    "human_reviewed": False,
                }
            )

        scene_rows = [
            {
                "scene_id": group.scene_id,
                "split": group.split,
                "source_frame_numbers": list(group.frame_numbers),
                "selected_frame_numbers": list(group.selected_frame_numbers),
                "selected_sha256": [
                    source_records[f"frame_{number:03d}.jpg"].sha256
                    for number in group.selected_frame_numbers
                ],
            }
            for group in scene_groups
        ]
        if type(detector) is IntelYoloDetector:
            model_provenance: dict[str, object] = {
                "name": "Intel YOLO26n OpenVINO",
                "artifacts_hash_verified": True,
                "uses_project_pinned_hashes": (
                    detector.model_xml_sha256 == MODEL_XML_SHA256
                    and detector.model_bin_sha256 == MODEL_BIN_SHA256
                ),
                "xml_sha256": detector.model_xml_sha256,
                "bin_sha256": detector.model_bin_sha256,
                "detector_confidence_threshold": detector.confidence_threshold,
            }
        else:
            model_provenance = {
                "name": type(detector).__qualname__,
                "artifacts_hash_verified": False,
                "purpose": "custom_or_test_detector",
            }
        model_provenance.update(
            {
                "coco_allowlist": dict(COCO_PRELABEL_CLASSES),
                "class_confidence_thresholds": dict(CLASS_THRESHOLDS),
                "class_aware_nms_iou": 0.50,
                "training_reference_size": _TRAINING_INPUT_SIZE,
                "minimum_object_side_at_reference_size": _MINIMUM_TRAINING_OBJECT_SIDE,
            }
        )
        manifest: dict[str, object] = {
            "schema_version": 1,
            "dataset": DATASET_NAME,
            "source": "local authorized photos anonymized with neutral filenames",
            "authorization": "user attested that depicted TCC members consented",
            "contains_real_people": True,
            "face_redaction_applied": True,
            "human_privacy_reviewed": False,
            "metadata_removed": True,
            "source_names_and_timestamps_omitted": True,
            "classes": dict(DATASET_CLASSES),
            "cell_phone_class_included": False,
            "annotation_status": "model_generated_prelabels_needing_human_review",
            "ready_for_training": False,
            "intended_use": "dry-run dataset preparation and annotation review",
            "selection": {
                "source_images": len(images),
                "selected_images": len(rows),
                "not_selected_after_scene_review": len(images) - len(rows),
            },
            "source_fingerprint_sha256": source_fingerprint,
            "source_manifest_sha256": source_manifest_sha256,
            "scene_plan_sha256": _scene_plan_fingerprint(scene_groups),
            "prelabel_model": model_provenance,
            "split_counts": dict(sorted(split_counts.items())),
            "prelabel_counts": {label: class_counts[label] for label in DATASET_CLASSES.values()},
            "scenes": scene_rows,
            "images": rows,
            "activity_classification_performed": False,
            "limitations": [
                "prelabels are model suggestions and are not ground truth",
                "all boxes require human review before any fine-tuning",
                "few independent scenes cannot demonstrate generalization",
                "no cell phone examples or cell phone class are present",
                "object presence does not establish work, distraction, attention, or intent",
            ],
            "pixels_tracked_by_git": False,
            "onedrive_path_component_present": any(
                part.casefold() == "onedrive" for part in (*source.parts, *output.parts)
            ),
        }
        (staging / "manifest.json").write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
            newline="\n",
        )
        (staging / "dataset.yaml").write_text(_dataset_yaml(), encoding="utf-8", newline="\n")
        staging.replace(output)
        return manifest
