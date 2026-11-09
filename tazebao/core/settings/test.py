"""Settings for the automated test suite.

Run with:
    python manage.py test --settings=core.settings.test

Expects a throwaway MySQL server, by default on 127.0.0.1:3317 with user root,
e.g.:
    docker run -d --name tazebao_test_mysql -e MYSQL_ROOT_PASSWORD=tazebao \
        -p 127.0.0.1:3317:3306 mysql:8.0
"""
import os

os.environ.setdefault("DB_PASSWORD", "tazebao")

from .common import *  # noqa

# fixed values: signed tracking links in the tests are computed from these
SECRET_KEY = "tazebao-test-secret-key"
POSTFIX_CLIENT_ID = "postfix-id"
POSTFIX_CLIENT_SECRET = "postfix-secret"

DEBUG = False
ALLOWED_HOSTS = ["testserver", "localhost"]

DATABASES["default"].update({  # noqa
    "NAME": os.environ.get("TEST_DB_NAME", "dbtazebao"),
    "HOST": os.environ.get("TEST_DB_HOST", "127.0.0.1"),
    "PORT": os.environ.get("TEST_DB_PORT", "3317"),
    "USER": os.environ.get("TEST_DB_USER", "root"),
    "PASSWORD": os.environ.get("TEST_DB_PASSWORD", "tazebao"),
})

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
    }
}

# no collectstatic in tests: plain storage, no hashed manifest lookup
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
}

PASSWORD_HASHERS =["django.contrib.auth.hashers.MD5PasswordHasher"]
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
MAILQUEUE_QUEUE_UP = True
MAILQUEUE_LIMIT = 100

# run celery tasks inline, no broker needed
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

# keep test output clean and do not write log files
LOGGING = {
    "version": 1,
    "disable_existing_loggers": True,
    "handlers": {"null": {"class": "logging.NullHandler"}},
    "root": {"handlers": ["null"]},
}

# django-simple-captcha accepts "PASSED" as answer
CAPTCHA_TEST_MODE = True
