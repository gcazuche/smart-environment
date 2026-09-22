"""Server-only configuration. Never log file contents or credential values."""

import os
import re
from pathlib import Path
from urllib.parse import urlsplit
from uuid import UUID

from django.core.exceptions import ImproperlyConfigured

ROOT = Path(__file__).resolve().parents[2]


def read_env(path: Path) -> dict[str, str]:
    if not path.is_file():
        return {}
    if path.stat().st_size > 65536:
        raise ImproperlyConfigured("Arquivo de configuração excede o limite.")
    values = {}
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip("\"'")
    return values


def origin(value: str, *, processing: bool = False) -> str:
    try:
        url = urlsplit(value)
        port = url.port
        local = url.hostname in {"localhost", "127.0.0.1", "::1"}
        if (
            not url.hostname
            or url.username
            or url.password
            or url.query
            or url.fragment
            or url.path not in {"", "/"}
            or (
                url.scheme != "https"
                and not (local and url.scheme == "http" and (not processing or port == 8766))
            )
        ):
            raise ValueError
    except ValueError as exc:
        raise ImproperlyConfigured(
            "Origem do serviço inválida; use HTTPS sem caminho/credenciais."
        ) from exc
    return f"{url.scheme}://{url.netloc}"


def load() -> dict[str, str]:
    # Compatibility bridge is local, read-only and allowlisted. No frontend injection.
    legacy = read_env(ROOT / "dashboard" / ".env.local")
    values = {
        "SUPABASE_URL": legacy.get("VITE_SUPABASE_URL", ""),
        "SUPABASE_PUBLISHABLE_KEY": legacy.get("VITE_SUPABASE_PUBLISHABLE_KEY", ""),
        "ORGANIZATION_ID": legacy.get("VITE_ORGANIZATION_ID", ""),
        "PROCESSING_SERVER_URL": legacy.get("VITE_PROCESSING_SERVER_URL", ""),
    }
    values.update(read_env(ROOT / "config" / "web" / ".env.web.local"))
    for key in (
        *values,
        "DJANGO_SECRET_KEY",
        "DJANGO_DEBUG",
        "DJANGO_ALLOWED_HOSTS",
        "DJANGO_CSRF_TRUSTED_ORIGINS",
        "DJANGO_PRODUCTION",
        "DJANGO_DATABASE_PATH",
        "LOCAL_MONITOR_ENABLED",
        "DJANGO_STATIC_ROOT",
    ):
        if key in os.environ:
            values[key] = os.environ[key]
    for key in ("SUPABASE_URL", "PROCESSING_SERVER_URL"):
        if values.get(key):
            values[key] = origin(values[key], processing=key == "PROCESSING_SERVER_URL")
    key = values.get("SUPABASE_PUBLISHABLE_KEY", "")
    if key and not re.fullmatch(r"sb_publishable_[A-Za-z0-9_-]+", key):
        raise ImproperlyConfigured("Use somente a chave publicável do Supabase.")
    if values.get("ORGANIZATION_ID"):
        try:
            values["ORGANIZATION_ID"] = str(UUID(values["ORGANIZATION_ID"]))
        except ValueError as exc:
            raise ImproperlyConfigured("Identificador da organização inválido.") from exc
    return values
