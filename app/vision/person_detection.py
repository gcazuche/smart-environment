"""Replaceable local person detector."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Protocol, cast

import cv2
import numpy as np

from app.cameras.opencv_source import Frame


@dataclass(frozen=True, slots=True)
class Detection:
    """A person candidate; score is a detector margin, not a probability."""

    x: int
    y: int
    width: int
    height: int
    score: float


class PersonDetector(Protocol):
    def detect(self, frame: Frame) -> tuple[Detection, ...]: ...


class HogLike(Protocol):
    def setSVMDetector(self, detector: object) -> None: ...  # noqa: N802

    def detectMultiScale(  # noqa: N802
        self,
        image: Frame,
        *,
        winStride: tuple[int, int],
        padding: tuple[int, int],
        scale: float,
    ) -> tuple[Sequence[Sequence[int]], Sequence[float]]: ...


HogFactory = Callable[[], HogLike]


def _default_hog_factory() -> HogLike:
    hog = cv2.HOGDescriptor()
    svm_detector = np.asarray(cv2.HOGDescriptor.getDefaultPeopleDetector(), dtype=np.float64)
    hog.setSVMDetector(svm_detector)
    return cast(HogLike, hog)


def _contains(outer: Detection, inner: Detection) -> bool:
    return (
        outer.x <= inner.x
        and outer.y <= inner.y
        and outer.x + outer.width >= inner.x + inner.width
        and outer.y + outer.height >= inner.y + inner.height
    )


class HogPersonDetector:
    """CPU-first full-body baseline bundled with OpenCV."""

    def __init__(self, *, hog_factory: HogFactory = _default_hog_factory) -> None:
        self._hog = hog_factory()

    def detect(self, frame: Frame) -> tuple[Detection, ...]:
        if (
            not isinstance(frame, np.ndarray)
            or frame.dtype != np.uint8
            or frame.ndim != 3
            or frame.shape[2] != 3
            or frame.size == 0
        ):
            raise ValueError("frame inválido para detecção")

        boxes, weights = self._hog.detectMultiScale(
            frame,
            winStride=(8, 8),
            padding=(8, 8),
            scale=1.05,
        )
        frame_height, frame_width = frame.shape[:2]
        candidates: list[Detection] = []
        for box, weight in zip(boxes, weights, strict=True):
            x, y, width, height = (int(value) for value in box)
            left = max(0, x)
            top = max(0, y)
            right = min(frame_width, x + width)
            bottom = min(frame_height, y + height)
            if right <= left or bottom <= top:
                continue
            candidates.append(Detection(left, top, right - left, bottom - top, float(weight)))

        result = [
            candidate
            for candidate in candidates
            if not any(other != candidate and _contains(other, candidate) for other in candidates)
        ]
        return tuple(sorted(result, key=lambda item: item.score, reverse=True))
