"""Authentication entry points and public process liveness; no vision imports."""

from django import forms
from django.db import OperationalError, ProgrammingError
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.utils import timezone
from django.views.decorators.cache import never_cache
from django.views.decorators.debug import sensitive_post_parameters
from django.views.decorators.http import require_http_methods, require_POST, require_safe

from app.web.auth import sign_in, sign_out
from app.web.backend import BackendError, configured


class LoginForm(forms.Form):
    email = forms.EmailField(
        label="E-mail",
        max_length=254,
        widget=forms.EmailInput(
            attrs={"autocomplete": "username", "placeholder": "voce@empresa.com"}
        ),
    )
    password = forms.CharField(
        label="Senha",
        max_length=1024,
        strip=False,
        widget=forms.PasswordInput(attrs={"autocomplete": "current-password"}),
    )


@never_cache
@require_safe
def index(request: HttpRequest) -> HttpResponse:
    return redirect("web:overview" if request.session.get("supabase") else "web:login")


@never_cache
@sensitive_post_parameters("password")
@require_http_methods(["GET", "HEAD", "POST"])
def login(request: HttpRequest) -> HttpResponse:
    available = configured()
    form = LoginForm(request.POST if request.method == "POST" else None)
    error, status = "", 200
    if request.method == "POST":
        if not available:
            error, status = "Configure o acesso no servidor antes de entrar.", 503
        elif form.is_valid():
            try:
                sign_in(request, form.cleaned_data["email"], form.cleaned_data["password"])
                return redirect("web:overview")
            except BackendError as exc:
                error = (
                    "Muitas tentativas. Aguarde cinco minutos."
                    if exc.status == 429
                    else "Não foi possível entrar. Confira suas credenciais, acesso e conexão."
                )
                status = 429 if exc.status == 429 else 400
            except (OperationalError, ProgrammingError):
                error, status = (
                    "Prepare o banco local de sessões conforme o guia de instalação.",
                    503,
                )
    return render(
        request,
        "web/login.html",
        {
            "current_year": timezone.localdate().year,
            "form": form,
            "configured": available,
            "error": error,
            "local_logout": request.GET.get("signed_out") == "local",
        },
        status=status,
    )


@never_cache
@require_POST
def logout(request: HttpRequest) -> HttpResponse:
    done = sign_out(request)
    return redirect("/login/" if done else "/login/?signed_out=local")


@never_cache
@require_safe
def health(request: HttpRequest) -> JsonResponse:
    """Liveness only: not proof of database, video or authentication readiness."""
    return JsonResponse(
        {
            "status": "ok",
            "component": "smart-environment-web",
            "phase": "django",
            "configured": configured(),
            "remote_checked": False,
        }
    )
