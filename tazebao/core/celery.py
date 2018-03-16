from __future__ import absolute_import

import os
from celery import Celery
from django.conf import settings
from dotenv import load_dotenv
from getenv import env


def here(*x):
    return os.path.join(os.path.dirname(
        os.path.realpath(__file__)), *x)

dotenv_path = here('..', '.env')
load_dotenv(dotenv_path)

app = Celery('tazebao', broker='redis://localhost:6379/0')

# set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', env('DJANGO_SETTINGS_MODULE'))

# Using a string here means the worker will not have to
# pickle the object when using Windows.
app.config_from_object('django.conf:settings')
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)
