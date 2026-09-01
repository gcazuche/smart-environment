"""Safe, testable OpenCV webcam input."""

from __future__ import annotations

import platform
from collections.abc import Callable
from ipaddress import ip_address
from types import TracebackType
from typing import Protocol, TypeAlias, TypeGuard, cast
from urllib.parse import urlsplit

import cv2
import numpy as np
from numpy.typing import NDArray

Frame: TypeAlias = NDArray[np.uint8]


class CameraError(RuntimeError):
    """Base error safe to present to a local operator."""


class CameraOpenError(CameraError):
    """Raised when no configured capture backend can open the camera."""


class CameraReadError(CameraError):
    """Raised when an opened camera does not return a valid frame."""


class CaptureLike(Protocol):
    def isOpened(self) -> bool: ...  # noqa: N802

    def read(self) -> tuple[bool, object]: ...

    def release(self) -> None: ...


CaptureFactory = Callable[[int, int], CaptureLike]
NetworkCaptureFactory = Callable[[str], CaptureLike]

_BACKENDS: dict[str, int] = {
    "any": cv2.CAP_ANY,
    "dshow": cv2.CAP_DSHOW,
    "msmf": cv2.CAP_MSMF,
}


def _default_capture_factory(index: int, backend: int) -> CaptureLike:
    return cast(CaptureLike, cv2.VideoCapture(index, backend))


def _default_network_capture_factory(url: str) -> CaptureLike:
    return cast(CaptureLike, cv2.VideoCapture(url))


def _backend_candidates(requested: str) -> tuple[tuple[str, int], ...]:
    if requested not in {"auto", *_BACKENDS}:
        raise ValueError(f"backend de câmera desconhecido: {requested}")
    if requested != "auto":
        return ((requested, _BACKENDS[requested]),)
    if platform.system() == "Windows":
        return (("dshow", cv2.CAP_DSHOW), ("msmf", cv2.CAP_MSMF), ("any", cv2.CAP_ANY))
    return (("any", cv2.CAP_ANY),)


def _is_valid_frame(frame: object) -> TypeGuard[Frame]:
    return (
        isinstance(frame, np.ndarray)
        and frame.dtype == np.uint8
        and frame.ndim == 3
        and frame.shape[2] == 3
        and frame.size > 0
    )


class OpenCVCamera:
    """Own one webcam handle and release it deterministically."""

    def __init__(
        self,
        index: int = 0,
        backend: str = "auto",
        *,
        capture_factory: CaptureFactory = _default_capture_factory,
    ) -> None:
        if index < 0:
            raise ValueError("o índice da câmera deve ser zero ou maior")
        self.index = index
        self.requested_backend = backend
        self.backend_name: str | None = None
        self._capture_factory = capture_factory
        self._capture: CaptureLike | None = None

    def open(self) -> None:
        if self._capture is not None:
            return
        attempted: list[str] = []
        for name, backend_id in _backend_candidates(self.requested_backend):
            attempted.append(name)
            capture = self._capture_factory(self.index, backend_id)
            if capture.isOpened():
                self._capture = capture
                self.backend_name = name
                return
            capture.release()
        joined = ", ".join(attempted)
        raise CameraOpenError(
            f"não foi possível abrir a câmera {self.index} (backends testados: {joined})"
        )

    def read(self) -> Frame:
        if self._capture is None:
            raise CameraReadError(f"a câmera {self.index} ainda não foi aberta")
        ok, frame = self._capture.read()
        if not ok or not _is_valid_frame(frame):
            raise CameraReadError(f"a câmera {self.index} não forneceu um frame válido")
        return frame

    def close(self) -> None:
        capture, self._capture = self._capture, None
        if capture is not None:
            capture.release()

    def __enter__(self) -> OpenCVCamera:
        self.open()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self.close()


def _validate_private_camera_url(url: str) -> None:
    parsed = urlsplit(url)
    if parsed.scheme not in {"http", "https", "rtsp"} or not parsed.hostname:
        raise ValueError("endereço da câmera de rede inválido")
    if parsed.username or parsed.password:
        raise ValueError("não coloque credenciais no endereço da câmera")
    hostname = parsed.hostname.lower()
    if hostname.endswith(".local") or hostname == "localhost":
        return
    try:
        address = ip_address(hostname)
    except ValueError as exc:
        raise ValueError("use um endereço da rede privada: IP local ou nome .local") from exc
    if not (address.is_private or address.is_loopback):
        raise ValueError("a câmera de teste deve estar na rede privada local")


class OpenCVNetworkCamera:
    """Read a trusted local MJPEG/RTSP camera without exposing its URL in errors."""

    def __init__(
        self,
        url: str,
        *,
        capture_factory: NetworkCaptureFactory = _default_network_capture_factory,
    ) -> None:
        _validate_private_camera_url(url)
        self.backend_name: str | None = "network"
        self._url = url
        self._capture_factory = capture_factory
        self._capture: CaptureLike | None = None

    def open(self) -> None:
        if self._capture is not None:
            return
        capture = self._capture_factory(self._url)
        if not capture.isOpened():
            capture.release()
            raise CameraOpenError("não foi possível abrir a câmera de rede local")
        self._capture = capture

    def read(self) -> Frame:
        if self._capture is None:
            raise CameraReadError("a câmera de rede ainda não foi aberta")
        ok, frame = self._capture.read()
        if not ok or not _is_valid_frame(frame):
            raise CameraReadError("a câmera de rede não forneceu um frame válido")
        return frame

    def close(self) -> None:
        capture, self._capture = self._capture, None
        if capture is not None:
            capture.release()

    def __enter__(self) -> OpenCVNetworkCamera:
        self.open()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self.close()
