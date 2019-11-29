import os

from django.conf import settings
from django.conf.urls import url
from django.views.static import serve

from .views import (appeditor, appindex, apptemplate, appupload,  # noqa
                    download, editor, image, index, template, template_content,
                    upload)

app_name = 'mosaico'

urlpatterns = [
    url(
        r'^img/social_def/(?P<path>.*)$', serve, {
            'document_root':
            os.path.join(settings.STATIC_ROOT, 'mosaico', 'templates',
                         'versafix-1', 'img', 'social_def')
        }),
]

urlpatterns += [
    url(r'^$', index, name="index"),
    url(r'^app.html$', appindex, name="app-index"),  # react app
    url(r'^editor.html$', editor, name="editor"),
    url(r'^appeditor.html$', appeditor, name="appeditor"),  # react app
    url(r'^img/$', image),
    url(r'^upload/$', upload),
    url(r'^appupload/$', appupload),
    url(r'^dl/$', download),
    url(r'^apptemplate/$', apptemplate),
    url(r'^template/$', template),
    url(r'^template/content/(?P<template_id>\d+)/?$',
        template_content,
        name='mosaico-template-content'),
]
