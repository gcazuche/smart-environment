"""Server-rendered dashboard: authenticated, scoped and never backed by demo data."""

from datetime import datetime
from typing import Any
from urllib.parse import urlencode

from django.conf import settings
from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_http_methods, require_POST, require_safe

from app.web.auth import require_account
from app.web.backend import BackendError
from app.web.forms import CameraForm, EnvironmentForm, RuleForm
from app.web.reports import csv_text, period_bounds
from app.web.repository import Repository, RepositoryError, data_error

TITLES = {
    "overview": "Visão geral",
    "cameras": "Câmeras",
    "environments": "Ambientes",
    "indicators": "Indicadores",
    "alerts": "Alertas",
    "history": "Histórico",
    "rules": "Regras de alertas",
    "profile": "Minha conta",
}
STATE_LABELS = {
    "occupied": "Ocupado",
    "empty": "Vazio",
    "unknown": "Sem leitura válida",
    "open": "Aberto",
    "reviewed": "Revisado",
    "resolved": "Resolvido",
}
SAFE_ERRORS = (BackendError, RepositoryError)


def _context(request: HttpRequest, section: str, catalog: dict[str, Any]) -> dict[str, Any]:
    return {
        "account": request.account,
        "section": section,
        "title": TITLES[section],
        "can_edit": catalog.get("role") == "admin",
        "catalog": catalog,
        "clock_now": timezone.now(),
        "video_mode": (
            "local"
            if getattr(settings, "LOCAL_MONITOR_ENABLED", False)
            and not getattr(settings, "PROCESSING_SERVER_URL", "")
            else "server"
        ),
    }


def _load(request: HttpRequest) -> tuple[Repository, dict[str, Any]]:
    repository = Repository(request.backend)
    return repository, repository.catalog(request.account["id"])


def _failure(request: HttpRequest, section: str, error: Exception) -> HttpResponse:
    context = _context(request, section, {})
    context["error"] = data_error(error)
    context["retry_url"] = (
        request.path if request.method in {"GET", "HEAD"} else reverse(f"web:{section}")
    )
    return render(request, "web/dashboard_error.html", context, status=503)


def _item(catalog: dict[str, Any], group: str, item_id: Any) -> dict[str, Any]:
    for item in catalog[group]:
        if item["id"] == str(item_id):
            return item
    raise Http404("Registro não encontrado nesta organização.")


def _camera_rows(catalog: dict[str, Any]) -> list[dict[str, Any]]:
    environments = {item["id"]: item["name"] for item in catalog["environments"]}
    return [
        dict(camera, environment_name=environments.get(camera["environment_id"], "—"))
        for camera in catalog["cameras"]
    ]


@require_safe
@require_account
def overview(request: HttpRequest) -> HttpResponse:
    try:
        _, catalog = _load(request)
    except SAFE_ERRORS as error:
        return _failure(request, "overview", error)
    context = _context(request, "overview", catalog)
    context["enabled_count"] = sum(bool(camera["enabled"]) for camera in catalog["cameras"])
    return render(request, "web/overview.html", context)


@require_safe
@require_account
def cameras(request: HttpRequest) -> HttpResponse:
    try:
        _, catalog = _load(request)
    except SAFE_ERRORS as error:
        return _failure(request, "cameras", error)
    search = request.GET.get("q", "").strip()[:120]
    state = request.GET.get("state", "all")
    environment_id = request.GET.get("environment", "")
    if environment_id:
        _item(catalog, "environments", environment_id)
    rows = [
        camera
        for camera in _camera_rows(catalog)
        if search.casefold() in f"{camera['name']} {camera['environment_name']}".casefold()
        and (not environment_id or camera["environment_id"] == environment_id)
        and (state not in {"enabled", "disabled"} or camera["enabled"] == (state == "enabled"))
    ]
    context = _context(request, "cameras", catalog)
    context.update(cameras=rows, search=search, state=state, environment_id=environment_id)
    return render(request, "web/cameras.html", context)


@require_safe
@require_account
def camera_detail(request: HttpRequest, camera_id: Any) -> HttpResponse:
    try:
        _, catalog = _load(request)
    except SAFE_ERRORS as error:
        return _failure(request, "cameras", error)
    camera = _item({"cameras": _camera_rows(catalog)}, "cameras", camera_id)
    context = _context(request, "cameras", catalog)
    context.update(camera=camera, title=camera["name"])
    return render(request, "web/camera_detail.html", context)


@require_safe
@require_account
def environments(request: HttpRequest) -> HttpResponse:
    try:
        _, catalog = _load(request)
    except SAFE_ERRORS as error:
        return _failure(request, "environments", error)
    search = request.GET.get("q", "").strip()[:120]
    rows = [
        dict(
            item,
            camera_count=sum(
                camera["environment_id"] == item["id"] for camera in catalog["cameras"]
            ),
        )
        for item in catalog["environments"]
        if search.casefold() in item["name"].casefold()
    ]
    context = _context(request, "environments", catalog)
    context.update(environments=rows, search=search)
    return render(request, "web/environments.html", context)


@require_safe
@require_account
def environment_detail(request: HttpRequest, environment_id: Any) -> HttpResponse:
    try:
        _, catalog = _load(request)
    except SAFE_ERRORS as error:
        return _failure(request, "environments", error)
    environment = _item(catalog, "environments", environment_id)
    context = _context(request, "environments", catalog)
    context.update(
        environment=environment,
        title=environment["name"],
        cameras=[
            camera
            for camera in _camera_rows(catalog)
            if camera["environment_id"] == environment["id"]
        ],
    )
    return render(request, "web/environment_detail.html", context)


def _period(request: HttpRequest, catalog: dict[str, Any]) -> dict[str, Any]:
    period = request.GET.get("period", "today")
    if period not in {"today", "7d", "30d"}:
        raise RepositoryError("Selecione um período válido.")
    environment_id = request.GET.get("environment", "")
    if environment_id:
        _item(catalog, "environments", environment_id)
    try:
        page = int(request.GET.get("page", "1"))
        if not 1 <= page <= 10000:
            raise ValueError
        now = timezone.now()
        if request.GET.get("as_of"):
            now = datetime.fromisoformat(request.GET["as_of"])
            if timezone.is_naive(now) or now > timezone.now():
                raise ValueError
    except (ValueError, OverflowError) as error:
        raise RepositoryError("Período ou página inválidos. Atualize os filtros.") from error
    try:
        bounds = period_bounds(period, now=now, environment_id=environment_id or None)
    except (ValueError, OverflowError) as error:
        raise RepositoryError("Período inválido. Atualize os filtros.") from error
    return {
        "period": period,
        "environment_id": environment_id,
        "page": page,
        "as_of": now.isoformat(),
        "bounds": bounds,
    }


def _query(filters: dict[str, Any], **extra: Any) -> str:
    return urlencode(
        {
            "period": filters["period"],
            "environment": filters["environment_id"],
            "as_of": filters["as_of"],
            "page": filters["page"],
            **extra,
        }
    )


def _records(request: HttpRequest, section: str) -> HttpResponse:
    try:
        repository, catalog = _load(request)
        filters = _period(request, catalog)
        if section == "indicators":
            rows, more = repository.report(filters["bounds"]), False
        else:
            result = getattr(repository, "samples" if section == "history" else "alerts")(
                filters["bounds"], filters["page"] - 1
            )
            rows, more = result["rows"], result["more"]
    except SAFE_ERRORS as error:
        return _failure(request, section, error)
    camera_names = {item["id"]: item["name"] for item in catalog["cameras"]}
    environment_names = {item["id"]: item["name"] for item in catalog["environments"]}
    display_rows = [
        dict(
            row,
            camera_name=camera_names.get(row.get("camera_id"), "Câmera não disponível"),
            environment_name=environment_names.get(row["environment_id"], "—"),
            state_label=STATE_LABELS.get(row.get("state", row.get("status", "")), "—"),
            recorded_at=_timestamp(row.get("bucket_start", row.get("occurred_at"))),
        )
        for row in rows
    ]
    if request.GET.get("export") == "csv":
        return _csv(section, display_rows, filters, environment_names)
    context = _context(request, section, catalog)
    context.update(
        filters,
        rows=display_rows,
        more=more,
        next_query=_query(filters, page=filters["page"] + 1),
        previous_query=_query(filters, page=max(1, filters["page"] - 1)),
        export_query=_query(filters, export="csv"),
        return_query=_query(filters),
    )
    return render(request, "web/records.html", context)


def _timestamp(value: Any) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        result = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return result if timezone.is_aware(result) else None
    except ValueError:
        return None


def _csv(
    section: str,
    rows: list[dict[str, Any]],
    filters: dict[str, Any],
    environment_names: dict[str, str],
) -> HttpResponse:
    output = [
        ["Início (UTC)", "Fim exclusivo (UTC)", "Ambiente", "Página"],
        [
            filters["bounds"]["start"],
            filters["bounds"]["end"],
            environment_names.get(filters["environment_id"], "Todos"),
            filters["page"],
        ],
    ]
    if section == "history":
        output.append(["Minuto (UTC)", "Câmera", "Ambiente", "Estado", "Pessoas", "Modelo"])
        fields = (
            "bucket_start",
            "camera_name",
            "environment_name",
            "state_label",
            "people_count",
            "model_version",
        )
    elif section == "alerts":
        output.append(["Ocorrência (UTC)", "Ambiente", "Alerta", "Detalhes", "Estado"])
        fields = ("occurred_at", "environment_name", "title", "detail", "state_label")
    else:
        output.append(
            [
                "Câmera",
                "Ambiente",
                "Minutos observados",
                "Ocupados",
                "Vazios",
                "Desconhecidos",
                "Pico de pessoas",
            ]
        )
        fields = (
            "camera_name",
            "environment_name",
            "observed_minutes",
            "occupied_minutes",
            "empty_minutes",
            "unknown_minutes",
            "peak_people",
        )
    output.extend([[row.get(field) for field in fields] for row in rows])
    response = HttpResponse(csv_text(output), content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = (
        f'attachment; filename="{section}-pagina-{filters["page"]}.csv"'
    )
    return response


@require_safe
@require_account
def history(request: HttpRequest) -> HttpResponse:
    return _records(request, "history")


@require_safe
@require_account
def indicators(request: HttpRequest) -> HttpResponse:
    return _records(request, "indicators")


@require_safe
@require_account
def alerts(request: HttpRequest) -> HttpResponse:
    return _records(request, "alerts")


@require_POST
@require_account
def review_alert(request: HttpRequest, alert_id: Any) -> HttpResponse:
    try:
        repository, catalog = _load(request)
        if catalog["role"] != "admin":
            return render(
                request,
                "web/dashboard_error.html",
                {
                    **_context(request, "alerts", catalog),
                    "error": "Seu perfil permite consulta. A revisão exige um administrador.",
                },
                status=403,
            )
        try:
            version = int(request.POST.get("version", ""))
            if version < 1:
                raise ValueError
        except ValueError as error:
            raise RepositoryError(
                "Versão inválida. Recarregue os alertas antes de revisar."
            ) from error
        status = request.POST.get("status", "")
        if status not in {"reviewed", "resolved"}:
            raise RepositoryError("Selecione uma revisão válida.")
        repository.review_alert(str(alert_id), version, status)
    except SAFE_ERRORS as error:
        return _failure(request, "alerts", error)
    return redirect("web:alerts")


@require_safe
@require_account
def rules(request: HttpRequest) -> HttpResponse:
    try:
        _, catalog = _load(request)
    except SAFE_ERRORS as error:
        return _failure(request, "rules", error)
    context = _context(request, "rules", catalog)
    environment_names = {item["id"]: item["name"] for item in catalog["environments"]}
    context["rules"] = [
        dict(item, environment_name=environment_names.get(item["environment_id"], "—"))
        for item in catalog["rules"]
    ]
    return render(request, "web/rules.html", context)


def _edit(request: HttpRequest, group: str, item_id: Any = None) -> HttpResponse:
    try:
        repository, catalog = _load(request)
    except SAFE_ERRORS as error:
        return _failure(request, group, error)
    context = _context(request, group, catalog)
    if not context["can_edit"]:
        context["error"] = "Seu perfil permite consulta. Alterações exigem um administrador."
        return render(request, "web/dashboard_error.html", context, status=403)
    existing = _item(catalog, group, item_id) if item_id else None
    form_class = {"environments": EnvironmentForm, "cameras": CameraForm, "rules": RuleForm}[group]
    form = form_class(
        request.POST if request.method == "POST" else None,
        environments=catalog["environments"],
        existing=existing,
        initial=existing or {"enabled": True, "source": "webcam", "address": "0"},
    )
    response_status = 200
    if request.method == "POST" and form.is_valid():
        try:
            expected = None
            if existing:
                if form.cleaned_data["version"] != existing["version"]:
                    raise RepositoryError("O registro foi alterado. Recarregue antes de salvar.")
                expected = {**existing, "version": form.cleaned_data["version"]}
            if group == "environments":
                saved = repository.save_environment(form.cleaned_data["name"], existing=expected)
                return redirect("web:environment_detail", environment_id=saved["id"])
            if group == "cameras":
                saved = repository.save_camera(form.cleaned_data, existing=expected)
                return redirect("web:camera_detail", camera_id=saved["id"])
            repository.save_rule(form.cleaned_data, existing=expected)
            return redirect("web:rules")
        except SAFE_ERRORS as error:
            form.add_error(None, data_error(error))
            response_status = 409 if existing else 400
    elif request.method == "POST":
        response_status = 400
    noun = {"environments": "ambiente", "cameras": "câmera", "rules": "regra"}[group]
    context.update(
        form=form,
        title=f"{'Editar' if existing else 'Adicionar'} {noun}",
        cancel_url=reverse(f"web:{group}"),
        existing=existing,
        group=group,
    )
    return render(request, "web/edit.html", context, status=response_status)


@require_http_methods(["GET", "HEAD", "POST"])
@require_account
def edit_camera(request: HttpRequest, camera_id: Any = None) -> HttpResponse:
    return _edit(request, "cameras", camera_id)


@require_http_methods(["GET", "HEAD", "POST"])
@require_account
def edit_environment(request: HttpRequest, environment_id: Any = None) -> HttpResponse:
    return _edit(request, "environments", environment_id)


@require_http_methods(["GET", "HEAD", "POST"])
@require_account
def edit_rule(request: HttpRequest, rule_id: Any = None) -> HttpResponse:
    return _edit(request, "rules", rule_id)


@require_safe
@require_account
def profile(request: HttpRequest) -> HttpResponse:
    try:
        _, catalog = _load(request)
    except SAFE_ERRORS as error:
        return _failure(request, "profile", error)
    return render(request, "web/profile.html", _context(request, "profile", catalog))
