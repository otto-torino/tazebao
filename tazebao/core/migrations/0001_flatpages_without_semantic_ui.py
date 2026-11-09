"""Rewrite the flatpages markup for the Tailwind based public stylesheet.

The public pages dropped Semantic UI and jQuery: the Semantic UI grid, menu,
message and table classes in the flatpage contents are replaced by the
component classes of core/tailwind/site.css, the jQuery "goto()" links of
the /api/ page become plain anchors. Bootstrap-like classes already used by
the contents (btn, alert, text-right) are kept: site.css defines them.

The previous contents are in the database dump taken before the upgrade
(dbtazebao-pre-django52-20261109.sql.gz): the reverse migration is a no-op.
"""
import re

from django.db import migrations

ICON_RE = re.compile(r'<i class="ui [^"]*icon">(?:&nbsp;|\s)*</i>\s*')
GOTO_RE = re.compile(r"""href="javascript:void\(0\)" onclick="goto\('([^']+)'\)\"""")
GOTO_SCRIPT_RE = re.compile(r'\s*<script>\s*function goto\(hash\).*?</script>\s*', re.S)

REPLACEMENTS = (
    ('<div class="row">', '<div class="cols-2">'),
    ('<div class="col-md-6">', '<div>'),
    ('<div class="ui info message">', '<div class="alert alert-info">'),
    ('<div class="ui warning message">', '<div class="alert alert-warning">'),
    ('<div class="ui two columns stackable grid">', '<div class="api-layout">'),
    ('<div class="ui four wide column">', '<div>'),
    ('<div class="ui twelve wide column">', '<div>'),
    ('<div class="ui vertical menu" id="api-menu" style="width: auto; !important">',
     '<div class="api-menu" id="api-menu">'),
    ('<div class="header">', '<div class="api-menu-header">'),
    ('<div class="menu">', '<div class="api-menu-items">'),
    ('<a class="item" href=', '<a href='),
    ('<div class="item">', '<div>'),
    ('<table border="1" cellpadding="1" cellspacing="1" class="ui celled table">', '<table>'),
)


def convert(content):
    content = ICON_RE.sub('', content)
    content = GOTO_RE.sub(r'href="#\1"', content)
    content = GOTO_SCRIPT_RE.sub('\n', content)
    for old, new in REPLACEMENTS:
        content = content.replace(old, new)
    return content


def forwards(apps, schema_editor):
    FlatPage = apps.get_model('flatpages', 'FlatPage')
    for page in FlatPage.objects.all():
        content = convert(page.content)
        if content != page.content:
            page.content = content
            page.save(update_fields=['content'])


class Migration(migrations.Migration):

    dependencies = [
        ('flatpages', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(forwards, migrations.RunPython.noop),
    ]
