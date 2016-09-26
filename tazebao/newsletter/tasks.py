from __future__ import absolute_import
import re

from django import template
from django.utils import timezone
from django.template import Context
from django.core.urlresolvers import reverse
from django.contrib.sites.models import Site

from core.celery import app
from celery.utils.log import get_task_logger

from mailqueue.models import MailerMessage

from .models import Dispatch, SubscriberList, Campaign
from .context import get_campaign_context

logger = get_task_logger('celery')


@app.task
def send_campaign(lists_ids, campaign_id):
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
    unsubscription_template = template.Template('{% load newsletter_tags %}' + str(campaign.topic.unsubscription_text)) # noqa
    unsubscription_html_template = template.Template('{% load newsletter_tags %}' + str(campaign.topic.unsubscription_html_text)) # noqa
    text_template = template.Template(campaign.plain_text)
    html_template = template.Template(campaign.html_text)
    from_header = "%s <%s>" % (
        campaign.topic.sending_name,
        campaign.topic.sending_address
    )
    for subscriber_list in lists_obj:
        for subscriber in subscriber_list.subscriber_set.all():
            msg = MailerMessage()
            # unsubscribe text
            unsubscription_text = ''
            unsubscription_html_text = ''
            if campaign.topic.unsubscription_text:
                ctx = Context()
                ctx.update({'client': campaign.client})
                ctx.update({'id': subscriber.id})
                ctx.update({'email': subscriber.email})
                ctx.update({'subscription_datetime': subscriber.subscription_datetime}) # noqa
                unsubscription_text = unsubscription_template.render(ctx)
            if campaign.topic.unsubscription_html_text:
                ctx = Context()
                ctx.update({'client': campaign.client})
                ctx.update({'id': subscriber.id})
                ctx.update({'email': subscriber.email})
                ctx.update({'subscription_datetime': subscriber.subscription_datetime}) # noqa
                unsubscription_html_text = unsubscription_html_template.render(ctx) # noqa
            # subject and body
            context = Context()
            context.update({'unsubscription_text': unsubscription_text})
            context.update(get_campaign_context(campaign))
            msg.app = dispatch.pk
            msg.subject = campaign.subject
            msg.to_address = subscriber.email
            msg.from_address = from_header
            msg.content = text_template.render(context)
            tracking = False
            if campaign.html_text is not None and campaign.html_text != u"": # noqa
                context.update({'unsubscription_text': unsubscription_html_text}) # noqa
                html_content = html_template.render(context)
                # add tracking image
                matches = re.match(r'[^\$]*(</body>)[^\$]*', html_content, re.I) # noqa
                if matches:
                    tracking_image = '''
                    <img src="%s" />
                    ''' % ''.join([
                        'http://',
                        str(Site.objects.get_current()),
                        reverse('newsletter-email-tracking',
                                kwargs={
                                    'dispatch_id': dispatch.id,
                                    'subscriber_id': subscriber.id
                                })
                    ])
                    rexp = re.compile(re.escape('</body>'), re.I)
                    html_content = rexp.sub(tracking_image + matches.group(1), html_content) # noqa
                    tracking = True
                msg.html_content = html_content

            try:
                msg.save()
                sent += 1
                used_addresses.append(subscriber.email)
            except:
                error_addresses.append(subscriber.email)
    dispatch.error = False
    dispatch.success = True
    dispatch.tracking = tracking
    dispatch.finished_at = timezone.now()
    dispatch.sent = sent
    dispatch.sent_recipients = ','.join(used_addresses)
    dispatch.error_recipients = ','.join(error_addresses)
    dispatch.save()
    return sent
