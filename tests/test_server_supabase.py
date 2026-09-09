"""Mocked transport contracts for server-only keys and idempotent metadata delivery."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import Mock
from urllib.parse import parse_qs, urlsplit

import pytest

from app.server import supabase
from app.server.config import Settings
from app.server.telemetry import DeliveryError

ORG = "10000000-0000-4000-8000-000000000001"
USER = "30000000-0000-4000-8000-000000000001"
TOKEN = "synthetic-user-access-token-only"  # noqa: S105 - test-only token


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch) -> tuple[supabase.Supabase, Mock]:
    settings = Settings(
        ORG,
        {},
        ("https://dashboard.example",),
        Path("unused.sqlite3"),
        "https://synthetic.supabase.co",
        "sb_publishable_fake",
        "sb_secret_fake",
    )
    transport = Mock(return_value=(200, {}, b"[]"))
    monkeypatch.setattr(supabase, "request", transport)
    return supabase.Supabase(settings), transport


def test_new_secret_key_is_apikey_not_bearer(client: tuple[supabase.Supabase, Mock]) -> None:
    backend, transport = client
    backend.api("/rest/v1/cameras")
    call = transport.call_args
    assert call.args[0] == "https://synthetic.supabase.co"
    assert call.args[3]["apikey"] == "sb_secret_fake"
    assert "Authorization" not in call.args[3]
    assert "sb_secret_fake" not in call.args[2]


def test_delegated_user_calls_use_publishable_key_and_user_bearer(
    client: tuple[supabase.Supabase, Mock],
) -> None:
    backend, transport = client
    backend.api("/auth/v1/user", token=TOKEN)
    headers = transport.call_args.args[3]
    assert headers["apikey"] == "sb_publishable_fake"
    assert headers["Authorization"] == "Bearer " + TOKEN
    assert "sb_secret_fake" not in repr(transport.call_args)


@pytest.mark.parametrize(
    "table,conflict",
    [
        ("occupancy_samples", "camera_id,bucket_start"),
        ("alerts", "organization_id,dedup_key"),
    ],
)
def test_delivery_retries_ignore_duplicates_without_overwriting(
    table: str,
    conflict: str,
    client: tuple[supabase.Supabase, Mock],
) -> None:
    backend, transport = client
    transport.return_value = (201, {}, b"")
    payload = {"organization_id": ORG, "synthetic": "metadata-only"}
    backend.deliver(table, payload)
    backend.deliver(table, payload)
    assert transport.call_count == 2
    assert transport.call_args_list[0] == transport.call_args_list[1]
    call = transport.call_args
    assert call.args[1] == "POST"
    assert call.args[2] == f"/rest/v1/{table}?on_conflict={conflict}"
    assert call.args[3]["Prefer"] == "resolution=ignore-duplicates,return=minimal"
    assert "merge-duplicates" not in repr(call)
    assert json.loads(call.args[4]) == payload


@pytest.mark.parametrize(
    "table,organization",
    [("cameras", ORG), ("organization_members", ORG), ("alerts", "other-org"), ("alerts", None)],
)
def test_delivery_rejects_wrong_table_and_organization_before_transport(
    table: str,
    organization: str | None,
    client: tuple[supabase.Supabase, Mock],
) -> None:
    backend, transport = client
    with pytest.raises(DeliveryError) as caught:
        backend.deliver(table, {"organization_id": organization})
    assert caught.value.retryable is False
    transport.assert_not_called()


@pytest.mark.parametrize(
    "status,retryable",
    [(400, False), (401, True), (403, True), (409, False), (429, True), (500, True), (503, True)],
)
def test_delivery_classifies_remote_failures_without_raw_body(
    status: int,
    retryable: bool,
    client: tuple[supabase.Supabase, Mock],
) -> None:
    backend, transport = client
    transport.return_value = (status, {}, b"private diagnostic content must not escape")
    with pytest.raises(DeliveryError) as caught:
        backend.deliver("alerts", {"organization_id": ORG})
    assert caught.value.retryable is retryable
    assert "private diagnostic" not in str(caught.value)


def test_authorization_checks_user_and_organization_membership(
    client: tuple[supabase.Supabase, Mock],
) -> None:
    backend, transport = client
    transport.side_effect = [
        (200, {}, json.dumps({"id": USER, "user_metadata": {"role": "admin"}}).encode()),
        (200, {}, json.dumps([{"user_id": USER, "role": "viewer"}]).encode()),
    ]
    assert backend.authorize(TOKEN) == USER
    first, second = transport.call_args_list
    assert first.args[2] == "/auth/v1/user"
    query = parse_qs(urlsplit(second.args[2]).query)
    assert query["organization_id"] == [f"eq.{ORG}"]
    assert query["user_id"] == [f"eq.{USER}"]
    assert query["limit"] == ["501"]
    assert second.args[3]["Authorization"] == "Bearer " + TOKEN


@pytest.mark.parametrize("memberships", [[], [{"role": "owner"}], [{"role": "viewer"}] * 2])
def test_user_metadata_cannot_grant_membership(
    memberships: list[dict[str, str]],
    client: tuple[supabase.Supabase, Mock],
) -> None:
    backend, transport = client
    transport.side_effect = [
        (200, {}, json.dumps({"id": USER, "user_metadata": {"role": "admin"}}).encode()),
        (200, {}, json.dumps(memberships).encode()),
    ]
    with pytest.raises(supabase.RemoteError) as caught:
        backend.authorize(TOKEN)
    assert caught.value.status == 403


@pytest.mark.parametrize("response", [{"id": USER}, [{}] * 501])
def test_rows_rejects_non_array_and_truncated_catalog(
    response: object,
    client: tuple[supabase.Supabase, Mock],
) -> None:
    backend, transport = client
    transport.return_value = (200, {}, json.dumps(response).encode())
    with pytest.raises(supabase.RemoteError) as caught:
        backend.rows("cameras", "id")
    assert caught.value.status == 502


def test_transport_does_not_follow_redirects_or_read_unbounded_body(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    response = Mock()
    response.status = 302
    response.getheaders.return_value = [("Location", "https://outside.example")]
    response.read.return_value = b""
    connection = Mock()
    connection.getresponse.return_value = response
    factory = Mock(return_value=connection)
    monkeypatch.setattr(supabase.http.client, "HTTPSConnection", factory)
    status, headers, _ = supabase.request(
        "https://synthetic.supabase.co",
        "GET",
        "/rest/v1/cameras",
        {"apikey": "synthetic"},
        limit=16,
    )
    assert status == 302
    assert headers["location"] == "https://outside.example"
    assert factory.call_count == 1
    connection.close.assert_called_once()
    response.read.assert_called_once_with(17)
    response.read.return_value = b"x" * 17
    with pytest.raises(supabase.RemoteError) as caught:
        supabase.request("https://synthetic.supabase.co", "GET", "/", {}, limit=16)
    assert caught.value.status == 502
