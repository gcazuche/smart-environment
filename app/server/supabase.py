"""Bounded HTTPS REST transport; secrets never leave the configured Supabase origin."""

from __future__ import annotations

import http.client
import json
from typing import Any
from urllib.parse import urlencode, urlsplit

from app.server.config import Settings, uuid
from app.server.telemetry import DeliveryError


class RemoteError(Exception):
    def __init__(self, status: int) -> None:
        self.status = status
        super().__init__(f"Serviço remoto indisponível ({status}).")


def request(
    origin: str,
    method: str,
    path: str,
    headers: dict[str, str],
    body: bytes | None = None,
    *,
    limit: int = 2_000_000,
    timeout: float = 8,
) -> tuple[int, dict[str, str], bytes]:
    parsed = urlsplit(origin)
    connection_type = (
        http.client.HTTPSConnection if parsed.scheme == "https" else http.client.HTTPConnection
    )
    connection = connection_type(parsed.hostname or "", parsed.port, timeout=timeout)
    try:
        connection.request(method, path, body, headers)
        response = connection.getresponse()
        content = response.read(limit + 1)
        if len(content) > limit:
            raise RemoteError(502)
        return response.status, dict((k.lower(), v) for k, v in response.getheaders()), content
    except (OSError, http.client.HTTPException) as exc:
        raise RemoteError(503) from exc
    finally:
        connection.close()


class Supabase:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def api(
        self,
        path: str,
        *,
        token: str | None = None,
        method: str = "GET",
        payload: dict[str, Any] | None = None,
    ) -> Any:
        headers = {
            "apikey": self.settings.publishable_key if token else self.settings.secret_key,
            "Content-Type": "application/json",
        }
        if token:
            headers["Authorization"] = f"Bearer {token}"
        if method == "POST":
            headers["Prefer"] = "resolution=ignore-duplicates,return=minimal"
        body = json.dumps(payload).encode() if payload is not None else None
        code, _, content = request(self.settings.supabase_url, method, path, headers, body)
        if not 200 <= code < 300:
            raise RemoteError(code)
        return json.loads(content) if content else None

    def rows(self, table: str, select: str, *, token: str | None = None, **filters: str) -> Any:
        query = urlencode(
            {
                "select": select,
                "organization_id": f"eq.{self.settings.organization_id}",
                "limit": "501",
                **filters,
            }
        )
        result = self.api(f"/rest/v1/{table}?{query}", token=token)
        if not isinstance(result, list) or len(result) >= 501:
            raise RemoteError(502)
        return result

    def authorize(self, token: str) -> str:
        user = self.api("/auth/v1/user", token=token)
        user_id = uuid(user["id"])
        membership = self.rows(
            "organization_members",
            "user_id,role",
            token=token,
            user_id=f"eq.{user_id}",
        )
        if len(membership) != 1 or membership[0]["role"] not in {"admin", "viewer"}:
            raise RemoteError(403)
        return user_id

    def catalog(self) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        cameras = self.rows(
            "cameras",
            "id,organization_id,environment_id,name,source,enabled,version",
            enabled="eq.true",
        )
        return cameras, self.rows("alert_rules", "*")

    def deliver(self, table: str, payload: dict[str, Any]) -> None:
        if table not in {"occupancy_samples", "alerts"} or (
            payload.get("organization_id") != self.settings.organization_id
        ):
            raise DeliveryError("Escopo de entrega inválido.", retryable=False)
        conflict = (
            "camera_id,bucket_start"
            if table == "occupancy_samples"
            else ("organization_id,dedup_key")
        )
        try:
            self.api(f"/rest/v1/{table}?on_conflict={conflict}", method="POST", payload=payload)
        except RemoteError as exc:
            raise DeliveryError(
                f"Entrega pendente: HTTP {exc.status}.",
                retryable=exc.status in {401, 403, 408, 429} or exc.status >= 500,
            ) from exc
