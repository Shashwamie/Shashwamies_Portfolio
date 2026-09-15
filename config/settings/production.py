"""
Production settings.

Host-agnostic on purpose: no hosting provider has been chosen yet. Configure
via environment variables when deploying (see .env.example).
"""

import os

import dj_database_url

from .base import *  # noqa: F401,F403
from .base import BASE_DIR

DEBUG = False

ALLOWED_HOSTS = [h for h in os.environ.get("ALLOWED_HOSTS", "").split(",") if h]

CSRF_TRUSTED_ORIGINS = [
    o for o in os.environ.get("CSRF_TRUSTED_ORIGINS", "").split(",") if o
]

# Falls back to local SQLite if DATABASE_URL isn't set, so this still runs
# before a real production database is provisioned. Set DATABASE_URL (e.g. a
# Postgres URL) when ready.
DATABASES = {
    "default": dj_database_url.config(
        default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}",
        conn_max_age=600,
    )
}

# Serve compressed, cache-busted static files via whitenoise.
# Requires `manage.py collectstatic` to have been run.
STORAGES["staticfiles"] = {  # noqa: F405
    "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
}

SECURE_SSL_REDIRECT = os.environ.get("SECURE_SSL_REDIRECT", "true").lower() == "true"
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
