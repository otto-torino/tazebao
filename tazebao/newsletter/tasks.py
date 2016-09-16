from __future__ import absolute_import

from django import template
from django.utils import timezone
from django.template import Context

from core.celery import app
from celery.utils.log import get_task_logger

from mailqueue.models import MailerMessage

from .models import Dispatch, SubscriberList, Campaign
from .context import get_campaign_context

logger = get_task_logger('celery')


@app.task
def send_campaign(lists_ids, campaign_id, fail_silently=False):
    """ Dispatches the newsletter """
    logger.debug('running task: send_newsletter')
    campaign = Campaign.objects.get(pk=campaign_id)
    logger.debug('sending campaign: %s' % campaign)
    dispatch = Dispatch(
        campaign=campaign,
        started_at=timezone.now(),
        error=True,
        success=False
    )
    dispatch.save()
    lists_obj = [SubscriberList.objects.get(pk=x) for x in lists_ids]
    dispatch.lists = lists_obj
    dispatch.save()
    # send
    sent = 0
    used_addresses = []
    error_addresses = []
    # param
    text_template = template.Template(campaign.plain_text)
    html_template = template.Template(campaign.html_text)
    from_header = "%s <%s>" % (
        campaign.topic.sending_name,
        campaign.topic.sending_address
    )
    for subscriber_list in lists_obj:
        for subscriber in subscriber_list.subscriber_set.all():
            msg = MailerMessage()
            context = Context()
            context.update({'email': subscriber.email})
            if campaign.view_online:
                context.update(get_campaign_context(campaign))
            msg.app = dispatch.pk
            msg.subject = campaign.subject
            msg.to_address = subscriber.email
            msg.from_address = from_header
            msg.content = text_template.render(context)
            # msg.body = text_template.render(context)
            if campaign.html_text is not None and campaign.html_text != u"": # noqa
                html_content = html_template.render(context)
                # msg.attach_alternative(html_content, 'text/html')
                msg.html_content = html_content
            try:
                msg.save()
                sent += 1
                used_addresses.append(subscriber.email)
            except:
                error_addresses.append(subscriber.email)
    dispatch.error = False
    dispatch.success = True
    dispatch.finished_at = timezone.now()
    dispatch.sent = sent
    dispatch.sent_recipients = ','.join(used_addresses)
    dispatch.error_recipients = ','.join(error_addresses)
    dispatch.save()
    return sent
