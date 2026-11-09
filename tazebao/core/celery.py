import os

from celery import Celery
from dotenv import load_dotenv


def here(*x):
    return os.path.join(os.path.dirname(os.path.realpath(__file__)), *x)


load_dotenv(here('..', '.env'))

# set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.production')

app = Celery('tazebao')

# All celery settings live in django settings, prefixed with CELERY_
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()
