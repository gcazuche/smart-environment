"""Offline regressions for debug gating, provider shape and trusted-proxy limits."""

import re
from unittest.mock import patch

from django.test import Client, RequestFactory, SimpleTestCase, TestCase, override_settings

from app.web.auth import authenticate, client_address, identity
from app.web.backend import Backend, BackendError, configured

USER = "22222222-2222-4222-8222-222222222222"
ACCESS = "synthetic-access-token-with-no-real-authority"


@override_settings(
    DEBUG=False,
    WEB_SECRET_CONFIGURED=True,
    SUPABASE_URL="https://example.invalid",
    SUPABASE_PUBLISHABLE_KEY="sb_publishable_test_only",
    ORGANIZATION_ID="11111111-1111-4111-8111-111111111111",
)
class DebugAuthenticationSecurityTests(SimpleTestCase):
    def test_valid_configuration_is_available_only_outside_debug(self):
        self.assertTrue(configured())
        with override_settings(DEBUG=True):
            self.assertFalse(configured())
        self.assertTrue(configured())

    @override_settings(DEBUG=True)
    def test_debug_authenticate_denies_before_session_or_remote_access(self):
        with (
            patch("app.web.auth.SessionStore") as store,
            patch("app.web.backend.Backend.api") as api,
            patch("app.web.backend.request_remote") as remote,
        ):
            # No session property: the debug gate must execute before touching it.
            with self.assertRaises(BackendError) as caught:
                authenticate(object())
        self.assertEqual(caught.exception.status, 503)
        store.assert_not_called()
        api.assert_not_called()
        remote.assert_not_called()

    @override_settings(DEBUG=True)
    def test_backend_itself_cannot_send_credentials_while_debugging(self):
        with patch("app.web.backend.request_remote") as remote:
            with self.assertRaises(BackendError) as caught:
                Backend().api(
                    "/auth/v1/token?grant_type=password",
                    method="POST",
                    payload={"email": "test@example.invalid", "password": "fixture-only"},
                )
        self.assertEqual(caught.exception.status, 503)
        remote.assert_not_called()


class ProviderShapeSecurityTests(SimpleTestCase):
    def test_non_mapping_membership_rows_fail_with_safe_backend_error(self):
        for rows in ([None], ["private-upstream-marker"], [42], [[]]):
            with self.subTest(rows=rows):
                with patch(
                    "app.web.backend.Backend.api",
                    side_effect=[{"id": USER, "email": "test@example.invalid"}, rows],
                ) as api:
                    with self.assertRaises(BackendError) as caught:
                        identity(Backend(ACCESS))
                self.assertEqual(caught.exception.status, 403)
                self.assertEqual(api.call_count, 2)
                self.assertNotIn("private-upstream-marker", str(caught.exception))
                self.assertNotIn(ACCESS, str(caught.exception))


class LoginOriginSecurityTests(TestCase):
    """Browser forms retain their own origin without relaxing Django CSRF checks."""

    def login_page(self):
        client = Client(enforce_csrf_checks=True)
        response = client.get("/login/")
        self.assertEqual(response.status_code, 200)
        match = re.search(r'name="csrfmiddlewaretoken" value="([^"]+)"', response.content.decode())
        self.assertIsNotNone(match)
        return client, response, match.group(1)

    def test_login_header_and_meta_use_same_origin_referrer_policy(self):
        _, response, _ = self.login_page()
        self.assertEqual(response.headers["Referrer-Policy"], "same-origin")
        self.assertContains(response, '<meta name="referrer" content="same-origin">')
        self.assertNotContains(response, '<meta name="referrer" content="no-referrer">')

    def test_same_origin_post_with_csrf_token_authenticates_normally(self):
        client, _, csrf = self.login_page()
        previous_cookie = client.cookies["csrftoken"].value
        with patch(
            "app.web.backend.Backend.api",
            side_effect=[
                {
                    "access_token": ACCESS,
                    "refresh_token": "synthetic-refresh-token-only",
                    "expires_in": 3600,
                },
                {"id": USER, "email": "test@example.invalid"},
                [{"role": "admin"}],
            ],
        ) as api:
            response = client.post(
                "/login/",
                {
                    "email": "test@example.invalid",
                    "password": "fixture-only",
                    "csrfmiddlewaretoken": csrf,
                },
                HTTP_ORIGIN="http://testserver",
            )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/dashboard/")
        self.assertEqual(api.call_count, 3)
        self.assertEqual(api.call_args_list[0].args[0], "/auth/v1/token?grant_type=password")
        self.assertEqual(client.session["supabase"]["user_id"], USER)
        self.assertNotEqual(client.cookies["csrftoken"].value, previous_cookie)

    def test_null_and_foreign_origins_are_rejected_before_provider_even_with_valid_csrf(self):
        for origin in ("null", "https://evil.example.invalid"):
            with self.subTest(origin=origin):
                client, _, csrf = self.login_page()
                with patch("app.web.backend.Backend.api") as api:
                    response = client.post(
                        "/login/",
                        {
                            "email": "test@example.invalid",
                            "password": "fixture-only",
                            "csrfmiddlewaretoken": csrf,
                        },
                        HTTP_ORIGIN=origin,
                    )
                self.assertEqual(response.status_code, 403)
                api.assert_not_called()
                self.assertNotIn("supabase", client.session)


class TrustedProxySecurityTests(SimpleTestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def request(self, peer, smart="", forwarded="198.51.100.200"):
        return self.factory.get(
            "/login/",
            REMOTE_ADDR=peer,
            HTTP_X_SMART_CLIENT_IP=smart,
            HTTP_X_FORWARDED_FOR=forwarded,
        )

    @override_settings(PRODUCTION=True)
    def test_production_loopback_proxy_accepts_only_dedicated_valid_ip(self):
        for peer in ("127.0.0.1", "::1"):
            for forwarded, expected in (
                ("192.0.2.40", "192.0.2.40"),
                ("2001:0db8:0000:0000::0040", "2001:db8::40"),
            ):
                with self.subTest(peer=peer, forwarded=forwarded):
                    self.assertEqual(client_address(self.request(peer, forwarded)), expected)

    @override_settings(PRODUCTION=False)
    def test_development_never_trusts_client_supplied_dedicated_header(self):
        for peer in ("127.0.0.1", "::1", "192.0.2.10"):
            with self.subTest(peer=peer):
                self.assertEqual(client_address(self.request(peer, "203.0.113.40")), peer)

    @override_settings(PRODUCTION=True)
    def test_non_loopback_peer_cannot_override_address_even_in_production(self):
        for peer in ("192.0.2.10", "2001:db8::10", "127.0.0.2"):
            with self.subTest(peer=peer):
                self.assertEqual(client_address(self.request(peer, "203.0.113.40")), peer)

    @override_settings(PRODUCTION=True)
    def test_x_forwarded_for_is_ignored_when_dedicated_header_is_absent(self):
        for peer in ("127.0.0.1", "::1", "192.0.2.10"):
            with self.subTest(peer=peer):
                self.assertEqual(client_address(self.request(peer)), peer)

    @override_settings(PRODUCTION=True)
    def test_invalid_dedicated_proxy_addresses_fail_closed(self):
        for value in (
            "example.invalid",
            "192.0.2.40, 192.0.2.41",
            "192.0.2.40:443",
            " 192.0.2.40",
            "192.0.2.40 ",
            "[2001:db8::40]",
            "private-invalid-marker",
        ):
            with self.subTest(value=value):
                with self.assertRaises(BackendError) as caught:
                    client_address(self.request("127.0.0.1", value))
                self.assertEqual(caught.exception.status, 400)
                self.assertNotIn(value, str(caught.exception))

    @override_settings(PRODUCTION=False)
    def test_untrusted_invalid_headers_are_ignored_not_parsed(self):
        self.assertEqual(client_address(self.request("127.0.0.1", "not-an-ip")), "127.0.0.1")
