"""SSR parity with mocked repositories: no remote writes, cameras or live authentication."""

import copy
import inspect
import os
from html.parser import HTMLParser
from unittest.mock import Mock, patch
from uuid import UUID

import django
from django.http import Http404
from django.test import RequestFactory, SimpleTestCase, override_settings
from django.urls import resolve, reverse

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "app.web.settings")
django.setup()

from app.web.repository import RepositoryError  # noqa: E402

USER = "11111111-1111-4111-8111-111111111111"
ENV = "22222222-2222-4222-8222-222222222222"
OTHER_ENV = "33333333-3333-4333-8333-333333333333"
CAM = "44444444-4444-4444-8444-444444444444"
OTHER_CAM = "55555555-5555-4555-8555-555555555555"
RULE = "66666666-6666-4666-8666-666666666666"
ALERT = "77777777-7777-4777-8777-777777777777"


class Tags(HTMLParser):
    def __init__(self, html: str) -> None:
        super().__init__()
        self.tags: list[tuple[str, dict[str, str | None]]] = []
        self.feed(html)

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.tags.append((tag, dict(attrs)))


class DashboardTests(SimpleTestCase):
    def setUp(self) -> None:
        self.factory = RequestFactory()
        self.catalog = {
            "role": "admin",
            "environments": [
                {"id": ENV, "name": "Laboratório", "version": 2},
                {"id": OTHER_ENV, "name": "Escritório", "version": 1},
            ],
            "cameras": [
                {
                    "id": CAM,
                    "name": "Câmera principal",
                    "environment_id": ENV,
                    "source": "webcam",
                    "address": "0",
                    "monitor_id": "pc",
                    "enabled": True,
                    "version": 3,
                },
                {
                    "id": OTHER_CAM,
                    "name": "Câmera externa",
                    "environment_id": OTHER_ENV,
                    "source": "rtsp",
                    "address": "rtsp://192.168.1.2/live",
                    "monitor_id": "ip",
                    "enabled": False,
                    "version": 1,
                },
            ],
            "rules": [
                {
                    "id": RULE,
                    "name": "Fora do horário",
                    "environment_id": ENV,
                    "kind": "occupied_outside_hours",
                    "enabled": True,
                    "start_time": "08:00",
                    "end_time": "18:00",
                    "delay_seconds": 60,
                    "version": 2,
                },
            ],
        }
        self.repository = Mock()
        self.repository.catalog.side_effect = lambda _: copy.deepcopy(self.catalog)
        self.repository.samples.return_value = {"rows": [], "more": False}
        self.repository.alerts.return_value = {"rows": [], "more": False}
        self.repository.report.return_value = []
        self.repository.save_environment.return_value = self.catalog["environments"][0]
        self.repository.save_camera.return_value = self.catalog["cameras"][0]
        self.repo_patch = patch("app.web.dashboard_views.Repository", return_value=self.repository)
        self.repo_patch.start()
        self.addCleanup(self.repo_patch.stop)

    def call(self, name: str, method: str = "get", data=None, **kwargs):
        path = reverse(f"web:{name}", kwargs=kwargs or None)
        request = getattr(self.factory, method)(path, data or {}, HTTP_HOST="localhost")
        request.account = {"id": USER, "email": "tester@example.invalid", "role": "admin"}
        request.backend = Mock()
        view = resolve(path).func
        return inspect.unwrap(view)(request, **kwargs)

    def test_all_read_pages_render_real_navigation(self) -> None:
        for name in (
            "overview",
            "cameras",
            "environments",
            "indicators",
            "history",
            "alerts",
            "rules",
            "profile",
        ):
            with self.subTest(name=name):
                response = self.call(name)
                self.assertEqual(response.status_code, 200)
                self.assertContains(response, 'href="/cameras/"')
                self.assertContains(response, 'href="/environments/"')
                self.assertContains(response, 'action="/logout/"')
                self.assertContains(response, 'name="csrfmiddlewaretoken"')
                self.assertNotContains(response, "protótipo acadêmico")

    def test_environment_contains_all_and_only_its_cameras(self) -> None:
        extra = dict(self.catalog["cameras"][0], id=ALERT, name="Segunda câmera")
        self.catalog["cameras"].append(extra)
        response = self.call("environment_detail", environment_id=UUID(ENV))
        self.assertContains(response, "Câmera principal")
        self.assertContains(response, "Segunda câmera")
        self.assertNotContains(response, "Câmera externa")
        self.assertContains(response, f'data-camera-id="{CAM}"')
        self.assertContains(response, f'data-camera-id="{ALERT}"')

    def test_camera_search_and_enabled_filters(self) -> None:
        response = self.call("cameras", data={"q": "escritório", "state": "disabled"})
        self.assertContains(response, "Câmera externa")
        self.assertNotContains(response, "Câmera principal")
        response = self.call("cameras", data={"environment": ENV, "state": "enabled"})
        self.assertContains(response, "Câmera principal")
        self.assertNotContains(response, "Câmera externa")

    def test_viewer_never_autoconnects_or_shows_fake_zero(self) -> None:
        response = self.call("camera_detail", camera_id=UUID(CAM))
        self.assertContains(response, "Desconectado. Inicie para visualizar.")
        self.assertContains(response, "data-people-count>—")
        self.assertContains(response, 'data-video-mode="server"')
        self.assertNotContains(response, "rtsp://")
        tags = Tags(response.content.decode()).tags
        video = next(attrs for tag, attrs in tags if tag == "video")
        self.assertNotIn("src", video)

    @override_settings(LOCAL_MONITOR_ENABLED=True, PROCESSING_SERVER_URL="")
    def test_local_viewer_only_with_explicit_configuration(self) -> None:
        response = self.call("camera_detail", camera_id=UUID(CAM))
        self.assertContains(response, 'data-video-mode="local"')

    def test_unknown_ids_are_not_visible(self) -> None:
        with self.assertRaises(Http404):
            self.call("camera_detail", camera_id=UUID(USER))
        with self.assertRaises(Http404):
            self.call("environment_detail", environment_id=UUID(USER))
        with self.assertRaises(Http404):
            self.call("history", data={"environment": USER})

    def test_catalog_failure_is_not_empty_success(self) -> None:
        self.repository.catalog.side_effect = RepositoryError("Consulta indisponível")
        response = self.call("overview")
        self.assertEqual(response.status_code, 503)
        self.assertContains(response, "Consulta indisponível", status_code=503)
        self.assertNotContains(response, "Câmeras cadastradas", status_code=503)

    def test_telemetry_failure_is_not_empty_history(self) -> None:
        self.repository.samples.side_effect = RepositoryError("Histórico indisponível")
        response = self.call("history")
        self.assertEqual(response.status_code, 503)
        self.assertNotContains(response, "Nenhum registro neste período", status_code=503)

    def test_empty_history_explicitly_is_not_proof_of_absence(self) -> None:
        response = self.call("history")
        self.assertContains(response, "Isso não confirma ausência de pessoas")

    def test_data_is_autoescaped(self) -> None:
        self.catalog["cameras"][0]["name"] = "<script>alert('test')</script>"
        response = self.call("cameras")
        self.assertContains(response, "&lt;script&gt;")
        self.assertNotContains(response, "<script>alert(")

    def test_history_filter_pagination_and_csv_are_same_scope(self) -> None:
        self.repository.samples.return_value = {
            "rows": [
                {
                    "camera_id": CAM,
                    "environment_id": ENV,
                    "bucket_start": "2026-09-18T12:00:00Z",
                    "state": "unknown",
                    "people_count": None,
                    "model_version": "model-test",
                }
            ],
            "more": True,
        }
        query = {
            "period": "7d",
            "page": "2",
            "environment": ENV,
            "as_of": "2026-09-19T14:00:00+00:00",
        }
        response = self.call("history", data=query)
        self.assertContains(response, "Página 2")
        self.assertContains(response, "Próxima")
        self.assertContains(response, "18/09/2026 09:00")
        self.assertContains(response, "Sem leitura válida")
        args = self.repository.samples.call_args.args
        self.assertEqual(args[1], 1)
        self.assertEqual(args[0]["environment_id"], ENV)
        response = self.call("history", data={**query, "export": "csv"})
        self.assertEqual(self.repository.samples.call_args.args, args)
        self.assertEqual(response["Content-Type"], "text/csv; charset=utf-8")
        self.assertIn("pagina-2", response["Content-Disposition"])
        self.assertContains(response, "2026-09-19T14:00:00Z")
        self.assertContains(response, "Sem leitura válida")

    def test_invalid_filter_values_fail_safely(self) -> None:
        for query in (
            {"page": "0"},
            {"page": "x"},
            {"period": "year"},
            {"as_of": "2026-09-01T00:00:00"},
            {"period": "30d", "as_of": "0001-01-02T00:00:00+00:00"},
        ):
            with self.subTest(query=query):
                response = self.call("history", data=query)
                self.assertEqual(response.status_code, 503)
        self.repository.samples.assert_not_called()

    def test_indicators_show_accessible_real_camera_minutes(self) -> None:
        self.repository.report.return_value = [
            {
                "camera_id": CAM,
                "environment_id": ENV,
                "observed_minutes": 12,
                "occupied_minutes": 5,
                "empty_minutes": 3,
                "unknown_minutes": 4,
                "peak_people": 2,
            }
        ]
        response = self.call("indicators")
        meters = [attrs for tag, attrs in Tags(response.content.decode()).tags if tag == "meter"]
        self.assertEqual([item["value"] for item in meters], ["5", "3", "4"])
        self.assertTrue(all(item["max"] == "12" for item in meters))
        self.assertTrue(all(item.get("aria-labelledby") for item in meters))
        self.assertContains(response, "Desconhecidos")
        self.repository.report.return_value[0].update(
            observed_minutes=0,
            occupied_minutes=0,
            empty_minutes=0,
            unknown_minutes=0,
        )
        response = self.call("indicators")
        self.assertNotContains(response, "<meter ")
        self.assertContains(response, "Sem minutos observados")

    def test_camera_and_rule_save_use_validated_fields(self) -> None:
        response = self.call(
            "camera_new",
            "post",
            {
                "name": "Nova câmera",
                "environment_id": ENV,
                "source": "webcam",
                "address": "0",
                "monitor_id": "pc-new",
                "enabled": "on",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.repository.save_camera.call_args.args[0]["environment_id"], ENV)
        self.assertTrue(self.repository.save_camera.call_args.args[0]["enabled"])
        response = self.call(
            "rule_new",
            "post",
            {
                "name": "Nova regra",
                "environment_id": ENV,
                "kind": "camera_offline",
                "start_time": "08:00",
                "end_time": "18:00",
                "delay_seconds": "60",
                "enabled": "on",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.repository.save_rule.call_args.args[0]["delay_seconds"], 60)

    def test_all_create_and_edit_forms_render(self) -> None:
        for name, kwargs in (
            ("camera_new", {}),
            ("environment_new", {}),
            ("rule_new", {}),
            ("camera_edit", {"camera_id": UUID(CAM)}),
            ("environment_edit", {"environment_id": UUID(ENV)}),
            ("rule_edit", {"rule_id": UUID(RULE)}),
        ):
            with self.subTest(name=name):
                response = self.call(name, **kwargs)
                self.assertEqual(response.status_code, 200)
                self.assertContains(response, 'method="post"')
                self.assertContains(response, 'name="csrfmiddlewaretoken"')
                if kwargs:
                    self.assertContains(response, 'name="version"')

    def test_viewer_has_no_write_actions_and_cannot_post(self) -> None:
        self.catalog["role"] = "viewer"
        response = self.call("cameras")
        self.assertNotContains(response, 'href="/cameras/new/"')
        for name, kwargs in (
            ("camera_new", {}),
            ("environment_new", {}),
            ("rule_new", {}),
            ("alert_review", {"alert_id": UUID(ALERT)}),
        ):
            with self.subTest(name=name):
                self.assertEqual(
                    self.call(name, "post", {"name": "Blocked"}, **kwargs).status_code, 403
                )
        self.repository.save_camera.assert_not_called()
        self.repository.save_environment.assert_not_called()
        self.repository.save_rule.assert_not_called()
        self.repository.review_alert.assert_not_called()

    def test_successful_environment_save_redirects_after_backend_ack(self) -> None:
        response = self.call("environment_new", "post", {"name": "Sala nova"})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], reverse("web:environment_detail", args=[ENV]))
        self.repository.save_environment.assert_called_once_with("Sala nova", existing=None)

    def test_conflicting_version_is_not_silently_replaced(self) -> None:
        response = self.call(
            "environment_edit",
            "post",
            {"name": "Renomeado", "version": 1},
            environment_id=UUID(ENV),
        )
        self.assertEqual(response.status_code, 409)
        self.repository.save_environment.assert_not_called()

    def test_edit_preserves_posted_version(self) -> None:
        response = self.call(
            "environment_edit",
            "post",
            {"name": "Renomeado", "version": 2},
            environment_id=UUID(ENV),
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            self.repository.save_environment.call_args.kwargs["existing"]["version"], 2
        )

    def test_invalid_form_never_calls_repository_write(self) -> None:
        response = self.call(
            "camera_new",
            "post",
            {"name": "Invalid", "source": "rtsp", "address": "rtsp://user:pass@localhost/x"},
        )
        self.assertEqual(response.status_code, 400)
        self.repository.save_camera.assert_not_called()

    def test_backend_save_failure_does_not_redirect_as_success(self) -> None:
        self.repository.save_environment.side_effect = RepositoryError("Não foi possível salvar")
        response = self.call("environment_new", "post", {"name": "Sala nova"})
        self.assertEqual(response.status_code, 400)
        self.assertContains(response, "Não foi possível salvar", status_code=400)

    def test_alert_review_uses_expected_version_and_allowed_status(self) -> None:
        response = self.call(
            "alert_review", "post", {"version": "3", "status": "reviewed"}, alert_id=UUID(ALERT)
        )
        self.assertEqual(response.status_code, 302)
        self.repository.review_alert.assert_called_once_with(ALERT, 3, "reviewed")
        self.repository.review_alert.reset_mock()
        for data in ({"version": "3", "status": "open"}, {"status": "resolved"}):
            with self.subTest(data=data):
                response = self.call("alert_review", "post", data, alert_id=UUID(ALERT))
                self.assertEqual(response.status_code, 503)
        self.repository.review_alert.assert_not_called()

    def test_no_inline_script_handlers_or_styles(self) -> None:
        response = self.call("cameras")
        for tag, attrs in Tags(response.content.decode()).tags:
            with self.subTest(tag=tag):
                self.assertNotIn("style", attrs)
                self.assertFalse(any(name.startswith("on") for name in attrs))
                if tag == "script":
                    self.assertTrue((attrs.get("src") or "").startswith("/static/"))
