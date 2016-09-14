from django.core.management.base import BaseCommand

from mailqueue.models import MailerMessage


class Command(BaseCommand):
    help = 'Can be run as a cronjob or directly to send queued messages.'

    def add_arguments(self, parser):

        # Named (optional) arguments
        parser.add_argument(
            '--limit',
            action='store',
            dest='limit',
            help='Limit the number of emails to process',
        )

    def handle(self, *args, **options):
        MailerMessage.objects.send_queued(limit=options['limit'])
