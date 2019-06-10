import base64
import hashlib
import hmac
from urllib.parse import quote_plus

from django import template
from django.contrib.sites.models import Site
from django.core.signing import Signer
from django.urls import reverse

from ..models import Dispatch, Subscriber, SubscriberList, Tracking

register = template.Library()


@register.inclusion_tag('admin/dashboard.html')
def dashboard(client):
    THRESHOLD = 20

    dispatches = Dispatch.objects.filter(
        campaign__client=client, error=False,
        sent__gt=THRESHOLD).order_by('-started_at')
    last_dispatches = dispatches[:4]
    lists = SubscriberList.objects.filter(client=client)
    tot_subscribers = Subscriber.objects.filter(client=client).count()
    opening_data = []
    click_data = []
    for d in dispatches:
        opening_data.append({
            'name': d.campaign.name,
            'dt':
            d.started_at,
            'num':
            Tracking.objects.filter(dispatch=d,
                                    type=Tracking.OPEN_TYPE).count()
        })
        click_data.append({
            'name': d.campaign.name,
            'dt':
            d.started_at,
            'num':
            Tracking.objects.filter(dispatch=d,
                                    type=Tracking.CLICK_TYPE).count()
        })
    return {
        'client': client,
        'last_dispatches': last_dispatches,
        'dispatches': dispatches,
        'lists': lists,
        'tot_subscribers': tot_subscribers,
        'opening_data': opening_data,
        'click_data': click_data,
        'threshold': THRESHOLD,
    }


@register.simple_tag(takes_context=True)
def encrypt(context, *args):
    try:
        bs = ''.join([str(x) for x in args]).encode('utf-8')
        dig = hmac.new(
            bytes(context['client'].secret_key, 'latin-1'), bs,
            digestmod=hashlib.sha256).digest()
        signature = base64.b64encode(dig).decode()
        return quote_plus(signature)
    except:
        return ''


@register.simple_tag(takes_context=True)
def link(context, url):
    ''' Returns a wrapped link if subscriber_id and dispatch_id
        are present in the context, otherwise returns the given url
    '''
    if 'dispatch_id' not in context or 'subscriber_id' not in context:
        return url

    current_site = Site.objects.get_current()

    signer = Signer()
    s = signer.sign('%s-%s-%s' % (str(context['dispatch_id']),
                                  str(context['subscriber_id']), url)).rsplit(
                                      ':', 1)[1]
    return ''.join([
        'http://', current_site.domain,
        reverse(
            'newsletter-click-tracking',
            args=[context['dispatch_id'], context['subscriber_id']]),
        '?url=' + url, '&s=' + s
    ])
