from django.contrib.sites.models import Site

from .templatetags.newsletter_tags import encrypt


def get_campaign_context(campaign, subscriber=None):
    view_online_url = ''.join([
        'http://',
        Site.objects.get_current().domain,
        campaign.get_absolute_url()
    ])

    if (subscriber is not None):
        sig = encrypt({'client': campaign.client}, str(subscriber.id))
        view_online_url += '?subscriber=%s&sig=%s' % (
            subscriber.id,
            sig
        )

    return {
        'id': campaign.pk,
        'view_online_url': view_online_url,
        'domain': Site.objects.get_current().domain
    }
