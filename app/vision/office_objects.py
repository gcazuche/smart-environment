"""Restricted office-object signals for the initial fixed-workstation context."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType

from app.cameras.opencv_source import Frame
from app.vision.intel_yolo import (
    MODEL_BIN_SHA256,
    MODEL_XML_SHA256,
    IntelYoloDetector,
    RunnerFactory,
    default_runner_factory,
)

OFFICE_OBJECT_CLASSES: Mapping[int, str] = MappingProxyType(
    {
        63: "laptop",
        64: "mouse",
        66: "keyboard",
        67: "cell_phone",
    }
)


@dataclass(frozen=True, slots=True)
class OfficeObjectDetection:
    """A visible object candidate; it does not describe a person's activity or intent."""

    x: int
    y: int
    width: int
    height: int
    score: float
    label: str
    source: str = "intel_yolo26"


class IntelOfficeObjectDetector:
    """Detect only reviewed workstation-related COCO classes with the local model."""

    def __init__(
        self,
        model_path: Path | None = None,
        *,
        confidence_threshold: float = 0.25,
        device: str = "CPU",
        xml_sha256: str = MODEL_XML_SHA256,
        bin_sha256: str = MODEL_BIN_SHA256,
        runner_factory: RunnerFactory = default_runner_factory,
    ) -> None:
        self._detector = IntelYoloDetector(
            OFFICE_OBJECT_CLASSES,
            model_path,
            confidence_threshold=confidence_threshold,
            device=device,
            xml_sha256=xml_sha256,
            bin_sha256=bin_sha256,
            runner_factory=runner_factory,
        )
        self.confidence_threshold = confidence_threshold
        self.target_labels = tuple(OFFICE_OBJECT_CLASSES.values())

    def detect(self, frame: Frame) -> tuple[OfficeObjectDetection, ...]:
        return tuple(
            OfficeObjectDetection(
                x=item.x,
                y=item.y,
                width=item.width,
                height=item.height,
                score=item.score,
                label=item.label,
            )
            for item in self._detector.detect(frame)
        )
