"""
Django settings for tazebao project.
"""

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os
import sys
import datetime

from django.core.exceptions import ImproperlyConfigured
from dotenv import load_dotenv


def env(name, default=None, required=False):
    value = os.environ.get(name, default)
    if required and value is None:
        raise ImproperlyConfigured("Missing required environment variable %s" % name)
    return value


here = lambda *x: os.path.join(
    os.path.dirname(  # noqa
        os.path.realpath(__file__)
    ),
    *x,
)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

dotenv_path = here("..", "..", ".env")
load_dotenv(dotenv_path)

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.8/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env("SECRET_KEY", "49saa%ruey1&!nveiz*f(cu$)0pje8wz7u++y-0ljd2)9r)j8h")
POSTFIX_CLIENT_ID = env("POSTFIX_CLIENT_ID")
POSTFIX_CLIENT_SECRET = env("POSTFIX_CLIENT_SECRET")
OPENAI_API_KEY = env("AI_API_KEY")
OPENAI_ORGANIZATION = env("AI_ORGANIZATION")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False
HTTPS = False

ALLOWED_HOSTS = []

ADMINS = (("abidibo", "web.sites.logs@gmail.com"),)

# SITE
SITE_ID = 1

# MAIL
EMAIL_HOST = "localhost"
EMAIL_PORT = 25

TEST_EMAIL_MAX_NUM = 50

# Database
# https://docs.djangoproject.com/en/1.8/ref/settings/#databases

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": env("DB_NAME", "dbtazebao"),
        "HOST": env("DB_HOST", "localhost"),
        "USER": env("DB_USER", "tazebao"),
        "PASSWORD": env("DB_PASSWORD", required=True),
        "PORT": "",
        "OPTIONS": {
            "init_command": "SET default_storage_engine=InnoDB",
        },
    }
}

# Application definition

INSTALLED_APPS = (
    "core",
    "baton",
    "django.contrib.sites",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.flatpages",
    "ckeditor",
    "ckeditor_uploader",
    "pipeline",
    "django_cleanup",
    "export_action",
    "captcha",
    "rest_framework",
    "corsheaders",
    "mailqueue",
    "mosaico",
    "newsletter",
    "baton.autodiscover",
)

MIDDLEWARE = (
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django.contrib.flatpages.middleware.FlatpageFallbackMiddleware",
)

ROOT_URLCONF = "core.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "debug": False,
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "core.context_processors.debug",
            ],
        },
    },
]

WSGI_APPLICATION = "core.wsgi.application"

# Internationalization
# https://docs.djangoproject.com/en/1.8/topics/i18n/

LANGUAGE_CODE = "it-it"

TIME_ZONE = "Europe/Rome"

USE_I18N = True

USE_TZ = True

# django-ckeditor bundles CKEditor 4, which is end of life. Replacing the editor
# (SystemMessage.html, flatpages) is tracked as a separate task.
SILENCED_SYSTEM_CHECKS = ["ckeditor.W001"]

# keep integer primary keys: avoids new migrations for every model
DEFAULT_AUTO_FIELD = "django.db.models.AutoField"

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": "redis://127.0.0.1:6379/10",
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        },
    },
}


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.8/howto/static-files/

STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "core.storage.StaticStorage",
    },
}
STATICFILES_FINDERS = (
    "django.contrib.staticfiles.finders.FileSystemFinder",
    "django.contrib.staticfiles.finders.AppDirectoriesFinder",
    "pipeline.finders.PipelineFinder",
)
STATIC_URL = "/static/"
STATIC_ROOT = os.path.join(BASE_DIR, "static")

# Uploaded files
MEDIA_URL = "/media/"
MEDIA_ROOT = os.path.join(BASE_DIR, "media")

# LOGIN
LOGIN_URL = "/admin/"

# MENU
# menu icons are Material Symbols names (https://fonts.google.com/icons)
BATON = {
    "SITE_HEADER": '<img src="/static/core/img/logo-sm.png" /> <span style="font-size: 36px !important; position: relative; top: 8px;">Tazebao</span>',
    "SITE_TITLE": "Tazebao",
    "INDEX_TITLE": "Dashboard",
    "MENU": (
        {
            "type": "title",
            "label": "Sistema",
            "apps": (
                "auth",
                "sites",
                "newsletter",
            ),
        },
        {
            "type": "app",
            "name": "auth",
            "label": "Autenticazione",
            "icon": "lock",
        },
        {
            "type": "model",
            "app": "sites",
            "name": "site",
            "label": "Siti",
            "icon": "eco",
        },
        {
            "type": "model",
            "app": "newsletter",
            "name": "client",
            "label": "Client",
            "icon": "computer",
        },
        {
            "type": "model",
            "app": "newsletter",
            "name": "systemmessage",
            "label": "Messaggi",
            "icon": "campaign",
        },
        {
            "type": "model",
            "app": "newsletter",
            "name": "systemmessageread",
            "label": "Letture messaggi",
            "icon": "done_all",
        },
        {
            "type": "model",
            "app": "flatpages",
            "name": "flatpage",
            "label": "Pagine",
            "icon": "menu_book",
        },
        {"type": "title", "label": "Iscrizioni", "apps": ("newsletter",)},
        {
            "type": "model",
            "app": "newsletter",
            "name": "subscriberlist",
            "label": "Liste iscritti",
            "icon": "list",
        },
        {
            "type": "model",
            "app": "newsletter",
            "name": "subscriber",
            "label": "Iscritti",
            "icon": "person",
        },
        {
            "type": "model",
            "app": "newsletter",
            "name": "unsubscription",
            "label": "Disiscrizioni",
            "icon": "warning",
        },
        {
            "type": "model",
            "app": "newsletter",
            "name": "subscriptionform",
            "label": "Form sottoscrizione",
            "icon": "dynamic_form",
        },
        {
            "type": "model",
            "app": "newsletter",
            "name": "suggestionrequest",
            "label": "Richieste suggerimenti",
            "icon": "chat_bubble",
        },
        {"type": "title", "label": "Newsletter", "apps": ("newsletter",)},
        {
            "type": "model",
            "app": "mosaico",
            "name": "template",
            "label": "Template",
            "icon": "grid_view",
        },
        {
            "type": "model",
            "app": "newsletter",
            "name": "topic",
            "label": "Topic",
            "icon": "sell",
        },
        {
            "type": "model",
            "app": "newsletter",
            "name": "campaign",
            "label": "Campagne",
            "icon": "mail",
        },
        {
            "type": "model",
            "app": "mosaico",
            "name": "upload",
            "label": "Upload",
            "icon": "upload",
        },
        {
            "type": "free",
            "url": "/help/",
            "label": "Aiuto",
            "icon": "help",
        },
        {"type": "title", "label": "Invii", "apps": ("newsletter",)},
        {
            "type": "model",
            "app": "newsletter",
            "name": "planning",
            "label": "Planning",
            "icon": "schedule",
        },
        {
            "type": "model",
            "app": "newsletter",
            "name": "dispatch",
            "label": "Report",
            "icon": "send",
        },
        {
            "type": "model",
            "app": "newsletter",
            "name": "failedemail",
            "label": "Bounces",
            "icon": "block",
        },
        {"type": "title", "label": "Statistiche", "apps": ("newsletter",)},
        {
            "type": "model",
            "app": "newsletter",
            "name": "tracking",
            "label": "Tracking",
            "icon": "pie_chart",
        },
        {
            "type": "model",
            "app": "newsletter",
            "name": "usermailermessage",
            "label": "Log invii",
            "icon": "monitor_heart",
        },
    ),
    "COPYRIGHT": "© 2016-2019 otto.to.it",
    "SUPPORT_HREF": "mailto:stefano.contini@otto.to.it",
    "POWERED_BY": '<a href="https://www.otto.to.it">Otto srl</a>',
}

# CKEDITOR
CKEDITOR_UPLOAD_PATH = "ckeditor/"
CKEDITOR_JQUERY_URL = ""
CKEDITOR_IMAGE_BACKEND = "pillow"
CKEDITOR_CONFIGS = {
    "default": {
        "skin": "moono",
        "toolbar_Basic": [["Source", "-", "Bold", "Italic"]],
        "toolbar_Full": [
            [
                "Styles",
                "Format",
                "Bold",
                "Italic",
                "Underline",
                "Strike",
                "SpellChecker",
                "Undo",
                "Redo",
            ],
            ["NumberedList", "BulletedList"],
            ["Link", "Unlink", "Anchor"],
            ["Image", "Flash", "Table", "HorizontalRule"],
            ["TextColor", "BGColor"],
            ["SpecialChar"],
            ["PasteFromWord"],
            ["Source"],
        ],
        "toolbar": "Full",
        "height": 291,
        "width": "100%",
        "filebrowserWindowWidth": 940,
        "filebrowserWindowHeight": 725,
        "removePlugins": "stylesheetparser",
        "allowedContent": True,
        "extraAllowedContent": "iframe[*]",
    }
}

# pipeline
PIPELINE = {
    "STYLESHEETS": {
        "vendor": {
            "source_filenames": (
                "core/src/vendor/Font-Awesome/scss/font-awesome.scss",  # noqa
                "core/src/vendor/swiper/css/swiper.min.css",  # noqa
                "core/src/vendor/semantic-ui/semantic.min.css",  # noqa
            ),
            "output_filename": "core/css/vendor.min.css",  # noqa
        },
        "tazebao": {  # custom
            "source_filenames": ("core/src/scss/styles.scss",),
            "output_filename": "core/css/core.min.css",  # noqa
        },
    },
    "JAVASCRIPT": {
        "vendor": {
            "source_filenames": (
                "core/src/vendor/jquery/jquery.min.js",  # noqa
                # 'core/src/vendor/jquery.form/jquery.form.js', # noqa
                # 'core/src/vendor/jquery.formset/jquery.formset.js', # noqa
                "core/src/vendor/tocca/tocca.min.js",  # noqa
                "core/src/vendor/semantic-ui/semantic.min.js",  # noqa
                "core/src/vendor/moment/moment-with-locales.min.js",  # noqa
            ),
            "output_filename": "core/js/vendor.min.js",
        },
        "tazebao": {
            "source_filenames": (
                "core/src/js/core.js",  # noqa
            ),
            "output_filename": "core/js/core.min.js",  # noqa
        },
    },
    "COMPILERS": ("pipeline.compilers.sass.SASSCompiler",),
    # pysassc comes with the libsass package, installed in the same virtualenv
    "SASS_BINARY": os.path.join(os.path.dirname(sys.executable), "pysassc"),
    "CSS_COMPRESSOR": None,
    "JS_COMPRESSOR": None,
    "MIMETYPES": (
        ("text/coffeescript", ".coffee"),
        ("text/less", ".less"),
        ("text/javascript", ".js"),
        ("text/x-sass", ".sass"),
        ("text/x-scss", ".scss"),
    ),
}

# API
# Sliding tokens keep the old django-rest-framework-jwt contract:
# login and refresh both take/return {"token": ...}, header "Authorization: JWT <token>"
SIMPLE_JWT = {
    "AUTH_HEADER_TYPES": ("JWT",),
    "AUTH_TOKEN_CLASSES": ("rest_framework_simplejwt.tokens.SlidingToken",),
    "SLIDING_TOKEN_LIFETIME": datetime.timedelta(minutes=60),
    "SLIDING_TOKEN_REFRESH_LIFETIME": datetime.timedelta(days=7),
    "UPDATE_LAST_LOGIN": False,
}
CORS_ALLOWED_ORIGINS = (
    "http://127.0.0.1",
    "http://192.168.0.4:3001",
    "https://app.tazebao.sqrt64.it",
    "https://app.tazebao.email",
    "http://localhost",
    "http://localhost:3000",
    "http://localhost:3001",
)
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_HEADERS = (
    "cache-control",
    "content-type",
    "authorization",
    "set-cookie",
)
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
        "newsletter.auth.NewsletterAPISignatureAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.IsAuthenticated",),
    "DEFAULT_RENDERER_CLASSES": ("rest_framework.renderers.JSONRenderer",),
}

# CELERY (read by core/celery.py with namespace "CELERY")
CELERY_BROKER_URL = env("CELERY_BROKER_URL", "redis://localhost:6379/0")
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_WORKER_HIJACK_ROOT_LOGGER = False
CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = True

# LOGGING

LOGGING_DEFAULT = {
    "handlers": ["console", "file"],
    "level": "DEBUG",
    "propagate": True,
}

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "%(levelname)s %(asctime)s %(module)s %(process)d %(thread)d %(message)s"  # noqa
        },
        "simple": {"format": "%(levelname)s %(message)s"},
    },
    "handlers": {
        "null": {
            "level": "DEBUG",
            "class": "logging.NullHandler",
        },
        "console": {
            "level": "ERROR",
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
        # configure the log to be rotated daily
        # see
        # https://docs.python.org/2.7/library/logging.handlers.html#logging.handlers.TimedRotatingFileHandler
        # noqa
        "file": {
            "level": "DEBUG",
            "formatter": "verbose",
            "class": "logging.handlers.TimedRotatingFileHandler",
            "filename": here("..", "..", "..", os.path.join("logs", "debug.log")),
            "when": "midnight",
        },
        "file_email": {
            "level": "DEBUG",
            "formatter": "verbose",
            "class": "logging.handlers.TimedRotatingFileHandler",
            "filename": here("..", "..", "..", os.path.join("logs", "mail.log")),
            "when": "midnight",
        },
        "celery_logger": {
            "level": "DEBUG",
            "filters": None,
            "class": "logging.handlers.TimedRotatingFileHandler",
            "filename": here("..", "..", "..", os.path.join("logs", "celery.log")),
            "formatter": "verbose",
        },
        "mail_admins": {
            "level": "ERROR",
            "class": "django.utils.log.AdminEmailHandler",
            "include_html": True,
        },
    },
    "loggers": {
        "django": {
            "handlers": ["file"],
            "level": "DEBUG",
            "propagate": True,
        },
        "django.request": {
            "handlers": [
                "mail_admins",
                "console",
                "file",
            ],
            "level": "ERROR",
            "propagate": False,
        },
        # http://stackoverflow.com/questions/7768027/turn-off-sql-logging-while-keeping-settings-debug
        # noqa
        "django.db.backends": {
            "handlers": ["null"],  # Quiet by default!
            "propagate": False,
            "level": "DEBUG",
        },
        "newsletter": {
            "handlers": ["file_email"],
            "level": "DEBUG",
            "propagate": True,
        },
        "celery_newsletter": {
            "handlers": ["mail_admins", "celery_logger", "console"],
            "level": "DEBUG",
            "propagate": True,
        },
        "core": LOGGING_DEFAULT,
        "": LOGGING_DEFAULT,  # root logger
    },
}
