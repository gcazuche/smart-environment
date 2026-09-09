"""Explicit, fail-closed server configuration. No browser secrets or camera URLs."""

from __future__ import annotations

import os
import re
import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import urlsplit
from uuid import UUID


def uuid(value: str) -> str:
    return str(UUID(value))


def origin(value: str, *, loopback: bool = False) -> str:
    if any(char.isspace() or ord(char) < 32 for char in value):
        raise ValueError("Origem inválida.")
    parsed = urlsplit(value)
    _ = parsed.port  # Reject malformed and out-of-range ports before any network access.
    local = loopback and parsed.hostname in {"localhost", "127.0.0.1"}
    if (parsed.scheme != "https" and not (local and parsed.scheme == "http")) or (
        not parsed.hostname
        or parsed.username
        or parsed.password
        or parsed.query
        or parsed.fragment
        or parsed.path not in {"", "/"}
    ):
        raise ValueError("Use uma origem HTTPS sem caminho, credenciais ou parâmetros.")
    return value.rstrip("/")


def load_env(path: Path) -> None:
    """Read a systemd-compatible KEY=value subset, never execute shell syntax."""
    if os.name != "nt" and path.stat().st_mode & 0o077:
        raise ValueError("O arquivo de segredos deve ter permissão 600.")
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        key, sep, value = line.partition("=")
        if not sep or key not in {
            "SUPABASE_URL",
            "SUPABASE_PUBLISHABLE_KEY",
            "SUPABASE_SECRET_KEY",
        }:
            raise ValueError("Variável não permitida no arquivo do servidor.")
        os.environ[key] = value.strip().strip('"').strip("'")


@dataclass(frozen=True)
class Settings:
    organization_id: str
    streams: dict[str, str]
    allowed_origins: tuple[str, ...]
    database: Path
    supabase_url: str
    publishable_key: str = field(repr=False)
    secret_key: str = field(repr=False)
    analysis_fps: float = 2.0
    cpu_threads: int = 4
    port: int = 8766

    @classmethod
    def read(cls, path: Path) -> Settings:
        data = tomllib.loads(path.read_text(encoding="utf-8"))
        streams = {uuid(key): value for key, value in data.get("streams", {}).items()}
        if (
            not 1 <= len(streams) <= 4
            or any(
                not isinstance(value, str)
                or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,63}", value)
                for value in streams.values()
            )
            or len(set(streams.values())) != len(streams)
        ):
            raise ValueError("Configure 1 a 4 UUIDs com caminhos de stream únicos e simples.")
        origins = tuple(origin(value, loopback=True) for value in data["allowed_origins"])
        if not origins or len(origins) > 8:
            raise ValueError("Informe explicitamente as origens permitidas do dashboard.")
        raw_fps, raw_threads = data.get("analysis_fps", 2), data.get("cpu_threads", 4)
        if type(raw_fps) not in {int, float} or type(raw_threads) is not int:
            raise ValueError("Use FPS numérico e número inteiro de threads.")
        fps, threads = float(raw_fps), raw_threads
        if not 0.2 <= fps <= 5 or not 1 <= threads <= 8:
            raise ValueError("Análise: 0,2 a 5 FPS; threads CPU: 1 a 8.")
        public = os.environ.get("SUPABASE_PUBLISHABLE_KEY", "")
        secret = os.environ.get("SUPABASE_SECRET_KEY", "")
        if not public.startswith("sb_publishable_") or not secret.startswith("sb_secret_"):
            raise ValueError("Configure as chaves publicável e secret do Supabase no servidor.")
        return cls(
            uuid(data["organization_id"]),
            streams,
            origins,
            (path.parent / data.get("database", "../../data/server/outbox.sqlite3")).resolve(),
            origin(os.environ.get("SUPABASE_URL", "")),
            public,
            secret,
            fps,
            threads,
        )
