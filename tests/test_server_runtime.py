"""Pure runtime state tests: no threads, model, database, cameras or HTTP requests."""

from __future__ import annotations

from pathlib import Path
from typing import Any
from unittest.mock import Mock

import pytest

from app.server import runtime
from app.server.config import Settings

ORG = "10000000-0000-4000-8000-000000000001"
CAMERA = "20000000-0000-4000-8000-000000000001"
OTHER_CAMERA = "20000000-0000-4000-8000-000000000002"
ENVIRONMENT = "50000000-0000-4000-8000-000000000001"


def camera(camera_id: str = CAMERA, *, version: int = 1) -> dict[str, Any]:
    return {
        "id": camera_id,
        "organization_id": ORG,
        "environment_id": ENVIRONMENT,
        "name": "Synthetic authorized room",
        "source": "local_rtsp",
        "enabled": True,
        "version": version,
    }


def reading(*, captured_at: float = 999.0, people: int = 2) -> dict[str, Any]:
    return {
        "captured_at": captured_at,
        "last_seen_at": "synthetic-utc",
        "people_count": people,
        "boxes": [{"x": 0.1, "y": 0.1, "width": 0.2, "height": 0.3}],
        "latency_ms": 12.0,
        "inference_fps": 2.0,
    }


@pytest.fixture
def bundle(monkeypatch: pytest.MonkeyPatch) -> tuple[runtime.Runtime, Mock, Mock, Mock, Mock]:
    backend, telemetry = Mock(), Mock()
    backend.catalog.return_value = ([camera()], [])
    telemetry.stats.return_value = {"pending": 3, "failed": 1}
    monkeypatch.setattr(runtime, "Supabase", Mock(return_value=backend))
    monkeypatch.setattr(runtime, "Telemetry", Mock(return_value=telemetry))
    monotonic, utc = Mock(return_value=100.0), Mock(return_value=1000.0)
    monkeypatch.setattr(runtime.time, "monotonic", monotonic)
    monkeypatch.setattr(runtime.time, "time", utc)
    settings = Settings(
        ORG,
        {CAMERA: "camera1"},
        ("https://dashboard.example",),
        Path("not-created.sqlite3"),
        "https://synthetic.supabase.co",
        "sb_publishable_fake",
        "sb_secret_fake",
    )
    instance = runtime.Runtime(settings)
    instance.catalog = {CAMERA: camera()}
    instance.catalog_at = 100.0
    return instance, backend, telemetry, monotonic, utc


def stop_after_one_iteration(instance: runtime.Runtime, monkeypatch: pytest.MonkeyPatch) -> None:
    def stop_wait(_timeout: float | None = None) -> bool:
        instance.stop.set()
        return True

    monkeypatch.setattr(instance.stop, "wait", stop_wait)


def test_available_requires_both_catalog_and_local_stream_allowlist(
    bundle: tuple[runtime.Runtime, Mock, Mock, Mock, Mock],
) -> None:
    instance, backend, telemetry, _, _ = bundle
    assert instance.available(CAMERA)
    instance.catalog[OTHER_CAMERA] = camera(OTHER_CAMERA)
    assert not instance.available(OTHER_CAMERA)
    instance.catalog.pop(CAMERA)
    assert not instance.available(CAMERA)
    backend.catalog.assert_not_called()
    telemetry.observe.assert_not_called()


def test_stop_immediately_revokes_available_and_hides_last_reading(
    bundle: tuple[runtime.Runtime, Mock, Mock, Mock, Mock],
) -> None:
    instance, _, _, _, _ = bundle
    instance.readings[CAMERA] = reading()
    assert instance.cameras()[0]["people_count"] == 2
    instance.stop.set()
    assert not instance.available(CAMERA)
    output = instance.cameras()[0]
    assert output["configured"] is False
    assert output["status"] == "waiting"
    assert output["people_count"] is None
    assert output["boxes"] == []


@pytest.mark.parametrize("age,available", [(29.999, True), (30.0, False), (31.0, False)])
def test_catalog_grant_expires_at_thirty_seconds(
    age: float,
    available: bool,
    bundle: tuple[runtime.Runtime, Mock, Mock, Mock, Mock],
) -> None:
    instance, _, _, monotonic, _ = bundle
    monotonic.return_value = 100.0 + age
    assert instance.available(CAMERA) is available
    assert instance.health()["catalog_ready"] is available


@pytest.mark.parametrize("age,fresh", [(0.0, True), (1.999, True), (2.0, False), (3.0, False)])
def test_stale_readings_become_unknown_not_zero(
    age: float,
    fresh: bool,
    bundle: tuple[runtime.Runtime, Mock, Mock, Mock, Mock],
) -> None:
    instance, _, _, _, utc = bundle
    instance.readings[CAMERA] = reading(captured_at=1000.0)
    utc.return_value = 1000.0 + age
    output = instance.cameras()[0]
    assert output["configured"] is True
    assert output["status"] == ("online" if fresh else "waiting")
    assert output["people_count"] == (2 if fresh else None)
    assert bool(output["boxes"]) is fresh
    if not fresh:
        assert output["last_seen_at"] is None
        assert output["latency_ms"] is None
        assert output["inference_fps"] is None


def test_missing_reading_is_unknown_but_valid_zero_is_preserved(
    bundle: tuple[runtime.Runtime, Mock, Mock, Mock, Mock],
) -> None:
    instance, _, _, _, _ = bundle
    assert instance.cameras()[0]["people_count"] is None
    instance.readings[CAMERA] = reading(people=0)
    assert instance.cameras()[0]["people_count"] == 0
    assert instance.cameras()[0]["status"] == "online"


def test_unconfigured_camera_cannot_show_injected_reading(
    bundle: tuple[runtime.Runtime, Mock, Mock, Mock, Mock],
) -> None:
    instance, _, _, _, _ = bundle
    instance.catalog[OTHER_CAMERA] = camera(OTHER_CAMERA)
    instance.readings[OTHER_CAMERA] = reading()
    output = {item["camera_id"]: item for item in instance.cameras()}[OTHER_CAMERA]
    assert output["configured"] is False
    assert output["people_count"] is None
    assert output["boxes"] == []


def test_catalog_failure_expires_grants_and_health_reports_unavailable(
    bundle: tuple[runtime.Runtime, Mock, Mock, Mock, Mock],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    instance, backend, _, monotonic, _ = bundle
    instance.readings[CAMERA] = reading()
    backend.catalog.side_effect = RuntimeError("private-provider-detail")
    monotonic.return_value = 131.0
    stop_after_one_iteration(instance, monkeypatch)
    instance.network_loop()
    assert instance.catalog_at == 100.0  # Failure must not renew the grant.
    assert instance.health()["catalog_ready"] is False
    assert instance.health()["network_error"] == "catalog_unavailable"
    assert "private-provider-detail" not in repr(instance.health())
    assert instance.cameras()[0]["people_count"] is None


def test_new_catalog_invalidates_readings_for_changed_camera_version(
    bundle: tuple[runtime.Runtime, Mock, Mock, Mock, Mock],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    instance, backend, _, _, _ = bundle
    instance.readings[CAMERA] = reading()
    backend.catalog.return_value = ([camera(version=2)], [])
    stop_after_one_iteration(instance, monkeypatch)
    instance.network_loop()
    assert instance.catalog[CAMERA]["version"] == 2
    assert CAMERA not in instance.readings
    assert instance.network_error is None


def test_delivery_failure_preserves_reported_queue_counts_without_raw_exception(
    bundle: tuple[runtime.Runtime, Mock, Mock, Mock, Mock],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    instance, _, telemetry, _, _ = bundle
    telemetry.flush.side_effect = RuntimeError("private-delivery-detail")
    stop_after_one_iteration(instance, monkeypatch)
    instance.delivery_loop()
    health = instance.health()
    assert health["network_error"] == "delivery_unavailable"
    assert health["delivery"] == {"pending": 3, "failed": 1}
    assert health["analysis_target_fps"] == 2.0
    assert "private-delivery-detail" not in repr(health)


def test_camera_api_only_exposes_selected_metadata(
    bundle: tuple[runtime.Runtime, Mock, Mock, Mock, Mock],
) -> None:
    instance, _, _, _, _ = bundle
    instance.catalog[CAMERA]["credentials"] = "synthetic-do-not-expose"
    instance.readings[CAMERA] = {**reading(), "frame": b"not-public", "raw_url": "not-public"}
    output = instance.cameras()[0]
    assert "credentials" not in output
    assert "frame" not in output
    assert "raw_url" not in output
    assert "synthetic-do-not-expose" not in repr(output)
