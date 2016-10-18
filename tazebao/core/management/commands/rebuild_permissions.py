from django.core.management.base import BaseCommand
from django.apps import apps as dapps
from django.contrib.auth.management import create_permissions


class Command(BaseCommand):
    args = '<app app ...>'
    help = 'reloads permissions for all apps'

    def handle(self, *args, **options):
        apps = []
        for model in dapps.get_models():
            apps.append(dapps.get_app_config(model._meta.app_label))
        for app in apps:
            create_permissions(app, dapps.get_models(), options.get('verbosity', 0))
