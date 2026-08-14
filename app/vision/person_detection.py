"""Replaceable local person detector."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol, cast

import cv2
import numpy as np

from app.cameras.opencv_source import Frame


@dataclass(frozen=True, slots=True)
class Detection:
    """A person candidate; score is detector-specific, not a probability."""

    x: int
    y: int
    width: int
    height: int
    score: float
    source: str = "full_body"


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


class UpperBodyLike(Protocol):
    def empty(self) -> bool: ...

    def detectMultiScale(  # noqa: N802
        self,
        image: Frame,
        *,
        scaleFactor: float,
        minNeighbors: int,
        minSize: tuple[int, int],
    ) -> Sequence[Sequence[int]]: ...


UpperBodyFactory = Callable[[], UpperBodyLike]


def _default_hog_factory() -> HogLike:
    hog = cv2.HOGDescriptor()
    svm_detector = np.asarray(cv2.HOGDescriptor.getDefaultPeopleDetector(), dtype=np.float64)
    hog.setSVMDetector(svm_detector)
    return cast(HogLike, hog)


def _default_upper_body_factory() -> UpperBodyLike:
    cascade_path = Path(cv2.__file__).resolve().parent / "data" / "haarcascade_upperbody.xml"
    cascade = cv2.CascadeClassifier(str(cascade_path))
    if cascade.empty():
        raise RuntimeError("classificador local de parte superior indisponível")
    return cast(UpperBodyLike, cascade)


def _validate_frame(frame: Frame) -> None:
    if (
        not isinstance(frame, np.ndarray)
        or frame.dtype != np.uint8
        or frame.ndim != 3
        or frame.shape[2] != 3
        or frame.size == 0
    ):
        raise ValueError("frame inválido para detecção")


def _clip_detection(
    box: Sequence[int],
    *,
    frame_width: int,
    frame_height: int,
    score: float,
    source: str,
) -> Detection | None:
    x, y, width, height = (int(value) for value in box)
    left = max(0, x)
    top = max(0, y)
    right = min(frame_width, x + width)
    bottom = min(frame_height, y + height)
    if right <= left or bottom <= top:
        return None
    return Detection(left, top, right - left, bottom - top, score, source)


def _duplicate_overlap(first: Detection, second: Detection) -> bool:
    left = max(first.x, second.x)
    top = max(first.y, second.y)
    right = min(first.x + first.width, second.x + second.width)
    bottom = min(first.y + first.height, second.y + second.height)
    intersection = max(0, right - left) * max(0, bottom - top)
    if intersection == 0:
        return False
    first_area = first.width * first.height
    second_area = second.width * second.height
    union = first_area + second_area - intersection
    return intersection / min(first_area, second_area) >= 0.8 or intersection / union >= 0.5


def _deduplicate(candidates: Sequence[Detection]) -> tuple[Detection, ...]:
    preferred = sorted(
        candidates,
        key=lambda item: (
            item.width * item.height,
            item.source == "full_body",
            item.score,
        ),
        reverse=True,
    )
    kept: list[Detection] = []
    for candidate in preferred:
        if not any(_duplicate_overlap(candidate, existing) for existing in kept):
            kept.append(candidate)
    return tuple(sorted(kept, key=lambda item: item.score, reverse=True))


class HogPersonDetector:
    """CPU-first full-body baseline bundled with OpenCV."""

    def __init__(self, *, hog_factory: HogFactory = _default_hog_factory) -> None:
        self._hog = hog_factory()

    def detect(self, frame: Frame) -> tuple[Detection, ...]:
        _validate_frame(frame)

        boxes, weights = self._hog.detectMultiScale(
            frame,
            winStride=(8, 8),
            padding=(8, 8),
            scale=1.05,
        )
        frame_height, frame_width = frame.shape[:2]
        candidates: list[Detection] = []
        for box, weight in zip(boxes, weights, strict=True):
            detection = _clip_detection(
                box,
                frame_width=frame_width,
                frame_height=frame_height,
                score=float(weight),
                source="full_body",
            )
            if detection is not None:
                candidates.append(detection)
        return _deduplicate(candidates)


class HybridPersonDetector:
    """Local CPU baseline combining full-body and upper-body evidence."""

    def __init__(
        self,
        *,
        hog_factory: HogFactory = _default_hog_factory,
        upper_body_factory: UpperBodyFactory = _default_upper_body_factory,
    ) -> None:
        self._hog = HogPersonDetector(hog_factory=hog_factory)
        self._upper_body = upper_body_factory()
        if self._upper_body.empty():
            raise RuntimeError("classificador local de parte superior indisponível")

    def detect(self, frame: Frame) -> tuple[Detection, ...]:
        _validate_frame(frame)
        candidates = list(self._hog.detect(frame))
        grayscale = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        normalized = cast(Frame, cv2.equalizeHist(grayscale))
        boxes = self._upper_body.detectMultiScale(
            normalized,
            scaleFactor=1.05,
            minNeighbors=4,
            minSize=(24, 24),
        )
        frame_height, frame_width = frame.shape[:2]
        for box in boxes:
            detection = _clip_detection(
                box,
                frame_width=frame_width,
                frame_height=frame_height,
                score=0.5,
                source="upper_body",
            )
            if detection is not None:
                candidates.append(detection)
        return _deduplicate(candidates)
