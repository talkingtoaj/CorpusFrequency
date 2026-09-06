"""Settings for the CorpusFrequency web service.

Everything environment-specific is read from the environment so the same
image can run locally on SQLite and hosted on Postgres.
"""

import os
from pathlib import Path

import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent

# A dev-only fallback: any real deployment must set DJANGO_SECRET_KEY.
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "dev-insecure-key-do-not-deploy")

DEBUG = os.environ.get("DJANGO_DEBUG", "1") == "1"

# Cloud Run sets K_SERVICE for services and CLOUD_RUN_JOB for jobs. Both
# matter: the migration job needs the same Cloud SQL socket rewrite as the
# service, and checking only K_SERVICE would silently skip it there.
ON_CLOUD_RUN = bool(os.environ.get("K_SERVICE") or os.environ.get("CLOUD_RUN_JOB"))

ALLOWED_HOSTS = [
    host.strip()
    for host in os.environ.get("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")
    if host.strip()
]
if ON_CLOUD_RUN:
    # Safe to wildcard: ALLOWED_HOSTS only validates the Host header, and the
    # service URL is not known until after the first deploy.
    ALLOWED_HOSTS += [".run.app", ".a.run.app"]

# Never wildcard this one. CSRF_TRUSTED_ORIGINS governs which origins may make
# authenticated requests, so 'https://*.run.app' would trust every Cloud Run
# service on the platform, including other people's.
CSRF_TRUSTED_ORIGINS = [
    origin.strip()
    for origin in os.environ.get("DJANGO_CSRF_TRUSTED_ORIGINS", "").split(",")
    if origin.strip()
]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sites",
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    "allauth.socialaccount.providers.google",
    "corpus",
]

SITE_ID = 1

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "allauth.account.middleware.AccountMiddleware",
]

AUTHENTICATION_BACKENDS = [
    # Kept so `createsuperuser` accounts can still reach /admin/ if the
    # OAuth configuration ever breaks.
    "django.contrib.auth.backends.ModelBackend",
    "allauth.account.auth_backends.AuthenticationBackend",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        # Project-level templates win over app ones, which is how the
        # allauth sign-in page is overridden - allauth is listed ahead of
        # `corpus` in INSTALLED_APPS, so an app-level override would lose.
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

DATABASES = {
    "default": dj_database_url.config(
        default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}",
        conn_max_age=600,
        conn_health_checks=True,
    )
}

# Cloud Run reaches Cloud SQL over a Unix socket, not TCP, so the same
# DATABASE_URL that works locally fails there with "connection refused".
# Rewriting the host here means one secret serves both environments.
CLOUD_SQL_INSTANCE = os.environ.get("CLOUD_SQL_INSTANCE", "")
if ON_CLOUD_RUN and CLOUD_SQL_INSTANCE:
    database = DATABASES["default"]
    if not str(database.get("HOST", "")).startswith("/cloudsql/"):
        database["HOST"] = f"/cloudsql/{CLOUD_SQL_INSTANCE}"
        database.pop("PORT", None)

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"},
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Django's default configuration routes request errors to mail_admins only,
# so with DEBUG off and no mail configured a 500 leaves nothing behind but an
# access-log line. Cloud Run collects stdout into Cloud Logging, so send
# tracebacks there.
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {"format": "{levelname} {name} {message}", "style": "{"},
    },
    "handlers": {
        "console": {"class": "logging.StreamHandler", "formatter": "verbose"},
    },
    "root": {"handlers": ["console"], "level": "WARNING"},
    "loggers": {
        "django.request": {
            "handlers": ["console"],
            "level": "ERROR",
            "propagate": False,
        },
    },
}

LOGIN_URL = "account_login"
LOGIN_REDIRECT_URL = "corpus-list"
LOGOUT_REDIRECT_URL = "account_login"

# Sign-in is Google only. Any Google account may sign in and an account is
# created on first arrival - there is no separate registration step, and no
# password for us to store or reset.
SOCIALACCOUNT_ONLY = True
ACCOUNT_EMAIL_VERIFICATION = "none"
SOCIALACCOUNT_AUTO_SIGNUP = True
# Skip allauth's "continue with Google?" interstitial; the button on our
# login page is already the confirmation.
SOCIALACCOUNT_LOGIN_ON_GET = True

SOCIALACCOUNT_PROVIDERS = {
    "google": {
        "APP": {
            "client_id": os.environ.get("GOOGLE_OAUTH_CLIENT_ID", ""),
            "secret": os.environ.get("GOOGLE_OAUTH_SECRET", ""),
            "key": "",
        },
        "SCOPE": ["profile", "email"],
        "AUTH_PARAMS": {"access_type": "online"},
    }
}

# Uploaded documents are parsed and discarded; only extracted text is kept,
# so this cap is about parse cost rather than storage.
MAX_UPLOAD_BYTES = int(os.environ.get("CORPUS_MAX_UPLOAD_BYTES", 20 * 1024 * 1024))

if not DEBUG:
    # Deployed behind a TLS-terminating proxy (Cloud Run, a load balancer),
    # so the scheme has to come from the forwarded header.
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SECURE_SSL_REDIRECT = os.environ.get("DJANGO_SSL_REDIRECT", "1") == "1"
    # Cloud Run's startup and liveness probes reach the container directly,
    # without the proxy's X-Forwarded-Proto header, so the SSL redirect would
    # answer them with a 301 and the probe would read that as a failure.
    SECURE_REDIRECT_EXEMPT = [r"^health$"]
    SECURE_HSTS_SECONDS = int(os.environ.get("DJANGO_HSTS_SECONDS", 60 * 60 * 24 * 365))
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
