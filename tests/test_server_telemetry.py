"""Real SQLite, synthetic UTC observations; no photos, inference or external delivery."""

from __future__ import annotations

import threading
from datetime import UTC, datetime, timedelta

import pytest

from app.server.telemetry import DeliveryError, Telemetry

ORG = "10000000-0000-4000-8000-000000000001"
CAMERA = {
    "id": "20000000-0000-4000-8000-000000000001",
    "organization_id": ORG,
    "environment_id": "30000000-0000-4000-8000-000000000001",
    "version": 1,
}
START = datetime(2026, 9, 8, 3, 0, tzinfo=UTC)


def at(seconds):
    return START + timedelta(seconds=seconds)


def collected(queue, now=None):
    sent = []
    queue.flush(lambda table, payload: sent.append((table, payload)), now or at(60))
    return sent


def test_complete_empty_minute_and_repeated_tick_are_idempotent(tmp_path):
    queue = Telemetry(ORG, tmp_path / "queue.sqlite3")
    for second in range(60):
        queue.observe(CAMERA, 0, at(second), [])
    queue.tick(at(60))
    queue.tick(at(61))
    sent = collected(queue)
    assert len(sent) == 1 and sent[0][0] == "occupancy_samples"
    assert sent[0][1]["state"] == "empty" and sent[0][1]["people_count"] == 0
    assert "boxes" not in sent[0][1] and "frames" not in sent[0][1]
    queue.close()


@pytest.mark.parametrize(
    "observations", [[(30, 0), (59, 0)], [(0, 0), (59, 0)], [(0, 0), (2, None), (59, 0)]]
)
def test_partial_gap_and_failed_readings_are_unknown_not_empty(tmp_path, observations):
    queue = Telemetry(ORG, tmp_path / "queue.sqlite3")
    for second, count in observations:
        queue.observe(CAMERA, count, at(second), [])
    queue.tick(at(60))
    payload = collected(queue)[0][1]
    assert payload["state"] == "unknown" and payload["people_count"] is None
    queue.close()


def test_observed_presence_retains_peak_even_in_partial_minute(tmp_path):
    queue = Telemetry(ORG, tmp_path / "queue.sqlite3")
    for second, count in [(20, 2), (21, 4), (25, None)]:
        queue.observe(CAMERA, count, at(second), [])
    queue.tick(at(60))
    payload = collected(queue)[0][1]
    assert payload["state"] == "occupied" and payload["people_count"] == 4
    queue.close()


def test_next_minute_can_be_empty_with_carried_boundary_coverage(tmp_path):
    queue = Telemetry(ORG, tmp_path / "queue.sqlite3")
    for second in range(30, 120):
        queue.observe(CAMERA, 0, at(second + 0.1), [])
        queue.tick(at(second + 0.1))
    queue.tick(at(120))
    sent = collected(queue, at(121))
    assert [payload["state"] for _, payload in sent] == ["unknown", "empty"]
    queue.close()


def test_restart_preserves_active_minute_outbox_and_tenant(tmp_path):
    path = tmp_path / "queue.sqlite3"
    queue = Telemetry(ORG, path)
    queue.observe(CAMERA, 2, at(10), [])
    queue.close()
    queue = Telemetry(ORG, path)
    queue.tick(at(60))
    queue.close()
    queue = Telemetry(ORG, path)
    assert queue.stats()["pending"] == 1
    assert collected(queue)[0][1]["people_count"] == 2
    queue.close()
    with pytest.raises(ValueError):
        Telemetry("10000000-0000-4000-8000-000000000009", path)


def test_assignment_change_is_unknown_and_does_not_rewrite_old_environment(tmp_path):
    queue = Telemetry(ORG, tmp_path / "queue.sqlite3")
    queue.observe(CAMERA, 2, at(10), [])
    queue.observe(
        {**CAMERA, "environment_id": "30000000-0000-4000-8000-000000000002", "version": 2},
        3,
        at(20),
        [],
    )
    queue.tick(at(60))
    payload = collected(queue)[0][1]
    assert payload["state"] == "unknown"
    assert payload["environment_id"] == CAMERA["environment_id"]
    queue.close()


def test_retry_backoff_and_permanent_failure_preserve_payload(tmp_path):
    queue = Telemetry(ORG, tmp_path / "queue.sqlite3")
    queue.observe(CAMERA, 1, at(10), [])
    queue.tick(at(60))
    calls = []

    def fail(table, payload):
        calls.append(payload)
        raise DeliveryError("synthetic", retryable=True)

    queue.flush(fail, at(60))
    queue.flush(fail, at(61))
    assert len(calls) == 1 and queue.stats()["pending"] == 1

    def dead(table, payload):
        assert payload == calls[0]
        raise DeliveryError("synthetic permanent", retryable=False)

    queue.flush(dead, at(63))
    assert queue.stats()["pending"] == 0 and queue.stats()["dead_letter"] == 1
    assert collected(queue, at(400)) == []
    queue.close()


def test_full_outbox_rolls_back_bucket_finalization_and_never_drops(tmp_path):
    queue = Telemetry(ORG, tmp_path / "queue.sqlite3", max_pending=1)
    queue.observe(CAMERA, 1, at(0), [])
    queue.observe(CAMERA, 2, at(60), [])
    with pytest.raises(RuntimeError, match="Fila cheia"):
        queue.tick(at(120))
    assert queue.stats()["full"] == 1
    assert collected(queue, at(121))[0][1]["people_count"] == 1
    queue.tick(at(120))
    assert collected(queue, at(122))[0][1]["people_count"] == 2
    queue.close()


def rule(kind="camera_offline", start="08:00:00", end="18:00:00"):
    return {
        "id": "40000000-0000-4000-8000-000000000001",
        "organization_id": ORG,
        "environment_id": CAMERA["environment_id"],
        "version": 1,
        "enabled": True,
        "kind": kind,
        "start_time": start,
        "end_time": end,
        "delay_seconds": 10,
    }


def test_offline_alert_one_per_episode_and_recovery_rearms(tmp_path):
    queue = Telemetry(ORG, tmp_path / "queue.sqlite3")
    for second in range(21):
        queue.observe(CAMERA, None, at(second), [rule()])
    first = collected(queue, at(22))
    assert len(first) == 1 and first[0][0] == "alerts"
    queue.observe(CAMERA, 0, at(23), [rule()])
    for second in range(24, 36):
        queue.observe(CAMERA, None, at(second), [rule()])
    second = collected(queue, at(36))
    assert len(second) == 1 and first[0][1]["dedup_key"] != second[0][1]["dedup_key"]
    queue.close()


def test_outside_hours_requires_observed_presence_and_handles_overnight(tmp_path):
    queue = Telemetry(ORG, tmp_path / "queue.sqlite3")
    for second in range(12):
        queue.observe(CAMERA, None, at(second), [rule("occupied_outside_hours")])
    assert collected(queue) == []
    for second in range(12, 24):
        queue.observe(
            CAMERA, 1, at(second), [rule("occupied_outside_hours", "22:00:00", "06:00:00")]
        )
    assert collected(queue) == []  # Midnight in Brasilia is within an overnight shift.
    for second in range(24, 36):
        queue.observe(CAMERA, 1, at(second), [rule("occupied_outside_hours")])
    assert len(collected(queue)) == 1
    queue.close()


def test_http_callback_does_not_hold_observation_lock(tmp_path):
    queue = Telemetry(ORG, tmp_path / "queue.sqlite3")
    queue.observe(CAMERA, 1, at(0), [])
    queue.tick(at(60))
    done = threading.Event()

    def deliver(table, payload):
        worker = threading.Thread(target=lambda: (queue.observe(CAMERA, 2, at(61), []), done.set()))
        worker.start()
        assert done.wait(2)
        worker.join(2)

    queue.flush(deliver, at(62))
    assert done.is_set()
    queue.close()
