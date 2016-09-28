import base64
import hmac
import hashlib
import urllib

from django import template
from django.core.urlresolvers import reverse
from django.contrib.sites.models import Site
from django.core.signing import Signer

register = template.Library()


@register.simple_tag(takes_context=True)
def encrypt(context, *args):
    bs = ''.join([str(x) for x in args])
    dig = hmac.new(
        str(context['client'].secret_key),
        bs,
        digestmod=hashlib.sha256).digest()
    signature = base64.b64encode(dig).decode()
    return urllib.quote_plus(signature)


@register.simple_tag(takes_context=True)
def link(context, url):
    ''' Returns a wrapped link if subscriber_id and dispatch_id
        are present in the context, otherwise returns the given url
    '''
    if 'dispatch_id' not in context or 'subscriber_id' not in context:
        return url

    current_site = Site.objects.get_current()

    signer = Signer()
    s = signer.sign('%s-%s' % (str(context['dispatch_id']), str(context['subscriber_id']))).split(':')[1] # noqa
    return ''.join([
        'http://',
        current_site.domain,
        reverse('newsletter-click-tracking',
                args=[
                    context['dispatch_id'],
                    context['subscriber_id']
                ]),
        '?url=' + url,
        '&s=' + s
        ])
