"""Authenticated, bounded control bridge; WebRTC media bypasses Django.

Only configured origins and constructed paths are reachable. Supabase credentials
are never returned to the browser or forwarded to the optional local JPEG monitor.
"""

from __future__ import annotations

import json
import re
from datetime import UTC, datetime
from typing import Any
from urllib.parse import urlencode, urlsplit
from uuid import UUID

from django.conf import settings
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from app.web.auth import require_account
from app.web.backend import BackendError, request_remote

SDP_LIMIT = 131072
MONITOR_ORIGIN = "http://127.0.0.1:8765"


def _error(status: int) -> JsonResponse:
    safe_status = status if status in {400, 401, 403, 404, 405, 413, 415, 429} else 503
    return JsonResponse({"error": "video_unavailable"}, status=safe_status)


def _catalog(request: HttpRequest, camera_id: UUID | None = None) -> list[dict[str, Any]]:
    backend = request.backend  # type: ignore[attr-defined]
    query = {
        "select": "id,organization_id,environment_id,name,source,enabled,monitor_id",
        "organization_id": f"eq.{backend.org}",
        "enabled": "eq.true",
        "limit": "501",
    }
    if camera_id:
        query["id"] = f"eq.{camera_id}"
    rows = backend.api(f"/rest/v1/cameras?{urlencode(query)}")
    if not isinstance(rows, list) or len(rows) > 500:
        raise BackendError(502)
    for row in rows:
        if (
            not isinstance(row, dict)
            or row.get("organization_id") != backend.org
            or row.get("enabled") is not True
            or (camera_id is not None and row.get("id") != str(camera_id))
        ):
            raise BackendError(502)
        try:
            if str(UUID(row["id"])) != row["id"]:
                raise ValueError("noncanonical camera")
        except (ValueError, TypeError, KeyError) as exc:
            raise BackendError(502) from exc
    if camera_id and len(rows) != 1:
        raise BackendError(404)
    return rows


def _remote(
    request: HttpRequest, method: str, path: str, body: bytes | None = None
) -> tuple[int, dict[str, str], bytes]:
    origin = settings.PROCESSING_SERVER_URL
    if not origin:
        raise BackendError(503)
    headers = {"Authorization": f"Bearer {request.backend.token}"}  # type: ignore[attr-defined]
    if body is not None:
        headers["Content-Type"] = "application/sdp"
    limit = SDP_LIMIT if "/whep" in path else 2_000_000
    return request_remote(origin, method, path, headers, body, limit=limit, timeout=8)


def _json(headers: dict[str, str], content: bytes) -> Any:
    if headers.get("content-type", "").split(";", 1)[0].strip() != "application/json":
        raise BackendError(502)
    try:
        return json.loads(content)
    except (ValueError, UnicodeDecodeError) as exc:
        raise BackendError(502) from exc


@require_GET
@require_account
def cameras(request: HttpRequest) -> HttpResponse:
    try:
        ids = {row["id"] for row in _catalog(request)}
        code, headers, content = _remote(request, "GET", "/v1/cameras")
        if code != 200:
            return _error(code)
        value = _json(headers, content)
        if not isinstance(value, dict) or not isinstance(value.get("cameras"), list):
            raise BackendError(502)
        rows = value["cameras"]
        if len(rows) > 500 or any(not isinstance(item, dict) for item in rows):
            raise BackendError(502)
        # Never forward source URLs, debug fields or data outside the Django organization.
        fields = {
            "camera_id",
            "name",
            "environment_id",
            "configured",
            "source",
            "status",
            "people_count",
            "boxes",
            "last_seen_at",
            "latency_ms",
            "inference_fps",
            "detector",
            "backend",
        }
        return JsonResponse(
            {
                "cameras": [
                    {key: item.get(key) for key in fields}
                    for item in rows
                    if isinstance(item.get("camera_id"), str) and item["camera_id"] in ids
                ]
            }
        )
    except BackendError as exc:
        return _error(exc.status)


@require_GET
@require_account
def health(request: HttpRequest) -> HttpResponse:
    try:
        code, headers, content = _remote(request, "GET", "/v1/health")
        if code != 200:
            return _error(code)
        value = _json(headers, content)
        if not isinstance(value, dict):
            raise BackendError(502)
        return JsonResponse(
            {
                "catalog_ready": value.get("catalog_ready") is True,
                "analysis_target_fps": value.get("analysis_target_fps"),
                "network_available": value.get("network_error") is None,
            }
        )
    except BackendError as exc:
        return _error(exc.status)


def _location(camera_id: UUID, location: str) -> str:
    origin = settings.PROCESSING_SERVER_URL
    parsed = urlsplit(location)
    if parsed.scheme or parsed.netloc:
        if f"{parsed.scheme}://{parsed.netloc}" != origin:
            raise BackendError(502)
    if parsed.query or parsed.fragment or parsed.username or parsed.password:
        raise BackendError(502)
    match = re.fullmatch(rf"/v1/cameras/{camera_id}/whep/([0-9a-f-]{{36}})", parsed.path)
    if not match:
        raise BackendError(502)
    try:
        key = str(UUID(match[1]))
        if key != match[1]:
            raise ValueError("noncanonical session")
    except ValueError as exc:
        raise BackendError(502) from exc
    return f"/api/processing/cameras/{camera_id}/whep/{key}/"


@require_POST
@require_account
def connect(request: HttpRequest, camera_id: UUID) -> HttpResponse:
    try:
        _catalog(request, camera_id)
        if request.content_type != "application/sdp":
            return _error(415)
        if request.headers.get("Transfer-Encoding"):
            return _error(413)
        body = request.body
        if not 1 <= len(body) <= SDP_LIMIT:
            return _error(413)
        if not body.startswith(b"v=0"):
            return _error(400)
        code, headers, answer = _remote(request, "POST", f"/v1/cameras/{camera_id}/whep", body)
        if code != 201:
            return _error(code)
        location = _location(camera_id, headers.get("location", ""))
        if (
            headers.get("content-type", "").split(";", 1)[0].strip() != "application/sdp"
            or not answer.startswith(b"v=0")
            or len(answer) > SDP_LIMIT
        ):
            # A known valid upstream session must be revoked on malformed answers.
            key = location.rstrip("/").rsplit("/", 1)[-1]
            _remote(request, "DELETE", f"/v1/cameras/{camera_id}/whep/{key}")
            raise BackendError(502)
        response = HttpResponse(answer, status=201, content_type="application/sdp")
        response["Location"] = location
        response["Cache-Control"] = "no-store"
        return response
    except BackendError as exc:
        return _error(exc.status)


@require_http_methods(["DELETE"])
@require_account
def disconnect(request: HttpRequest, camera_id: UUID, session_id: UUID) -> HttpResponse:
    return _control(request, camera_id, session_id, renew=False)


@require_POST
@require_account
def keepalive(request: HttpRequest, camera_id: UUID, session_id: UUID) -> HttpResponse:
    return _control(request, camera_id, session_id, renew=True)


def _control(
    request: HttpRequest, camera_id: UUID, session_id: UUID, *, renew: bool
) -> HttpResponse:
    try:
        # DELETE may revoke a session whose camera was disabled just now. Gateway still
        # requires the same account/session owner; keepalive must re-check enabled state.
        if renew:
            _catalog(request, camera_id)
        suffix = "/keepalive" if renew else ""
        code, _, _ = _remote(
            request,
            "POST" if renew else "DELETE",
            f"/v1/cameras/{camera_id}/whep/{session_id}{suffix}",
        )
        return HttpResponse(status=204) if code == 204 else _error(code)
    except BackendError as exc:
        return _error(exc.status)


@require_GET
@require_account
def local_cameras(request: HttpRequest) -> HttpResponse:
    if not settings.LOCAL_MONITOR_ENABLED:
        return _error(404)
    try:
        catalog = _catalog(request)
        readings = _local_readings()
        result = []
        for camera in catalog:
            item = readings.get(camera.get("monitor_id"), {})
            fresh = _local_fresh(item)
            result.append(
                {
                    "camera_id": camera["id"],
                    "configured": bool(item),
                    "status": "online" if fresh else "waiting",
                    "people_count": item.get("people_count") if fresh else None,
                    "last_seen_at": item.get("last_seen_at") if fresh else None,
                    "latency_ms": None,
                    "inference_fps": None,
                    "boxes": [],
                }
            )
        return JsonResponse({"cameras": result})
    except BackendError as exc:
        return _error(exc.status)


def _local_readings() -> dict[str, dict[str, Any]]:
    code, headers, content = request_remote(
        MONITOR_ORIGIN, "GET", "/api/cameras", {}, limit=200_000, timeout=4
    )
    if code != 200:
        raise BackendError(code)
    data = _json(headers, content)
    if not isinstance(data, dict) or not isinstance(data.get("cameras"), list):
        raise BackendError(502)
    rows = data["cameras"]
    if len(rows) > 500:
        raise BackendError(502)
    result = {}
    for row in rows:
        if not isinstance(row, dict) or not isinstance(row.get("camera_id"), str):
            raise BackendError(502)
        result[row["camera_id"]] = row
    return result


def _local_fresh(reading: dict[str, Any]) -> bool:
    try:
        age = (datetime.now(UTC) - datetime.fromisoformat(reading["last_seen_at"])).total_seconds()
        count = reading["people_count"]
        return (
            reading.get("status") == "online"
            and -5 <= age < 2
            and type(count) is int
            and count >= 0
        )
    except (KeyError, TypeError, ValueError):
        return False


@require_GET
@require_account
def local_frame(request: HttpRequest, camera_id: UUID) -> HttpResponse:
    if not settings.LOCAL_MONITOR_ENABLED:
        return _error(404)
    try:
        camera = _catalog(request, camera_id)[0]
        monitor_id = camera.get("monitor_id")
        if not isinstance(monitor_id, str) or not re.fullmatch(r"[A-Za-z0-9_-]{1,64}", monitor_id):
            return _error(404)
        if not _local_fresh(_local_readings().get(monitor_id, {})):
            return _error(503)
        code, headers, jpeg = request_remote(
            MONITOR_ORIGIN,
            "GET",
            f"/api/cameras/{monitor_id}/frame.jpg",
            {"Origin": "http://127.0.0.1:3000"},
            limit=2_000_000,
            timeout=4,
        )
        if code != 200:
            return _error(code)
        if headers.get("content-type") != "image/jpeg" or not jpeg.startswith(b"\xff\xd8"):
            raise BackendError(502)
        response = HttpResponse(jpeg, content_type="image/jpeg")
        response["Cache-Control"] = "no-store"
        return response
    except BackendError as exc:
        return _error(exc.status)
