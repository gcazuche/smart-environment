"""Mock-only video bridge contracts; never contact a camera, Supabase or gateway."""

import inspect
import json
import os
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import Mock, patch
from urllib.parse import parse_qs, urlsplit
from uuid import UUID

import django
from django.test import RequestFactory, SimpleTestCase, override_settings

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "app.web.testing")
django.setup()

from app.web import video  # noqa: E402
from app.web.backend import BackendError  # noqa: E402

CAMERA = UUID("11111111-1111-4111-8111-111111111111")
SESSION = UUID("22222222-2222-4222-8222-222222222222")
ORG = "33333333-3333-4333-8333-333333333333"
ORIGIN = "https://processor.example.invalid"


@override_settings(PROCESSING_SERVER_URL=ORIGIN, LOCAL_MONITOR_ENABLED=False)
class VideoBridgeTests(SimpleTestCase):
    def setUp(self) -> None:
        self.factory = RequestFactory()
        self.row = {
            "id": str(CAMERA),
            "organization_id": ORG,
            "enabled": True,
            "monitor_id": "computer",
            "environment_id": str(SESSION),
        }
        self.backend = SimpleNamespace(org=ORG, token="synthetic-test-token", api=Mock())  # noqa: S106
        self.backend.api.return_value = [self.row]

    def request(self, method: str = "get", body: bytes = b"v=0\r\n") -> object:
        request = getattr(self.factory, method)(
            "/api/processing/",
            data=body if method == "post" else {},
            content_type="application/sdp",
            HTTP_AUTHORIZATION="attacker-supplied",
            HTTP_COOKIE="must-not-forward=anything",
            HTTP_HOST="localhost",
        )
        # RequestFactory omits the header for an empty body; this case deliberately
        # models a declared SDP request with no offer, not a missing media type.
        if method == "post":
            request.content_type = "application/sdp"
        request.backend = self.backend
        request.account = {"id": str(SESSION), "role": "viewer"}
        return request

    def call(self, name: str, request: object, *args: object) -> object:
        # Authentication itself is separately covered by auth tests; this test injects
        # the trusted decorator's context to exercise every proxy boundary offline.
        return inspect.unwrap(getattr(video, name))(request, *args)

    def test_sdp_bridge_constructs_target_and_only_forwards_server_token(self) -> None:
        headers = {
            "content-type": "application/sdp",
            "location": f"/v1/cameras/{CAMERA}/whep/{SESSION}",
        }
        with patch.object(video, "request_remote", return_value=(201, headers, b"v=0\r\n")) as send:
            response = self.call("connect", self.request("post"), CAMERA)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response["Location"], f"/api/processing/cameras/{CAMERA}/whep/{SESSION}/")
        self.assertEqual(
            send.call_args.args,
            (
                ORIGIN,
                "POST",
                f"/v1/cameras/{CAMERA}/whep",
                {"Authorization": "Bearer synthetic-test-token", "Content-Type": "application/sdp"},
                b"v=0\r\n",
            ),
        )
        self.assertEqual(send.call_args.kwargs["limit"], video.SDP_LIMIT)
        query = parse_qs(urlsplit(self.backend.api.call_args.args[0]).query)
        self.assertEqual(query["organization_id"], [f"eq.{ORG}"])
        self.assertEqual(query["enabled"], ["eq.true"])

    def test_camera_scope_and_enabled_fail_before_gateway(self) -> None:
        for rows in (
            [],
            [{**self.row, "enabled": False}],
            [{**self.row, "organization_id": "other"}],
            [{**self.row, "id": str(SESSION)}],
        ):
            with self.subTest(rows=rows), patch.object(video, "request_remote") as send:
                self.backend.api.return_value = rows
                response = self.call("connect", self.request("post"), CAMERA)
                self.assertIn(response.status_code, {404, 503})
                send.assert_not_called()

    def test_sdp_input_limits_and_content_type(self) -> None:
        for body, expected in ((b"", 413), (b"x" * (video.SDP_LIMIT + 1), 413), (b"not-sdp", 400)):
            with self.subTest(expected=expected), patch.object(video, "request_remote") as send:
                self.assertEqual(
                    self.call("connect", self.request("post", body), CAMERA).status_code, expected
                )
                send.assert_not_called()
        request = self.factory.post("/", {}, content_type="application/json")
        request.backend = self.backend
        self.assertEqual(self.call("connect", request, CAMERA).status_code, 415)

    def test_location_cannot_escape_configured_origin_or_camera(self) -> None:
        good = f"/v1/cameras/{CAMERA}/whep/{SESSION}"
        for location in (
            "",
            f"https://attacker.invalid{good}",
            f"//attacker.invalid{good}",
            good + "?token=anything",
            good + "#fragment",
            good + "/../x",
            f"/v1/cameras/{SESSION}/whep/{SESSION}",
        ):
            with self.subTest(location=location), self.assertRaises(BackendError):
                video._location(CAMERA, location)
        self.assertEqual(
            video._location(CAMERA, ORIGIN + good),
            f"/api/processing/cameras/{CAMERA}/whep/{SESSION}/",
        )

    def test_malformed_answer_revokes_known_session(self) -> None:
        headers = {"content-type": "text/html", "location": f"/v1/cameras/{CAMERA}/whep/{SESSION}"}
        with patch.object(
            video, "request_remote", side_effect=[(201, headers, b"oops"), (204, {}, b"")]
        ) as send:
            response = self.call("connect", self.request("post"), CAMERA)
        self.assertEqual(response.status_code, 503)
        self.assertEqual(
            send.call_args.args[1:3], ("DELETE", f"/v1/cameras/{CAMERA}/whep/{SESSION}")
        )

    def test_telemetry_filters_outside_org_and_provider_extras(self) -> None:
        content = json.dumps(
            {
                "cameras": [
                    {
                        "camera_id": str(CAMERA),
                        "people_count": None,
                        "source_url": "private",
                        "token": "hidden",
                    },
                    {"camera_id": str(SESSION), "people_count": 55},
                    {"camera_id": ["malformed"]},
                ]
            }
        ).encode()
        with patch.object(
            video,
            "request_remote",
            return_value=(200, {"content-type": "application/json"}, content),
        ):
            response = self.call("cameras", self.request())
        payload = json.loads(response.content)
        self.assertEqual(len(payload["cameras"]), 1)
        self.assertIsNone(payload["cameras"][0]["people_count"])
        self.assertNotIn("private", response.content.decode())
        self.assertNotIn("hidden", response.content.decode())

    def test_access_failures_preserved_and_remote_bodies_not_exposed(self) -> None:
        for status in (401, 403, 404, 429, 302, 500):
            with (
                self.subTest(status=status),
                patch.object(video, "request_remote", return_value=(status, {}, b"secret")),
            ):
                response = self.call("cameras", self.request())
                self.assertEqual(
                    response.status_code, status if status in {401, 403, 404, 429} else 503
                )
                self.assertNotIn(b"secret", response.content)

    def test_keepalive_rechecks_camera_while_delete_still_revokes_disabled(self) -> None:
        self.backend.api.return_value = []
        with patch.object(video, "request_remote", return_value=(204, {}, b"")) as send:
            self.assertEqual(
                self.call("keepalive", self.request("post"), CAMERA, SESSION).status_code, 404
            )
            send.assert_not_called()
            self.assertEqual(
                self.call("disconnect", self.request(), CAMERA, SESSION).status_code, 204
            )
            self.assertEqual(send.call_args.args[1], "DELETE")

    def test_local_monitor_is_opt_in_and_no_requests_when_disabled(self) -> None:
        with patch.object(video, "request_remote") as send:
            self.assertEqual(self.call("local_frame", self.request(), CAMERA).status_code, 404)
            self.assertEqual(self.call("local_cameras", self.request()).status_code, 404)
            send.assert_not_called()

    @override_settings(LOCAL_MONITOR_ENABLED=True)
    def test_local_frame_has_fixed_origin_bound_id_and_no_auth_forwarding(self) -> None:
        status = {
            "cameras": [
                {
                    "camera_id": "computer",
                    "status": "online",
                    "people_count": 0,
                    "last_seen_at": datetime.now(UTC).isoformat(),
                }
            ]
        }
        responses = [
            (200, {"content-type": "application/json"}, json.dumps(status).encode()),
            (200, {"content-type": "image/jpeg"}, b"\xff\xd8jpeg\xff\xd9"),
        ]
        with patch.object(video, "request_remote", side_effect=responses) as send:
            response = self.call("local_frame", self.request(), CAMERA)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            send.call_args.args,
            (
                video.MONITOR_ORIGIN,
                "GET",
                "/api/cameras/computer/frame.jpg",
                {"Origin": "http://127.0.0.1:3000"},
            ),
        )
        self.assertEqual(response["Cache-Control"], "no-store")

    @override_settings(LOCAL_MONITOR_ENABLED=True)
    def test_local_identifier_rejects_url_and_path_input(self) -> None:
        for monitor_id in ("../camera", "https://evil.invalid", "id?x=1", "", None):
            with self.subTest(monitor_id=monitor_id), patch.object(video, "request_remote") as send:
                self.row["monitor_id"] = monitor_id
                self.assertEqual(self.call("local_frame", self.request(), CAMERA).status_code, 404)
                send.assert_not_called()

    def test_local_unknown_and_stale_not_zero(self) -> None:
        now = datetime.now(UTC)
        for item in (
            {},
            {"last_seen_at": now.isoformat(), "status": "offline", "people_count": 0},
            {
                "last_seen_at": (now - timedelta(seconds=10)).isoformat(),
                "status": "online",
                "people_count": 0,
            },
            {"last_seen_at": now.isoformat(), "status": "online", "people_count": True},
        ):
            with self.subTest(item=item):
                self.assertFalse(video._local_fresh(item))
