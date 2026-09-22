"""Server-side validation for the existing Supabase catalog contracts."""

import re
from collections.abc import Mapping, Sequence
from typing import Any
from urllib.parse import urlsplit

from django import forms


def normalized_name(value: str) -> str:
    """Keep display names readable and consistent with the database unique index."""
    return " ".join(value.split())


def camera_address(source: str, address: str) -> str:
    """Validate configuration only; this function never connects to a camera."""
    address = address.strip()
    if not address or len(address) > 500:
        raise forms.ValidationError("Informe um endereço de até 500 caracteres.")
    if source == "webcam":
        if not re.fullmatch(r"[0-9]{1,2}", address):
            raise forms.ValidationError("Informe o índice da webcam, entre 0 e 99.")
        return address
    if source not in {"mjpeg", "rtsp"}:
        raise forms.ValidationError("Tipo de câmera inválido.")
    if any(char.isspace() or ord(char) < 32 or ord(char) == 127 for char in address):
        raise forms.ValidationError("O endereço não pode conter espaços ou caracteres de controle.")
    if any(char in address for char in "@?#\\"):
        raise forms.ValidationError(
            "Não inclua credenciais, parâmetros ou fragmentos no endereço. "
            "As credenciais são configuradas somente no servidor."
        )
    try:
        parsed = urlsplit(address)
        expected = {"rtsp"} if source == "rtsp" else {"http", "https"}
        valid = (
            parsed.scheme in expected
            and address.startswith(f"{parsed.scheme}://")
            and bool(parsed.hostname)
            and not parsed.username
            and not parsed.password
            and not parsed.query
            and not parsed.fragment
        )
        # Accessing port detects malformed/out-of-range ports, without making network requests.
        if parsed.port is not None and parsed.port == 0:
            valid = False
    except ValueError:
        valid = False
    if not valid:
        raise forms.ValidationError(
            "Informe o endereço completo com o protocolo correto da câmera."
        )
    return address


class CatalogForm(forms.Form):
    """Edits must carry the version originally displayed to the user."""

    name = forms.CharField(label="Nome", max_length=80)
    version = forms.IntegerField(
        required=False, min_value=1, max_value=2147483647, widget=forms.HiddenInput
    )

    def __init__(
        self,
        *args: Any,
        environments: Sequence[Mapping[str, Any]] = (),
        existing: Mapping[str, Any] | None = None,
        **kwargs: Any,
    ) -> None:
        self.environments = environments
        self.existing = existing
        super().__init__(*args, **kwargs)
        self.fields["version"].required = existing is not None

    def clean_name(self) -> str:
        name = normalized_name(self.cleaned_data["name"])
        if not name:
            raise forms.ValidationError("Informe um nome.")
        return name


class EnvironmentForm(CatalogForm):
    def clean_name(self) -> str:
        name = super().clean_name()
        current_id = self.existing.get("id") if self.existing else None
        if any(
            item.get("id") != current_id
            and normalized_name(str(item.get("name", ""))).casefold() == name.casefold()
            for item in self.environments
        ):
            raise forms.ValidationError("Já existe um ambiente com esse nome.")
        return name


class EnvironmentBoundForm(CatalogForm):
    environment_id = forms.ChoiceField(label="Ambiente", choices=())

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.fields["environment_id"].choices = [  # type: ignore[attr-defined]
            ("", "Selecione um ambiente"),
            *((str(item["id"]), str(item["name"])) for item in self.environments),
        ]


class CameraForm(EnvironmentBoundForm):
    source = forms.ChoiceField(
        label="Tipo de câmera",
        choices=(("webcam", "Webcam"), ("mjpeg", "Celular / MJPEG"), ("rtsp", "IP / RTSP")),
        initial="webcam",
    )
    address = forms.CharField(
        label="Endereço ou índice da webcam",
        max_length=500,
        initial="0",
        help_text="Sem senhas ou tokens. Salvar o cadastro não abre a câmera.",
        widget=forms.TextInput(attrs={"autocomplete": "off", "spellcheck": "false"}),
    )
    monitor_id = forms.RegexField(
        label="Identificador no monitor",
        regex=r"\A[a-zA-Z0-9_-]{1,64}\Z",
        max_length=64,
        required=False,
        help_text="Opcional. Deve corresponder ao identificador configurado no servidor.",
        error_messages={"invalid": "Use somente letras, números, hífen ou sublinhado."},
    )
    enabled = forms.BooleanField(label="Câmera habilitada", required=False, initial=True)

    def clean(self) -> dict[str, Any]:
        cleaned = super().clean() or {}
        if "source" in cleaned and "address" in cleaned:
            try:
                cleaned["address"] = camera_address(cleaned["source"], cleaned["address"])
            except forms.ValidationError as error:
                self.add_error("address", error)
        return cleaned


class RuleForm(EnvironmentBoundForm):
    kind = forms.ChoiceField(
        label="Condição",
        choices=(
            ("camera_offline", "Câmera indisponível"),
            ("occupied_outside_hours", "Ocupação fora do horário"),
        ),
    )
    start_time = forms.TimeField(
        label="Início do expediente (Brasília)",
        initial="08:00",
        input_formats=["%H:%M", "%H:%M:%S"],
        widget=forms.TimeInput(format="%H:%M", attrs={"type": "time"}),
    )
    end_time = forms.TimeField(
        label="Fim do expediente (Brasília)",
        initial="18:00",
        input_formats=["%H:%M", "%H:%M:%S"],
        widget=forms.TimeInput(format="%H:%M", attrs={"type": "time"}),
    )
    delay_seconds = forms.IntegerField(
        label="Duração mínima (segundos)", min_value=10, max_value=3600, initial=60
    )
    enabled = forms.BooleanField(label="Regra habilitada", required=False, initial=True)

    def clean(self) -> dict[str, Any]:
        cleaned = super().clean() or {}
        if (
            "start_time" in cleaned
            and "end_time" in cleaned
            and cleaned["start_time"] == cleaned["end_time"]
        ):
            self.add_error("end_time", "Os horários de início e fim precisam ser diferentes.")
        return cleaned
