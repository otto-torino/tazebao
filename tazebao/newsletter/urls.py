from django.urls import path

from .views import (campaign_detail_view, email_tracking, link_tracking, subscription_form_standalone,
                    unsubscribe)

urlpatterns = [
    path(
        '<slug:client_slug>/<int:year>/<int:month>/<int:day>/<slug:campaign_slug>/',  # noqa
        campaign_detail_view,
        name='newsletter-campaign-detail'),
    path(
        'tracking/click/<int:dispatch_id>/<int:subscriber_id>/',
        link_tracking,
        name='newsletter-click-tracking'),
    path(
        'tracking/<int:dispatch_id>/<int:subscriber_id>/',
        email_tracking,
        name='newsletter-email-tracking'),
    path('unsubscribe/', unsubscribe, name='newsletter-unsubscribe'),
    path('subscribe/<uuid:code>/', subscription_form_standalone, name='newsletter-subscription-form-standalone'),
]
