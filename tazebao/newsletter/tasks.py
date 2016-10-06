from __future__ import absolute_import
import re

from django import template
from django.utils import timezone
from django.template import Context
from django.core.urlresolvers import reverse
from django.contrib.sites.models import Site
from django.core.signing import Signer

from core.celery import app
from celery.utils.log import get_task_logger

from mailqueue.models import MailerMessage

from .models import Dispatch, SubscriberList, Campaign
from .context import get_campaign_context

logger = get_task_logger('celery')


@app.task # noqa
def send_campaign(lists_ids, campaign_id):
    """ Dispatches the newsletter """
    logger.debug('running task: send_newsletter')
    campaign = Campaign.objects.get(pk=campaign_id)
    logger.debug('sending campaign: %s' % campaign)
    # init the dispatch object
    dispatch = Dispatch(
        campaign=campaign,
        started_at=timezone.now(),
        error=False,
        success=False
    )
    dispatch.save()
    try:
        lists_obj = [SubscriberList.objects.get(pk=x) for x in lists_ids]
        dispatch.lists = lists_obj
        dispatch.save()
        # send params
        sent = 0
        error_addresses = []
        # templates
        unsubscribe_url_template = template.Template('{% load newsletter_tags %}' + str(campaign.topic.unsubscribe_url)) # noqa
        text_template = template.Template('{% load newsletter_tags %}' + campaign.plain_text) # noqa
        html_template = template.Template('{% load newsletter_tags %}' + campaign.html_text) # noqa
        # email from header
        from_header = "%s <%s>" % (
            campaign.topic.sending_name,
            campaign.topic.sending_address
        )
        for subscriber_list in lists_obj:
            for subscriber in subscriber_list.subscriber_set.all():
                msg = MailerMessage()
                # unsubscribe text
                unsubscribe_url = ''
                if campaign.topic.unsubscribe_url:
                    ctx = Context()
                    ctx.update({'client': campaign.client})
                    ctx.update({'id': subscriber.id})
                    ctx.update({'email': subscriber.email})
                    ctx.update({'subscription_datetime': subscriber.subscription_datetime}) # noqa
                    unsubscribe_url = unsubscribe_url_template.render(ctx)
                # subject and body
                context = Context()
                context.update({'unsubscribe_url': unsubscribe_url})
                context.update(get_campaign_context(campaign))
                context.update({'subscriber_id': subscriber.id})
                context.update({'dispatch_id': dispatch.id})
                msg.app = dispatch.pk
                msg.subject = campaign.subject
                msg.to_address = subscriber.email
                msg.from_address = from_header
                msg.content = text_template.render(context)
                open_tracking = False
                click_tracking = False
                if campaign.html_text is not None and campaign.html_text != u"": # noqa
                    html_content = html_template.render(context)
                    # add tracking image
                    matches = re.match(r'[^\$]*(</body>)[^\$]*', html_content, re.I) # noqa
                    if matches:
                        signer = Signer()
                        s = signer.sign('%s-%s' % (str(dispatch.id), str(subscriber.id))).split(':')[1] # noqa
                        current_site = Site.objects.get_current()
                        tracking_image = '''
                        <img src="%s" />
                        ''' % ''.join([
                            'http://',
                            current_site.domain,
                            reverse('newsletter-email-tracking',
                                    kwargs={
                                        'dispatch_id': dispatch.id,
                                        'subscriber_id': subscriber.id
                                    }),
                            '?s=' + s
                        ])
                        rexp = re.compile(re.escape('</body>'), re.I)
                        html_content = rexp.sub(tracking_image + matches.group(1), html_content) # noqa
                        open_tracking = True

                    if re.match('[^\$]*{% ?link[^\$]*?%}[^\$]*', campaign.html_text): # noqa
                        click_tracking = True
                    msg.html_content = html_content

                try:
                    msg.save()
                    sent += 1
                except:
                    error_addresses.append(subscriber.email)
        dispatch.error = False
        dispatch.success = True
        dispatch.open_statistics = open_tracking
        dispatch.click_statistics = click_tracking
        dispatch.finished_at = timezone.now()
        dispatch.sent = sent
        dispatch.error_recipients = ','.join(error_addresses)
        dispatch.save()
    except:
        dispatch.error = True
        dispatch.success = False
        dispatch.save()

    return sent
