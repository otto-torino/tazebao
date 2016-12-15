from __future__ import unicode_literals
import urllib
import re
import posixpath
from urlparse import urlparse, urlunparse

from django.db import models
from django.conf import settings
from django.contrib.sites.models import Site
from sorl.thumbnail import ImageField
from jsonfield import JSONField

from newsletter.models import Client


class Upload(models.Model):
    client = models.ForeignKey(Client, verbose_name='client')
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
    client = models.ForeignKey(Client, verbose_name='client',
                               blank=True, null=True)
    key = models.CharField('chiave', max_length=10)
    name = models.CharField('nome', max_length=200)
    html = models.TextField()
    last_modified = models.DateTimeField('ultima modifica', auto_now=True)
    created = models.DateTimeField('inserimento', auto_now_add=True)
    template_data = JSONField()
    meta_data = JSONField()

    def __unicode__(self):
        return "%s - %s" % (self.name, self.key)

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
