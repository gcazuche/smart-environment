"""Download the small, reviewed workstation reference set used by the TCC."""

from __future__ import annotations

import json
import math
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import BinaryIO, cast
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

from app.datasets.image_references import validate_pinned_image_payload

DATASET_REPOSITORY = (
    "https://huggingface.co/datasets/shangzx/Open-Office-Workstation-Usage-Detection-Dataset"
)
DATASET_LICENSE = "CC-BY-NC-SA-4.0"
DATASET_LICENSE_URL = "https://creativecommons.org/licenses/by-nc-sa/4.0/"
DEFAULT_OUTPUT_DIRECTORY = Path("data/datasets/workstation-references/huggingface")

_SOURCE_HOST = "huggingface.co"
_REDIRECT_HOSTS = frozenset(
    {
        _SOURCE_HOST,
        "cdn-lfs.hf.co",
        "cas-bridge.xethub.hf.co",
        "us.aws.cdn.hf.co",
    }
)
_MAXIMUM_IMAGE_BYTES = 1_000_000


@dataclass(frozen=True, slots=True)
class ReferenceImage:
    """Pinned source metadata for one qualitative workstation reference image."""

    filename: str
    sha256: str
    occupancy_status: str
    number_of_people: int
    desk_count: str
    lighting_condition: str
    seating_arrangement: str
    equipment_count: str
    personal_items_count: str
    noise_level: str

    @property
    def source_url(self) -> str:
        return f"{DATASET_REPOSITORY}/resolve/main/{self.filename}?download=true"


REFERENCE_IMAGES = (
    ReferenceImage(
        filename="00e5dad3f71c21e151b3c382faff49a0.jpg",
        sha256="c404032699708f815ec04a7d2547ee20ea8b2080f2cb9a451c2558e6bf9042d2",
        occupancy_status="occupied",
        number_of_people=8,
        desk_count="12",
        lighting_condition="bright",
        seating_arrangement="open",
        equipment_count="8",
        personal_items_count="many",
        noise_level="quiet",
    ),
    ReferenceImage(
        filename="275f9fdcdae42afc6048d54951c20fc4.jpg",
        sha256="3954edcd1692e1d27a204dd9044e4cf9221b4f6f3edea04d8e09a1cbe9303aff",
        occupancy_status="occupied",
        number_of_people=9,
        desk_count="approximately 12",
        lighting_condition="bright",
        seating_arrangement="open plan",
        equipment_count="multiple computers and other devices",
        personal_items_count="multiple",
        noise_level="moderate",
    ),
    ReferenceImage(
        filename="8a390ba3ad16cbf50e5394b70b2a799a.jpg",
        sha256="64d5456f089a59a937752ebcd59450e7aa53465996e861944e39ce7108e1d995",
        occupancy_status="occupied",
        number_of_people=4,
        desk_count="2",
        lighting_condition="bright",
        seating_arrangement="open",
        equipment_count="multiple computers",
        personal_items_count="multiple",
        noise_level="moderate",
    ),
)


def _validate_https_host(url: str, allowed_hosts: frozenset[str]) -> None:
    parsed = urlsplit(url)
    if parsed.scheme != "https" or parsed.hostname not in allowed_hosts:
        raise ValueError("URL de referência fora das origens permitidas")
    if parsed.username is not None or parsed.password is not None:
        raise ValueError("URL de referência não pode conter credenciais")


def _read_response(response: BinaryIO, *, maximum_bytes: int) -> bytes:
    payload = response.read(maximum_bytes + 1)
    if not payload or len(payload) > maximum_bytes:
        raise RuntimeError("download vazio ou acima do limite configurado")
    return payload


def download_reference_bytes(
    reference: ReferenceImage,
    *,
    maximum_bytes: int = _MAXIMUM_IMAGE_BYTES,
    timeout_seconds: float = 30.0,
) -> bytes:
    """Download one bounded, pinned image from the reviewed repository."""

    if maximum_bytes <= 0 or not math.isfinite(timeout_seconds) or timeout_seconds <= 0:
        raise ValueError("limites de download inválidos")
    _validate_https_host(reference.source_url, frozenset({_SOURCE_HOST}))
    request = Request(  # noqa: S310 - exact source host and file list are pinned
        reference.source_url,
        headers={"User-Agent": "SmartEnvironment-TCC/0.1"},
    )
    with urlopen(request, timeout=timeout_seconds) as response:  # noqa: S310
        _validate_https_host(cast(str, response.geturl()), _REDIRECT_HOSTS)
        raw_length = response.headers.get("Content-Length")
        if raw_length is not None:
            try:
                content_length = int(raw_length)
            except ValueError as exc:
                raise RuntimeError("Content-Length remoto inválido") from exc
            if content_length > maximum_bytes:
                raise RuntimeError("imagem remota acima do limite configurado")
        return _read_response(cast(BinaryIO, response), maximum_bytes=maximum_bytes)


def validate_reference_payload(
    payload: bytes,
    reference: ReferenceImage,
) -> tuple[int, int]:
    """Verify the pinned digest and decode the JPEG before it reaches the dataset."""

    return validate_pinned_image_payload(payload, reference)


def _atomic_write(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(f"{path.suffix}.part")
    temporary.write_bytes(payload)
    temporary.replace(path)


def prepare_workstation_references(
    output_directory: Path = DEFAULT_OUTPUT_DIRECTORY,
    *,
    maximum_image_bytes: int = _MAXIMUM_IMAGE_BYTES,
) -> dict[str, object]:
    """Prepare three qualitative references; never label human intent or performance."""

    if not 100_000 <= maximum_image_bytes <= 5_000_000:
        raise ValueError("limite por imagem deve estar entre 100 KB e 5 MB")
    output = output_directory.resolve()
    manifest_rows: list[dict[str, object]] = []
    for reference in REFERENCE_IMAGES:
        destination = output / reference.filename
        payload = (
            destination.read_bytes()
            if destination.is_file()
            else download_reference_bytes(reference, maximum_bytes=maximum_image_bytes)
        )
        width, height = validate_reference_payload(payload, reference)
        if not destination.is_file():
            _atomic_write(destination, payload)
        row = asdict(reference)
        row.update(
            {
                "source_url": reference.source_url,
                "width": width,
                "height": height,
                "bytes": len(payload),
            }
        )
        manifest_rows.append(row)

    summary: dict[str, object] = {
        "dataset": "Open Office Workstation Usage Detection Dataset",
        "repository": DATASET_REPOSITORY,
        "license": DATASET_LICENSE,
        "license_url": DATASET_LICENSE_URL,
        "commercial_use_allowed": False,
        "intended_use": "qualitative reference and detector smoke tests for the TCC",
        "limitations": [
            "only three images",
            "all source rows are occupied office scenes",
            "not labeled for productivity, distraction, posture, or human intent",
            "not sufficient for training or quantitative evaluation",
        ],
        "total_images": len(manifest_rows),
        "images": manifest_rows,
        "pixels_tracked_by_git": False,
    }
    rendered = json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True).encode("utf-8")
    _atomic_write(output / "source-manifest.json", rendered)
    return summary
