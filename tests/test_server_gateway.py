"""Unit-level gateway requests only: no sockets, MediaMTX, Supabase or real JWTs."""

from __future__ import annotations

import hashlib
import io
from http.client import HTTPMessage
from pathlib import Path
from types import SimpleNamespace
from typing import cast
from unittest.mock import Mock
from uuid import UUID

import pytest

from app.server import gateway
from app.server.config import Settings
from app.server.supabase import RemoteError

ORG = "10000000-0000-4000-8000-000000000001"
CAMERA = "20000000-0000-4000-8000-000000000001"
OTHER_CAMERA = "20000000-0000-4000-8000-000000000002"
OWNER = "30000000-0000-4000-8000-000000000001"
OTHER_OWNER = "30000000-0000-4000-8000-000000000002"
SECRET = "40000000-0000-4000-8000-000000000001"  # noqa: S105 - synthetic session identifier
TOKEN = "synthetic-access-token-for-unit-tests-only"  # noqa: S105 - test-only token
ORIGIN = "https://dashboard.example"


@pytest.fixture
def bundle(monkeypatch: pytest.MonkeyPatch) -> tuple[gateway.Gateway, Mock, Mock, Mock]:
    settings = Settings(
        ORG,
        {CAMERA: "camera1"},
        (ORIGIN,),
        Path("unused.sqlite3"),
        "https://synthetic.supabase.co",
        "sb_publishable_fake",
        "sb_secret_fake",
    )
    backend = Mock()
    backend.authorize.return_value = OWNER
    status = Mock()
    status.available.side_effect = lambda camera_id: camera_id == CAMERA
    status.cameras.return_value = [{"camera_id": CAMERA}]
    status.health.return_value = {"catalog_ready": True}
    transport = Mock(
        return_value=(
            201,
            {
                "location": f"/camera1/whep/{SECRET}",
                "content-type": "application/sdp",
            },
            b"synthetic-answer",
        )
    )
    monkeypatch.setattr(gateway, "request", transport)
    return gateway.Gateway(settings, backend, status), backend, status, transport


def assert_remote_status(expected: int, caught: pytest.ExceptionInfo[RemoteError]) -> None:
    assert caught.value.status == expected


def handler(
    instance: gateway.Gateway,
    monkeypatch: pytest.MonkeyPatch,
    *,
    method: str = "GET",
    path: str = "/v1/cameras",
    headers: dict[str, str] | None = None,
    body: bytes = b"",
) -> tuple[gateway.Handler, Mock]:
    value = object.__new__(gateway.Handler)
    value.server = cast(gateway.Server, SimpleNamespace(gateway=instance))
    value.command, value.path = method, path
    value.headers = HTTPMessage()
    for key, content in (headers or {}).items():
        value.headers[key] = content
    value.rfile, value.wfile = io.BytesIO(body), io.BytesIO()
    reply = Mock()
    monkeypatch.setattr(value, "reply", reply)
    return value, reply


@pytest.mark.parametrize(
    "bearer", ["", "Basic fake", "Bearer short", "bearer " + TOKEN, "Bearer " + "x" * 8192]
)
def test_invalid_bearer_never_reaches_backend(
    bearer: str,
    bundle: tuple[gateway.Gateway, Mock, Mock, Mock],
) -> None:
    instance, backend, _, _ = bundle
    with pytest.raises(RemoteError) as caught:
        instance.authorize(bearer)
    assert_remote_status(401, caught)
    backend.authorize.assert_not_called()


def test_cache_is_hashed_bounded_and_expires_after_ten_seconds(
    bundle: tuple[gateway.Gateway, Mock, Mock, Mock],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    instance, backend, _, _ = bundle
    clock = Mock(return_value=100.0)
    monkeypatch.setattr(gateway.time, "monotonic", clock)
    assert instance.authorize("Bearer " + TOKEN) == OWNER
    assert instance.authorize("Bearer " + TOKEN) == OWNER
    backend.authorize.assert_called_once_with(TOKEN)
    assert list(instance.tokens) == [hashlib.sha256(TOKEN.encode()).hexdigest()]
    assert TOKEN not in repr(instance.tokens)
    clock.return_value = 110.0
    instance.authorize("Bearer " + TOKEN)
    assert backend.authorize.call_count == 2
    for index in range(140):
        instance.authorize("Bearer " + TOKEN + str(index))
    assert len(instance.tokens) == 128


@pytest.mark.parametrize("status", [401, 403, 503])
def test_fresh_auth_failure_invalidates_existing_cache(
    status: int,
    bundle: tuple[gateway.Gateway, Mock, Mock, Mock],
) -> None:
    instance, backend, _, _ = bundle
    instance.authorize("Bearer " + TOKEN)
    backend.authorize.side_effect = RemoteError(status)
    with pytest.raises(RemoteError) as caught:
        instance.authorize("Bearer " + TOKEN, fresh=True)
    assert_remote_status(status, caught)
    assert not instance.tokens
    with pytest.raises(RemoteError):
        instance.authorize("Bearer " + TOKEN)
    assert backend.authorize.call_count == 3


def test_camera_outside_allowlist_cannot_create_stream(
    bundle: tuple[gateway.Gateway, Mock, Mock, Mock],
) -> None:
    instance, _, _, transport = bundle
    with pytest.raises(RemoteError) as caught:
        instance.create(OWNER, OTHER_CAMERA, b"offer")
    assert_remote_status(404, caught)
    transport.assert_not_called()


def test_create_rewrites_secret_location_and_never_forwards_user_bearer(
    bundle: tuple[gateway.Gateway, Mock, Mock, Mock],
) -> None:
    instance, _, _, transport = bundle
    answer, location = instance.create(OWNER, CAMERA, b"offer")
    assert answer == b"synthetic-answer"
    assert location.startswith(f"/v1/cameras/{CAMERA}/whep/")
    assert SECRET not in location
    key = location.rsplit("/", 1)[1]
    assert str(UUID(key)) == key
    assert instance.sessions[key].location == f"/camera1/whep/{SECRET}"
    assert instance.sessions[key].owner == OWNER
    transport.assert_called_once_with(
        gateway.MEDIA,
        "POST",
        "/camera1/whep",
        {"Content-Type": "application/sdp"},
        b"offer",
        limit=131072,
    )


@pytest.mark.parametrize(
    "location",
    [
        "",
        f"https://outside.example/camera1/whep/{SECRET}",
        f"//outside.example/camera1/whep/{SECRET}",
        f"/camera2/whep/{SECRET}",
        f"/camera1/whep/{SECRET}?token=x",
        f"/camera1/whep/{SECRET}#fragment",
        f"/camera1/whep/{SECRET}/../other",
        "/camera1/whep/not-a-uuid",
        "/camera1/whep/" + "-" * 36,
    ],
)
def test_rejects_untrusted_or_malformed_upstream_location(
    location: str,
    bundle: tuple[gateway.Gateway, Mock, Mock, Mock],
) -> None:
    instance, _, _, transport = bundle
    transport.return_value = (
        201,
        {"location": location, "content-type": "application/sdp"},
        b"answer",
    )
    with pytest.raises(RemoteError) as caught:
        instance.create(OWNER, CAMERA, b"offer")
    assert_remote_status(502, caught)
    assert not instance.sessions


@pytest.mark.parametrize(
    "code,content_type",
    [
        (200, "application/sdp"),
        (302, "application/sdp"),
        (201, "text/html"),
        (201, "not/application/sdp-evil"),
    ],
)
def test_requires_created_sdp_response(
    code: int,
    content_type: str,
    bundle: tuple[gateway.Gateway, Mock, Mock, Mock],
) -> None:
    instance, _, _, transport = bundle
    transport.return_value = (
        code,
        {"location": f"/camera1/whep/{SECRET}", "content-type": content_type},
        b"answer",
    )
    with pytest.raises(RemoteError) as caught:
        instance.create(OWNER, CAMERA, b"offer")
    assert_remote_status(502, caught)
    assert not instance.sessions


@pytest.mark.parametrize(
    "owner,camera,renew",
    [
        (OTHER_OWNER, CAMERA, False),
        (OTHER_OWNER, CAMERA, True),
        (OWNER, OTHER_CAMERA, False),
        (OWNER, OTHER_CAMERA, True),
    ],
)
def test_session_controls_are_bound_to_owner_and_camera(
    owner: str,
    camera: str,
    renew: bool,
    bundle: tuple[gateway.Gateway, Mock, Mock, Mock],
) -> None:
    instance, _, _, transport = bundle
    _, location = instance.create(OWNER, CAMERA, b"offer")
    key = location.rsplit("/", 1)[1]
    transport.reset_mock()
    with pytest.raises(RemoteError) as caught:
        instance.control(owner, camera, key, renew=renew)
    assert_remote_status(404, caught)
    assert key in instance.sessions
    transport.assert_not_called()


def test_expiration_and_missing_catalog_close_remote_session(
    bundle: tuple[gateway.Gateway, Mock, Mock, Mock],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    instance, _, status, transport = bundle
    clock = Mock(return_value=100.0)
    monkeypatch.setattr(gateway.time, "monotonic", clock)
    _, location = instance.create(OWNER, CAMERA, b"offer")
    key = location.rsplit("/", 1)[1]
    clock.return_value = 134.0
    instance.control(OWNER, CAMERA, key, renew=True)
    assert instance.sessions[key].renewed == 134.0
    clock.return_value = 170.0
    with pytest.raises(RemoteError) as caught:
        instance.control(OWNER, CAMERA, key, renew=True)
    assert_remote_status(404, caught)
    transport.return_value = (200, {}, b'{"status":"ok"}')
    instance.expire()
    assert not instance.sessions
    transport.assert_called_with(
        gateway.MEDIA, "DELETE", f"/camera1/whep/{SECRET}", {}, limit=131072, timeout=2
    )
    instance.sessions[key] = gateway.Session(OWNER, CAMERA, f"/camera1/whep/{SECRET}", 170.0)
    status.available.side_effect = lambda _camera: False
    instance.expire()
    assert not instance.sessions


def test_camera_revoked_during_offer_is_cleaned_up(
    bundle: tuple[gateway.Gateway, Mock, Mock, Mock],
) -> None:
    instance, _, status, transport = bundle
    status.available.side_effect = [True, False]
    transport.side_effect = [transport.return_value, (200, {}, b'{"status":"ok"}')]
    with pytest.raises(RemoteError) as caught:
        instance.create(OWNER, CAMERA, b"offer")
    assert_remote_status(404, caught)
    assert not instance.sessions
    assert transport.call_args_list[-1].args[1] == "DELETE"


@pytest.mark.parametrize("failure", [500, 503, "network"])
@pytest.mark.parametrize("success", [200, 204, 404])
def test_failed_delete_stays_pending_and_watchdog_retries_until_acknowledged(
    failure: int | str, success: int, bundle: tuple[gateway.Gateway, Mock, Mock, Mock],
) -> None:
    instance, _, _, transport = bundle
    _, location = instance.create(OWNER, CAMERA, b"offer")
    key = location.rsplit("/", 1)[1]
    transport.reset_mock()
    if failure == "network":
        transport.side_effect = RemoteError(503)
    else:
        transport.return_value = (failure, {}, b"unavailable")
    instance.remove(key)
    assert key in instance.sessions
    assert instance.sessions[key].closing is True
    with pytest.raises(RemoteError) as caught:
        instance.control(OWNER, CAMERA, key, renew=True)
    assert_remote_status(404, caught)
    transport.side_effect = None
    transport.return_value = (success, {}, b"")
    instance.expire()
    assert key not in instance.sessions
    assert transport.call_count == 2
    for call in transport.call_args_list:
        assert call.args == (gateway.MEDIA, "DELETE", f"/camera1/whep/{SECRET}", {})
        assert call.kwargs == {"limit": 131072, "timeout": 2}
    instance.remove(key)
    assert transport.call_count == 2  # Repeated close cannot target a different session.


def test_expire_all_closes_even_fresh_sessions(
    bundle: tuple[gateway.Gateway, Mock, Mock, Mock],
) -> None:
    instance, _, _, transport = bundle
    instance.create(OWNER, CAMERA, b"offer")
    transport.return_value = (200, {}, b"")
    instance.expire(all_sessions=True)
    assert not instance.sessions


@pytest.mark.parametrize("count,same_owner", [(4, True), (16, False)])
def test_session_limits_are_enforced_before_upstream_request(
    count: int,
    same_owner: bool,
    bundle: tuple[gateway.Gateway, Mock, Mock, Mock],
) -> None:
    instance, _, _, transport = bundle
    for index in range(count):
        instance.sessions[str(index)] = gateway.Session(
            OWNER if same_owner else f"other-{index}",
            CAMERA,
            "/unused",
            100.0,
        )
    with pytest.raises(RemoteError) as caught:
        instance.create(OWNER, CAMERA, b"offer")
    assert_remote_status(429, caught)
    transport.assert_not_called()


def test_http_auth_and_origin_are_required_independently(
    bundle: tuple[gateway.Gateway, Mock, Mock, Mock],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    instance, backend, _, _ = bundle
    value, reply = handler(instance, monkeypatch, headers={"Origin": ORIGIN})
    value.dispatch()
    assert reply.call_args.args[0] == 401
    value, reply = handler(
        instance,
        monkeypatch,
        headers={
            "Origin": "https://other.example",
            "Authorization": "Bearer " + TOKEN,
        },
    )
    value.dispatch()
    assert reply.call_args.args[0] == 403
    backend.authorize.assert_not_called()


def test_keepalive_forces_fresh_authorization(
    bundle: tuple[gateway.Gateway, Mock, Mock, Mock],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    instance, _, _, _ = bundle
    authorize, control = Mock(return_value=OWNER), Mock()
    monkeypatch.setattr(instance, "authorize", authorize)
    monkeypatch.setattr(instance, "control", control)
    value, reply = handler(
        instance,
        monkeypatch,
        method="POST",
        path=f"/v1/cameras/{CAMERA}/whep/{SECRET}/keepalive",
        headers={"Authorization": "Bearer " + TOKEN},
    )
    value.dispatch()
    authorize.assert_called_once_with("Bearer " + TOKEN, fresh=True)
    control.assert_called_once_with(OWNER, CAMERA, SECRET, renew=True)
    assert reply.call_args.args[0] == 204


@pytest.mark.parametrize(
    "length,extra,body,expected",
    [
        ("0", {}, b"", 413),
        ("131073", {}, b"", 413),
        ("-1", {}, b"", 413),
        ("abc", {}, b"", 400),
        ("5", {}, b"abc", 400),
        ("3", {"Transfer-Encoding": "chunked"}, b"abc", 413),
        ("3", {"Content-Type": "text/plain"}, b"abc", 415),
    ],
)
def test_http_offer_size_type_and_framing_limits(
    length: str,
    extra: dict[str, str],
    body: bytes,
    expected: int,
    bundle: tuple[gateway.Gateway, Mock, Mock, Mock],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    instance, _, _, transport = bundle
    value, reply = handler(
        instance,
        monkeypatch,
        method="POST",
        path=f"/v1/cameras/{CAMERA}/whep",
        body=body,
        headers={
            "Authorization": "Bearer " + TOKEN,
            "Content-Length": length,
            "Content-Type": "application/sdp",
            **extra,
        },
    )
    value.dispatch()
    assert reply.call_args.args[0] == expected
    transport.assert_not_called()


def test_reply_uses_no_store_and_only_exact_cors_origin(
    bundle: tuple[gateway.Gateway, Mock, Mock, Mock],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    instance, _, _, _ = bundle
    value, _ = handler(instance, monkeypatch, headers={"Origin": ORIGIN})
    send_header = Mock()
    monkeypatch.setattr(value, "send_response", Mock())
    monkeypatch.setattr(value, "send_header", send_header)
    monkeypatch.setattr(value, "end_headers", Mock())
    gateway.Handler.reply(value, 200, b"ok")
    returned = dict(call.args for call in send_header.call_args_list)
    assert returned["Cache-Control"] == "no-store"
    assert returned["Access-Control-Allow-Origin"] == ORIGIN
    assert returned["Access-Control-Expose-Headers"] == "Location"
    assert returned["Content-Length"] == "2"
    assert value.wfile.getvalue() == b"ok"  # type: ignore[attr-defined]
