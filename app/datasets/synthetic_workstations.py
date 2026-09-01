"""Manifest contract for provisional synthetic workstation references."""

from __future__ import annotations

import json
from collections.abc import Sequence
from dataclasses import asdict, dataclass
from pathlib import Path

from app.datasets.image_references import validate_pinned_image_payload

SYNTHETIC_DATASET_NAME = "Smart Environment synthetic workstation references"
SYNTHETIC_DATASET_SOURCE = "OpenAI built-in image generation via Codex"
SYNTHETIC_DATASET_USAGE = "project-generated synthetic media for the academic TCC"
DEFAULT_SYNTHETIC_DIRECTORY = Path("data/datasets/workstation-references/synthetic")
_ALLOWED_EXPECTED_OBJECTS = frozenset({"laptop", "mouse", "keyboard", "cell_phone"})


@dataclass(frozen=True, slots=True)
class SyntheticReferenceImage:
    """Pinned synthetic scene metadata without productivity or intent labels."""

    filename: str
    sha256: str
    scenario: str
    expected_visible_objects: tuple[str, ...]
    person_visible: bool
    face_visible: bool = False


SYNTHETIC_REFERENCE_IMAGES = (
    SyntheticReferenceImage(
        filename="synth-01-laptop-typing.png",
        sha256="cd7eb67474a64690a9d944859f1e47e84a85adf2e5018611d5e5980477b10045",
        scenario="occupied workstation with laptop visible",
        expected_visible_objects=("laptop",),
        person_visible=True,
    ),
    SyntheticReferenceImage(
        filename="synth-02-phone-handheld.png",
        sha256="ccda59d25bf383ab3d8a254a1032427cf26714e815d84d2ad5fa118827d6ab02",
        scenario="occupied workstation with handheld phone visible",
        expected_visible_objects=("cell_phone",),
        person_visible=True,
    ),
    SyntheticReferenceImage(
        filename="synth-03-laptop-phone-on-desk.png",
        sha256="3c586d91de9b9a9ee97bbf77782a82e9e0ddcd10526b2748f5d89b9839a37386",
        scenario="occupied workstation with laptop and resting phone visible",
        expected_visible_objects=("laptop", "cell_phone"),
        person_visible=True,
    ),
    SyntheticReferenceImage(
        filename="synth-04-empty-desk-devices.png",
        sha256="beb493d2a683261cfd0252533bd79d7379be03f7150f2503ffe38d180e0a5d21",
        scenario="unoccupied workstation with laptop and phone visible",
        expected_visible_objects=("laptop", "cell_phone"),
        person_visible=False,
    ),
    SyntheticReferenceImage(
        filename="synth-05-pause-clear-desk.png",
        sha256="f5c09d6a33e60943aff74118303ad1e8d7ba6ba88c0a34a9ed96320c6c460d44",
        scenario="occupied workstation without target objects",
        expected_visible_objects=(),
        person_visible=True,
    ),
    SyntheticReferenceImage(
        filename="synth-06-phone-use-laptop-open.png",
        sha256="2009e9a7c6d6e41f77d76b33e8b90f3fec1a95ebbd005260976ba927ba19ffc6",
        scenario="ambiguous occupied workstation with laptop and handheld phone visible",
        expected_visible_objects=("laptop", "cell_phone"),
        person_visible=True,
    ),
)


def _atomic_write(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(f"{path.suffix}.part")
    temporary.write_bytes(payload)
    temporary.replace(path)


def prepare_synthetic_workstation_manifest(
    input_directory: Path = DEFAULT_SYNTHETIC_DIRECTORY,
    *,
    references: Sequence[SyntheticReferenceImage] = SYNTHETIC_REFERENCE_IMAGES,
) -> dict[str, object]:
    """Validate generated pixels and write a provenance manifest beside them."""

    if not references:
        raise ValueError("ao menos uma referência sintética deve ser fornecida")
    source = input_directory.resolve()
    image_rows: list[dict[str, object]] = []
    for reference in references:
        unexpected_objects = set(reference.expected_visible_objects) - _ALLOWED_EXPECTED_OBJECTS
        if unexpected_objects:
            raise ValueError("referência sintética contém objeto esperado não permitido")
        if reference.face_visible:
            raise ValueError("referência sintética não pode declarar rosto visível")
        image_path = source / reference.filename
        if not image_path.is_file():
            raise FileNotFoundError(f"referência sintética ausente: {reference.filename}")
        payload = image_path.read_bytes()
        width, height = validate_pinned_image_payload(payload, reference)
        row = asdict(reference)
        row.update({"width": width, "height": height, "bytes": len(payload)})
        image_rows.append(row)

    summary: dict[str, object] = {
        "dataset": SYNTHETIC_DATASET_NAME,
        "source": SYNTHETIC_DATASET_SOURCE,
        "usage": SYNTHETIC_DATASET_USAGE,
        "generated_on": "2026-08-23",
        "contains_real_people": False,
        "faces_visible": False,
        "commercial_use_reviewed": False,
        "intended_use": "qualitative detector smoke for the academic TCC",
        "prompt_specification": (
            ".planning/phases/se-04-activity-observation/STEP-03-SYNTHETIC-DATASET-SPEC.md"
        ),
        "total_images": len(image_rows),
        "images": image_rows,
        "activity_classification_performed": False,
        "limitations": [
            "synthetic images have a domain gap relative to real cameras",
            "six images are not sufficient for training or quantitative evaluation",
            "expected objects are scene-level observations, not bounding-box annotations",
            "object presence does not establish work, distraction, posture, or intent",
        ],
        "pixels_tracked_by_git": False,
    }
    rendered = json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True).encode("utf-8")
    _atomic_write(source / "source-manifest.json", rendered)
    return summary
