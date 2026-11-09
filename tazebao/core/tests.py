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
