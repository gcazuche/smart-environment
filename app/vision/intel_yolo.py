"""Shared Intel YOLO26/OpenVINO inference with an explicit class allowlist."""

from __future__ import annotations

import hashlib
import math
import re
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np

from app.cameras.opencv_source import Frame

MODEL_XML_SHA256 = "d9120135a234b51dcfae7ee904247df7bfc7830d55955beedb1aed3c7400f2e1"
MODEL_BIN_SHA256 = "f555e06c74c0ab1d4338428bf41ca5f6674f25902f2c6a4530b5af3605485193"
MODEL_RELATIVE_PATH = Path("models/intel-person/yolo26n_openvino_model/yolo26n.xml")

_LABEL_PATTERN = re.compile(r"[a-z][a-z0-9_]{0,31}", re.ASCII)
_COCO_CLASS_COUNT = 80


class IntelYoloModelError(RuntimeError):
    """Raised when the pinned Intel model is unavailable, altered, or cannot run."""


@dataclass(frozen=True, slots=True)
class YoloDetection:
    """One allowlisted COCO object emitted by the local model."""

    x: int
    y: int
    width: int
    height: int
    score: float
    class_id: int
    label: str


InferenceRunner = Callable[[np.ndarray], np.ndarray]
RunnerFactory = Callable[[Path, str], InferenceRunner]


def default_model_path() -> Path:
    return Path(__file__).resolve().parents[2] / MODEL_RELATIVE_PATH


def _digest(path: Path) -> str:
    with path.open("rb") as artifact:
        return hashlib.file_digest(artifact, "sha256").hexdigest()


def _validate_model(model_path: Path, xml_sha256: str, bin_sha256: str) -> None:
    weights_path = model_path.with_suffix(".bin")
    if not model_path.is_file() or not weights_path.is_file():
        raise IntelYoloModelError(
            "modelo Intel ausente; execute scripts/download_intel_person_detection.ps1"
        )
    if _digest(model_path) != xml_sha256 or _digest(weights_path) != bin_sha256:
        raise IntelYoloModelError("hash do modelo Intel não confere")


def default_runner_factory(model_path: Path, device: str) -> InferenceRunner:
    try:
        import openvino as ov  # type: ignore[import-untyped]
    except ModuleNotFoundError as exc:
        raise IntelYoloModelError(
            "OpenVINO ausente no Conda; recrie smart-environment com environment.yml"
        ) from exc

    try:
        core = ov.Core()
        compiled = core.compile_model(core.read_model(model_path), device)
        output_port = compiled.output(0)
    except Exception as exc:
        raise IntelYoloModelError("não foi possível carregar o modelo Intel local") from exc

    def run(blob: np.ndarray) -> np.ndarray:
        try:
            return np.asarray(compiled([blob])[output_port])
        except Exception as exc:
            raise IntelYoloModelError("falha local durante a inferência Intel") from exc

    return run


def _validate_frame(frame: Frame) -> None:
    if (
        not isinstance(frame, np.ndarray)
        or frame.dtype != np.uint8
        or frame.ndim != 3
        or frame.shape[2] != 3
        or frame.size == 0
    ):
        raise ValueError("frame inválido para detecção")


def _validate_target_classes(target_classes: Mapping[int, str]) -> dict[int, str]:
    if not target_classes:
        raise ValueError("ao menos uma classe alvo deve ser configurada")
    reviewed: dict[int, str] = {}
    for class_id, label in target_classes.items():
        if (
            isinstance(class_id, bool)
            or not isinstance(class_id, int)
            or not 0 <= class_id < _COCO_CLASS_COUNT
        ):
            raise ValueError("ID de classe COCO inválido")
        if not isinstance(label, str) or _LABEL_PATTERN.fullmatch(label) is None:
            raise ValueError("rótulo de classe inválido")
        if label in reviewed.values():
            raise ValueError("rótulos de classe devem ser únicos")
        reviewed[class_id] = label
    return reviewed


class IntelYoloDetector:
    """Pinned YOLO26n inference restricted to explicitly reviewed COCO classes."""

    def __init__(
        self,
        target_classes: Mapping[int, str],
        model_path: Path | None = None,
        *,
        confidence_threshold: float = 0.4,
        device: str = "CPU",
        xml_sha256: str = MODEL_XML_SHA256,
        bin_sha256: str = MODEL_BIN_SHA256,
        runner_factory: RunnerFactory = default_runner_factory,
    ) -> None:
        if (
            isinstance(confidence_threshold, bool)
            or not math.isfinite(confidence_threshold)
            or not 0 < confidence_threshold <= 1
        ):
            raise ValueError("confidence_threshold deve estar entre zero e um")
        if not device.strip() or len(device) > 64 or not device.isascii():
            raise ValueError("device OpenVINO inválido")
        self._target_classes = _validate_target_classes(target_classes)
        self._model_path = model_path or default_model_path()
        _validate_model(self._model_path, xml_sha256, bin_sha256)
        self._runner = runner_factory(self._model_path, device)
        self._confidence_threshold = confidence_threshold
        self._input_size = 640
        self.model_xml_sha256 = xml_sha256
        self.model_bin_sha256 = bin_sha256

    @property
    def confidence_threshold(self) -> float:
        """Detector-level threshold applied before downstream class policy."""

        return self._confidence_threshold

    def detect(self, frame: Frame) -> tuple[YoloDetection, ...]:
        _validate_frame(frame)
        frame_height, frame_width = frame.shape[:2]
        resized = cv2.resize(frame, (self._input_size, self._input_size))
        rgb = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
        blob = rgb.astype(np.float32) / 255.0
        blob = blob.transpose(2, 0, 1)[np.newaxis, ...]
        output = np.asarray(self._runner(blob))
        if output.shape == (1, 300, 6):
            output = output[0]
        if output.ndim != 2 or output.shape[1] != 6:
            raise IntelYoloModelError("saída inesperada do modelo Intel")

        x_scale = frame_width / self._input_size
        y_scale = frame_height / self._input_size
        detections: list[YoloDetection] = []
        for row in output:
            if not np.isfinite(row).all():
                continue
            score = float(row[4])
            raw_class_id = float(row[5])
            class_id = int(round(raw_class_id))
            label = self._target_classes.get(class_id)
            if (
                label is None
                or abs(raw_class_id - class_id) > 1e-3
                or score < self._confidence_threshold
            ):
                continue
            x1 = max(0, min(frame_width, round(float(row[0]) * x_scale)))
            y1 = max(0, min(frame_height, round(float(row[1]) * y_scale)))
            x2 = max(0, min(frame_width, round(float(row[2]) * x_scale)))
            y2 = max(0, min(frame_height, round(float(row[3]) * y_scale)))
            if x2 <= x1 or y2 <= y1:
                continue
            detections.append(
                YoloDetection(
                    x=x1,
                    y=y1,
                    width=x2 - x1,
                    height=y2 - y1,
                    score=score,
                    class_id=class_id,
                    label=label,
                )
            )
        return tuple(sorted(detections, key=lambda item: item.score, reverse=True))
