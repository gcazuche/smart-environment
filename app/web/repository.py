"""Organization-scoped Supabase REST/RPC access using the signed-in user's JWT.

No service-role key, bootstrap, camera connection or schema migration belongs here.
Database RLS and composite foreign keys remain the final authorization boundary.
"""

import re
from collections.abc import Mapping
from datetime import UTC, datetime, time, timedelta
from typing import Any
from urllib.parse import urlencode
from uuid import UUID

from django.core.exceptions import ValidationError

from app.web.backend import Backend, BackendError
from app.web.forms import camera_address, normalized_name

ENVIRONMENT_FIELDS = "id,organization_id,name,version"
CAMERA_FIELDS = "id,organization_id,environment_id,name,source,address,monitor_id,enabled,version"
RULE_FIELDS = (
    "id,organization_id,environment_id,name,kind,enabled,start_time,end_time,delay_seconds,version"
)
SAMPLE_FIELDS = (
    "id,organization_id,environment_id,camera_id,bucket_start,state,people_count,model_version"
)
ALERT_FIELDS = (
    "id,organization_id,environment_id,camera_id,title,detail,status,"
    "occurred_at,reviewed_at,version"
)
CONFLICT = "O registro foi alterado ou não está disponível. Atualize a página e tente novamente."


class RepositoryError(ValueError):
    """A safe, user-facing catalog, validation or concurrency failure."""


def data_error(error: Exception) -> str:
    if isinstance(error, RepositoryError):
        return str(error)
    if isinstance(error, BackendError):
        messages = {
            "23505": "Já existe um registro com esse nome ou identificador.",
            "23503": "O ambiente ou a câmera selecionada não está disponível.",
            "42501": "Sua conta não tem permissão para esta operação.",
            "40001": CONFLICT,
            "PGRST116": CONFLICT,
            "23514": "Confira os campos e a operação selecionada.",
            "22023": "Confira os campos e a operação selecionada.",
        }
        return messages.get(error.code, str(error))
    return "Não foi possível concluir a operação. Confira a conexão e tente novamente."


def _uuid(value: Any) -> str:
    try:
        return str(UUID(str(value)))
    except (ValueError, TypeError, AttributeError) as error:
        raise RepositoryError("Identificador inválido.") from error


def _version(value: Any) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or not 1 <= value <= 2147483647:
        raise RepositoryError("Versão do registro inválida. Atualize a página.")
    return value


def _name(value: Any) -> str:
    name = normalized_name(str(value or ""))
    if not name or len(name) > 80:
        raise RepositoryError("Informe um nome de até 80 caracteres.")
    return name


def _rows(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list) or any(not isinstance(row, dict) for row in value):
        raise RepositoryError("O serviço retornou dados inválidos. Tente novamente.")
    return value


def _instant(value: Any) -> datetime:
    try:
        instant = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        if instant.tzinfo is None or instant.utcoffset() is None:
            raise ValueError("missing timezone")
        return instant.astimezone(UTC)
    except (ValueError, TypeError) as error:
        raise RepositoryError("Período inválido.") from error


def _period(period: Mapping[str, Any]) -> tuple[datetime, datetime, str | None]:
    start, end = _instant(period.get("start")), _instant(period.get("end"))
    if end < start or end - start > timedelta(days=31):
        raise RepositoryError("Selecione um período de até 31 dias.")
    env = _uuid(period["environment_id"]) if period.get("environment_id") else None
    return start, end, env


class Repository:
    def __init__(self, backend: Backend) -> None:
        self.backend = backend
        self.org = _uuid(backend.org)

    def _path(self, table: str, params: Mapping[str, Any]) -> str:
        return f"/rest/v1/{table}?{urlencode(params)}"

    def _scoped_rows(self, value: Any) -> list[dict[str, Any]]:
        rows = _rows(value)
        if any(row.get("organization_id") != self.org for row in rows):
            raise RepositoryError("Os dados retornados não pertencem à organização selecionada.")
        return rows

    def catalog(self, user_id: str) -> dict[str, Any]:
        member = _rows(
            self.backend.api(
                self._path(
                    "organization_members",
                    {
                        "select": "role",
                        "organization_id": f"eq.{self.org}",
                        "user_id": f"eq.{_uuid(user_id)}",
                        "limit": 2,
                    },
                )
            )
        )
        if len(member) != 1 or member[0].get("role") not in {"admin", "viewer"}:
            raise RepositoryError("Sua conta ainda não foi vinculada a esta organização.")
        catalog: dict[str, Any] = {"role": member[0]["role"]}
        for key, table, fields in (
            ("environments", "environments", ENVIRONMENT_FIELDS),
            ("cameras", "cameras", CAMERA_FIELDS),
            ("rules", "alert_rules", RULE_FIELDS),
        ):
            rows = self._scoped_rows(
                self.backend.api(
                    self._path(
                        table,
                        {
                            "select": fields,
                            "organization_id": f"eq.{self.org}",
                            "order": "name.asc,id.asc",
                            "limit": 500,
                        },
                    )
                )
            )
            if len(rows) >= 500:
                raise RepositoryError(
                    "O catálogo atingiu o limite desta versão. Contate o administrador."
                )
            catalog[key] = rows
        return catalog

    def _environment(self, environment_id: Any) -> str:
        identifier = _uuid(environment_id)
        rows = self._scoped_rows(
            self.backend.api(
                self._path(
                    "environments",
                    {
                        "select": "id,organization_id",
                        "organization_id": f"eq.{self.org}",
                        "id": f"eq.{identifier}",
                        "limit": 1,
                    },
                )
            )
        )
        if len(rows) != 1 or rows[0].get("id") != identifier:
            raise RepositoryError("O ambiente selecionado não está disponível nesta organização.")
        return identifier

    def _save(
        self,
        table: str,
        fields: str,
        values: dict[str, Any],
        existing: Mapping[str, Any] | None,
    ) -> dict[str, Any]:
        params = {"select": fields, "organization_id": f"eq.{self.org}"}
        if existing is not None:
            if existing.get("organization_id") != self.org:
                raise RepositoryError("O registro não pertence à organização selecionada.")
            params.update(
                id=f"eq.{_uuid(existing.get('id'))}",
                version=f"eq.{_version(existing.get('version'))}",
            )
            method = "PATCH"
        else:
            values = {**values, "organization_id": self.org}
            method = "POST"
        rows = self._scoped_rows(
            self.backend.api(
                self._path(table, params),
                method=method,
                payload=values,
                headers={"Prefer": "return=representation"},
            )
        )
        if len(rows) != 1:
            raise RepositoryError(CONFLICT)
        return rows[0]

    def save_environment(
        self, name: str, existing: Mapping[str, Any] | None = None
    ) -> dict[str, Any]:
        return self._save("environments", ENVIRONMENT_FIELDS, {"name": _name(name)}, existing)

    def save_camera(
        self, values: Mapping[str, Any], existing: Mapping[str, Any] | None = None
    ) -> dict[str, Any]:
        source = str(values.get("source", ""))
        try:
            address = camera_address(source, str(values.get("address", "")))
        except ValidationError as error:
            raise RepositoryError(error.messages[0]) from error
        monitor = str(values.get("monitor_id") or "").strip()
        if monitor and not re.fullmatch(r"[a-zA-Z0-9_-]{1,64}", monitor):
            raise RepositoryError(
                "O identificador do monitor deve usar letras, números, hífen ou sublinhado."
            )
        if not isinstance(values.get("enabled"), bool):
            raise RepositoryError("Informe se a câmera está habilitada.")
        payload = {
            "name": _name(values.get("name")),
            "source": source,
            "address": address,
            "monitor_id": monitor or None,
            "enabled": values["enabled"],
            "environment_id": self._environment(values.get("environment_id")),
        }
        return self._save("cameras", CAMERA_FIELDS, payload, existing)

    def save_rule(
        self, values: Mapping[str, Any], existing: Mapping[str, Any] | None = None
    ) -> dict[str, Any]:
        kind = values.get("kind")
        if kind not in {"camera_offline", "occupied_outside_hours"}:
            raise RepositoryError("Condição da regra inválida.")
        try:
            start = time.fromisoformat(str(values.get("start_time", "")))
            end = time.fromisoformat(str(values.get("end_time", "")))
        except ValueError as error:
            raise RepositoryError("Informe horários válidos para a regra.") from error
        if start == end or start.tzinfo is not None or end.tzinfo is not None:
            raise RepositoryError("Informe horários locais diferentes para início e fim.")
        delay = values.get("delay_seconds")
        if isinstance(delay, bool) or not isinstance(delay, int) or not 10 <= delay <= 3600:
            raise RepositoryError("A duração mínima deve estar entre 10 e 3600 segundos.")
        if not isinstance(values.get("enabled"), bool):
            raise RepositoryError("Informe se a regra está habilitada.")
        payload = {
            "name": _name(values.get("name")),
            "kind": kind,
            "enabled": values["enabled"],
            "start_time": start.isoformat(),
            "end_time": end.isoformat(),
            "delay_seconds": delay,
            "environment_id": self._environment(values.get("environment_id")),
        }
        return self._save("alert_rules", RULE_FIELDS, payload, existing)

    def _page(
        self, table: str, period: Mapping[str, Any], page: int, *, samples: bool
    ) -> dict[str, Any]:
        if isinstance(page, bool) or not isinstance(page, int) or not 0 <= page <= 10000:
            raise RepositoryError("Página inválida.")
        start, end, environment = _period(period)
        if start == end or (samples and end - start < timedelta(minutes=1)):
            return {"rows": [], "more": False}
        date_field = "bucket_start" if samples else "occurred_at"
        last = end - timedelta(minutes=1) if samples else end
        upper = "lte" if samples else "lt"
        params: dict[str, Any] = {
            "select": SAMPLE_FIELDS if samples else ALERT_FIELDS,
            "organization_id": f"eq.{self.org}",
            "and": (
                f"({date_field}.gte.{start.isoformat()},{date_field}.{upper}.{last.isoformat()})"
            ),
            "order": f"{date_field}.desc,id.asc",
            "offset": page * 50,
            "limit": 51,
        }
        if environment:
            params["environment_id"] = f"eq.{environment}"
        rows = self._scoped_rows(self.backend.api(self._path(table, params)))
        return {"rows": rows[:50], "more": len(rows) > 50}

    def samples(self, period: Mapping[str, Any], page: int = 0) -> dict[str, Any]:
        return self._page("occupancy_samples", period, page, samples=True)

    def alerts(self, period: Mapping[str, Any], page: int = 0) -> dict[str, Any]:
        return self._page("alerts", period, page, samples=False)

    def report(self, period: Mapping[str, Any]) -> list[dict[str, Any]]:
        start, end, environment = _period(period)
        if start == end:
            return []
        rows = _rows(
            self.backend.api(
                "/rest/v1/rpc/occupancy_report?limit=500",
                method="POST",
                payload={
                    "org": self.org,
                    "starts_at": start.isoformat(),
                    "ends_at": end.isoformat(),
                    "env": environment,
                },
            )
        )
        if len(rows) >= 500:
            raise RepositoryError(
                "O relatório atingiu o limite desta versão. Selecione um ambiente."
            )
        return rows

    def review_alert(self, alert_id: str, expected_version: int, status: str) -> dict[str, Any]:
        identifier = _uuid(alert_id)
        version = _version(expected_version)
        if status not in {"reviewed", "resolved"}:
            raise RepositoryError("Estado de revisão inválido.")
        # Existing RPC has no organization argument. Pre-scope it explicitly; the SQL
        # function locks the immutable row and independently verifies admin + version.
        rows = self._scoped_rows(
            self.backend.api(
                self._path(
                    "alerts",
                    {
                        "select": "id,organization_id,status,version",
                        "organization_id": f"eq.{self.org}",
                        "id": f"eq.{identifier}",
                        "limit": 1,
                    },
                )
            )
        )
        if len(rows) != 1 or rows[0].get("id") != identifier or rows[0].get("version") != version:
            raise RepositoryError(CONFLICT)
        if (rows[0].get("status"), status) not in {("open", "reviewed"), ("reviewed", "resolved")}:
            raise RepositoryError("Atualize o alerta antes de alterar seu estado.")
        result = self.backend.api(
            "/rest/v1/rpc/review_alert",
            method="POST",
            payload={"alert_id": identifier, "expected_version": version, "next_status": status},
        )
        returned = self._scoped_rows([result] if isinstance(result, dict) else result)
        if len(returned) != 1 or returned[0].get("id") != identifier:
            raise RepositoryError(CONFLICT)
        return returned[0]
