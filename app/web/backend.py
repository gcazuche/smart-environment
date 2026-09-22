"""Allowlisted REST adapter; public key plus the user's token, never service-role."""

import http.client
import json
from typing import Any
from urllib.parse import urlsplit

from django.conf import settings


class BackendError(Exception):
    def __init__(self, status: int, code: str = "") -> None:
        self.status, self.code = status, code
        messages = {
            401: "Sessão inválida ou expirada. Entre novamente.",
            403: "Sua conta não tem permissão para esta operação.",
            409: "O registro mudou. Atualize a página antes de salvar novamente.",
            429: "Muitas tentativas. Aguarde alguns minutos e tente novamente.",
        }
        super().__init__(
            messages.get(status, "Não foi possível acessar o serviço. Tente novamente.")
        )


def request_remote(
    origin: str,
    method: str,
    path: str,
    headers: dict[str, str],
    body: bytes | None = None,
    *,
    limit: int = 2_000_000,
    timeout: float = 8,
) -> tuple[int, dict[str, str], bytes]:
    """No redirects, bounded body/timeout; callers select fixed configured origins."""
    parsed = urlsplit(origin)
    if not path.startswith("/") or path.startswith("//") or "\r" in path or "\n" in path:
        raise BackendError(400)
    cls = http.client.HTTPSConnection if parsed.scheme == "https" else http.client.HTTPConnection
    conn = cls(parsed.hostname or "", parsed.port, timeout=timeout)
    try:
        conn.request(method, path, body, headers)
        response = conn.getresponse()
        payload = response.read(limit + 1)
        if len(payload) > limit:
            raise BackendError(502)
        return response.status, {k.lower(): v for k, v in response.getheaders()}, payload
    except (OSError, http.client.HTTPException, ValueError) as exc:
        raise BackendError(503) from exc
    finally:
        conn.close()


def configured() -> bool:
    return bool(
        not settings.DEBUG
        and settings.SUPABASE_URL
        and settings.SUPABASE_PUBLISHABLE_KEY
        and settings.ORGANIZATION_ID
        and settings.WEB_SECRET_CONFIGURED
    )


class Backend:
    def __init__(self, token: str = "") -> None:
        self.token = token
        self.org = settings.ORGANIZATION_ID

    def api(
        self,
        path: str,
        *,
        method: str = "GET",
        payload: Any = None,
        headers: dict[str, str] | None = None,
    ) -> Any:
        if not configured():
            raise BackendError(503)
        if not path.startswith(("/auth/v1/", "/rest/v1/")):
            raise BackendError(400)
        combined = {"Content-Type": "application/json", "apikey": settings.SUPABASE_PUBLISHABLE_KEY}
        if headers:
            combined.update(headers)
        if self.token:
            combined["Authorization"] = f"Bearer {self.token}"
        body = json.dumps(payload).encode() if payload is not None else None
        code, _, content = request_remote(settings.SUPABASE_URL, method, path, combined, body)
        try:
            data = json.loads(content) if content else None
        except (ValueError, UnicodeError) as exc:
            raise BackendError(502) from exc
        if not 200 <= code < 300:
            error_code = str(data.get("code", ""))[:40] if isinstance(data, dict) else ""
            raise BackendError(code, error_code)
        return data
