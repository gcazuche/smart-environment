"""Supabase login with opaque Django sessions and serialized refresh (one worker)."""

import hashlib
import ipaddress
import threading
import time
from functools import wraps
from urllib.parse import urlencode
from uuid import UUID

from django.conf import settings
from django.contrib.sessions.backends.db import SessionStore
from django.http import JsonResponse
from django.middleware.csrf import rotate_token
from django.shortcuts import redirect, render
from django.utils.crypto import salted_hmac

from app.web.backend import Backend, BackendError, configured
from app.web.models import LoginAttempt

# Bounded lock striping, shared by refresh and logout within the single web worker.
LOCKS = [threading.RLock() for _ in range(64)]


def session_lock(key: str):
    return LOCKS[int(hashlib.sha256(key.encode()).hexdigest()[:8], 16) % len(LOCKS)]


def identity(backend: Backend) -> dict:
    user = backend.api("/auth/v1/user")
    try:
        uid = str(UUID(user["id"]))
        email = str(user.get("email", ""))[:254]
    except (KeyError, TypeError, ValueError) as exc:
        raise BackendError(401) from exc
    query = urlencode(
        {
            "select": "role",
            "organization_id": f"eq.{backend.org}",
            "user_id": f"eq.{uid}",
            "limit": 2,
        }
    )
    rows = backend.api(f"/rest/v1/organization_members?{query}")
    if (
        not isinstance(rows, list)
        or len(rows) != 1
        or not isinstance(rows[0], dict)
        or rows[0].get("role") not in {"admin", "viewer"}
    ):
        raise BackendError(403)
    return {"id": uid, "email": email, "name": email.split("@")[0], "role": rows[0]["role"]}


def tokens(data: object) -> dict:
    if not isinstance(data, dict):
        raise BackendError(502)
    access, refresh = data.get("access_token"), data.get("refresh_token")
    duration = data.get("expires_in")
    if (
        not isinstance(access, str)
        or not 20 <= len(access) <= 8192
        or not isinstance(refresh, str)
        or not 10 <= len(refresh) <= 8192
        or not isinstance(duration, (int, float))
        or isinstance(duration, bool)
        or not 30 <= duration <= 86400
    ):
        raise BackendError(502)
    return {"access_token": access, "refresh_token": refresh, "expires_at": time.time() + duration}


def throttle(email: str, remote_addr: str) -> None:
    """Persistent fixed-window limits. Do not trust X-Forwarded-For from clients."""
    from django.db.models import F

    now = time.time()
    LoginAttempt.objects.filter(expires_at__lt=now).delete()
    # Account bucket prevents distributed guessing; address bucket limits account spraying.
    for scope, limit in ((f"email:{email.casefold()}", 8), (f"ip:{remote_addr}", 40)):
        key = salted_hmac("web-login", scope).hexdigest()
        record, _ = LoginAttempt.objects.get_or_create(
            key=key, defaults={"expires_at": now + 300, "attempts": 0}
        )
        updated = LoginAttempt.objects.filter(key=key, attempts__lt=limit).update(
            attempts=F("attempts") + 1
        )
        if not updated or record.expires_at <= now:
            raise BackendError(429)


def sign_in(request, email: str, password: str) -> dict:
    throttle(email, client_address(request))
    session = tokens(
        Backend().api(
            "/auth/v1/token?grant_type=password",
            method="POST",
            payload={"email": email, "password": password},
        )
    )
    account = identity(Backend(session["access_token"]))
    request.session.flush()
    rotate_token(request)
    session["user_id"] = account["id"]
    session["login_at"] = time.time()
    request.session["supabase"] = session
    request.session.set_expiry(settings.SESSION_COOKIE_AGE)
    return account


def authenticate(request) -> dict:
    if not configured():
        raise BackendError(503)
    key = request.session.session_key
    if not key:
        raise BackendError(401)
    with session_lock(key):
        store = SessionStore(session_key=key)
        session = store.get("supabase")
        if (
            not isinstance(session, dict)
            or not session.get("user_id")
            or time.time() - session.get("login_at", 0) >= settings.SESSION_COOKIE_AGE
        ):
            raise BackendError(401)
        if session.get("expires_at", 0) <= time.time() + 60:
            refreshed = tokens(
                Backend().api(
                    "/auth/v1/token?grant_type=refresh_token",
                    method="POST",
                    payload={"refresh_token": session["refresh_token"]},
                )
            )
            session = {**session, **refreshed}
            store["supabase"] = session
            store.save()
            store.modified = False
        backend = Backend(session["access_token"])
        account = identity(backend)
        if account["id"] != session["user_id"]:
            raise BackendError(401)
        request.session = store
        request.backend = backend
        return account


def client_address(request) -> str:
    peer = request.META.get("REMOTE_ADDR", "unknown")
    # The bundled Caddy config overwrites this dedicated header. The WSGI port
    # binds loopback and cannot be reached directly by network clients.
    if settings.PRODUCTION and peer in {"127.0.0.1", "::1"}:
        forwarded = request.META.get("HTTP_X_SMART_CLIENT_IP", "")
        if forwarded:
            try:
                return str(ipaddress.ip_address(forwarded))
            except ValueError:
                raise BackendError(400) from None
    return peer


def sign_out(request) -> bool:
    key = request.session.session_key or ""
    remote_ok = True
    with session_lock(key):
        store = SessionStore(session_key=key) if key else request.session
        session = store.get("supabase", {})
        try:
            if session.get("access_token"):
                Backend(session["access_token"]).api("/auth/v1/logout?scope=local", method="POST")
        except BackendError:
            remote_ok = False
        finally:
            store.flush()
            request.session = store
    return remote_ok


def require_account(view):
    @wraps(view)
    def wrapped(request, *args, **kwargs):
        try:
            request.account = authenticate(request)
            return view(request, *args, **kwargs)
        except BackendError as error:
            if error.status in {401, 403}:
                request.session.flush()
            if request.path.startswith("/api/"):
                return JsonResponse({"error": str(error)}, status=error.status)
            if error.status == 401:
                return redirect("web:login")
            return render(
                request,
                "web/service_error.html",
                {"error": str(error)},
                status=error.status if error.status in {403, 429} else 503,
            )

    return wrapped
