from datetime import time
from typing import Any
from urllib.parse import parse_qs, urlsplit

import pytest

from app.web.backend import BackendError
from app.web.repository import Repository, RepositoryError, data_error

ORG = "10000000-0000-0000-0000-000000000001"
USER = "20000000-0000-0000-0000-000000000001"
ENV = "30000000-0000-0000-0000-000000000001"
RECORD = "40000000-0000-0000-0000-000000000001"
PERIOD = {"start": "2026-09-20T03:00:00Z", "end": "2026-09-20T12:34:56Z"}


class FakeBackend:
    org = ORG

    def __init__(self, *responses: Any) -> None:
        self.responses = list(responses)
        self.calls: list[dict[str, Any]] = []

    def api(self, path: str, **kwargs: Any) -> Any:
        self.calls.append(
            {"path": urlsplit(path).path, "query": parse_qs(urlsplit(path).query), **kwargs}
        )
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response


def repository(*responses: Any) -> tuple[Repository, FakeBackend]:
    backend = FakeBackend(*responses)
    return Repository(backend), backend  # type: ignore[arg-type]


def record(**overrides: Any) -> dict[str, Any]:
    return {"id": RECORD, "organization_id": ORG, "version": 2, **overrides}


def test_catalog_checks_membership_and_scopes_every_query() -> None:
    repo, backend = repository([{"role": "viewer"}], [], [], [])
    assert repo.catalog(USER) == {"role": "viewer", "environments": [], "cameras": [], "rules": []}
    assert all(call["query"]["organization_id"] == [f"eq.{ORG}"] for call in backend.calls)
    assert backend.calls[0]["query"]["user_id"] == [f"eq.{USER}"]
    assert all(call["query"]["limit"] == ["500"] for call in backend.calls[1:])


@pytest.mark.parametrize("membership", [[], [{"role": "owner"}], [{"role": "admin"}] * 2])
def test_catalog_denies_invalid_or_missing_membership(membership: Any) -> None:
    repo, backend = repository(membership)
    with pytest.raises(RepositoryError, match="vinculada"):
        repo.catalog(USER)
    assert len(backend.calls) == 1


def test_catalog_fails_closed_at_limit_or_cross_organization_response() -> None:
    repo, _ = repository([{"role": "admin"}], [record()] * 500)
    with pytest.raises(RepositoryError, match="limite"):
        repo.catalog(USER)
    repo, _ = repository([{"role": "admin"}], [record(organization_id=USER)])
    with pytest.raises(RepositoryError, match="organização"):
        repo.catalog(USER)


def test_insert_allowlists_payload_and_organization() -> None:
    repo, backend = repository([record()])
    assert repo.save_environment(" Sala   A ")["id"] == RECORD
    assert backend.calls[0]["method"] == "POST"
    assert backend.calls[0]["payload"] == {"name": "Sala A", "organization_id": ORG}


def test_edit_keeps_original_version_filter_and_never_updates_identity() -> None:
    repo, backend = repository([record(version=3)])
    repo.save_environment("Novo nome", record())
    call = backend.calls[0]
    assert call["method"] == "PATCH"
    assert call["query"]["version"] == ["eq.2"]
    assert call["query"]["id"] == [f"eq.{RECORD}"]
    assert call["payload"] == {"name": "Novo nome"}


def test_zero_updated_rows_is_concurrency_conflict() -> None:
    repo, _ = repository([])
    with pytest.raises(RepositoryError, match="alterado"):
        repo.save_environment("Novo nome", record())


@pytest.mark.parametrize(
    "existing", [record(organization_id=USER), record(version=0), record(id="x")]
)
def test_invalid_edits_make_no_write(existing: Any) -> None:
    repo, backend = repository()
    with pytest.raises(RepositoryError):
        repo.save_environment("Nome", existing)
    assert backend.calls == []


def test_camera_validates_environment_and_drops_extra_fields() -> None:
    repo, backend = repository([record(id=ENV)], [record()])
    repo.save_camera(
        {
            "name": "PC",
            "source": "webcam",
            "address": "0",
            "environment_id": ENV,
            "enabled": True,
            "organization_id": USER,
            "version": 99,
            "monitor_id": "pc",
        }
    )
    assert backend.calls[0]["query"]["organization_id"] == [f"eq.{ORG}"]
    payload = backend.calls[1]["payload"]
    assert payload["organization_id"] == ORG
    assert "version" not in payload
    assert payload["monitor_id"] == "pc"


def test_camera_unavailable_environment_makes_no_write() -> None:
    repo, backend = repository([])
    with pytest.raises(RepositoryError, match="ambiente"):
        repo.save_camera(
            {
                "name": "PC",
                "source": "webcam",
                "address": "0",
                "environment_id": ENV,
                "enabled": True,
            }
        )
    assert len(backend.calls) == 1


def test_rule_serializes_cleaned_times_and_allowed_fields_only() -> None:
    repo, backend = repository([record(id=ENV)], [record()])
    repo.save_rule(
        {
            "name": "Regra",
            "kind": "occupied_outside_hours",
            "environment_id": ENV,
            "enabled": True,
            "delay_seconds": 60,
            "start_time": time(22),
            "end_time": time(6),
            "reviewed_by": USER,
            "organization_id": USER,
        }
    )
    payload = backend.calls[1]["payload"]
    assert payload["start_time"] == "22:00:00"
    assert payload["end_time"] == "06:00:00"
    assert payload["organization_id"] == ORG
    assert "reviewed_by" not in payload


@pytest.mark.parametrize(
    "patch",
    [
        {"kind": "productivity"},
        {"delay_seconds": True},
        {"delay_seconds": 9},
        {"start_time": "08:00", "end_time": "08:00"},
        {"enabled": "true"},
    ],
)
def test_invalid_rule_fails_before_network(patch: Any) -> None:
    repo, backend = repository()
    values = {
        "name": "Regra",
        "kind": "camera_offline",
        "environment_id": ENV,
        "enabled": True,
        "delay_seconds": 60,
        "start_time": "08:00",
        "end_time": "18:00",
    }
    with pytest.raises(RepositoryError):
        repo.save_rule({**values, **patch})
    assert backend.calls == []


def test_samples_paginate_complete_minutes_without_changing_unknown() -> None:
    repo, backend = repository([record(state="unknown", people_count=None)] * 51)
    result = repo.samples({**PERIOD, "environment_id": ENV}, 2)
    assert result["more"] is True
    assert len(result["rows"]) == 50
    assert result["rows"][0]["people_count"] is None
    query = backend.calls[0]["query"]
    assert query["offset"] == ["100"]
    assert query["limit"] == ["51"]
    assert query["environment_id"] == [f"eq.{ENV}"]
    assert "bucket_start.lte.2026-09-20T12:33:56+00:00" in query["and"][0]


def test_alerts_use_exclusive_end_and_stable_order() -> None:
    repo, backend = repository([])
    assert repo.alerts(PERIOD) == {"rows": [], "more": False}
    query = backend.calls[0]["query"]
    assert "occurred_at.lt.2026-09-20T12:34:56+00:00" in query["and"][0]
    assert query["order"] == ["occurred_at.desc,id.asc"]


@pytest.mark.parametrize("page", [-1, True, 10001])
def test_invalid_page_makes_no_request(page: int) -> None:
    repo, backend = repository()
    with pytest.raises(RepositoryError, match="Página"):
        repo.samples(PERIOD, page)
    assert backend.calls == []


def test_empty_period_has_no_false_events_or_request() -> None:
    repo, backend = repository()
    period = {"start": PERIOD["start"], "end": PERIOD["start"]}
    assert repo.samples(period) == {"rows": [], "more": False}
    assert repo.report(period) == []
    assert backend.calls == []


@pytest.mark.parametrize(
    "period",
    [
        {"start": "2026-09-20", "end": "2026-09-21"},
        {"start": "2026-09-20T00:00:00Z", "end": "2026-09-19T00:00:00Z"},
        {"start": "2026-08-01T00:00:00Z", "end": "2026-09-20T00:00:00Z"},
        {**PERIOD, "environment_id": "bad"},
    ],
)
def test_invalid_query_periods_make_no_request(period: Any) -> None:
    repo, backend = repository()
    with pytest.raises(RepositoryError):
        repo.report(period)
    assert backend.calls == []


def test_report_rpc_scopes_organization_and_limits_results() -> None:
    repo, backend = repository([])
    assert repo.report({**PERIOD, "environment_id": ENV}) == []
    assert backend.calls[0]["payload"]["org"] == ORG
    assert backend.calls[0]["payload"]["env"] == ENV
    assert backend.calls[0]["query"]["limit"] == ["500"]
    repo, _ = repository([{}] * 500)
    with pytest.raises(RepositoryError, match="limite"):
        repo.report(PERIOD)


def test_review_alert_prescopes_organization_then_invokes_locked_rpc() -> None:
    repo, backend = repository([record(status="open")], record(status="reviewed", version=3))
    assert repo.review_alert(RECORD, 2, "reviewed")["version"] == 3
    assert backend.calls[0]["query"]["organization_id"] == [f"eq.{ORG}"]
    assert backend.calls[1]["payload"] == {
        "alert_id": RECORD,
        "expected_version": 2,
        "next_status": "reviewed",
    }


@pytest.mark.parametrize("row", [None, record(version=3), record(status="resolved")])
def test_alert_conflict_or_invalid_transition_never_calls_rpc(row: Any) -> None:
    repo, backend = repository([] if row is None else [row])
    with pytest.raises(RepositoryError):
        repo.review_alert(RECORD, 2, "reviewed")
    assert len(backend.calls) == 1


def test_alert_from_another_organization_never_calls_rpc() -> None:
    repo, backend = repository([record(status="open", organization_id=USER)])
    with pytest.raises(RepositoryError, match="organização"):
        repo.review_alert(RECORD, 2, "reviewed")
    assert len(backend.calls) == 1


def test_backend_error_preserved_for_auth_and_translated_without_raw_provider_text() -> None:
    failure = BackendError(403, "42501")
    repo, _ = repository(failure)
    with pytest.raises(BackendError) as caught:
        repo.catalog(USER)
    assert caught.value is failure
    assert "permissão" in data_error(failure)
    assert "secret" not in data_error(ValueError("secret"))
