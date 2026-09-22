"""Opt-in, disposable browser QA fixture. Never connects to real services or cameras.

Run with the project's Conda environment:
    python scripts/preview_django_fixture.py --serve-fixture

Open http://127.0.0.1:8001/ and use test@example.invalid / fixture-only.
These are deliberately public, synthetic credentials, not a product demo login.
Stop with Ctrl+C. The session database and all edited fixture records are discarded.
"""

# ruff: noqa: S101 -- fixture assertions deliberately fail closed, never authorize real services.

from __future__ import annotations

import argparse
import copy
import os
import sys
import tempfile
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any
from unittest.mock import patch
from urllib.parse import parse_qs, urlsplit
from uuid import uuid4
from wsgiref.simple_server import WSGIRequestHandler, make_server

ROOT = Path(__file__).resolve().parents[1]
ORG = "11111111-1111-4111-8111-111111111111"
USER = "22222222-2222-4222-8222-222222222222"
ENV_A = "33333333-3333-4333-8333-333333333333"
ENV_B = "44444444-4444-4444-8444-444444444444"
CAM_A = "55555555-5555-4555-8555-555555555555"
CAM_B = "66666666-6666-4666-8666-666666666666"
RULE = "77777777-7777-4777-8777-777777777777"
ALERT = "88888888-8888-4888-8888-888888888888"
ACCESS = "synthetic-access-token-for-browser-qa-only"
REFRESH = "synthetic-refresh-token-for-browser-qa-only"
EMAIL = "test@example.invalid"
PASSWORD = "fixture-only"  # noqa: S105 -- public synthetic fixture, never a real credential.


class Fixture:
    """Small in-memory PostgREST substitute; unknown calls fail rather than use I/O."""

    def __init__(self) -> None:
        now = datetime.now(UTC).replace(second=0, microsecond=0)

        def row(identifier: str, **values: Any) -> dict[str, Any]:
            return {"id": identifier, "organization_id": ORG, "version": 1, **values}

        self.tables: dict[str, list[dict[str, Any]]] = {
            "environments": [
                row(ENV_A, name="Laboratório — cenário sintético"),
                row(ENV_B, name="Sala de reuniões — cenário sintético"),
            ],
            "cameras": [
                row(
                    CAM_A,
                    environment_id=ENV_A,
                    name="Estação 01 — câmera fictícia",
                    source="webcam",
                    address="0",
                    monitor_id="fixture-pc",
                    enabled=True,
                ),
                row(
                    CAM_B,
                    environment_id=ENV_A,
                    name="Entrada — câmera fictícia",
                    source="mjpeg",
                    address="http://camera.example.invalid/video",
                    monitor_id="fixture-entry",
                    enabled=True,
                ),
            ],
            "alert_rules": [
                row(
                    RULE,
                    environment_id=ENV_A,
                    name="Câmera indisponível — exemplo",
                    kind="camera_offline",
                    enabled=True,
                    start_time="08:00:00",
                    end_time="18:00:00",
                    delay_seconds=60,
                ),
            ],
            "alerts": [
                row(
                    ALERT,
                    environment_id=ENV_A,
                    camera_id=CAM_A,
                    title="Alerta sintético para revisão",
                    detail=(
                        "Registro inventado exclusivamente para testar a interface. "
                        "Não é um evento real."
                    ),
                    status="open",
                    occurred_at=(now - timedelta(minutes=10)).isoformat(),
                    reviewed_at=None,
                ),
            ],
            "occupancy_samples": [
                row(
                    str(uuid4()),
                    environment_id=ENV_A,
                    camera_id=CAM_A,
                    bucket_start=(now - timedelta(minutes=5)).isoformat(),
                    state="occupied",
                    people_count=2,
                    model_version="fixture-synthetic-not-inference",
                ),
                row(
                    str(uuid4()),
                    environment_id=ENV_A,
                    camera_id=CAM_A,
                    bucket_start=(now - timedelta(minutes=4)).isoformat(),
                    state="unknown",
                    people_count=None,
                    model_version="fixture-synthetic-not-inference",
                ),
                row(
                    str(uuid4()),
                    environment_id=ENV_A,
                    camera_id=CAM_B,
                    bucket_start=(now - timedelta(minutes=3)).isoformat(),
                    state="empty",
                    people_count=0,
                    model_version="fixture-synthetic-not-inference",
                ),
            ],
        }

    def api(
        self,
        backend: Any,
        path: str,
        *,
        method: str = "GET",
        payload: Any = None,
        headers: Any = None,
    ) -> Any:
        from app.web.backend import BackendError

        del headers
        parsed = urlsplit(path)
        query = parse_qs(parsed.query)
        if parsed.path == "/auth/v1/token" and method == "POST":
            grant = query.get("grant_type", [""])[0]
            valid = (grant == "password" and payload == {"email": EMAIL, "password": PASSWORD}) or (
                grant == "refresh_token" and payload == {"refresh_token": REFRESH}
            )
            if not valid:
                raise BackendError(401)
            return {"access_token": ACCESS, "refresh_token": REFRESH, "expires_in": 3600}
        if backend.token != ACCESS:
            raise BackendError(401)
        if parsed.path == "/auth/v1/user" and method == "GET":
            return {"id": USER, "email": EMAIL}
        if parsed.path == "/auth/v1/logout" and method == "POST":
            return None
        if parsed.path == "/rest/v1/organization_members" and method == "GET":
            assert query.get("organization_id") == [f"eq.{ORG}"]
            assert query.get("user_id") == [f"eq.{USER}"]
            return [{"role": "admin"}]
        if parsed.path == "/rest/v1/rpc/occupancy_report" and method == "POST":
            return self.report(payload)
        if parsed.path == "/rest/v1/rpc/review_alert" and method == "POST":
            for row in self.tables["alerts"]:
                if row["id"] == payload["alert_id"]:
                    if row["version"] != payload["expected_version"]:
                        raise BackendError(409, "40001")
                    if (row["status"], payload["next_status"]) not in {
                        ("open", "reviewed"),
                        ("reviewed", "resolved"),
                    }:
                        raise BackendError(400, "22023")
                    row.update(
                        status=payload["next_status"],
                        version=row["version"] + 1,
                        reviewed_at=datetime.now(UTC).isoformat(),
                    )
                    return copy.deepcopy(row)
            raise BackendError(403)
        assert parsed.path.startswith("/rest/v1/"), "Unexpected fixture path; network forbidden"
        table = parsed.path.removeprefix("/rest/v1/")
        assert table in self.tables, "Unknown fixture table; network forbidden"
        assert query.get("organization_id") == [f"eq.{ORG}"]
        if method == "GET":
            rows = [row for row in self.tables[table] if self.matches(row, query)]
            for order in reversed(query.get("order", [""])[0].split(",")):
                if order:
                    field, _, direction = order.partition(".")
                    rows.sort(key=lambda row: str(row.get(field, "")), reverse=direction == "desc")
            offset, limit = int(query.get("offset", ["0"])[0]), int(query.get("limit", ["500"])[0])
            return copy.deepcopy(rows[offset : offset + limit])
        assert table in {"environments", "cameras", "alert_rules"}, "Fixture table is read-only"
        assert method in {"POST", "PATCH"}, "Unsupported fixture write"
        if method == "POST":
            assert payload["organization_id"] == ORG
            if table == "environments" and any(
                row["name"].casefold() == payload["name"].casefold() for row in self.tables[table]
            ):
                raise BackendError(409, "23505")
            row = {**copy.deepcopy(payload), "id": str(uuid4()), "version": 1}
            self.tables[table].append(row)
            return [copy.deepcopy(row)]
        for row in self.tables[table]:
            if self.matches(row, query):
                row.update(copy.deepcopy(payload))
                row["version"] += 1
                return [copy.deepcopy(row)]
        return []

    @staticmethod
    def matches(row: dict[str, Any], query: dict[str, list[str]]) -> bool:
        for field, values in query.items():
            if field in {"select", "limit", "offset", "order"}:
                continue
            if field == "and":
                for condition in values[0].strip("()").split(","):
                    name, operation, expected = condition.split(".", 2)
                    actual = datetime.fromisoformat(row[name])
                    reference = datetime.fromisoformat(expected)
                    if not {
                        "gte": actual >= reference,
                        "lte": actual <= reference,
                        "lt": actual < reference,
                    }[operation]:
                        return False
                continue
            assert values[0].startswith("eq."), "Unsupported fixture query"
            actual = row.get(field)
            actual = str(actual).lower() if isinstance(actual, bool) else str(actual)
            if actual != values[0][3:]:
                return False
        return True

    def report(self, values: dict[str, Any]) -> list[dict[str, Any]]:
        assert values["org"] == ORG
        start, end = (datetime.fromisoformat(values[key]) for key in ("starts_at", "ends_at"))
        result: dict[tuple[str, str], dict[str, Any]] = {}
        for row in self.tables["occupancy_samples"]:
            bucket = datetime.fromisoformat(row["bucket_start"])
            if not start <= bucket or bucket + timedelta(minutes=1) > end:
                continue
            if values.get("env") and row["environment_id"] != values["env"]:
                continue
            key = row["camera_id"], row["environment_id"]
            report = result.setdefault(
                key,
                {
                    "camera_id": key[0],
                    "environment_id": key[1],
                    "observed_minutes": 0,
                    "occupied_minutes": 0,
                    "empty_minutes": 0,
                    "unknown_minutes": 0,
                    "peak_people": None,
                },
            )
            report["observed_minutes"] += 1
            report[f"{row['state']}_minutes"] += 1
            if row["people_count"] is not None:
                report["peak_people"] = max(report["peak_people"] or 0, row["people_count"])
        return list(result.values())


class SyntheticBannerMiddleware:
    """Fixture-only markup, never enabled by product settings."""

    def __init__(self, get_response: Any) -> None:
        self.get_response = get_response

    def __call__(self, request: Any) -> Any:
        response = self.get_response(request)
        if not response.streaming and response.get("Content-Type", "").startswith("text/html"):
            banner = (
                '<aside class="form-feedback migration-notice" role="alert">'
                "<strong>PRÉVIA SINTÉTICA — NÃO SÃO DADOS REAIS.</strong> "
                "Sem Supabase, câmera ou servidor remoto. Alterações serão descartadas. "
                "Use somente test@example.invalid / fixture-only.</aside>"
            ).encode()
            response.content = response.content.replace(b"<body>", b"<body>" + banner, 1)
            response["Content-Length"] = str(len(response.content))
        return response


class QuietHandler(WSGIRequestHandler):
    def log_message(self, format: str, *args: Any) -> None:
        # Request bodies, cookies and query parameters never enter fixture logs.
        del format, args


def deny_network(*args: Any, **kwargs: Any) -> None:
    del args, kwargs
    raise AssertionError("Outbound network forbidden by browser QA fixture")


def unavailable_video(*args: Any, **kwargs: Any) -> Any:
    from app.web.backend import BackendError

    del args, kwargs
    raise BackendError(503)


def fixture_csrf_failure(request: Any, reason: str = "") -> Any:
    """Expose only Django's rejection reason in isolated QA, never product settings."""
    from django.http import HttpResponseForbidden
    from django.utils.html import escape

    del request
    return HttpResponseForbidden("<body>Fixture CSRF: " + escape(reason) + "</body>")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--serve-fixture", action="store_true", help="Confirm synthetic local QA mode"
    )
    args = parser.parse_args()
    if not args.serve_fixture:
        parser.error("Use --serve-fixture explicitly. This command is not the product server.")
    sys.path.insert(0, str(ROOT))
    # Force hermetic settings before importing Django: no inherited/private env is loaded.
    os.environ["DJANGO_SETTINGS_MODULE"] = "app.web.testing"
    import django
    from django.conf import settings
    from django.contrib.staticfiles.handlers import StaticFilesHandler
    from django.core.management import call_command
    from django.core.wsgi import get_wsgi_application
    from django.db import connections

    fixture = Fixture()
    with tempfile.TemporaryDirectory(prefix="smart-environment-browser-fixture-") as temporary:
        settings.DATABASES["default"]["NAME"] = str(Path(temporary) / "sessions.sqlite3")
        settings.MIDDLEWARE = [*settings.MIDDLEWARE, f"{__name__}.SyntheticBannerMiddleware"]
        settings.CSRF_FAILURE_VIEW = f"{__name__}.fixture_csrf_failure"
        django.setup()
        call_command("migrate", verbosity=0, interactive=False)

        def fake_api(backend: Any, path: str, **kwargs: Any) -> Any:
            return fixture.api(backend, path, **kwargs)

        with (
            patch("app.web.backend.Backend.api", new=fake_api),
            patch("app.web.backend.request_remote", new=unavailable_video),
            patch("app.web.video.request_remote", new=unavailable_video),
            patch("socket.create_connection", new=deny_network),
            patch("socket.socket.connect", new=deny_network),
        ):
            application = StaticFilesHandler(get_wsgi_application())
            try:
                with make_server(
                    "127.0.0.1", 8001, application, handler_class=QuietHandler
                ) as server:
                    print("SYNTHETIC QA ONLY: http://127.0.0.1:8001/", flush=True)
                    print("Fixture login: test@example.invalid / fixture-only", flush=True)
                    print(
                        "No remote services or cameras. Ctrl+C stops and discards the fixture.",
                        flush=True,
                    )
                    server.serve_forever()
            except KeyboardInterrupt:
                print("Synthetic preview stopped; temporary data discarded.", flush=True)
            finally:
                connections.close_all()


if __name__ == "__main__":
    main()
