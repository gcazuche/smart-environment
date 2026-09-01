"""Shared validation for immutable local image references."""

from __future__ import annotations

import hashlib
import re
from pathlib import Path
from typing import Protocol

import cv2
import numpy as np

_SHA256_PATTERN = re.compile(r"[0-9a-f]{64}", re.ASCII)
_PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


class PinnedImageReference(Protocol):
    """Minimum metadata needed to validate an immutable image."""

    @property
    def filename(self) -> str: ...

    @property
    def sha256(self) -> str: ...


def validate_pinned_image_payload(
    payload: bytes,
    reference: PinnedImageReference,
) -> tuple[int, int]:
    """Verify digest, declared file format and decodability."""

    if _SHA256_PATTERN.fullmatch(reference.sha256) is None:
        raise ValueError("hash de referência inválido")
    if hashlib.sha256(payload).hexdigest() != reference.sha256:
        raise RuntimeError(f"hash inesperado para {reference.filename}")

    suffix = Path(reference.filename).suffix.lower()
    if suffix in {".jpg", ".jpeg"}:
        if not payload.startswith(b"\xff\xd8"):
            raise RuntimeError(f"{reference.filename} não é JPEG")
    elif suffix == ".png":
        if not payload.startswith(_PNG_SIGNATURE):
            raise RuntimeError(f"{reference.filename} não é PNG")
    else:
        raise ValueError(f"formato de referência não permitido: {suffix or 'ausente'}")

    decoded = cv2.imdecode(np.frombuffer(payload, dtype=np.uint8), cv2.IMREAD_COLOR)
    if decoded is None or decoded.ndim != 3 or decoded.size == 0:
        raise RuntimeError(f"imagem inválida: {reference.filename}")
    height, width = decoded.shape[:2]
    return int(width), int(height)
