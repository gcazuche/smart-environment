"""Create a privacy-preserving copy of an image ZIP.

The command is intentionally local and deterministic.  It never modifies the
input archive: each supported image is decoded, privacy regions are redacted,
and the result is re-encoded as a fresh JPEG so camera EXIF/XMP/ICC payloads
are not carried into the output.

This is an anonymisation aid, not a guarantee that a human review is
unnecessary.  Face cascades can miss side profiles, faces hidden in very small
screens, badges, logos, or text.  The generated manifest records those limits
without copying source filenames or paths.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import shutil
import tempfile
import zipfile
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Any

import cv2
import numpy as np

from app.vision.intel_yolo import IntelYoloDetector, YoloDetection

SUPPORTED_EXTENSIONS = frozenset({".jpg", ".jpeg", ".png"})
MAX_FILES = 500
MAX_ENTRY_BYTES = 50 * 1024 * 1024
MAX_TOTAL_BYTES = 500 * 1024 * 1024
MAX_IMAGE_SIDE = 8192
MAX_IMAGE_PIXELS = 40_000_000
FACE_DETECTION_MAX_SIDE = 960
JPEG_QUALITY = 95
PERSON_MIN_SCORE = 0.25
SCREEN_MIN_SCORE = 0.15
PHONE_MIN_SCORE = 0.25
MODEL_CLASSES: Mapping[int, str] = {
    0: "person",
    62: "tv",
    63: "laptop",
    67: "cell_phone",
}


class RedactionProfile(StrEnum):
    """Supported privacy/utility trade-offs for local derivative images."""

    PUBLICATION = "publication"
    TRAINING = "training"


class AnonymizationError(RuntimeError):
    """Raised when an input cannot be processed safely."""


@dataclass(frozen=True, slots=True)
class Region:
    """A clipped image region and its reason for redaction."""

    x: int
    y: int
    width: int
    height: int
    kind: str
    score: float | None = None

    @property
    def x2(self) -> int:
        return self.x + self.width

    @property
    def y2(self) -> int:
        return self.y + self.height


@dataclass(frozen=True, slots=True)
class ImageResult:
    """Public, source-name-free details written to the manifest."""

    output_name: str
    width: int
    height: int
    faces_redacted: int
    head_zones_redacted: int
    screens_redacted: int
    phones_redacted: int
    people_detected: int
    encoded_sha256: str


def _safe_member_name(name: str) -> str:
    """Return a normalized ZIP member name or raise on traversal tricks."""

    if not isinstance(name, str) or not name or "\x00" in name:
        raise AnonymizationError("ZIP contém um nome de arquivo inválido")
    normalized = name.replace("\\", "/")
    path = PurePosixPath(normalized)
    windows_path = PureWindowsPath(name)
    if (
        normalized.startswith("/")
        or path.drive
        or windows_path.drive
        or windows_path.root
        or ".." in path.parts
    ):
        raise AnonymizationError("ZIP contém caminho absoluto ou traversal")
    if any(part in {"", "."} for part in path.parts):
        raise AnonymizationError("ZIP contém caminho ambíguo")
    return "/".join(path.parts)


def _image_members(archive: zipfile.ZipFile) -> list[zipfile.ZipInfo]:
    infos = archive.infolist()
    if len(infos) > MAX_FILES:
        raise AnonymizationError(f"ZIP excede o limite de {MAX_FILES} entradas")
    members: list[zipfile.ZipInfo] = []
    seen: set[str] = set()
    total = 0
    for info in infos:
        if info.is_dir():
            continue
        if info.flag_bits & 0x1:
            raise AnonymizationError("ZIP criptografado não é aceito")
        if info.compress_type not in {zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED}:
            raise AnonymizationError("ZIP usa um método de compressão não aceito")
        normalized = _safe_member_name(info.filename)
        if normalized in seen:
            raise AnonymizationError("ZIP contém nomes de arquivo duplicados")
        seen.add(normalized)
        unix_mode = (info.external_attr >> 16) & 0o170000
        if unix_mode == 0o120000:
            raise AnonymizationError("ZIP contém link simbólico, que não é aceito")
        extension = Path(normalized).suffix.lower()
        if extension not in SUPPORTED_EXTENSIONS:
            raise AnonymizationError(
                f"ZIP contém arquivo não suportado: extensão {extension or '(sem extensão)'}"
            )
        if info.file_size < 1 or info.file_size > MAX_ENTRY_BYTES:
            raise AnonymizationError("ZIP contém imagem fora do limite de tamanho")
        total += info.file_size
        if total > MAX_TOTAL_BYTES:
            raise AnonymizationError("ZIP excede o limite total de tamanho descompactado")
        members.append(info)
    if not members:
        raise AnonymizationError("ZIP não contém imagens JPG, JPEG ou PNG")
    return sorted(members, key=lambda item: _safe_member_name(item.filename).casefold())


def _encoded_dimensions(payload: bytes, member_name: str) -> tuple[int, int]:
    extension = Path(member_name).suffix.lower()
    if extension == ".png":
        if len(payload) < 24 or payload[:8] != b"\x89PNG\r\n\x1a\n":
            raise AnonymizationError(f"cabeçalho PNG inválido em {member_name}")
        width = int.from_bytes(payload[16:20], "big")
        height = int.from_bytes(payload[20:24], "big")
        return width, height

    if not payload.startswith(b"\xff\xd8"):
        raise AnonymizationError(f"cabeçalho JPEG inválido em {member_name}")
    position = 2
    start_of_frame_markers = {
        0xC0,
        0xC1,
        0xC2,
        0xC3,
        0xC5,
        0xC6,
        0xC7,
        0xC9,
        0xCA,
        0xCB,
        0xCD,
        0xCE,
        0xCF,
    }
    while position + 3 < len(payload):
        if payload[position] != 0xFF:
            raise AnonymizationError(f"estrutura JPEG inválida em {member_name}")
        while position < len(payload) and payload[position] == 0xFF:
            position += 1
        if position >= len(payload):
            break
        marker = payload[position]
        position += 1
        if marker in {0x01, *range(0xD0, 0xD9)}:
            continue
        if marker in {0xD9, 0xDA} or position + 2 > len(payload):
            break
        segment_length = int.from_bytes(payload[position : position + 2], "big")
        if segment_length < 2 or position + segment_length > len(payload):
            break
        if marker in start_of_frame_markers:
            if segment_length < 7:
                break
            height = int.from_bytes(payload[position + 3 : position + 5], "big")
            width = int.from_bytes(payload[position + 5 : position + 7], "big")
            return width, height
        position += segment_length
    raise AnonymizationError(f"dimensões JPEG ausentes em {member_name}")


def _decode_image(payload: bytes, member_name: str) -> np.ndarray:
    encoded_width, encoded_height = _encoded_dimensions(payload, member_name)
    if (
        encoded_width < 1
        or encoded_height < 1
        or encoded_width > MAX_IMAGE_SIDE
        or encoded_height > MAX_IMAGE_SIDE
        or encoded_width * encoded_height > MAX_IMAGE_PIXELS
    ):
        raise AnonymizationError(f"imagem {member_name} excede a resolução permitida")
    encoded = np.frombuffer(payload, dtype=np.uint8)
    image = cv2.imdecode(encoded, cv2.IMREAD_COLOR)
    if image is None or image.size == 0 or image.ndim != 3 or image.shape[2] != 3:
        raise AnonymizationError(f"não foi possível decodificar a imagem {member_name}")
    height, width = image.shape[:2]
    if (width, height) != (encoded_width, encoded_height):
        raise AnonymizationError(f"dimensões decodificadas divergentes em {member_name}")
    if width > MAX_IMAGE_SIDE or height > MAX_IMAGE_SIDE:
        raise AnonymizationError(f"imagem {member_name} excede a resolução permitida")
    return image


def _clip_region(
    x: float,
    y: float,
    width: float,
    height: float,
    frame_width: int,
    frame_height: int,
    kind: str,
    score: float | None = None,
) -> Region | None:
    left = max(0, min(frame_width, math.floor(x)))
    top = max(0, min(frame_height, math.floor(y)))
    right = max(left, min(frame_width, math.ceil(x + width)))
    bottom = max(top, min(frame_height, math.ceil(y + height)))
    if right <= left or bottom <= top:
        return None
    return Region(left, top, right - left, bottom - top, kind, score)


def _iou(first: Region, second: Region) -> float:
    left = max(first.x, second.x)
    top = max(first.y, second.y)
    right = min(first.x2, second.x2)
    bottom = min(first.y2, second.y2)
    intersection = max(0, right - left) * max(0, bottom - top)
    if intersection == 0:
        return 0.0
    union = first.width * first.height + second.width * second.height - intersection
    return intersection / union if union else 0.0


def _deduplicate_regions(regions: Iterable[Region], overlap: float = 0.45) -> list[Region]:
    """Keep high-confidence regions while removing cascade/model duplicates."""

    ordered = sorted(
        regions,
        key=lambda region: (region.score or 0.0, region.width * region.height),
        reverse=True,
    )
    kept: list[Region] = []
    for candidate in ordered:
        if any(_iou(candidate, existing) >= overlap for existing in kept):
            continue
        kept.append(candidate)
    return kept


def _load_face_cascades() -> tuple[cv2.CascadeClassifier, ...]:
    base = Path(cv2.data.haarcascades)  # type: ignore[attr-defined]
    names = (
        "haarcascade_frontalface_default.xml",
        "haarcascade_frontalface_alt2.xml",
        "haarcascade_profileface.xml",
    )
    cascades: list[cv2.CascadeClassifier] = []
    for name in names:
        classifier = cv2.CascadeClassifier(str(base / name))
        if classifier.empty():
            raise AnonymizationError(f"cascata de face ausente: {name}")
        cascades.append(classifier)
    return tuple(cascades)


def _face_regions(image: np.ndarray, cascades: tuple[cv2.CascadeClassifier, ...]) -> list[Region]:
    """Find frontal/profile faces, including profiles observed after a flip."""

    height, width = image.shape[:2]
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    scale = min(1.0, FACE_DETECTION_MAX_SIDE / max(width, height))
    if scale < 1.0:
        detection_width = max(1, round(width * scale))
        detection_height = max(1, round(height * scale))
        gray = cv2.resize(gray, (detection_width, detection_height), interpolation=cv2.INTER_AREA)
    equalized = cv2.equalizeHist(gray)
    candidates: list[Region] = []

    def detect(source: np.ndarray, cascade: cv2.CascadeClassifier, flipped: bool = False) -> None:
        source_height, source_width = source.shape[:2]
        boxes = cascade.detectMultiScale(
            source,
            scaleFactor=1.10,
            minNeighbors=5,
            minSize=(18, 18),
            flags=cv2.CASCADE_SCALE_IMAGE,
        )
        x_scale = width / source_width
        y_scale = height / source_height
        for x, y, box_width, box_height in boxes:
            actual_x = source_width - x - box_width if flipped else x
            actual_x *= x_scale
            actual_y = y * y_scale
            actual_width = box_width * x_scale
            actual_height = box_height * y_scale
            # Include hair and chin; a tight face-only box can leave identity cues.
            expanded_x = actual_x - actual_width * 0.35
            expanded_y = actual_y - actual_height * 0.50
            expanded_width = actual_width * 1.70
            expanded_height = actual_height * 2.00
            region = _clip_region(
                expanded_x,
                expanded_y,
                expanded_width,
                expanded_height,
                width,
                height,
                "face",
                float(box_width * box_height),
            )
            if region is not None:
                candidates.append(region)

    detect(gray, cascades[0])
    detect(equalized, cascades[1])
    detect(gray, cascades[2])
    flipped_gray = cv2.flip(gray, 1)
    detect(flipped_gray, cascades[2], flipped=True)
    return _deduplicate_regions(candidates, overlap=0.35)


def _model_regions(
    image: np.ndarray,
    detections: Sequence[YoloDetection],
    *,
    profile: RedactionProfile = RedactionProfile.PUBLICATION,
) -> tuple[list[Region], list[Region], list[Region], list[Region]]:
    """Turn reviewed model classes into conservative privacy masks."""

    height, width = image.shape[:2]
    screens: list[Region] = []
    phones: list[Region] = []
    people: list[Region] = []
    head_zones: list[Region] = []
    for item in detections:
        if item.label == "person" and item.score >= PERSON_MIN_SCORE:
            people_region = _clip_region(
                item.x, item.y, item.width, item.height, width, height, "person", item.score
            )
            if people_region is not None:
                people.append(people_region)
                # A model person box is also a fail-safe when Haar cannot see a
                # profile, an occluded face, or a face in motion.  It intentionally
                # covers the head/shoulder zone rather than trying to infer identity.
                head_region = _clip_region(
                    item.x - item.width * 0.10,
                    item.y - item.height * 0.08,
                    item.width * 1.20,
                    item.height * (0.42 if profile is RedactionProfile.TRAINING else 0.65),
                    width,
                    height,
                    "person_head",
                    item.score,
                )
                if head_region is not None:
                    head_zones.append(head_region)
        elif item.label == "tv":
            if item.score < SCREEN_MIN_SCORE:
                continue
            # A small margin covers the complete visible display, including its border.
            region = _clip_region(
                item.x - item.width * 0.04,
                item.y - item.height * 0.04,
                item.width * 1.08,
                item.height * 1.08,
                width,
                height,
                "screen",
                item.score,
            )
            if region is not None:
                screens.append(region)
        elif item.label == "laptop":
            if item.score < SCREEN_MIN_SCORE:
                continue
            if profile is RedactionProfile.TRAINING:
                # Preserve enough of the laptop body and silhouette for object
                # annotation while hiding the visible display/content.
                region = _clip_region(
                    item.x + item.width * 0.03,
                    item.y + item.height * 0.02,
                    item.width * 0.94,
                    item.height * 0.62,
                    width,
                    height,
                    "screen",
                    item.score,
                )
            else:
                # Publication output prioritizes privacy over training utility.
                region = _clip_region(
                    item.x - item.width * 0.04,
                    item.y - item.height * 0.04,
                    item.width * 1.08,
                    item.height * 1.08,
                    width,
                    height,
                    "screen",
                    item.score,
                )
            if region is not None:
                screens.append(region)
        elif item.label == "cell_phone":
            if profile is RedactionProfile.TRAINING:
                # The authorized pilot was reviewed as containing no phones.  Do
                # not turn detector false positives into blurred training cues.
                continue
            if item.score < PHONE_MIN_SCORE:
                continue
            region = _clip_region(
                item.x - item.width * 0.15,
                item.y - item.height * 0.15,
                item.width * 1.30,
                item.height * 1.30,
                width,
                height,
                "phone",
                item.score,
            )
            if region is not None:
                phones.append(region)
    return (
        _deduplicate_regions(screens),
        _deduplicate_regions(phones),
        _deduplicate_regions(people),
        _deduplicate_regions(head_zones),
    )


def _privacy_blur(image: np.ndarray, region: Region) -> None:
    """Apply irreversible-looking pixelation plus a strong blur in-place."""

    crop = image[region.y : region.y2, region.x : region.x2]
    if crop.size == 0:
        return
    crop_height, crop_width = crop.shape[:2]
    # A tiny 4–12 pixel mosaic removes facial detail even when the source box is small.
    mosaic_width = max(2, min(12, crop_width // 10 or 2))
    mosaic_height = max(2, min(12, crop_height // 10 or 2))
    reduced = cv2.resize(crop, (mosaic_width, mosaic_height), interpolation=cv2.INTER_AREA)
    pixelated = cv2.resize(reduced, (crop_width, crop_height), interpolation=cv2.INTER_NEAREST)
    kernel_size = max(3, min(51, (min(crop_width, crop_height) // 2) | 1))
    if kernel_size % 2 == 0:
        kernel_size += 1
    image[region.y : region.y2, region.x : region.x2] = cv2.GaussianBlur(
        pixelated, (kernel_size, kernel_size), 0
    )


def _encode_jpeg(image: np.ndarray) -> bytes:
    success, encoded = cv2.imencode(".jpg", image, [int(cv2.IMWRITE_JPEG_QUALITY), JPEG_QUALITY])
    if not success:
        raise AnonymizationError("falha ao reencodar a imagem anonimizada")
    payload = encoded.tobytes()
    # OpenCV's fresh JPEG must not contain an EXIF APP1 payload.  Refuse to emit
    # anything that unexpectedly carries one if a future codec changes defaults.
    if b"Exif\x00\x00" in payload or b"http://ns.adobe.com/xap/1.0/" in payload:
        raise AnonymizationError("o reencodificador tentou preservar metadados de imagem")
    return payload


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _read_member(archive: zipfile.ZipFile, info: zipfile.ZipInfo) -> bytes:
    with archive.open(info, "r") as stream:
        payload = stream.read(MAX_ENTRY_BYTES + 1)
    if len(payload) > MAX_ENTRY_BYTES:
        raise AnonymizationError("entrada ZIP excedeu o limite durante a leitura")
    return payload


def _write_text(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8", newline="\n")


def _manifest(
    results: Sequence[ImageResult],
    warnings: Sequence[str],
    *,
    profile: RedactionProfile,
) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "redaction_profile": profile.value,
        "phone_absence_user_attested": profile is RedactionProfile.TRAINING,
        "human_privacy_review_required": True,
        "privacy": {
            "faces": "opencv-haar-frontal-profile-expanded-and-pixelated",
            "person_head_fallback": (
                "training-upper-42-percent-of-person-box"
                if profile is RedactionProfile.TRAINING
                else "publication-upper-65-percent-of-person-box"
            ),
            "screens": (
                "training-tv-full-and-laptop-display-region-pixelated"
                if profile is RedactionProfile.TRAINING
                else "publication-tv-and-laptop-boxes-expanded-and-pixelated"
            ),
            "phones": (
                "training-phone-redaction-disabled-after-human-absence-review"
                if profile is RedactionProfile.TRAINING
                else "publication-intel-yolo26-cell_phone-regions"
            ),
            "metadata": "fresh-jpeg-reencode; exif-xmp-icc-not-copied",
            "filenames": "sequential-neutral-names; source-names-omitted",
        },
        "summary": {
            "images": len(results),
            "faces_redacted": sum(item.faces_redacted for item in results),
            "head_zones_redacted": sum(item.head_zones_redacted for item in results),
            "screens_redacted": sum(item.screens_redacted for item in results),
            "phones_redacted": sum(item.phones_redacted for item in results),
            "people_detected": sum(item.people_detected for item in results),
        },
        "warnings": list(warnings),
        "images": [
            {
                "file": item.output_name,
                "width": item.width,
                "height": item.height,
                "faces_redacted": item.faces_redacted,
                "head_zones_redacted": item.head_zones_redacted,
                "screens_redacted": item.screens_redacted,
                "phones_redacted": item.phones_redacted,
                "people_detected": item.people_detected,
                "sha256": item.encoded_sha256,
            }
            for item in results
        ],
    }


def _zip_output(output_dir: Path, output_zip: Path) -> None:
    if output_zip.exists():
        raise AnonymizationError(f"arquivo de saída já existe: {output_zip}")
    output_zip.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(
        output_zip,
        mode="x",
        compression=zipfile.ZIP_DEFLATED,
        compresslevel=6,
        allowZip64=False,
    ) as archive:
        for path in sorted(output_dir.iterdir(), key=lambda item: item.name.casefold()):
            if not path.is_file():
                continue
            info = zipfile.ZipInfo(path.name, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.create_system = 0
            info.extra = b""
            info.comment = b""
            archive.writestr(info, path.read_bytes())


def anonymize_archive(
    input_zip: Path,
    output_dir: Path,
    output_zip: Path,
    *,
    detector: IntelYoloDetector,
    profile: RedactionProfile = RedactionProfile.PUBLICATION,
) -> tuple[dict[str, Any], Path]:
    """Anonymize an archive into a new directory and ZIP, atomically."""

    if not input_zip.is_file():
        raise AnonymizationError(f"ZIP de entrada não encontrado: {input_zip}")
    input_resolved = input_zip.resolve()
    output_dir = output_dir.resolve()
    output_zip = output_zip.resolve()
    if output_dir == input_resolved or output_zip == input_resolved:
        raise AnonymizationError("a saída não pode substituir o ZIP original")
    if (
        output_dir == output_zip
        or output_dir in output_zip.parents
        or output_zip in output_dir.parents
    ):
        raise AnonymizationError("a pasta e o ZIP de saída devem ser destinos separados")
    if output_dir.parent != output_zip.parent:
        raise AnonymizationError("a pasta e o ZIP de saída devem usar o mesmo diretório pai")
    if output_dir.exists() or output_zip.exists():
        raise AnonymizationError("a pasta ou ZIP de saída já existe; escolha um destino novo")
    output_dir.parent.mkdir(parents=True, exist_ok=True)
    face_cascades = _load_face_cascades()
    results: list[ImageResult] = []
    warnings: list[str] = [
        (
            "Revisão humana continua obrigatória: cascatas podem não detectar perfis, "
            "faces pequenas, crachás, logos ou texto."
        ),
        (
            "As regiões de telas/notebooks e as zonas de cabeça dependem do modelo "
            "Intel e podem incluir falsos positivos."
        ),
        (
            "As imagens foram autorizadas pelo usuário para o TCC; não publicar sem "
            "confirmar consentimento e finalidade."
        ),
    ]
    if profile is RedactionProfile.TRAINING:
        warnings.append(
            "A redação automática de celular foi desativada somente porque o usuário "
            "atestou ausência dessa classe; a revisão visual de privacidade segue obrigatória."
        )
    else:
        warnings.append(
            "Regiões candidatas de celular também são redigidas e podem incluir falsos positivos."
        )

    staging_parent = output_dir.parent
    with tempfile.TemporaryDirectory(
        prefix="smart-environment-anonymize-", dir=staging_parent
    ) as temp_name:
        staging = Path(temp_name) / output_dir.name
        staging.mkdir()
        try:
            with zipfile.ZipFile(input_zip, mode="r") as archive:
                members = _image_members(archive)
                for index, info in enumerate(members, start=1):
                    source_name = _safe_member_name(info.filename)
                    image = _decode_image(_read_member(archive, info), source_name)
                    faces = _face_regions(image, face_cascades)
                    detections = detector.detect(image)
                    screens, phones, people, head_zones = _model_regions(
                        image,
                        detections,
                        profile=profile,
                    )
                    for region in (*screens, *phones, *head_zones, *faces):
                        _privacy_blur(image, region)
                    payload = _encode_jpeg(image)
                    output_name = f"frame_{index:03d}.jpg"
                    (staging / output_name).write_bytes(payload)
                    results.append(
                        ImageResult(
                            output_name=output_name,
                            width=int(image.shape[1]),
                            height=int(image.shape[0]),
                            faces_redacted=len(faces),
                            head_zones_redacted=len(head_zones),
                            screens_redacted=len(screens),
                            phones_redacted=len(phones),
                            people_detected=len(people),
                            encoded_sha256=_sha256(payload),
                        )
                    )
            if not results:
                raise AnonymizationError("nenhuma imagem foi processada")
            manifest = _manifest(results, warnings, profile=profile)
            _write_text(
                staging / "manifest.json",
                json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            )
            _write_text(
                staging / "README.txt",
                "Cópia anonimizada para revisão autorizada.\n"
                f"Perfil de redação: {profile.value}.\n"
                "Rostos, zonas superiores de pessoas e telas detectadas foram "
                "pixelados e desfocados.\n"
                + (
                    "A redação automática de celular ficou desativada neste perfil após "
                    "o usuário atestar que não há celulares nas fotos.\n"
                    if profile is RedactionProfile.TRAINING
                    else "Regiões candidatas de celular também foram redigidas.\n"
                )
                + "Os arquivos foram reencodados como JPEG sem EXIF/XMP/ICC copiados.\n"
                "Faça revisão visual antes de compartilhar: logos, crachás, textos e "
                "faces pequenas podem permanecer.\n",
            )
            staging_zip = Path(temp_name) / f"{output_dir.name}.zip"
            _zip_output(staging, staging_zip)
            published_directory = False
            try:
                staging.rename(output_dir)
                published_directory = True
                staging_zip.rename(output_zip)
            except Exception:
                if published_directory and output_dir.is_dir():
                    shutil.rmtree(output_dir)
                raise
            return manifest, output_dir
        except Exception:
            # The temporary directory is removed by TemporaryDirectory; no existing
            # user data is touched and partial output is never exposed at the target.
            raise


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input-zip", type=Path, required=True, help="ZIP original, somente leitura"
    )
    parser.add_argument("--output-dir", type=Path, required=True, help="pasta nova para as imagens")
    parser.add_argument("--output-zip", type=Path, required=True, help="ZIP novo anonimizado")
    parser.add_argument(
        "--confidence-threshold",
        type=float,
        default=0.15,
        help="limiar do modelo Intel para ampliar a captura de telas (padrão: 0.15)",
    )
    parser.add_argument(
        "--profile",
        choices=tuple(profile.value for profile in RedactionProfile),
        default=RedactionProfile.PUBLICATION.value,
        help="publication prioriza privacidade; training preserva contornos úteis",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    try:
        detector = IntelYoloDetector(MODEL_CLASSES, confidence_threshold=args.confidence_threshold)
        manifest, output_dir = anonymize_archive(
            args.input_zip,
            args.output_dir,
            args.output_zip,
            detector=detector,
            profile=RedactionProfile(args.profile),
        )
    except (AnonymizationError, ValueError, OSError, zipfile.BadZipFile) as exc:
        print(f"ERRO: {exc}")
        return 2
    summary = manifest["summary"]
    print(f"OK: {summary['images']} imagens em {output_dir}")
    print(
        "Redações: "
        f"faces={summary['faces_redacted']}, "
        f"zonas_de_cabeca={summary['head_zones_redacted']}, "
        f"telas={summary['screens_redacted']}, "
        f"celulares={summary['phones_redacted']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
