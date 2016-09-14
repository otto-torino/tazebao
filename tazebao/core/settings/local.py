'''This module sets the configuration for a local development

'''
from .common import *

import os

DEBUG = True

INSTALLED_APPS += (
    'debug_toolbar',
)

# MAIL
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
MAILQUEUE_QUEUE_UP = True

# CKEDITOR
CKEDITOR_CONFIGS['default']['contentsCss'] = [
    STATIC_URL + 'core/src/vendor/Font-Awesome/scss/font-awesome.css',
    STATIC_URL + 'core/src/scss/styles.css',
    STATIC_URL + 'core/src/css/ckeditor.css']

# DEBUG_TOOLBAR
JQUERY_URL = ''
