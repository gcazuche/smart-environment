"""Prepare only an in-memory Django test DB; existing vision tests stay offline."""

import os

import django
import pytest
from django.test.utils import setup_databases, teardown_databases

os.environ["DJANGO_SETTINGS_MODULE"] = "app.web.testing"
django.setup()


@pytest.fixture(scope="session", autouse=True)
def django_test_database():
    configuration = setup_databases(verbosity=0, interactive=False)
    yield
    teardown_databases(configuration, verbosity=0)
