"""Person-only adapter over the pinned Intel YOLO26/OpenVINO runtime."""

from __future__ import annotations

from pathlib import Path

from app.cameras.opencv_source import Frame
from app.vision.intel_yolo import (
    MODEL_BIN_SHA256,
    MODEL_XML_SHA256,
    IntelYoloDetector,
    IntelYoloModelError,
    RunnerFactory,
    default_runner_factory,
)
from app.vision.person_detection import Detection

IntelPersonModelError = IntelYoloModelError


class IntelPersonDetector:
    """Experimental YOLO26n FP16 detector filtered to the COCO person class."""

    def __init__(
        self,
        model_path: Path | None = None,
        *,
        confidence_threshold: float = 0.4,
        device: str = "CPU",
        xml_sha256: str = MODEL_XML_SHA256,
        bin_sha256: str = MODEL_BIN_SHA256,
        runner_factory: RunnerFactory = default_runner_factory,
    ) -> None:
        self._detector = IntelYoloDetector(
            {0: "person"},
            model_path,
            confidence_threshold=confidence_threshold,
            device=device,
            xml_sha256=xml_sha256,
            bin_sha256=bin_sha256,
            runner_factory=runner_factory,
        )

    def detect(self, frame: Frame) -> tuple[Detection, ...]:
        return tuple(
            Detection(
                item.x,
                item.y,
                item.width,
                item.height,
                item.score,
                "intel_yolo26",
            )
            for item in self._detector.detect(frame)
        )
