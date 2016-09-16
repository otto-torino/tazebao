'''This module sets the configuration for a local development

'''
from .common import * # noqa

DEBUG = True

INSTALLED_APPS += (
    'debug_toolbar',
)

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

# CELERY
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERYD_HIJACK_ROOT_LOGGER = False
