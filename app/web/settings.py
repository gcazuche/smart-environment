"""Django settings. Credentials/configuration remain exclusively on the server."""

import secrets

from django.core.exceptions import ImproperlyConfigured

from app.web.configuration import ROOT, load

CONFIG = load()
BASE_DIR = ROOT
PRODUCTION = CONFIG.get("DJANGO_PRODUCTION", "false").lower() == "true"
DEBUG = CONFIG.get("DJANGO_DEBUG", "false").lower() == "true"
WEB_SECRET_CONFIGURED = len(CONFIG.get("DJANGO_SECRET_KEY", "")) >= 50
SECRET_KEY = CONFIG.get("DJANGO_SECRET_KEY") or secrets.token_urlsafe(64)
ALLOWED_HOSTS = [
    s.strip()
    for s in CONFIG.get("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1,[::1]").split(",")
    if s.strip()
]
CSRF_TRUSTED_ORIGINS = [
    s.strip() for s in CONFIG.get("DJANGO_CSRF_TRUSTED_ORIGINS", "").split(",") if s.strip()
]
if PRODUCTION and (not WEB_SECRET_CONFIGURED or DEBUG or not ALLOWED_HOSTS or "*" in ALLOWED_HOSTS):
    raise ImproperlyConfigured(
        "Produção exige segredo persistente, hosts explícitos e DEBUG=false."
    )
SUPABASE_URL = CONFIG.get("SUPABASE_URL", "")
SUPABASE_PUBLISHABLE_KEY = CONFIG.get("SUPABASE_PUBLISHABLE_KEY", "")
ORGANIZATION_ID = CONFIG.get("ORGANIZATION_ID", "")
PROCESSING_SERVER_URL = CONFIG.get("PROCESSING_SERVER_URL", "")
LOCAL_MONITOR_ENABLED = CONFIG.get("LOCAL_MONITOR_ENABLED", "false").lower() == "true"

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
WSGI_APPLICATION = "app.web.wsgi.application"
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
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": CONFIG.get("DJANGO_DATABASE_PATH", str(ROOT / "data/web.sqlite3")),
        "OPTIONS": {"timeout": 20},
    }
}
SESSION_ENGINE = "django.contrib.sessions.backends.db"
SESSION_COOKIE_NAME = "smart_environment_session"
SESSION_COOKIE_AGE = 8 * 60 * 60
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
SESSION_COOKIE_SECURE = PRODUCTION
SESSION_SAVE_EVERY_REQUEST = False
SECURE_SSL_REDIRECT = PRODUCTION
SECURE_HSTS_SECONDS = 31536000 if PRODUCTION else 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = False
SECURE_HSTS_PRELOAD = False
# Proxy must be loopback-only and overwrite this header; never append untrusted input.
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https") if PRODUCTION else None
DATA_UPLOAD_MAX_MEMORY_SIZE = 150000
DATA_UPLOAD_MAX_NUMBER_FIELDS = 40

LANGUAGE_CODE = "pt-br"
TIME_ZONE = "America/Sao_Paulo"
USE_I18N = True
USE_TZ = True
STATIC_URL = "/static/"
STATIC_ROOT = CONFIG.get("DJANGO_STATIC_ROOT", ROOT / "data/static")
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

SECURE_CONTENT_TYPE_NOSNIFF = True
# Preserve same-origin form Origin/Referer for CSRF; send no referrer to other sites.
SECURE_REFERRER_POLICY = "same-origin"
X_FRAME_OPTIONS = "DENY"
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SECURE = PRODUCTION
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"null": {"class": "logging.NullHandler"}},
    "loggers": {"django.request": {"handlers": ["null"], "propagate": False}},
}
