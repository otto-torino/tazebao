"""
Django settings for tazebao project.
"""

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os
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

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False
HTTPS = False

ALLOWED_HOSTS = []

ADMINS = (
    ('abidibo', 'abidibo@gmail.com'),
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
    'suit',
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
    'captcha',
    'easy_thumbnails',
    'taggit',
    'rest_framework',
    'rest_framework_httpsignature',
    'mailqueue',
    'jsonify',
    'mosaico',

    'newsletter',
)

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
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
SUIT_CONFIG = {
    'ADMIN_NAME': 'Tazebao',
    'MENU': (

        '-',

        {'app': 'auth', 'label': 'Autenticazione', 'icon': 'fa fa-lock'},
        {'app': 'sites', 'label': 'Siti', 'icon': 'fa fa-leaf'},


        '-',

        {'app': 'flatpages', 'label': 'Pagine', 'icon': 'fa fa-book'},

        '-',

        {'app': 'mosaico', 'label': 'Mosaico', 'icon': 'fa fa-th', 'models': (
            {'model': 'template', 'label': 'Template'},
            {'model': 'upload', 'label': 'Upload'},
        )},
        {'app': 'newsletter', 'label': 'Newsletter', 'icon':'fa fa-envelope', 'models': ( # noqa
            'client',
            'subscriberlist',
            'subscriber',
            'topic',
            'campaign',
            'dispatch',
            'tracking',
            'usermailermessage',
        )},
        {'label': 'Aiuto!', 'icon': 'fa fa-life-ring', 'url': '/help/'},
    ),
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
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
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
            'level': 'DEBUG',
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
        'celery': {
            'handlers': ['celery_logger'],
            'level': 'DEBUG',
            'propagate': True,
        },
        'core': LOGGING_DEFAULT,
        '': LOGGING_DEFAULT,  # root logger
    },
}
