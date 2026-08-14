"""Local live person-detection loop with no frame persistence."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

import cv2

from app.cameras.opencv_source import Frame
from app.vision import Detection, PersonDetector


class DisplayLike(Protocol):
    def show(self, frame: Frame) -> bool: ...

    def close(self) -> None: ...


class CameraLike(Protocol):
    backend_name: str | None

    def open(self) -> None: ...

    def read(self) -> Frame: ...

    def close(self) -> None: ...


class OpenCVDisplay:
    """Display annotated frames; q or Escape requests a stop."""

    def __init__(self, window_name: str = "Smart Environment - Pessoas") -> None:
        self._window_name = window_name

    def show(self, frame: Frame) -> bool:
        cv2.imshow(self._window_name, frame)
        key = cv2.waitKey(1) & 0xFF
        return key in (ord("q"), 27)

    def close(self) -> None:
        cv2.destroyAllWindows()


class NullDisplay:
    def show(self, frame: Frame) -> bool:
        del frame
        return False

    def close(self) -> None:
        return None


@dataclass(frozen=True, slots=True)
class RunSummary:
    frames_processed: int
    last_count: int
    max_count: int
    backend_name: str
    stopped_by: str


def annotate_frame(frame: Frame, detections: tuple[Detection, ...]) -> Frame:
    """Return an annotated copy, leaving the camera-owned frame untouched."""

    annotated = frame.copy()
    for detection in detections:
        top_left = (detection.x, detection.y)
        bottom_right = (detection.x + detection.width, detection.y + detection.height)
        cv2.rectangle(annotated, top_left, bottom_right, (40, 220, 40), 2)
    cv2.putText(
        annotated,
        f"Pessoas detectadas: {len(detections)}",
        (12, 28),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.65,
        (40, 220, 40),
        2,
        cv2.LINE_AA,
    )
    cv2.putText(
        annotated,
        "Q ou Esc para sair",
        (12, 54),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.5,
        (255, 255, 255),
        1,
        cv2.LINE_AA,
    )
    return annotated


def run_person_detection(
    camera: CameraLike,
    detector: PersonDetector,
    display: DisplayLike,
    *,
    max_frames: int | None = None,
) -> RunSummary:
    """Process frames locally and always release camera and display resources."""

    if max_frames is not None and max_frames <= 0:
        raise ValueError("max_frames deve ser positivo")

    processed = 0
    last_count = 0
    maximum = 0
    stopped_by = "display"
    try:
        camera.open()
        while True:
            frame = camera.read()
            detections = detector.detect(frame)
            processed += 1
            last_count = len(detections)
            maximum = max(maximum, last_count)
            if display.show(annotate_frame(frame, detections)):
                stopped_by = "operator"
                break
            if max_frames is not None and processed >= max_frames:
                stopped_by = "frame_limit"
                break
    finally:
        display.close()
        camera.close()

    return RunSummary(processed, last_count, maximum, camera.backend_name or "unknown", stopped_by)
