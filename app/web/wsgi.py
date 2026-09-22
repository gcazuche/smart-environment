"""WSGI entry point for the VM web service, separate from the inference service."""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "app.web.settings")
application = get_wsgi_application()
