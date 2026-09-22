import os
from typing import Any

import django
import pytest

from app.web.forms import CameraForm, EnvironmentForm, RuleForm

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "app.web.settings")
django.setup()

ENV_ID = "10000000-0000-0000-0000-000000000001"
ENVIRONMENTS = [{"id": ENV_ID, "name": "Laboratório"}]


def camera(**overrides: Any) -> CameraForm:
    values = {"name": "Câmera", "environment_id": ENV_ID, "source": "webcam", "address": "0"}
    return CameraForm({**values, **overrides}, environments=ENVIRONMENTS)


@pytest.mark.parametrize("address", ["0", "9", "99", "00"])
def test_webcam_indices(address: str) -> None:
    assert camera(address=address).is_valid()


@pytest.mark.parametrize("address", ["-1", "100", "１", "", "0:1"])
def test_invalid_webcam_indices(address: str) -> None:
    assert not camera(address=address).is_valid()


@pytest.mark.parametrize(
    ("source", "address"),
    [
        ("mjpeg", "http://192.168.1.36:8080/video"),
        ("mjpeg", "https://camera.local/video"),
        ("rtsp", "rtsp://192.168.1.40:554/live"),
        ("rtsp", "rtsp://[fd00::1]:554/live"),
    ],
)
def test_network_camera_configuration_without_connecting(source: str, address: str) -> None:
    assert camera(source=source, address=address).is_valid()


@pytest.mark.parametrize(
    "address",
    [
        "http://user:password@camera.local/video",
        "http://camera.local/video?token=secret",
        "http://camera.local/video#fragment",
        "http://camera.local/video?",
        "http://camera.local/video#",
        "rtsp://camera.local/video",
        "http:///video",
        "http://camera.local:99999/video",
        "http://camera.local:0/video",
        "http://camera.local/a b",
        "http://camera.local/\nvideo",
        "http://camera.local/\x7fvideo",
        "http://camera.local\\@elsewhere/video",
    ],
)
def test_bad_network_addresses_rejected(address: str) -> None:
    assert not camera(source="mjpeg", address=address).is_valid()


def test_camera_requires_authorized_environment_and_monitor_format() -> None:
    assert not camera(environment_id="20000000-0000-0000-0000-000000000001").is_valid()
    assert not camera(monitor_id="phone/user").is_valid()
    assert camera(monitor_id="pc_1-test").is_valid()


def test_environment_normalizes_duplicate_names_and_allows_own_name() -> None:
    assert not EnvironmentForm({"name": "  LABORATÓRIO  "}, environments=ENVIRONMENTS).is_valid()
    form = EnvironmentForm(
        {"name": " Laboratório ", "version": "2"},
        environments=ENVIRONMENTS,
        existing=ENVIRONMENTS[0],
    )
    assert form.is_valid()
    assert form.cleaned_data["name"] == "Laboratório"
    assert form.cleaned_data["version"] == 2
    assert not EnvironmentForm({"name": "Nome"}, existing=ENVIRONMENTS[0]).is_valid()


def test_missing_enabled_means_unchecked_not_default_true() -> None:
    form = camera()
    assert form.is_valid()
    assert form.cleaned_data["enabled"] is False


def test_rules_validate_time_duration_and_environment() -> None:
    values = {
        "name": "Alerta",
        "kind": "occupied_outside_hours",
        "environment_id": ENV_ID,
        "start_time": "22:00",
        "end_time": "06:00",
        "delay_seconds": "60",
    }
    assert RuleForm(values, environments=ENVIRONMENTS).is_valid()
    for patch in (
        {"end_time": "22:00"},
        {"delay_seconds": "9"},
        {"delay_seconds": "3601"},
        {"start_time": "25:00"},
        {"environment_id": "unknown"},
        {"kind": "productivity"},
    ):
        assert not RuleForm({**values, **patch}, environments=ENVIRONMENTS).is_valid()
