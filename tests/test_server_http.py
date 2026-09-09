"""Exercise the actual loopback HTTP boundary with synthetic identity and SDP only."""

from __future__ import annotations

import http.client
import json
import threading
from pathlib import Path
from unittest.mock import Mock

from app.server.config import Settings
from app.server.gateway import Gateway, Server


def test_http_auth_cors_and_whep_lifecycle(monkeypatch, tmp_path: Path):
    camera = "20000000-0000-4000-8000-000000000001"
    user = "30000000-0000-4000-8000-000000000001"
    settings = Settings(
        "10000000-0000-4000-8000-000000000001",
        {camera: "camera1"},
        ("http://localhost:3000",),
        tmp_path / "unused.sqlite3",
        "https://synthetic.supabase.co",
        "sb_publishable_test",
        "sb_secret_test",
        port=0,
    )
    backend, status = Mock(), Mock()
    backend.authorize.return_value = user
    status.available.return_value = True
    status.cameras.return_value = [{"camera_id": camera, "people_count": None}]
    media = Mock(
        return_value=(
            201,
            {
                "content-type": "application/sdp",
                "location": "/camera1/whep/40000000-0000-4000-8000-000000000001",
            },
            b"v=0\r\n",
        )
    )
    monkeypatch.setattr("app.server.gateway.request", media)
    gateway = Gateway(settings, backend, status)
    server = Server(gateway)
    worker = threading.Thread(target=server.serve_forever, daemon=True)
    worker.start()

    def call(method, path, headers=None, body=None):
        connection = http.client.HTTPConnection("127.0.0.1", server.server_port, timeout=3)
        try:
            connection.request(method, path, body, headers or {})
            response = connection.getresponse()
            return response.status, dict(response.getheaders()), response.read()
        finally:
            connection.close()

    try:
        assert call("GET", "/v1/cameras")[0] == 401
        assert call("OPTIONS", "/v1/cameras", {"Origin": "https://other.invalid"})[0] == 403
        assert call("OPTIONS", "/v1/cameras", {"Origin": "http://localhost:3000"})[0] == 204
        headers = {
            "Authorization": "Bearer synthetic-valid-session-token-only",
            "Origin": "http://localhost:3000",
        }
        code, reply, payload = call("GET", "/v1/cameras", headers)
        assert code == 200 and json.loads(payload)["cameras"][0]["people_count"] is None
        assert reply["Access-Control-Allow-Origin"] == "http://localhost:3000"
        assert reply["Cache-Control"] == "no-store"
        code, reply, _ = call(
            "POST",
            f"/v1/cameras/{camera}/whep",
            {**headers, "Content-Type": "application/sdp"},
            b"v=0\r\n",
        )
        assert code == 201
        location = reply["Location"]
        assert location.startswith(f"/v1/cameras/{camera}/whep/")
        assert call("POST", location + "/keepalive", headers)[0] == 204
        assert call("DELETE", location)[0] == 401
        media.return_value = (200, {}, b"{}")
        assert call("DELETE", location, headers)[0] == 204
        assert gateway.sessions == {}
    finally:
        server.shutdown()
        server.server_close()
        worker.join(3)
