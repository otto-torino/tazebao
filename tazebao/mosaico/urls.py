import os

from django.conf import settings
from django.urls import re_path
from django.views.static import serve

from .views import (appeditor, appindex, apptemplate, appupload,  # noqa
                    download, editor, image, index, template, template_content,
                    upload)

app_name = 'mosaico'

urlpatterns = [
    re_path(
        r'^img/social_def/(?P<path>.*)$', serve, {
            'document_root':
            os.path.join(settings.STATIC_ROOT, 'mosaico', 'templates',
                         'versafix-1', 'img', 'social_def')
        }),
]

urlpatterns += [
    re_path(r'^$', index, name="index"),
    re_path(r'^app.html$', appindex, name="app-index"),  # react app
    re_path(r'^editor.html$', editor, name="editor"),
    re_path(r'^appeditor.html$', appeditor, name="appeditor"),  # react app
    re_path(r'^img/$', image),
    re_path(r'^upload/$', upload),
    re_path(r'^appupload/$', appupload),
    re_path(r'^dl/$', download),
    re_path(r'^apptemplate/$', apptemplate),
    re_path(r'^template/$', template),
    re_path(r'^template/content/(?P<template_id>\d+)/?$',
        template_content,
        name='mosaico-template-content'),
]
