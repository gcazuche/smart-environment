"""NanoDet person-only inference using OpenCV DNN.

The decoding and letterbox math follow the Apache-2.0 OpenCV Zoo NanoDet sample,
adapted to discard every COCO class except ``person`` before NMS.
"""

from __future__ import annotations

import hashlib
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Protocol, cast

import cv2
import numpy as np

from app.cameras.opencv_source import Frame
from app.vision.person_detection import Detection

MODEL_SHA256 = "4b82da9944b88577175ee23a459dce2e26e6e4be573def65b1055dc2d9720186"
MODEL_RELATIVE_PATH = Path("models/nanodet/object_detection_nanodet_2022nov.onnx")


class NanoDetModelError(RuntimeError):
    """Raised when the local model is missing, altered, or cannot run."""


class DnnNetLike(Protocol):
    def setInput(self, blob: np.ndarray) -> None: ...  # noqa: N802

    def getUnconnectedOutLayersNames(self) -> Sequence[str]: ...  # noqa: N802

    def forward(self, names: Sequence[str]) -> Sequence[np.ndarray]: ...


NetFactory = Callable[[Path], DnnNetLike]


def _default_net_factory(model_path: Path) -> DnnNetLike:
    try:
        return cast(DnnNetLike, cv2.dnn.readNet(str(model_path)))
    except cv2.error as exc:
        raise NanoDetModelError("não foi possível carregar o modelo NanoDet local") from exc


def default_model_path() -> Path:
    return Path(__file__).resolve().parents[2] / MODEL_RELATIVE_PATH


def _validate_model(model_path: Path, expected_sha256: str) -> None:
    if not model_path.is_file():
        raise NanoDetModelError("modelo NanoDet ausente; execute scripts/download_nanodet.ps1")
    with model_path.open("rb") as model_file:
        digest = hashlib.file_digest(model_file, "sha256").hexdigest()
    if digest != expected_sha256:
        raise NanoDetModelError("hash do modelo NanoDet não confere")


def _validate_frame(frame: Frame) -> None:
    if (
        not isinstance(frame, np.ndarray)
        or frame.dtype != np.uint8
        or frame.ndim != 3
        or frame.shape[2] != 3
        or frame.size == 0
    ):
        raise ValueError("frame inválido para detecção")


def _letterbox(frame: Frame, size: int) -> tuple[Frame, tuple[int, int, int, int]]:
    height, width = frame.shape[:2]
    scale = min(size / width, size / height)
    resized_width = max(1, round(width * scale))
    resized_height = max(1, round(height * scale))
    resized = cv2.resize(frame, (resized_width, resized_height), interpolation=cv2.INTER_AREA)
    left = (size - resized_width) // 2
    right = size - resized_width - left
    top = (size - resized_height) // 2
    bottom = size - resized_height - top
    padded = cv2.copyMakeBorder(
        resized,
        top,
        bottom,
        left,
        right,
        cv2.BORDER_CONSTANT,
        value=(0, 0, 0),
    )
    return cast(Frame, padded), (top, left, resized_height, resized_width)


def _anchors(size: int, stride: int) -> np.ndarray:
    feature_size = size // stride
    shift = np.arange(feature_size, dtype=np.float32) * stride + 0.5 * (stride - 1)
    x_coordinates, y_coordinates = np.meshgrid(shift, shift)
    return np.column_stack((x_coordinates.ravel(), y_coordinates.ravel()))


class NanoDetPersonDetector:
    """Multiple-person NanoDet baseline with local, hash-pinned ONNX weights."""

    def __init__(
        self,
        model_path: Path | None = None,
        *,
        confidence_threshold: float = 0.35,
        iou_threshold: float = 0.6,
        expected_sha256: str = MODEL_SHA256,
        net_factory: NetFactory = _default_net_factory,
    ) -> None:
        if not 0 < confidence_threshold <= 1:
            raise ValueError("confidence_threshold deve estar entre zero e um")
        if not 0 < iou_threshold <= 1:
            raise ValueError("iou_threshold deve estar entre zero e um")
        self._model_path = model_path or default_model_path()
        _validate_model(self._model_path, expected_sha256)
        self._net = net_factory(self._model_path)
        self._confidence_threshold = confidence_threshold
        self._iou_threshold = iou_threshold
        self._size = 416
        self._strides = (8, 16, 32)
        self._reg_max = 7
        self._project = np.arange(self._reg_max + 1, dtype=np.float32)
        self._anchors = tuple(_anchors(self._size, stride) for stride in self._strides)
        self._mean = np.array([103.53, 116.28, 123.675], dtype=np.float32).reshape(1, 1, 3)
        self._std = np.array([57.375, 57.12, 58.395], dtype=np.float32).reshape(1, 1, 3)

    def detect(self, frame: Frame) -> tuple[Detection, ...]:
        _validate_frame(frame)
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        padded, transform = _letterbox(cast(Frame, rgb), self._size)
        normalized = (padded.astype(np.float32) - self._mean) / self._std
        blob = cv2.dnn.blobFromImage(normalized)
        try:
            self._net.setInput(blob)
            outputs = self._net.forward(self._net.getUnconnectedOutLayersNames())
        except cv2.error as exc:
            raise NanoDetModelError("falha local durante a inferência NanoDet") from exc
        boxes, scores = self._decode(outputs)
        if not boxes:
            return ()
        xywh = [[x1, y1, x2 - x1, y2 - y1] for x1, y1, x2, y2 in boxes]
        indices = cv2.dnn.NMSBoxes(
            xywh,
            scores,
            self._confidence_threshold,
            self._iou_threshold,
        )
        detections = [
            self._to_detection(boxes[int(index)], scores[int(index)], frame.shape[:2], transform)
            for index in np.asarray(indices).reshape(-1)
        ]
        return tuple(
            sorted(
                (item for item in detections if item is not None),
                key=lambda item: item.score,
                reverse=True,
            )
        )

    def _decode(self, outputs: Sequence[np.ndarray]) -> tuple[list[list[float]], list[float]]:
        if len(outputs) != len(self._strides) * 2:
            raise NanoDetModelError("saída inesperada do modelo NanoDet")
        boxes: list[list[float]] = []
        scores: list[float] = []
        for stride, anchors, class_output, box_output in zip(
            self._strides,
            self._anchors,
            outputs[::2],
            outputs[1::2],
            strict=True,
        ):
            class_scores = np.asarray(class_output).squeeze(axis=0)
            box_logits = np.asarray(box_output).squeeze(axis=0)
            person_scores = class_scores[:, 0]
            candidates = np.flatnonzero(person_scores >= self._confidence_threshold)
            if candidates.size > 1000:
                order = np.argsort(person_scores[candidates])[::-1][:1000]
                candidates = candidates[order]
            if candidates.size == 0:
                continue
            selected_logits = box_logits[candidates].reshape(-1, self._reg_max + 1)
            selected_logits -= selected_logits.max(axis=1, keepdims=True)
            probabilities = np.exp(selected_logits)
            probabilities /= probabilities.sum(axis=1, keepdims=True)
            distances = (probabilities @ self._project).reshape(-1, 4) * stride
            points = anchors[candidates]
            decoded = np.column_stack(
                (
                    points[:, 0] - distances[:, 0],
                    points[:, 1] - distances[:, 1],
                    points[:, 0] + distances[:, 2],
                    points[:, 1] + distances[:, 3],
                )
            )
            decoded = np.clip(decoded, 0, self._size)
            boxes.extend(decoded.tolist())
            scores.extend(person_scores[candidates].astype(float).tolist())
        return boxes, scores

    @staticmethod
    def _to_detection(
        box: list[float],
        score: float,
        frame_shape: tuple[int, int],
        transform: tuple[int, int, int, int],
    ) -> Detection | None:
        frame_height, frame_width = frame_shape
        top, left, resized_height, resized_width = transform
        x_scale = frame_width / resized_width
        y_scale = frame_height / resized_height
        x1 = max(0, round((box[0] - left) * x_scale))
        y1 = max(0, round((box[1] - top) * y_scale))
        x2 = min(frame_width, round((box[2] - left) * x_scale))
        y2 = min(frame_height, round((box[3] - top) * y_scale))
        if x2 <= x1 or y2 <= y1:
            return None
        return Detection(x1, y1, x2 - x1, y2 - y1, score, "nanodet")
