"""Point the example previews of the /help/esempi/ flatpages to local copies.

The previews were iframes on cdn.rawgit.com, a service shut down years ago.
The same gist revisions are now static files (core/static/core/help/examples/),
with the dead lorempixel.com images replaced by the mosaico placeholders.
The iframes get the sandbox attribute: the examples are plain HTML e-mails.
The gist embeds showing the source code (gist.github.com) still work.
"""
import re

from django.db import migrations

RAWGIT_IFRAME_RE = re.compile(
    r'<iframe([^>]*?) src="https://cdn\.rawgit\.com/abidibo/[0-9a-f]+/raw/[0-9a-f]+/([\w.-]+\.html)"')


def convert(content):
    return RAWGIT_IFRAME_RE.sub(r'<iframe\1 sandbox="" src="/static/core/help/examples/\2"', content)


def forwards(apps, schema_editor):
    FlatPage = apps.get_model('flatpages', 'FlatPage')
    for page in FlatPage.objects.filter(content__contains='cdn.rawgit.com'):
        content = convert(page.content)
        if content != page.content:
            page.content = content
            page.save(update_fields=['content'])


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_flatpages_without_semantic_ui'),
    ]

    operations = [
        migrations.RunPython(forwards, migrations.RunPython.noop),
    ]
