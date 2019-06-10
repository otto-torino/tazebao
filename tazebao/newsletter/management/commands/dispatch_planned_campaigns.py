# Set a cronjob to make it work.
from django.utils import timezone

from django.core.management.base import BaseCommand

from ...models import Planning
from ...tasks import send_campaign


class Command(BaseCommand):
    help = 'Checks if a dispatch was planned and in case launches it'

    def handle(self, *args, **options):
        now = timezone.now()
        planned = Planning.objects.filter(schedule__lte=now, sent=False)
        for p in planned:
            lists_ids = [l.pk for l in p.lists.all()]
            send_campaign.delay(lists_ids, p.campaign.pk)
            p.sent = True
            p.save()
