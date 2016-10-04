from django.contrib.sites.models import Site


def get_campaign_context(campaign):
    return {
        'id': campaign.pk,
        'view_online_url': ''.join([
            'http://',
            Site.objects.get_current().domain,
            campaign.get_absolute_url()
        ]),
        'domain': Site.objects.get_current().domain
    }
