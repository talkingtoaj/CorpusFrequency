"""Sign-in is Google-only, and any Google account is allowed."""

import pytest
from django.conf import settings
from django.urls import reverse

pytestmark = pytest.mark.django_db


def test_sign_in_page_offers_google(client):
    response = client.get(reverse("account_login"))
    assert response.status_code == 200
    assert b"Sign in with Google" in response.content


def test_sign_in_page_has_no_password_field(client):
    """Nothing to store, verify or reset - that is the point of SSO here."""
    response = client.get(reverse("account_login"))
    assert b'type="password"' not in response.content


def test_password_signup_is_disabled(client):
    """SOCIALACCOUNT_ONLY: there is no local registration route."""
    assert settings.SOCIALACCOUNT_ONLY is True
    response = client.get("/accounts/signup/")
    assert response.status_code in (404, 302, 410)


def test_any_google_account_is_accepted(settings):
    """No allowlist and no domain restriction: auto-signup on first arrival."""
    assert settings.SOCIALACCOUNT_AUTO_SIGNUP is True
    assert settings.ACCOUNT_EMAIL_VERIFICATION == "none"


def test_google_credentials_come_from_the_environment(settings):
    app = settings.SOCIALACCOUNT_PROVIDERS["google"]["APP"]
    assert set(app) == {"client_id", "secret", "key"}


def test_model_backend_is_kept_for_admin_access(settings):
    """A createsuperuser account must still reach /admin/ if OAuth breaks."""
    assert "django.contrib.auth.backends.ModelBackend" in settings.AUTHENTICATION_BACKENDS


def test_admin_login_form_still_exists(client):
    response = client.get("/admin/login/", follow=True)
    assert b'name="password"' in response.content


def test_protected_pages_redirect_to_the_google_sign_in(client):
    response = client.get(reverse("corpus-list"))
    assert response.status_code == 302
    assert reverse("account_login") in response.url


def test_a_signed_in_user_reaches_their_corpora(client, user):
    client.force_login(user)
    assert client.get(reverse("corpus-list")).status_code == 200
