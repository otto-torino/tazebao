import os

from django.conf.urls import url
from django.views.static import serve
from django.conf import settings

from .views import index, editor, upload, download, image, template, template_content # noqa

app_name = 'mosaico'

urlpatterns = [
    url(
        r'^img/social_def/(?P<path>.*)$',
        serve,
        {
            'document_root': os.path.join(
                settings.STATIC_ROOT,
                'mosaico',
                'templates',
                'versafix-1',
                'img',
                'social_def'
            )
        }
    ),
]

urlpatterns += [
    url(r'^$', index, name="index"),
    url(r'^editor.html$', editor, name="editor"),
    url(r'^img/$', image),
    url(r'^upload/$', upload),
    url(r'^dl/$', download),
    url(r'^template/$', template),
    url(r'^template/content/(?P<template_id>\d+)/?$',
        template_content,
        name='mosaico-template-content'),
]
