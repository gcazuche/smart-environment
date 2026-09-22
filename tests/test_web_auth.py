"""Auth and session security with synthetic provider responses; never calls Supabase."""

import time
from unittest.mock import patch

from django.conf import settings
from django.contrib.sessions.models import Session
from django.test import Client, TestCase, override_settings

from app.web.auth import identity, throttle, tokens
from app.web.backend import Backend, BackendError

USER = "22222222-2222-4222-8222-222222222222"
ACCESS = "synthetic-access-token-with-no-real-authority"
REFRESH = "synthetic-refresh-token-only"


def provider(path, **kwargs):
    if "grant_type=" in path:
        return {"access_token": ACCESS, "refresh_token": REFRESH, "expires_in": 3600}
    if path == "/auth/v1/user":
        return {"id": USER, "email": "test@example.invalid"}
    if path.startswith("/rest/v1/organization_members"):
        return [{"role": "admin"}]
    if "logout" in path:
        return None
    if any(f"/rest/v1/{name}?" in path for name in ("environments", "cameras", "alert_rules")):
        return []
    raise AssertionError(f"Unexpected fixture route: {path}")


class AuthenticationTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.api = patch("app.web.backend.Backend.api", side_effect=provider).start()
        self.addCleanup(patch.stopall)

    def login(self):
        return self.client.post(
            "/login/", {"email": "test@example.invalid", "password": "test-pass"}
        )

    def test_login_and_dashboard_never_disclose_tokens_or_password(self):
        response = self.login()
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/dashboard/")
        for page in (response, self.client.get("/dashboard/"), self.client.get("/profile/")):
            text = page.content.decode() + str(page.cookies)
            for secret in (ACCESS, REFRESH, "test-pass", settings.SUPABASE_PUBLISHABLE_KEY):
                self.assertNotIn(secret, text)
        session = self.client.session
        self.assertEqual(session["supabase"]["access_token"], ACCESS)
        self.assertTrue(self.client.cookies[settings.SESSION_COOKIE_NAME]["httponly"])

    def test_session_key_rotates_on_login(self):
        session = self.client.session
        session["before"] = True
        session.save()
        old = session.session_key
        self.login()
        self.assertNotEqual(self.client.session.session_key, old)
        self.assertFalse(Session.objects.filter(session_key=old).exists())

    def test_denied_member_does_not_create_session(self):
        def denied(path, **kwargs):
            return [] if "organization_members" in path else provider(path, **kwargs)

        self.api.side_effect = denied
        self.assertEqual(self.login().status_code, 400)
        self.assertNotIn("supabase", self.client.session)

    def test_revocation_blocks_dashboard_and_flushes_local_session(self):
        self.login()
        self.api.side_effect = BackendError(403)
        self.assertEqual(self.client.get("/dashboard/").status_code, 403)
        self.assertNotIn("supabase", self.client.session)

    def test_expired_access_refreshes_without_extending_absolute_session(self):
        self.login()
        store = self.client.session
        data = store["supabase"]
        initial_login = data["login_at"]
        store["supabase"] = {**data, "expires_at": time.time() - 1}
        store.save()
        self.api.reset_mock()
        self.assertEqual(self.client.get("/dashboard/").status_code, 200)
        calls = [call.args[0] for call in self.api.call_args_list]
        self.assertIn("/auth/v1/token?grant_type=refresh_token", calls)
        self.assertEqual(self.client.session["supabase"]["login_at"], initial_login)

    def test_absolute_expiry_fails_without_refresh(self):
        self.login()
        store = self.client.session
        store["supabase"] = {**store["supabase"], "login_at": time.time() - 29000}
        store.save()
        self.api.reset_mock()
        response = self.client.get("/dashboard/")
        self.assertEqual(response.url, "/login/")
        self.api.assert_not_called()

    def test_failed_refresh_clears_session_not_silent_demo(self):
        self.login()
        store = self.client.session
        store["supabase"] = {**store["supabase"], "expires_at": 0}
        store.save()
        self.api.side_effect = BackendError(401)
        response = self.client.get("/dashboard/")
        self.assertEqual(response.url, "/login/")
        self.assertNotIn("supabase", self.client.session)

    def test_logout_requires_post_and_clears_even_if_remote_unreachable(self):
        self.login()
        self.assertEqual(self.client.get("/logout/").status_code, 405)
        self.api.side_effect = BackendError(503)
        response = self.client.post("/logout/")
        self.assertEqual(response.url, "/login/?signed_out=local")
        self.assertNotIn("supabase", self.client.session)

    def test_csrf_enforced_for_login_logout_and_video(self):
        client = Client(enforce_csrf_checks=True)
        for path in ("/login/", "/logout/", f"/api/processing/cameras/{USER}/whep/"):
            self.assertEqual(client.post(path, {}).status_code, 403)

    def test_rate_limit_persists_after_eight_account_attempts(self):
        for _ in range(8):
            throttle("test@example.invalid", "127.0.0.1")
        with self.assertRaises(BackendError) as caught:
            throttle("test@example.invalid", "192.0.2.1")
        self.assertEqual(caught.exception.status, 429)

    @override_settings(WEB_SECRET_CONFIGURED=False)
    def test_missing_secret_disables_login_without_remote(self):
        response = self.login()
        self.assertEqual(response.status_code, 503)
        self.api.assert_not_called()

    def test_provider_errors_and_password_are_not_reflected(self):
        self.api.side_effect = BackendError(503, "sensitive-provider-info")
        response = self.login()
        self.assertNotIn(b"sensitive-provider-info", response.content)
        self.assertNotIn(b"test-pass", response.content)

    def test_identity_only_allows_known_roles(self):
        self.api.side_effect = [{"id": USER}, [{"role": "owner"}]]
        with self.assertRaises(BackendError):
            identity(Backend(ACCESS))

    def test_token_shape_is_bounded(self):
        for data in (None, {}, {"access_token": "a", "refresh_token": "b", "expires_in": 3600}):
            with self.assertRaises(BackendError):
                tokens(data)
