"""Public web contracts after DJ-02..06; business pages are authenticated."""

import hashlib
import os
from html.parser import HTMLParser
from pathlib import Path

import django
from django.conf import settings
from django.contrib.staticfiles import finders
from django.test import Client, SimpleTestCase
from django.urls import reverse
from django.utils import timezone

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "app.web.settings")
django.setup()

ROOT = Path(__file__).resolve().parents[1]


class PageTags(HTMLParser):
    def __init__(self, html: str) -> None:
        super().__init__()
        self.tags: list[tuple[str, dict[str, str | None]]] = []
        self.feed(html)

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.tags.append((tag, dict(attrs)))


class WebFoundationTests(SimpleTestCase):
    def setUp(self) -> None:
        self.client = Client(HTTP_HOST="localhost")

    def test_root_redirects_to_login_ignoring_external_next(self) -> None:
        response = self.client.get("/?next=https://example.invalid/")
        self.assertRedirects(response, reverse("web:login"))

    def test_login_uses_existing_account_and_current_year(self) -> None:
        response = self.client.get(reverse("web:login"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Use a conta vinculada à sua organização")
        self.assertContains(response, str(timezone.localdate().year))
        self.assertNotIn("sessionid", response.cookies)

    def test_post_form_has_csrf_without_inline_handlers(self) -> None:
        tags = PageTags(self.client.get("/login/").content.decode()).tags
        self.assertIn("form", [tag for tag, _ in tags])
        inputs = [attrs for tag, attrs in tags if tag == "input"]
        self.assertEqual(len(inputs), 3)
        self.assertIn("csrfmiddlewaretoken", [attrs.get("name") for attrs in inputs])
        password = next(attrs for attrs in inputs if attrs.get("name") == "password")
        self.assertNotIn("value", password)
        for _, attrs in tags:
            self.assertFalse(any(key.startswith("on") for key in attrs))
            self.assertNotIn("style", attrs)
        submit = [attrs for tag, attrs in tags if attrs.get("class") == "auth-submit"]
        self.assertEqual(len(submit), 1)
        self.assertEqual(submit[0]["type"], "submit")

    def test_safe_methods_only_and_no_credentials_reflected(self) -> None:
        for path in ("/", "/health/"):
            with self.subTest(path=path):
                response = self.client.post(path, {"password": "dummy-not-a-real-secret"})
                self.assertEqual(response.status_code, 405)
                self.assertNotIn(b"dummy-not-a-real-secret", response.content)
                self.assertEqual(self.client.head(path).status_code, 302 if path == "/" else 200)

    def test_csrf_enforced_even_without_a_form(self) -> None:
        client = Client(enforce_csrf_checks=True, HTTP_HOST="localhost")
        self.assertEqual(client.post("/login/", {}).status_code, 403)

    def test_health_is_liveness_not_operational_readiness(self) -> None:
        response = self.client.get("/health/")
        self.assertEqual(
            response.json(),
            {
                "status": "ok",
                "component": "smart-environment-web",
                "phase": "django",
                "configured": True,
                "remote_checked": False,
            },
        )

    def test_no_dashboard_admin_or_registration_routes(self) -> None:
        for path in ("/admin/", "/signup/"):
            with self.subTest(path=path):
                self.assertEqual(self.client.get(path).status_code, 404)
        for path in ("/dashboard/", "/cameras/", "/environments/", "/history/"):
            self.assertRedirects(self.client.get(path), reverse("web:login"))

    def test_no_duplicate_user_database_and_opaque_session_backend(self) -> None:
        self.assertNotIn("django.contrib.auth", settings.INSTALLED_APPS)
        self.assertIn("django.contrib.sessions", settings.INSTALLED_APPS)
        self.assertEqual(settings.SESSION_ENGINE, "django.contrib.sessions.backends.db")

    def test_hosts_are_restricted_to_loopback(self) -> None:
        for host in ("example.invalid", "192.0.2.10"):
            with self.subTest(host=host):
                self.assertEqual(self.client.get("/login/", HTTP_HOST=host).status_code, 400)

    def test_security_headers_disable_embeds_network_and_forms(self) -> None:
        response = self.client.get("/login/")
        self.assertEqual(response.headers["X-Frame-Options"], "DENY")
        self.assertEqual(response.headers["X-Content-Type-Options"], "nosniff")
        self.assertEqual(response.headers["Referrer-Policy"], "same-origin")
        self.assertIn("no-store", response.headers["Cache-Control"])
        csp = response.headers["Content-Security-Policy"]
        for directive in ("form-action 'self'", "connect-src 'self'", "default-src 'none'"):
            self.assertIn(directive, csp)
        self.assertNotIn("unsafe-inline", csp)
        self.assertNotIn("unsafe-eval", csp)

    def test_static_assets_resolve_without_dashboard_or_external_cdn(self) -> None:
        tags = PageTags(self.client.get("/login/").content.decode()).tags
        asset_urls = [attrs["src"] for tag, attrs in tags if tag in ("img", "script")]
        asset_urls += [attrs["href"] for tag, attrs in tags if tag == "link"]
        self.assertEqual(len(asset_urls), 5)
        for url in asset_urls:
            assert url is not None
            self.assertTrue(url.startswith("/static/"))
            asset = finders.find(url.removeprefix("/static/"))
            self.assertIsNotNone(asset)
            self.assertTrue(Path(str(asset)).is_relative_to(ROOT / "app" / "web"))

    def test_brand_assets_identical_to_user_supplied_logos(self) -> None:
        for name in ("smart-environment-horizontal.png", "smart-environment-symbol.png"):
            with self.subTest(name=name):
                old = (ROOT / "dashboard" / "public" / "brand" / name).read_bytes()
                new = (ROOT / "app" / "web" / "static" / "brand" / name).read_bytes()
                self.assertEqual(hashlib.sha256(old).digest(), hashlib.sha256(new).digest())

    def test_no_node_build_syntax_in_new_assets(self) -> None:
        script = (ROOT / "app/web/static/web/login.js").read_text(encoding="utf-8")
        css = (ROOT / "app/web/static/web/login.css").read_text(encoding="utf-8")
        self.assertNotIn("tailwindcss", css)
        for forbidden in ("fetch(", "XMLHttpRequest", "localStorage", "sessionStorage"):
            self.assertNotIn(forbidden, script)
        self.assertFalse(list((ROOT / "app/web").rglob("*.ts")))
        self.assertFalse(list((ROOT / "app/web").rglob("*.tsx")))
