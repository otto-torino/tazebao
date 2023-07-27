"""URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.8/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Add an import:  from blog import urls as blog_urls
    2. Add a URL to urlpatterns:  url(r'^blog/', include(blog_urls))
"""
from baton.autodiscover import admin
from django.conf import settings
from django.contrib.staticfiles.views import serve
from django.urls import include, path, re_path
from django.views import static
from django.views.generic import TemplateView
from rest_framework.routers import DefaultRouter
from rest_framework_jwt.views import obtain_jwt_token, refresh_jwt_token

from core.views.api import WhoAmI
from newsletter.views import (CampaignViewSet, DispatchStatsApiView, DispatchViewSet,
                              FailedEmailApiView, FailedEmailViewSet,
                              ImportSubscribersFromCsv, MailerMessageViewSet,
                              PlanningViewSet, StatsApiView, SubjectSuggestionApiView,
                              SubscriberListViewSet, SubscriberViewSet, SubscriptionFormViewSet, SubscriptionsStatsApiView, SystemMessageViewSet,
                              TopicViewSet)

# BEGIN API
router = DefaultRouter()
router.register(r'newsletter/subscriberlist', SubscriberListViewSet)
router.register(r'newsletter/subscriber', SubscriberViewSet)
router.register(r'newsletter/topic', TopicViewSet)
router.register(r'newsletter/campaign', CampaignViewSet)
router.register(r'newsletter/dispatch', DispatchViewSet)
router.register(r'newsletter/planning', PlanningViewSet)
router.register(r'newsletter/bounces', FailedEmailViewSet)
router.register(r'newsletter/mailermessage', MailerMessageViewSet)
router.register(r'newsletter/subscriptionform', SubscriptionFormViewSet)
router.register(r'newsletter/systemmessages', SystemMessageViewSet)
# END API

urlpatterns = [
    path(r'admin/', admin.site.urls),
    path('baton/', include('baton.urls')),
    path('', TemplateView.as_view(template_name='home.html'), name='home'),
    # newsletter
    path('newsletter/', include('newsletter.urls')),
    # ckeditor uploader
    path('ckeditor/', include('ckeditor_uploader.urls')),
    # captcha
    path('captcha/', include('captcha.urls')),
    # mosaico
    path('mosaico/', include('mosaico.urls')),
    path('export_action/',
         include("export_action.urls", namespace="export_action")),
    # API
    path('api/v1/newsletter/failedemail/',
         FailedEmailApiView.as_view(),
         name='failed-email-api'),
    path('api/v1/login/', obtain_jwt_token),
    path('api/v1/refresh-token/', refresh_jwt_token),
    path('api/v1/whoami/', WhoAmI.as_view()),
    path('api/v1/newsletter/stats/', StatsApiView.as_view()),
    path('api/v1/newsletter/dispatches/stats/', DispatchStatsApiView.as_view()),
    path('api/v1/newsletter/subscriptions/stats/', SubscriptionsStatsApiView.as_view()),
    path('api/v1/newsletter/subscriber/import/',
         ImportSubscribersFromCsv.as_view()),
    path('api/v1/newsletter/suggestions/subject/', SubjectSuggestionApiView.as_view()),
    path('api/v1/', include(router.urls))
]

if settings.DEBUG:
    urlpatterns += [
        re_path(r'^media/(?P<path>.*)$', static.serve,
                {'document_root': settings.MEDIA_ROOT}),
    ]
    urlpatterns += [
        re_path(r'^static/(?P<path>.*)$', serve),
    ]
    # debug toolbar
    import debug_toolbar
    urlpatterns += [
        re_path(r'^__debug__/', include(debug_toolbar.urls)),
    ]
