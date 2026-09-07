"""Settings and endpoints the Cloud Run deployment depends on."""

import pytest
from django.conf import settings
from django.urls import reverse

pytestmark = pytest.mark.django_db


def test_health_endpoint_needs_no_authentication(client):
    """Cloud Run's probe is unauthenticated; a redirect would fail it."""
    response = client.get(reverse("health"))
    assert response.status_code == 200
    assert response.content == b"ok"


def test_csrf_trusted_origins_never_wildcards():
    """'https://*.run.app' would trust every Cloud Run service on the platform."""
    assert not any("*" in origin for origin in settings.CSRF_TRUSTED_ORIGINS)


def test_cloud_run_detection_covers_jobs_as_well_as_services(monkeypatch):
    """The migration job needs the same Cloud SQL socket rewrite."""
    import importlib

    from config import settings as settings_module

    monkeypatch.delenv("K_SERVICE", raising=False)
    monkeypatch.setenv("CLOUD_RUN_JOB", "corpusfrequency-migrate")
    reloaded = importlib.reload(settings_module)
    assert reloaded.ON_CLOUD_RUN is True

    monkeypatch.delenv("CLOUD_RUN_JOB", raising=False)
    importlib.reload(settings_module)


def test_cloud_sql_socket_replaces_the_tcp_host(monkeypatch):
    """A TCP DATABASE_URL must become a /cloudsql/ socket path in Cloud Run."""
    import importlib

    from config import settings as settings_module

    monkeypatch.setenv("K_SERVICE", "corpusfrequency")
    monkeypatch.setenv("CLOUD_SQL_INSTANCE", "proj:us-central1:lb-db2")
    monkeypatch.setenv("DATABASE_URL", "postgresql://u:p@127.0.0.1:5432/corpus")
    reloaded = importlib.reload(settings_module)

    database = reloaded.DATABASES["default"]
    assert database["HOST"] == "/cloudsql/proj:us-central1:lb-db2"
    assert "PORT" not in database or not database["PORT"]

    for name in ("K_SERVICE", "CLOUD_SQL_INSTANCE", "DATABASE_URL"):
        monkeypatch.delenv(name, raising=False)
    importlib.reload(settings_module)


def test_local_database_url_is_left_alone(monkeypatch):
    import importlib

    from config import settings as settings_module

    monkeypatch.delenv("K_SERVICE", raising=False)
    monkeypatch.delenv("CLOUD_RUN_JOB", raising=False)
    monkeypatch.setenv("DATABASE_URL", "postgresql://u:p@127.0.0.1:5432/corpus")
    reloaded = importlib.reload(settings_module)
    assert reloaded.DATABASES["default"]["HOST"] == "127.0.0.1"

    monkeypatch.delenv("DATABASE_URL", raising=False)
    importlib.reload(settings_module)


def test_health_is_exempt_from_the_ssl_redirect(monkeypatch):
    """Probes arrive without X-Forwarded-Proto; a 301 reads as a failure."""
    import importlib
    import re

    from config import settings as settings_module

    monkeypatch.setenv("DJANGO_DEBUG", "0")
    monkeypatch.setenv("DJANGO_SECRET_KEY", "test-only")
    reloaded = importlib.reload(settings_module)

    assert reloaded.SECURE_SSL_REDIRECT is True
    assert any(re.compile(p).search("health") for p in reloaded.SECURE_REDIRECT_EXEMPT)

    monkeypatch.delenv("DJANGO_DEBUG", raising=False)
    monkeypatch.delenv("DJANGO_SECRET_KEY", raising=False)
    importlib.reload(settings_module)
