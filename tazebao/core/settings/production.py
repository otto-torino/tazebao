'''This module sets the configuration for a local development

'''
from .common import * #noqa

import os

DEBUG = False

ALLOWED_HOSTS = ['tazebao.email', 'www.tazebao.email', 'tazebao.sqrt64.it', ]

# ssl
HTTPS = True
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTOCOL', 'https')
SESSION_COOKIE_SECURE = True

STATIC_ROOT = '/home/otto/www/tazebao/static/'
MEDIA_ROOT = '/home/otto/www/tazebao/media'

# MAIL
MAILQUEUE_QUEUE_UP = True
MAILQUEUE_LIMIT = 100

# CKEDITOR
CKEDITOR_CONFIGS['default']['contentsCss'] = [
    STATIC_URL + 'core/css/vendor.min.css',
    STATIC_URL + 'core/css/core.min.css',
    STATIC_URL + 'core/src/css/ckeditor.css']

LOGGING['handlers']['file']['filename'] = here('..', '..', '..', '..', os.path.join('logs', 'debug.log')) # noqa
LOGGING['handlers']['file_email']['filename'] = here('..', '..', '..', '..', os.path.join('logs', 'mail.log')) # noqa
LOGGING['handlers']['celery_logger']['filename'] = here('..', '..', '..', '..', os.path.join('logs', 'celery.log')) # noqa

# CELERY
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERYD_HIJACK_ROOT_LOGGER = False
