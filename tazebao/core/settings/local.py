'''This module sets the configuration for a local development

'''
from .common import * # noqa

DEBUG = True
INTERNAL_IPS = ('127.0.0.1', )  # debug toolbar

ALLOWED_HOSTS = ['192.168.1.62', '127.0.0.1', 'localhost',  ]

INSTALLED_APPS += (
    'debug_toolbar',
)

TEMPLATES[0]['OPTIONS']['debug'] = True

MIDDLEWARE = (
    'debug_toolbar.middleware.DebugToolbarMiddleware',
) + MIDDLEWARE

# MAIL
# send to console in dev mode
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
MAILQUEUE_QUEUE_UP = True
MAILQUEUE_LIMIT = 500

# CKEDITOR
CKEDITOR_CONFIGS['default']['contentsCss'] = [
    STATIC_URL + 'core/src/vendor/Font-Awesome/scss/font-awesome.css',
    STATIC_URL + 'core/src/scss/styles.css',
    STATIC_URL + 'core/src/css/ckeditor.css']

# DEBUG_TOOLBAR
JQUERY_URL = ''

# DEBUG TOOLBAR
DEBUG_TOOLBAR_PANELS = [
    'debug_toolbar.panels.versions.VersionsPanel',
    'debug_toolbar.panels.timer.TimerPanel',
    'debug_toolbar.panels.settings.SettingsPanel',
    'debug_toolbar.panels.headers.HeadersPanel',
    'debug_toolbar.panels.request.RequestPanel',
    'debug_toolbar.panels.sql.SQLPanel',
    'debug_toolbar.panels.staticfiles.StaticFilesPanel',
    'debug_toolbar.panels.templates.TemplatesPanel',
    'debug_toolbar.panels.cache.CachePanel',
    'debug_toolbar.panels.signals.SignalsPanel',
    'debug_toolbar.panels.logging.LoggingPanel',
    'debug_toolbar.panels.redirects.RedirectsPanel',
    'debug_toolbar.panels.profiling.ProfilingPanel',
    'cachalot.panels.CachalotPanel',
]

# CELERY
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERYD_HIJACK_ROOT_LOGGER = False
