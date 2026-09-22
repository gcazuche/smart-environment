"""Calendar filters and spreadsheet-safe exports, independent from video inference."""

import csv
import io
import re
from collections.abc import Iterable, Mapping
from datetime import UTC, datetime, time, timedelta
from typing import Any
from uuid import UUID
from zoneinfo import ZoneInfo

DASHBOARD_TIME_ZONE = ZoneInfo("America/Sao_Paulo")


def period_bounds(
    period: str = "today", now: datetime | None = None, environment_id: str | None = None
) -> dict[str, str | None]:
    """Use local calendar midnights and an exclusive, frozen UTC end timestamp."""
    if period not in {"today", "7d", "30d"}:
        raise ValueError("Período inválido. Selecione hoje, 7 dias ou 30 dias.")
    instant = now or datetime.now(UTC)
    if instant.tzinfo is None or instant.utcoffset() is None:
        raise ValueError("O horário de referência precisa conter fuso horário.")
    local_day = instant.astimezone(DASHBOARD_TIME_ZONE).date()
    first_day = local_day - timedelta(days={"today": 0, "7d": 6, "30d": 29}[period])
    start = datetime.combine(first_day, time.min, tzinfo=DASHBOARD_TIME_ZONE)
    if environment_id:
        try:
            environment_id = str(UUID(environment_id))
        except (ValueError, TypeError, AttributeError) as error:
            raise ValueError("Ambiente inválido.") from error
    return {
        "start": start.astimezone(UTC).isoformat().replace("+00:00", "Z"),
        "end": instant.astimezone(UTC).isoformat().replace("+00:00", "Z"),
        "environment_id": environment_id or None,
    }


def csv_text(rows: Iterable[Iterable[object]]) -> str:
    """Quote every cell and neutralize formula prefixes for spreadsheet consumers."""
    buffer = io.StringIO(newline="")
    buffer.write("\ufeff")
    writer = csv.writer(buffer, delimiter=";", quoting=csv.QUOTE_ALL, lineterminator="\r\n")
    for row in rows:
        cells = []
        for value in row:
            text = "" if value is None else str(value)
            if re.match(r"^\s*[=+@-]", text) or (text and ord(text[0]) < 32):
                text = "'" + text
            cells.append(text)
        writer.writerow(cells)
    return buffer.getvalue()


def summary(rows: Iterable[Mapping[str, Any]]) -> dict[str, int | float | None]:
    """Aggregate camera-minutes only: overlapping cameras are never a people total."""
    records = list(rows)
    observed = sum(int(row.get("observed_minutes", 0)) for row in records)
    occupied = sum(int(row.get("occupied_minutes", 0)) for row in records)
    empty = sum(int(row.get("empty_minutes", 0)) for row in records)
    unknown = sum(int(row.get("unknown_minutes", 0)) for row in records)
    known = occupied + empty
    return {
        "camera_count": len({row["camera_id"] for row in records}),
        "observed_minutes": observed,
        "occupied_minutes": occupied,
        "empty_minutes": empty,
        "unknown_minutes": unknown,
        "occupancy_percent": round(100 * occupied / known, 1) if known else None,
    }
