"""
Django settings for tazebao project.
"""

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os
import datetime
from dotenv import load_dotenv
from getenv import env

here = lambda *x: os.path.join(os.path.dirname( # noqa
                               os.path.realpath(__file__)), *x)

BASE_DIR = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

dotenv_path = here('..', '..', '.env')
load_dotenv(dotenv_path)

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.8/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env(
    'SECRET_KEY',
    '49saa%ruey1&!nveiz*f(cu$)0pje8wz7u++y-0ljd2)9r)j8h')
POSTFIX_CLIENT_ID = env('POSTFIX_CLIENT_ID')
POSTFIX_CLIENT_SECRET = env('POSTFIX_CLIENT_SECRET')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False
HTTPS = False

ALLOWED_HOSTS = []

ADMINS = (
    ('abidibo', 'web.sites.logs@gmail.com'),
)

# SITE
SITE_ID = 1

# MAIL
EMAIL_HOST = 'localhost'
EMAIL_PORT = 25

# Database
# https://docs.djangoproject.com/en/1.8/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': env('DB_NAME', 'dbtazebao'),
        'HOST': env('DB_HOST', 'localhost'),
        'USER': env('DB_USER', 'tazebao'),
        'PASSWORD': env('DB_PASSWORD', required=True),
        'PORT': '',
        'OPTIONS': {
            'init_command': 'SET default_storage_engine=InnoDB',
        }
    }
}

# Application definition

INSTALLED_APPS = (
    'core',
    'baton',
    'django.contrib.sites',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.flatpages',
    'ckeditor',
    'ckeditor_uploader',
    'pipeline',
    'django_cleanup',
    'export_action',
    'captcha',
    'easy_thumbnails',
    'taggit',
    'rest_framework',
    'rest_framework_httpsignature',
    'corsheaders',
    'mailqueue',
    'jsonify',
    'mosaico',
    'newsletter',
    'baton.autodiscover',
)

MIDDLEWARE = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.flatpages.middleware.FlatpageFallbackMiddleware',
)

ROOT_URLCONF = 'core.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'debug': False,
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'core.context_processors.debug',
            ],
        },
    },
]

WSGI_APPLICATION = 'core.wsgi.application'

# Internationalization
# https://docs.djangoproject.com/en/1.8/topics/i18n/

LANGUAGE_CODE = 'it-it'

TIME_ZONE = 'Europe/Rome'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.8/howto/static-files/

STATICFILES_STORAGE = 'pipeline.storage.PipelineCachedStorage'
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    'pipeline.finders.PipelineFinder',
)
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'static')

# Uploaded files
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# LOGIN
LOGIN_URL = '/admin/'

# MENU
BATON = {
    'SITE_HEADER': '<img src="/static/core/img/logo-sm.png" /> <span style="font-size: 36px !important; position: relative; top: 8px;">Tazebao</span>',
    'SITE_TITLE': 'Tazebao',
    'INDEX_TITLE': 'Dashboard',
    'MENU': (
        {'type': 'title', 'label': 'Sistema',  'apps': ('auth', 'sites', 'newsletter', )},
        {'type': 'app', 'name': 'auth', 'label': 'Autenticazione', 'icon':'fa fa-lock'},
        {'type': 'model', 'app': 'sites', 'name': 'site', 'label': 'Siti', 'icon':'fa fa-leaf'},
        {'type': 'model', 'app': 'newsletter', 'name': 'client', 'label': 'Client', 'icon':'fa fa-laptop-code'},
        {'type': 'model', 'app': 'flatpages', 'name': 'flatpage', 'label': 'Pagine', 'icon':'fa fa-book'},

        {'type': 'title', 'label': 'Iscrizioni',  'apps': ('newsletter', )},
        {'type': 'model', 'app': 'newsletter', 'name': 'subscriberlist', 'label': 'Liste iscritti', 'icon':'fa fa-list'},
        {'type': 'model', 'app': 'newsletter', 'name': 'subscriber', 'label': 'Iscritti', 'icon':'fa fa-user-tie'},


        {'type': 'title', 'label': 'Newsletter',  'apps': ('newsletter', )},
        {'type': 'model', 'app': 'mosaico', 'name': 'template', 'label': 'Template', 'icon':'fa fa-th'},
        {'type': 'model', 'app': 'newsletter', 'name': 'topic', 'label': 'Topic', 'icon':'fa fa-tag'},
        {'type': 'model', 'app': 'newsletter', 'name': 'campaign', 'label': 'Campagne', 'icon':'fa fa-envelope'},
        {'type': 'model', 'app': 'mosaico', 'name': 'upload', 'label': 'Upload', 'icon':'fa fa-upload'},
        {'type': 'free', 'url': '/help/', 'label': 'Aiuto', 'icon':'fa fa-question-circle'},

        {'type': 'title', 'label': 'Invii',  'apps': ('newsletter', )},
        {'type': 'model', 'app': 'newsletter', 'name': 'planning', 'label': 'Planning', 'icon':'fa fa-clock'},
        {'type': 'model', 'app': 'newsletter', 'name': 'dispatch', 'label': 'Report', 'icon':'fa fa-paper-plane'},
        {'type': 'model', 'app': 'newsletter', 'name': 'failedemail', 'label': 'Bounces', 'icon':'fa fa-ban'},

        {'type': 'title', 'label': 'Statistiche',  'apps': ('newsletter', )},
        {'type': 'model', 'app': 'newsletter', 'name': 'tracking', 'label': 'Tracking', 'icon':'fa fa-chart-pie'},
        {'type': 'model', 'app': 'newsletter', 'name': 'usermailermessage', 'label': 'Log invii', 'icon':'fa fa-stethoscope'},
    ),
    'COPYRIGHT': '© 2016-2019 otto.to.it',
    'SUPPORT_HREF': 'mailto:stefano.contini@otto.to.it',
    'POWERED_BY': '<a href="https://www.otto.to.it">Otto srl</a>'
}

# CKEDITOR
CKEDITOR_UPLOAD_PATH = 'ckeditor/'
CKEDITOR_JQUERY_URL = ''
CKEDITOR_IMAGE_BACKEND = 'pillow'
CKEDITOR_CONFIGS = {
    'default': {
        'skin': 'moono',
        'toolbar_Basic': [
                ['Source', '-', 'Bold', 'Italic']
        ],
        'toolbar_Full': [
            ['Styles', 'Format', 'Bold', 'Italic', 'Underline', 'Strike',
             'SpellChecker', 'Undo', 'Redo'],
            ['NumberedList', 'BulletedList'],
            ['Link', 'Unlink', 'Anchor'],
            ['Image', 'Flash', 'Table', 'HorizontalRule'],
            ['TextColor', 'BGColor'],
            ['SpecialChar'], ['PasteFromWord'], ['Source']
        ],
        'toolbar': 'Full',
        'height': 291,
        'width': '100%',
        'filebrowserWindowWidth': 940,
        'filebrowserWindowHeight': 725,
        'removePlugins': 'stylesheetparser',
        'allowedContent': True,
        'extraAllowedContent': 'iframe[*]',
    }
}

# pipeline
PIPELINE = {
    'STYLESHEETS': {
        'vendor': {
            'source_filenames': (
                'core/src/vendor/Font-Awesome/scss/font-awesome.scss',
            ),
            'output_filename': 'core/css/vendor.min.css',
        },
        'tazebao': {  # bootstrap + custom
            'source_filenames': (
                'core/src/scss/styles.scss',
            ),
            'output_filename': 'core/css/core.min.css',
        },
    },
    'JAVASCRIPT': {
        'vendor': {
            'source_filenames': (
                'core/src/vendor/bootstrap/js/bootstrap.min.js',
                'core/src/vendor/moment/moment-with-locales.min.js',
            ),
            'output_filename': 'core/js/vendor.min.js'
        },
        'tazebao': {
            'source_filenames': (
                'core/src/js/core.js',
            ),
            'output_filename': 'core/js/core.min.js'
        },
    },
    'COMPILERS': ('pipeline.compilers.sass.SASSCompiler', ),
    'CSS_COMPRESSOR': None,
    'JS_COMPRESSOR': None,
}

# API
JWT_AUTH = {
    'JWT_EXPIRATION_DELTA': datetime.timedelta(minutes=60),
    'JWT_ALLOW_REFRESH': True,
}
CORS_ORIGIN_WHITELIST = (
    'http://127.0.0.1',
    'http://localhost',
    'http://localhost:3000',
)
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_HEADERS = (
    'cache-control',
    'content-type',
    'authorization',
    'set-cookie',
)
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_jwt.authentication.JSONWebTokenAuthentication',
        'newsletter.auth.NewsletterAPISignatureAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_RENDERER_CLASSES': (
        'rest_framework.renderers.JSONRenderer',
    )
}

# LOGGING

LOGGING_DEFAULT = {
    'handlers': ['console', 'file'],
    'level': 'DEBUG',
    'propagate': True,
}

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '%(levelname)s %(asctime)s %(module)s %(process)d %(thread)d %(message)s' # noqa
        },
        'simple': {
            'format': '%(levelname)s %(message)s'
        },
    },
    'handlers': {
        'null': {
            'level': 'DEBUG',
            'class': 'logging.NullHandler',
        },
        'console': {
            'level': 'ERROR',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose'
        },
        # configure the log to be rotated daily
        # see
        # https://docs.python.org/2.7/library/logging.handlers.html#logging.handlers.TimedRotatingFileHandler
        # noqa
        'file': {
            'level': 'DEBUG',
            'formatter': 'verbose',
            'class': 'logging.handlers.TimedRotatingFileHandler',
            'filename': here('..', '..', '..',
                             os.path.join('logs', 'debug.log')),
            'when':     'midnight',
        },
        'file_email': {
            'level': 'DEBUG',
            'formatter': 'verbose',
            'class': 'logging.handlers.TimedRotatingFileHandler',
            'filename': here('..', '..', '..',
                             os.path.join('logs', 'mail.log')),
            'when':     'midnight',
        },
        'celery_logger': {
            'level': 'DEBUG',
            'filters': None,
            'class': 'logging.handlers.TimedRotatingFileHandler',
            'filename': here('..', '..', '..',
                             os.path.join('logs', 'celery.log')),
            'formatter': 'verbose'
        },
        'mail_admins': {
            'level': 'ERROR',
            'class': 'django.utils.log.AdminEmailHandler',
            'include_html': True,
        }
    },
    'loggers': {
        'django': {
            'handlers': ['file'],
            'level': 'DEBUG',
            'propagate': True,
        },
        'django.request': {
            'handlers': ['mail_admins', 'console', 'file', ],
            'level': 'ERROR',
            'propagate': False,
        },
        # http://stackoverflow.com/questions/7768027/turn-off-sql-logging-while-keeping-settings-debug
        # noqa
       'django.db.backends': {
            'handlers': ['null'],  # Quiet by default!
            'propagate': False,
            'level': 'DEBUG',
        },
        'newsletter': {
            'handlers': ['file_email'],
            'level': 'DEBUG',
            'propagate': True,
        },
        'celery_newsletter': {
            'handlers': ['mail_admins', 'celery_logger', 'console'],
            'level': 'DEBUG',
            'propagate': True,
        },
        'core': LOGGING_DEFAULT,
        '': LOGGING_DEFAULT,  # root logger
    },
}
