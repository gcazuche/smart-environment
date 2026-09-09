"""Loopback-only authenticated WHEP gateway. Put Caddy/TLS in front of it."""

from __future__ import annotations

import hashlib
import json
import re
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Protocol
from urllib.parse import urlsplit
from uuid import UUID, uuid4

from app.server.config import Settings
from app.server.supabase import RemoteError, Supabase, request

MEDIA = "http://127.0.0.1:8889"
ROUTE = re.compile(r"/v1/cameras/([0-9a-f-]{36})/whep(?:/([0-9a-f-]{36})(/keepalive)?)?\Z")


class StatusProvider(Protocol):
    def cameras(self) -> list[dict[str, Any]]: ...
    def available(self, camera_id: str) -> bool: ...
    def health(self) -> dict[str, Any]: ...


@dataclass
class Session:
    owner: str
    camera: str
    location: str
    renewed: float
    closing: bool = False


class Gateway:
    def __init__(self, settings: Settings, backend: Supabase, status: StatusProvider) -> None:
        self.settings, self.backend, self.status = settings, backend, status
        self.sessions: dict[str, Session] = {}
        self.tokens: dict[str, tuple[str, float]] = {}
        self.lock = threading.RLock()

    def authorize(self, bearer: str, *, fresh: bool = False) -> str:
        if not bearer.startswith("Bearer ") or not 30 <= len(bearer) <= 8192:
            raise RemoteError(401)
        token = bearer[7:]
        key, now = hashlib.sha256(token.encode()).hexdigest(), time.monotonic()
        with self.lock:
            cached = self.tokens.get(key)
            if not fresh and cached and now - cached[1] < 10:
                return cached[0]
        try:
            owner = self.backend.authorize(token)
        except Exception:
            with self.lock:
                self.tokens.pop(key, None)
            raise
        with self.lock:
            self.tokens = {k: v for k, v in self.tokens.items() if now - v[1] < 10}
            if len(self.tokens) < 128:
                self.tokens[key] = (owner, now)
        return owner

    def remove(self, key: str) -> None:
        with self.lock:
            session = self.sessions.get(key)
            if session:
                session.closing = True
        if session:
            try:
                code, _, _ = request(MEDIA, "DELETE", session.location, {}, limit=131072, timeout=2)
                if 200 <= code < 300 or code == 404:
                    with self.lock:
                        self.sessions.pop(key, None)
            except RemoteError:
                pass  # Preserve the pending revocation for the watchdog to retry.

    def expire(self, *, all_sessions: bool = False) -> None:
        with self.lock:
            expired = [
                key
                for key, item in self.sessions.items()
                if (
                    all_sessions
                    or item.closing
                    or time.monotonic() - item.renewed > 35
                    or not self.status.available(item.camera)
                )
            ]
        if expired:
            with ThreadPoolExecutor(max_workers=4, thread_name_prefix="video-close") as workers:
                list(workers.map(self.remove, expired))

    def create(self, owner: str, camera: str, sdp: bytes) -> tuple[bytes, str]:
        if not self.status.available(camera):
            raise RemoteError(404)
        # Serialize the bounded create operation so concurrent offers cannot exceed the limit.
        with self.lock:
            if (
                len(self.sessions) >= 16
                or sum(s.owner == owner for s in self.sessions.values()) >= 4
            ):
                raise RemoteError(429)
            endpoint = f"/{self.settings.streams[camera]}/whep"
            code, headers, answer = request(
                MEDIA,
                "POST",
                endpoint,
                {"Content-Type": "application/sdp"},
                sdp,
                limit=131072,
            )
            location = headers.get("location", "")
            parsed = urlsplit(location)
            # MediaMTX 1.20.1 returns a path-absolute Location; no redirects/query accepted.
            if (
                code != 201
                or not re.fullmatch(
                    re.escape(endpoint) + r"/[0-9a-f-]{36}",
                    location,
                )
                or parsed.query
            ):
                raise RemoteError(502)
            try:
                if str(UUID(location.rsplit("/", 1)[-1])) != location.rsplit("/", 1)[-1]:
                    raise ValueError("Invalid session UUID")
            except ValueError as exc:
                raise RemoteError(502) from exc
            key = str(uuid4())
            self.sessions[key] = Session(owner, camera, location, time.monotonic())
            if headers.get("content-type", "").split(";", 1)[0].strip() != "application/sdp":
                self.remove(key)
                raise RemoteError(502)
        if not self.status.available(camera):
            self.remove(key)
            raise RemoteError(404)
        return answer, f"/v1/cameras/{camera}/whep/{key}"

    def control(self, owner: str, camera: str, key: str, *, renew: bool) -> None:
        with self.lock:
            item = self.sessions.get(key)
            if not item or item.closing or item.owner != owner or item.camera != camera:
                raise RemoteError(404)
            if renew:
                if time.monotonic() - item.renewed > 35 or not self.status.available(camera):
                    raise RemoteError(404)
                item.renewed = time.monotonic()
        if not renew:
            self.remove(key)


class Server(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True

    def __init__(self, gateway: Gateway) -> None:
        self.gateway = gateway
        self.slots = threading.BoundedSemaphore(16)
        super().__init__(("127.0.0.1", gateway.settings.port), Handler)

    def process_request(self, request_socket: Any, client_address: Any) -> None:
        if not self.slots.acquire(blocking=False):
            self.shutdown_request(request_socket)
            return
        try:
            super().process_request(request_socket, client_address)
        except Exception:
            self.slots.release()
            raise

    def process_request_thread(self, request_socket: Any, client_address: Any) -> None:
        try:
            super().process_request_thread(request_socket, client_address)
        finally:
            self.slots.release()

    def handle_error(self, request_socket: Any, client_address: Any) -> None:
        pass  # Do not put SDP, URLs, tokens or raw provider responses into logs.


class Handler(BaseHTTPRequestHandler):
    server: Server
    server_version = "SmartEnvironment"
    sys_version = ""

    def setup(self) -> None:
        super().setup()
        self.connection.settimeout(10)

    def log_message(self, format: str, *args: Any) -> None:
        pass

    def reply(self, code: int, body: bytes = b"", **headers: str) -> None:
        self.send_response(code)
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        origin = self.headers.get("Origin", "")
        if origin in self.server.gateway.settings.allowed_origins:
            self.send_header("Access-Control-Allow-Origin", origin)
            self.send_header("Vary", "Origin")
            self.send_header("Access-Control-Expose-Headers", "Location")
        for key, value in headers.items():
            self.send_header(key.replace("_", "-"), value)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def dispatch(self) -> None:
        gateway = self.server.gateway
        try:
            origin = self.headers.get("Origin")
            if origin and origin not in gateway.settings.allowed_origins:
                raise RemoteError(403)
            if self.command == "OPTIONS":
                if not origin or not self.path.startswith("/v1/"):
                    raise RemoteError(403)
                self.reply(
                    204,
                    Access_Control_Allow_Methods="GET, POST, DELETE, OPTIONS",
                    Access_Control_Allow_Headers="Authorization, Content-Type",
                    Access_Control_Max_Age="300",
                )
                return
            owner = gateway.authorize(
                self.headers.get("Authorization", ""),
                fresh=self.path.endswith("/keepalive"),
            )
            if self.path in {"/v1/cameras", "/v1/health"} and self.command == "GET":
                payload = (
                    {"cameras": gateway.status.cameras()}
                    if self.path.endswith("cameras")
                    else gateway.status.health()
                )
                self.reply(200, json.dumps(payload).encode(), Content_Type="application/json")
                return
            match = ROUTE.fullmatch(self.path)
            if not match:
                raise RemoteError(404)
            camera, key, keepalive = match.groups()
            if key and (
                (keepalive and self.command == "POST")
                or (not keepalive and self.command == "DELETE")
            ):
                gateway.control(owner, camera, key, renew=bool(keepalive))
                self.reply(204)
                return
            if key or self.command != "POST":
                raise RemoteError(405)
            length = int(self.headers.get("Content-Length", "0"))
            if self.headers.get("Transfer-Encoding") or not 1 <= length <= 131072:
                raise RemoteError(413)
            if self.headers.get_content_type() != "application/sdp":
                raise RemoteError(415)
            body = self.rfile.read(length)
            if len(body) != length:
                raise RemoteError(400)
            answer, location = gateway.create(owner, camera, body)
            self.reply(201, answer, Content_Type="application/sdp", Location=location)
        except RemoteError as exc:
            code = exc.status if exc.status in {400, 401, 403, 404, 405, 413, 415, 429} else 503
            self.reply(code, b'{"error":"request_unavailable"}', Content_Type="application/json")
        except (ValueError, KeyError, TypeError):
            self.reply(400)

    do_GET = dispatch
    do_POST = dispatch
    do_DELETE = dispatch
    do_OPTIONS = dispatch
