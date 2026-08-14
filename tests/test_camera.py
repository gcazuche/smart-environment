"""Tests for deterministic webcam ownership and fallback."""

from __future__ import annotations

from unittest import TestCase

import numpy as np

from app.cameras import CameraOpenError, CameraReadError, OpenCVCamera


class FakeCapture:
    def __init__(self, opened: bool, frame: object | None = None, *, ok: bool = True) -> None:
        self.opened = opened
        self.frame = frame if frame is not None else np.zeros((20, 30, 3), dtype=np.uint8)
        self.ok = ok
        self.releases = 0

    def isOpened(self) -> bool:  # noqa: N802
        return self.opened

    def read(self) -> tuple[bool, object]:
        return self.ok, self.frame

    def release(self) -> None:
        self.releases += 1


class CameraTests(TestCase):
    def test_open_falls_back_and_releases_failed_candidate(self) -> None:
        failed = FakeCapture(False)
        working = FakeCapture(True)
        captures = iter((failed, working))
        camera = OpenCVCamera(capture_factory=lambda _index, _backend: next(captures))

        camera.open()

        self.assertEqual(failed.releases, 1)
        self.assertEqual(camera.backend_name, "msmf")
        self.assertEqual(camera.read().shape, (20, 30, 3))
        camera.close()
        camera.close()
        self.assertEqual(working.releases, 1)

    def test_open_failure_releases_every_candidate(self) -> None:
        captures = [FakeCapture(False) for _ in range(3)]
        iterator = iter(captures)
        camera = OpenCVCamera(capture_factory=lambda _index, _backend: next(iterator))

        with self.assertRaises(CameraOpenError):
            camera.open()

        self.assertTrue(all(capture.releases == 1 for capture in captures))

    def test_read_rejects_failed_or_malformed_frame(self) -> None:
        capture = FakeCapture(True, np.zeros((20, 30), dtype=np.uint8))
        camera = OpenCVCamera(backend="any", capture_factory=lambda _index, _backend: capture)
        camera.open()

        with self.assertRaises(CameraReadError):
            camera.read()

        camera.close()

    def test_context_manager_releases_on_error(self) -> None:
        capture = FakeCapture(True)
        camera = OpenCVCamera(backend="any", capture_factory=lambda _index, _backend: capture)

        with self.assertRaisesRegex(RuntimeError, "teste"):
            with camera:
                raise RuntimeError("teste")

        self.assertEqual(capture.releases, 1)

    def test_negative_index_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            OpenCVCamera(index=-1)
