"""Hermetic settings for offline tests; never reads any private configuration file."""

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]
SECRET_KEY = "offline-test-only-not-a-deployment-key-" * 3
DEBUG = False
PRODUCTION = False
WEB_SECRET_CONFIGURED = True
SUPABASE_URL = "https://example.invalid"
SUPABASE_PUBLISHABLE_KEY = "sb_publishable_test_only"
ORGANIZATION_ID = "11111111-1111-4111-8111-111111111111"
PROCESSING_SERVER_URL = "https://processing.example.invalid"
LOCAL_MONITOR_ENABLED = False
ALLOWED_HOSTS = ["testserver", "localhost", "127.0.0.1"]
INSTALLED_APPS = ["django.contrib.staticfiles", "django.contrib.sessions", "app.web"]
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "app.web.middleware.FoundationHeadersMiddleware",
]
ROOT_URLCONF = "app.web.urls"
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.template.context_processors.csrf",
            ]
        },
    }
]
DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}}
SESSION_ENGINE = "django.contrib.sessions.backends.db"
SESSION_COOKIE_AGE = 28800
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_NAME = "smart_environment_session"
CSRF_COOKIE_HTTPONLY = True
LANGUAGE_CODE = "pt-br"
TIME_ZONE = "America/Sao_Paulo"
USE_TZ = True
STATIC_URL = "/static/"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
SECURE_REFERRER_POLICY = "same-origin"
X_FRAME_OPTIONS = "DENY"
