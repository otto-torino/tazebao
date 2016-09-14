from django.conf.urls import url
from .views import campaign_detail_view

urlpatterns = [
    url(r'^(?P<client_slug>[-\w\d]+)/(?P<year>\d{4})/(?P<month>\d{2})/(?P<day>\d{2})/(?P<campaign_slug>[-\w\d]+)/$', # noqa
        campaign_detail_view,
        name='newsletter-campaign-detail'),
]
