import json
import shutil
import tempfile

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings

from mosaico.models import Template, Upload
from newsletter.models import Campaign, Client, Topic

TEMPLATE_DATA = {'type': 'template', 'mainBlocks': {'blocks': []}}
META_DATA = {'template': '/static/mosaico/templates/versafix-1/template-versafix-1.html', 'key': 'abc1234'}


def png_bytes():
    from io import BytesIO
    from PIL import Image
    buf = BytesIO()
    Image.new('RGB', (400, 200), 'red').save(buf, 'PNG')
    return buf.getvalue()


MEDIA_ROOT = tempfile.mkdtemp(prefix='tazebao-test-media-')


@override_settings(MEDIA_ROOT=MEDIA_ROOT)
class MosaicoTest(TestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(MEDIA_ROOT, ignore_errors=True)

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_superuser('admin', 'admin@example.com', 'pwd')
        cls.client_obj = Client.objects.create(
            user=cls.user, name='Client', slug='client', domain='example.com', id_key='key00001', secret_key='s' * 32)
        cls.topic = Topic.objects.create(
            client=cls.client_obj, name='News', sending_address='news@example.com', sending_name='News')

    def setUp(self):
        self.client.force_login(self.user)

    def save_payload(self, **kwargs):
        data = {
            'action': 'save', 'key': 'abc1234', 'name': 'My template', 'html': '<html><body>hi</body></html>',
            'template_data': json.dumps(TEMPLATE_DATA), 'meta_data': json.dumps(META_DATA),
        }
        data.update(kwargs)
        return data

    def test_editor_saves_new_template(self):
        """Regression: creating a template used to call save() with meta_data None."""
        response = self.client.post('/mosaico/template/', self.save_payload())
        self.assertEqual(response.status_code, 201)
        template = Template.objects.get(key='abc1234')
        self.assertEqual(template.template_data, TEMPLATE_DATA)
        self.assertEqual(template.meta_data, dict(META_DATA, name='My template'))

    def test_editor_updates_existing_template(self):
        self.client.post('/mosaico/template/', self.save_payload())
        response = self.client.post('/mosaico/template/', self.save_payload(html='<html>v2</html>'))
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Template.objects.get(key='abc1234').html, '<html>v2</html>')

    def test_template_without_data_has_empty_dicts(self):
        template = Template.objects.create(key='empty', name='Empty', html='')
        template.refresh_from_db()
        self.assertEqual(template.template_data, {})
        self.assertEqual(template.meta_data, {'name': 'Empty'})

    def test_app_saves_template_and_campaign(self):
        token = self.client.post(
            '/api/v1/login/', data=json.dumps({'username': 'admin', 'password': 'pwd'}),
            content_type='application/json').json()['token']
        response = self.client.post('/mosaico/apptemplate/?bearer=%s' % token, self.save_payload(
            key='app0001', topic=str(self.topic.id), subject='Subject', view_online='true'))
        self.assertIn(response.status_code, (200, 201), response.content[:500])
        template = Template.objects.get(key='app0001')
        self.assertEqual(template.template_data, TEMPLATE_DATA)
        self.assertTrue(Campaign.objects.filter(subject='Subject', client=self.client_obj).exists())

    def test_admin_change_form_embeds_json(self):
        template = Template.objects.create(
            key='abc1234', name='My template', html='', template_data=TEMPLATE_DATA, meta_data=META_DATA)
        response = self.client.get('/admin/mosaico/template/%s/change/' % template.id)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'var mosaico_template_data = %s;' % json.dumps(TEMPLATE_DATA))

    def test_upload_and_resize(self):
        image = SimpleUploadedFile('red.png', png_bytes(), content_type='image/png')
        response = self.client.post('/mosaico/upload/', {'files[]': image})
        self.assertEqual(response.status_code, 200, response.content[:300])
        upload = Upload.objects.get()
        response = self.client.get('/mosaico/img/', {
            'src': upload.image.url, 'method': 'resize', 'params': '200,null'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'image/png')
        from io import BytesIO
        from PIL import Image
        self.assertEqual(Image.open(BytesIO(response.content)).size[0], 200)
