import base64
import hmac
import hashlib
import urllib

from django import template
from django.core.urlresolvers import reverse
from django.contrib.sites.models import Site

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
    return ''.join([
        'http',
        Site.objects.get_current(),
        reverse('newsletter-click-tracking',
                args=[
                    context['dispatch_id'],
                    context['subscriber_id']
                ]) + '?url=' + url
        ])
