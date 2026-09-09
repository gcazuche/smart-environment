"""Durable, metadata-only minute aggregation and bounded idempotent delivery."""

from __future__ import annotations

import json
import sqlite3
import threading
import time
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import NAMESPACE_URL, UUID, uuid5
from zoneinfo import ZoneInfo

MODEL = "intel-yolo26n-openvino-person-v1"


class DeliveryError(Exception):
    def __init__(self, message: str, *, retryable: bool) -> None:
        super().__init__(message)
        self.retryable = retryable


def timestamp(value: datetime) -> float:
    if value.tzinfo is None:
        raise ValueError("Use data/hora com fuso explícito.")
    return value.timestamp()


def iso(value: float) -> str:
    return datetime.fromtimestamp(value, UTC).isoformat()


class Telemetry:
    """One SQLite writer lock; HTTP callbacks never hold it. Full queue stops ingestion.

    Active buckets and alert episodes survive restarts. Successful sends are removed;
    permanent failures remain in the same bounded outbox as dead letters for review.
    A crash after remote acceptance is safe because the caller uses ignore-duplicates.
    """

    def __init__(
        self,
        organization_id: str,
        db_path: Path,
        max_pending: int = 10000,
        stale_seconds: float = 5,
    ) -> None:
        self.org = str(UUID(organization_id))
        if max_pending < 1 or stale_seconds <= 0:
            raise ValueError("Limites de telemetria inválidos.")
        self.max_pending, self.stale = max_pending, stale_seconds
        self.lock = threading.RLock()
        self.delivery_lock = threading.Lock()
        db_path.parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(db_path, check_same_thread=False, timeout=5)
        self.db.execute("pragma journal_mode=WAL")
        self.db.execute("pragma synchronous=FULL")
        self.db.execute("create table if not exists metadata (key text primary key, value text)")
        self.db.execute("create table if not exists active (camera text primary key, payload text)")
        self.db.execute("create table if not exists episodes (key text primary key, payload text)")
        self.db.execute("""create table if not exists outbox (
            id text primary key, target text not null, payload text not null,
            attempts integer not null default 0, next_try real not null default 0,
            dead integer not null default 0)""")
        existing = self.db.execute("select value from metadata where key='organization'").fetchone()
        if existing and existing[0] != self.org:
            self.db.close()
            raise ValueError("A fila pertence a outra organização; preserve-a separadamente.")
        self.db.execute("insert or ignore into metadata values ('organization', ?)", (self.org,))
        self.db.commit()

    def _enqueue(self, target: str, payload: dict[str, Any]) -> None:
        if self.db.execute("select 1 from outbox where id=?", (payload["id"],)).fetchone():
            return
        count = self.db.execute("select count(*) from outbox").fetchone()[0]
        if count >= self.max_pending:
            raise RuntimeError("Fila cheia; dados preservados. Intervenção necessária.")
        self.db.execute(
            "insert into outbox(id,target,payload) values (?,?,?)",
            (payload["id"], target, json.dumps(payload, separators=(",", ":"))),
        )

    def _finish(self, bucket: dict[str, Any]) -> None:
        full = bucket["covered"] and bucket["last"] >= bucket["minute"] + 60 - self.stale
        state = (
            "unknown"
            if bucket["changed"]
            else ("occupied" if bucket["peak"] > 0 else "empty" if full else "unknown")
        )
        camera = bucket["camera"]
        key = f"{self.org}:{camera['id']}:{iso(bucket['minute'])}"
        self._enqueue(
            "occupancy_samples",
            {
                "id": str(uuid5(NAMESPACE_URL, key)),
                "organization_id": self.org,
                "environment_id": camera["environment_id"],
                "camera_id": camera["id"],
                "bucket_start": iso(bucket["minute"]),
                "state": state,
                "people_count": None if state == "unknown" else bucket["peak"],
                "model_version": MODEL,
            },
        )

    def observe(
        self,
        camera: dict[str, Any],
        count: int | None,
        at: datetime,
        rules: list[dict[str, Any]],
    ) -> None:
        now = timestamp(at)
        if count is not None and (type(count) is not int or not 0 <= count <= 10000):
            raise ValueError("Contagem inválida.")
        if camera.get("organization_id", self.org) != self.org:
            raise ValueError("Câmera de outra organização.")
        item = {
            "id": str(UUID(camera["id"])),
            "environment_id": str(UUID(camera["environment_id"])),
            "version": camera["version"],
        }
        minute = now // 60 * 60
        with self.lock, self.db:
            row = self.db.execute(
                "select payload from active where camera=?", (item["id"],)
            ).fetchone()
            previous = json.loads(row[0]) if row else None
            if previous and now < previous["last"]:
                return  # Do not let reordered captures or clock rollback rewrite observations.
            if previous and minute > previous["minute"] and not previous.get("finished"):
                self._finish(previous)
            if previous and minute == previous["minute"]:
                bucket = previous
                if bucket.get("finished"):
                    return
                bucket["changed"] |= item != bucket["camera"]
                bucket["covered"] &= count is not None and now - bucket["last"] <= self.stale
            else:
                carry = (
                    previous is not None
                    and previous["camera"] == item
                    and previous["last_count"] is not None
                    and 0 <= minute - previous["last"] <= self.stale
                )
                bucket = {
                    "camera": item,
                    "minute": minute,
                    "peak": 0,
                    "covered": count is not None and (now == minute or carry),
                    "changed": False,
                }
            bucket["last"], bucket["last_count"] = now, count
            bucket["peak"] = max(bucket["peak"], count or 0)
            self.db.execute(
                "insert or replace into active values (?,?)", (item["id"], json.dumps(bucket))
            )
            self._alerts(item, count, now, rules)

    def tick(self, now: datetime) -> None:
        current = timestamp(now)
        with self.lock, self.db:
            for camera_id, payload in self.db.execute(
                "select camera,payload from active"
            ).fetchall():
                bucket = json.loads(payload)
                if bucket["minute"] + 60 <= current and not bucket.get("finished"):
                    self._finish(bucket)
                    bucket["finished"] = True
                    self.db.execute(
                        "update active set payload=? where camera=?",
                        (json.dumps(bucket), camera_id),
                    )

    def _alerts(
        self,
        camera: dict[str, Any],
        count: int | None,
        now: float,
        rules: list[dict[str, Any]],
    ) -> None:
        valid = {
            str(rule["id"]): rule
            for rule in rules
            if (
                rule.get("enabled")
                and rule.get("organization_id", self.org) == self.org
                and rule.get("environment_id") == camera["environment_id"]
                and rule.get("kind") in {"camera_offline", "occupied_outside_hours"}
            )
        }
        prefix = camera["id"] + ":"
        for key, payload in self.db.execute("select key,payload from episodes").fetchall():
            if key.startswith(prefix) and json.loads(payload)["rule_id"] not in valid:
                self.db.execute("delete from episodes where key=?", (key,))
        for rule_id, rule in valid.items():
            key = prefix + rule_id
            offline = rule["kind"] == "camera_offline"
            condition = count is None if offline else count is not None and count > 0
            if not offline:
                local = datetime.fromtimestamp(now, ZoneInfo("America/Sao_Paulo"))
                clock = local.strftime("%H:%M:%S")
                start, end = rule["start_time"], rule["end_time"]
                inside = (start <= clock < end) if start < end else (clock >= start or clock < end)
                condition = condition and not inside
            row = self.db.execute("select payload from episodes where key=?", (key,)).fetchone()
            episode = json.loads(row[0]) if row else None
            fingerprint = f"{camera['environment_id']}:{rule.get('version', 1)}"
            if not condition:
                self.db.execute("delete from episodes where key=?", (key,))
                continue
            if (
                not episode
                or episode["fingerprint"] != fingerprint
                or now - episode["last"] > self.stale
            ):
                episode = {
                    "start": now,
                    "sent": False,
                    "rule_id": rule_id,
                    "fingerprint": fingerprint,
                }
            episode["last"] = now
            if not episode["sent"] and now - episode["start"] >= rule["delay_seconds"]:
                dedup = str(
                    uuid5(NAMESPACE_URL, f"{self.org}:{key}:{fingerprint}:{episode['start']}")
                )
                self._enqueue(
                    "alerts",
                    {
                        "id": dedup,
                        "organization_id": self.org,
                        "environment_id": camera["environment_id"],
                        "camera_id": camera["id"],
                        "rule_id": rule_id,
                        "dedup_key": dedup,
                        "occurred_at": iso(now),
                        "title": "Câmera sem leitura" if offline else "Presença fora do horário",
                        "detail": "Sem leitura válida; confira a câmera e o serviço de análise."
                        if offline
                        else "Presença detectada fora da faixa configurada; requer revisão humana.",
                    },
                )
                episode["sent"] = True
            self.db.execute(
                "insert or replace into episodes values (?,?)", (key, json.dumps(episode))
            )

    def flush(self, send: Callable[[str, dict[str, Any]], None], now: datetime) -> None:
        if not self.delivery_lock.acquire(blocking=False):
            return
        started, current = time.monotonic(), timestamp(now)
        try:
            for _ in range(8):
                if time.monotonic() - started > 8:
                    break
                with self.lock:
                    row = self.db.execute(
                        "select id,target,payload,attempts from outbox "
                        "where dead=0 and next_try<=? order by rowid limit 1",
                        (current,),
                    ).fetchone()
                if row is None:
                    break
                identifier, table, payload, attempts = row
                try:
                    send(table, json.loads(payload))
                except Exception as exc:
                    retry = not isinstance(exc, DeliveryError) or exc.retryable
                    with self.lock, self.db:
                        self.db.execute(
                            "update outbox set attempts=?,next_try=?,dead=? where id=?",
                            (
                                attempts + 1,
                                current + min(300, 2 ** min(attempts + 1, 9)),
                                0 if retry else 1,
                                identifier,
                            ),
                        )
                    if retry:
                        break
                else:
                    with self.lock, self.db:
                        self.db.execute("delete from outbox where id=?", (identifier,))
        finally:
            self.delivery_lock.release()

    def stats(self) -> dict[str, int]:
        with self.lock:
            pending, dead = self.db.execute(
                "select coalesce(sum(dead=0),0),coalesce(sum(dead=1),0) from outbox"
            ).fetchone()
            return {
                "pending": pending,
                "dead_letter": dead,
                "capacity": self.max_pending,
                "full": int(pending + dead >= self.max_pending),
            }

    def close(self) -> None:
        with self.delivery_lock, self.lock:
            self.db.close()
