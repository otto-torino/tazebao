from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.test import TestCase
from django.urls import reverse

from newsletter.models import Client, Subscriber


class AdminSmokeTest(TestCase):
    """Every admin page must render: catches template/baton/static breakage."""

    @classmethod
    def setUpTestData(cls):
        cls.admin_user = User.objects.create_superuser('admin', 'admin@example.com', 'pwd')
        client = Client.objects.create(
            user=cls.admin_user, name='Admin client', slug='admin-client', domain='example.com',
            id_key='key00009', secret_key='a' * 32)
        cls.subscriber = Subscriber.objects.create(client=client, email='reader@example.com')

    def setUp(self):
        self.client.force_login(self.admin_user)

    def test_index(self):
        response = self.client.get(reverse('admin:index'))
        self.assertEqual(response.status_code, 200)

    def test_changelists_and_add_forms(self):
        for model in admin.site._registry:
            opts = model._meta
            with self.subTest(model=opts.label):
                response = self.client.get(reverse('admin:%s_%s_changelist' % (opts.app_label, opts.model_name)))
                self.assertEqual(response.status_code, 200)

    def test_change_form(self):
        response = self.client.get(reverse('admin:newsletter_subscriber_change', args=[self.subscriber.id]))
        self.assertEqual(response.status_code, 200)

    def test_mosaico_pages(self):
        for url in ('/mosaico/', '/mosaico/editor.html'):
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 200)

    def test_export_csv(self):
        ct = ContentType.objects.get_for_model(Subscriber)
        url = reverse('export_action:export') + '?ct=%s&ids=%s' % (ct.id, self.subscriber.id)
        self.assertEqual(self.client.get(url).status_code, 200)
        response = self.client.post(url, {'email': 'on', '__format': 'csv'})
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'reader@example.com', response.content)

    def test_export_xlsx(self):
        ct = ContentType.objects.get_for_model(Subscriber)
        url = reverse('export_action:export') + '?ct=%s&ids=%s' % (ct.id, self.subscriber.id)
        response = self.client.post(url, {'email': 'on', '__format': 'xlsx'})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.content.startswith(b'PK'))  # zip container


class StaticReferencesTest(TestCase):
    """Every {% static %} file used by templates must exist: with the manifest
    storage a missing file is a 500 (e.g. the home page and public newsletter pages)."""

    def test_static_files_exist(self):
        import re
        from pathlib import Path

        from django.conf import settings
        from django.contrib.staticfiles import finders

        pattern = re.compile(r"""\{%\s*static\s+['"]([^'"]+)['"]""")
        missing = []
        for template in Path(settings.BASE_DIR).glob('*/templates/**/*.html'):
            for path in pattern.findall(template.read_text(encoding='utf-8')):
                if path.endswith('/'):  # directories are not hashed by the storage
                    continue
                if not finders.find(path):
                    missing.append('%s: %s' % (template.relative_to(settings.BASE_DIR), path))
        self.assertEqual(missing, [])

    def test_public_pages_render(self):
        self.assertEqual(self.client.get('/').status_code, 200)


class FlatpagesMigrationTest(TestCase):
    """core.0001 rewrites the Semantic UI / jQuery markup of the flatpages."""

    API_SAMPLE = (
        '<div class="ui info message"><i class="ui info circle icon">&nbsp;</i> <strong>In aggiornamento</strong></div>\n'
        '<div class="ui two columns stackable grid">\n<div class="ui four wide column">\n'
        '<div class="ui vertical menu" id="api-menu" style="width: auto; !important">\n<div class="item">\n'
        '<div class="header"><a href="javascript:void(0)" onclick="goto(\'iscritti\')">Iscritti</a></div>\n'
        '<div class="menu"><a class="item" href="javascript:void(0)" onclick="goto(\'iscritti-lista\')">Lista</a></div>\n'
        '</div>\n</div>\n</div>\n<div class="ui twelve wide column">\n'
        '<table border="1" cellpadding="1" cellspacing="1" class="ui celled table"><tr><td>q</td></tr></table>\n'
        '</div>\n</div>\n<script>\nfunction goto(hash) {\n  location.hash = \'#\' + hash;\n'
        '  $(\'#api-menu .item\').removeClass(\'active\');\n}\n\n</script>'
    )

    def convert(self, content):
        import importlib
        return importlib.import_module('core.migrations.0001_flatpages_without_semantic_ui').convert(content)

    def test_api_page(self):
        html = self.convert(self.API_SAMPLE)
        for gone in ('class="ui', 'goto(', 'javascript:void', '$(', '<script', '<i '):
            self.assertNotIn(gone, html)
        self.assertIn('<div class="alert alert-info"><strong>In aggiornamento</strong></div>', html)
        self.assertIn('<div class="api-layout">', html)
        self.assertIn('<div class="api-menu-header"><a href="#iscritti">Iscritti</a></div>', html)
        self.assertIn('<div class="api-menu-items"><a href="#iscritti-lista">Lista</a></div>', html)
        self.assertIn('<table><tr>', html)

    def test_help_page_and_idempotency(self):
        html = self.convert('<div class="row">\n<div class="col-md-6">x</div>\n</div>'
                            '<p class="text-right"><a class="btn btn-success" href="/help/">Indice</a></p>')
        self.assertEqual(html, '<div class="cols-2">\n<div>x</div>\n</div>'
                               '<p class="text-right"><a class="btn btn-success" href="/help/">Indice</a></p>')
        self.assertEqual(self.convert(html), html)


class PublicPagesTest(TestCase):
    def test_no_jquery_nor_semantic_ui(self):
        for url in ('/',):
            html = self.client.get(url).content.decode()
            for gone in ('jquery', 'semantic', 'class="ui ', 'core.Modal'):
                self.assertNotIn(gone, html.lower() if gone != 'class="ui ' else html)
            self.assertIn('core/css/site.css', html)

    def test_flatpage(self):
        from django.contrib.flatpages.models import FlatPage
        from django.contrib.sites.models import Site
        page = FlatPage.objects.create(url='/api/', title='API Rest', content='<div class="api-layout">doc</div>')
        page.sites.add(Site.objects.get_current())
        response = self.client.get('/api/')
        self.assertContains(response, '<h1 class="text-4xl">API Rest</h1>', html=False)
        self.assertContains(response, '<div class="api-layout">doc</div>')


class SubscriptionFormPageTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        from newsletter.models import Client, SubscriberList, SubscriptionForm
        user = User.objects.create_user('client', 'client@example.com', 'pwd')
        client = Client.objects.create(user=user, name='C', slug='c', domain='example.com', id_key='key00007', secret_key='k' * 32)
        cls.subscriber_list = SubscriberList.objects.create(client=client, name='L')
        cls.form = SubscriptionForm.objects.create(
            client=client, name='Form', content='<p>Iscriviti!</p>', privacy_disclaimer='Accetto la <b>privacy</b>')
        cls.form.lists.add(cls.subscriber_list)
        cls.url = '/newsletter/subscribe/%s/' % cls.form.code

    def test_get(self):
        response = self.client.get(self.url)
        self.assertContains(response, '<p>Iscriviti!</p>')
        self.assertContains(response, 'Accetto la <b>privacy</b>')
        self.assertNotContains(response, '<dialog')

    def test_subscribe(self):
        response = self.client.post(self.url, {
            'email': 'new@example.com', 'opt_in': 'on', 'captcha_0': 'x', 'captcha_1': 'PASSED'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '<dialog id="messages-dialog"')
        self.assertContains(response, 'avvenuta con successo')
        self.assertTrue(self.subscriber_list.subscriber_set.filter(email='new@example.com').exists())

    def test_privacy_required(self):
        response = self.client.post(self.url, {'email': 'new@example.com', 'captcha_0': 'x', 'captcha_1': 'PASSED'})
        self.assertContains(response, 'alert-error')
        self.assertFalse(self.subscriber_list.subscriber_set.exists())


class FlatpagesExamplesMigrationTest(TestCase):
    """core.0002 replaces the dead rawgit iframes with local static copies."""

    def test_rawgit_iframes(self):
        import importlib
        import re

        from django.contrib.staticfiles import finders
        convert = importlib.import_module('core.migrations.0002_flatpages_examples_without_rawgit').convert
        html = convert(
            '<p><iframe frameborder="0" src="https://cdn.rawgit.com/abidibo/1429d3225631bd6d6043591e843d7847/raw/'
            'ca7cd40bcc8e320b88bb65f120748113ddfe50cf/tazebao-campaign-template-1.html" style="width:100%"></iframe></p>')
        self.assertEqual(html, '<p><iframe frameborder="0" sandbox="" src="/static/core/help/examples/'
                               'tazebao-campaign-template-1.html" style="width:100%"></iframe></p>')
        self.assertEqual(convert(html), html)
        for name in ('tazebao-campaign-template-1.html', 'tazebao-campaign-template-1-mobile.html',
                     'tazebao-campaign-template-2.html'):
            path = finders.find('core/help/examples/' + name)
            self.assertTrue(path, name)
            content = open(path, encoding='utf-8').read()
            self.assertNotIn('http://lorempixel', content)
            self.assertFalse(re.search(r'<script', content, re.I))


class DispatchAdminChartsTest(TestCase):
    def test_charts_without_highcharts(self):
        from django.utils import timezone
        from newsletter.models import Campaign, Client, Dispatch, Topic
        user = User.objects.create_superuser('admin', 'admin@example.com', 'pwd')
        client = Client.objects.create(user=user, name='C', slug='c', domain='example.com', id_key='key00008', secret_key='q' * 32)
        topic = Topic.objects.create(client=client, name='T', sending_address='t@example.com', sending_name='T')
        campaign = Campaign.objects.create(client=client, name='C', slug='c', topic=topic, subject='S', plain_text='x', html_text='x')
        dispatch = Dispatch.objects.create(campaign=campaign, started_at=timezone.now(), sent=4,
                                           open_statistics=True, click_statistics=True)
        self.client.force_login(user)
        response = self.client.get(reverse('admin:newsletter_dispatch_change', args=[dispatch.id]))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'highcharts')
        self.assertContains(response, 'id="open-chart"')
        self.assertContains(response, 'id="click-chart"')
        self.assertContains(response, "['E-mail aperte', 0.0]")
