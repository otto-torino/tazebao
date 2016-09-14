'''This module sets the configuration for a local development

'''
from .common import *

import os

DEBUG = False

ALLOWED_HOSTS = ['tazebao.sqrt64.it',]

STATIC_ROOT = '/home/tazebao/www/tazebao/static/'
MEDIA_ROOT = '/home/tazebao/www/tazebao/media'

# MAIL
MAILQUEUE_QUEUE_UP = True

# CKEDITOR
CKEDITOR_CONFIGS['default']['contentsCss'] = [
    STATIC_URL + 'core/css/vendor.min.css',
    STATIC_URL + 'core/css/core.min.css',
    STATIC_URL + 'core/src/css/ckeditor.css']

LOGGING['handlers']['file']['filename'] = here('..', '..', '..', '..', os.path.join('logs', 'debug.log'))
