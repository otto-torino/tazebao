from __future__ import unicode_literals
import posixpath
from urlparse import urlparse, urlunparse

from django.db import models
from django.contrib.sites.models import Site
from sorl.thumbnail import ImageField
from jsonfield import JSONField

from newsletter.models import Client


class Upload(models.Model):
    client = models.ForeignKey(Client, verbose_name='client')
    name = models.CharField(max_length=200)
    image = ImageField(upload_to="uploads")

    def __unicode__(self):
        return posixpath.basename(self.image.name)

    def to_json_data(self):
        url = self.image.url
        parts = urlparse(url)
        if parts.netloc == '':
            newparts = list(parts)
            domain = Site.objects.get_current().domain
            newparts[0] = 'http'
            newparts[1] = domain
            url = urlunparse(newparts)
        data = {
            'deleteType': 'DELETE',
            'deleteUrl': url,
            'name': posixpath.basename(self.image.name),
            'originalName': posixpath.basename(self.name),
            'size': self.image.size,
            'thumbnailUrl': url,
            'type': None,
            'url': url,
        }
        return data


class Template(models.Model):
    client = models.ForeignKey(Client, verbose_name='client')
    key = models.CharField('chiave', max_length=10)
    name = models.CharField('nome', max_length=200)
    html = models.TextField()
    last_modified = models.DateTimeField('ultima modifica', auto_now=True)
    created = models.DateTimeField('inserimento', auto_now_add=True)
    template_data = JSONField()
    meta_data = JSONField()

    def __unicode__(self):
        return "%s - %s" % (self.name, self.key)