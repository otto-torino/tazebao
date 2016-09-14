from django.contrib.sites.models import Site


def get_campaign_context(campaign):
    return {
        'view_online_url': campaign.get_absolute_url,
        'site_url': Site.objects.get_current()
    }
