"""HTTP boundaries and configuration with fake connections/files only."""

import json
from unittest.mock import MagicMock, patch

import pytest
from django.core.exceptions import ImproperlyConfigured

from app.web.backend import Backend, BackendError, request_remote
from app.web.configuration import origin, read_env


def test_adapter_sends_only_user_bearer_to_fixed_origin():
    with patch("app.web.backend.request_remote", return_value=(200, {}, b"[]")) as transport:
        Backend("synthetic-token").api("/rest/v1/cameras", method="GET")
    args = transport.call_args.args
    assert args[0] == "https://example.invalid"
    assert args[3]["Authorization"] == "Bearer synthetic-token"
    assert "Cookie" not in args[3]


def test_error_hides_provider_details():
    body = json.dumps({"code": "23505", "message": "provider-sensitive-detail"}).encode()
    with patch("app.web.backend.request_remote", return_value=(409, {}, body)):
        with pytest.raises(BackendError) as caught:
            Backend("synthetic-token").api("/rest/v1/cameras")
    assert caught.value.code == "23505"
    assert "sensitive" not in str(caught.value)


def test_http_never_follows_redirects_and_closes():
    conn = MagicMock()
    conn.getresponse.return_value.status = 302
    conn.getresponse.return_value.read.return_value = b""
    conn.getresponse.return_value.getheaders.return_value = [
        ("Location", "https://elsewhere.invalid")
    ]
    with patch("app.web.backend.http.client.HTTPSConnection", return_value=conn):
        code, _, _ = request_remote("https://example.invalid", "GET", "/auth/v1/user", {})
    assert code == 302
    conn.request.assert_called_once()
    conn.close.assert_called_once()


def test_transport_rejects_oversized_body():
    conn = MagicMock()
    conn.getresponse.return_value.read.return_value = b"12345"
    with patch("app.web.backend.http.client.HTTPSConnection", return_value=conn):
        with pytest.raises(BackendError):
            request_remote("https://example.invalid", "GET", "/health", {}, limit=4)
    conn.close.assert_called_once()


@pytest.mark.parametrize(
    "value",
    [
        "http://external.invalid",
        "https://u:p@host",
        "https://host/path",
        "https://host/?key=bad",
        "https://host/#fragment",
        "https://host:bad",
    ],
)
def test_untrusted_origin_rejected(value):
    with pytest.raises(ImproperlyConfigured):
        origin(value)


def test_only_gateway_loopback_port_accepted():
    assert origin("http://127.0.0.1:8766", processing=True) == "http://127.0.0.1:8766"
    with pytest.raises(ImproperlyConfigured):
        origin("http://127.0.0.1:8000", processing=True)


def test_env_reader_handles_missing_and_size_limit(tmp_path):
    assert read_env(tmp_path / "missing") == {}
    path = tmp_path / "large"
    path.write_text("x" * 65537)
    with pytest.raises(ImproperlyConfigured):
        read_env(path)
