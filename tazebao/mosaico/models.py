from __future__ import unicode_literals
import json

import posixpath
import re
import urllib
from urllib.parse import urlparse, urlunparse

from django.conf import settings
from django.contrib.sites.models import Site
from django.db import models
from jsonfield import JSONField
from sorl.thumbnail import ImageField

from newsletter.models import Campaign, Client


class Upload(models.Model):
    client = models.ForeignKey(
        Client, verbose_name='client', on_delete=models.CASCADE)
    name = models.CharField('nome', max_length=200)
    image = ImageField('immagine', upload_to="uploads")

    def __unicode__(self):
        return posixpath.basename(self.image.name)

    def to_json_data(self):
        url = self.image.url
        parts = urlparse(url)
        if parts.netloc == '':
            newparts = list(parts)
            domain = Site.objects.get_current().domain
            newparts[0] = 'https' if settings.HTTPS else 'http'
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
    client = models.ForeignKey(
        Client,
        verbose_name='client',
        blank=True,
        null=True,
        on_delete=models.SET_NULL)
    campaign = models.OneToOneField(
        Campaign,
        verbose_name='campagna',
        on_delete=models.CASCADE,
        blank=True,
        null=True)
    key = models.CharField('chiave', max_length=10)
    name = models.CharField('nome', max_length=200)
    html = models.TextField()
    last_modified = models.DateTimeField('ultima modifica', auto_now=True)
    created = models.DateTimeField('inserimento', auto_now_add=True)
    template_data = JSONField()
    meta_data = JSONField()

    def __unicode__(self):
        return "%s - %s" % (self.name, self.key)

    def meta_data_json(self):
        return json.dumps(self.meta_data)

    def template_data_json(self):
        return json.dumps(self.template_data)

    def save(self, *args, **kwargs):
        self.meta_data['name'] = self.name
        """
        uncomment this if you want to have images served directly as static
        files from media folder. The drawback is images are not resized on
        the fly if served statically, causing rendering problems on some
        clients
        if settings.HTTPS:
            def url_fixer(m):
                url = urllib.unquote(m.group(1))
                return re.sub(r'&.*', '', url)
            site = Site.objects.get_current()
            regexp = r"https://" + re.escape(site.domain) + r"/mosaico/img/\?src=([^'\"]*)" # noqa
            self.html = re.sub(regexp, url_fixer, self.html)
        """
        super(Template, self).save(*args, **kwargs)
