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
from django.conf.urls import include, url
from django.contrib import admin
from django.conf import settings
from django.views.static import serve
from django.contrib.staticfiles import views as staticfiles_views
from django.views.generic import TemplateView

from rest_framework.routers import DefaultRouter

from newsletter.views import SubscriberListViewSet, SubscriberViewSet
from newsletter.views import CampaignViewSet

admin.site.site_header = 'Tazebao'
admin.site.site_title = 'Tazebao'

# BEGIN API
router = DefaultRouter()
router.register(r'newsletter/subscriberlist', SubscriberListViewSet)
router.register(r'newsletter/subscriber', SubscriberViewSet)
router.register(r'newsletter/campaign', CampaignViewSet)
# END API

urlpatterns = [
    url(r'^admin/', include(admin.site.urls)),
    url(r'^$', TemplateView.as_view(template_name='home.html'), name='home'),
    # newsletter
    url(r'^newsletter/', include('newsletter.urls')),
    # ckeditor uploader
    url(r'^ckeditor/', include('ckeditor_uploader.urls')),
    # mosaico
    url(r'^mosaico/', include('mosaico.urls')),
    # API
    url(r'^api/v1/', include(router.urls))

]

if settings.DEBUG:
    urlpatterns += [
        url(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}), # noqa
    ]
    urlpatterns += [
        url(r'^static/(?P<path>.*)$', staticfiles_views.serve),
    ]
