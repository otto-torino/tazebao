from django.core.files.uploadedfile import SimpleUploadedFile

from newsletter.models import Subscriber, SubscriberList

from .base import NewsletterTestCase, hmac_headers

IMPORT_URL = '/api/v1/newsletter/subscriber/import/'


class ImportSubscribersTest(NewsletterTestCase):
    def upload(self, content, lists=None, key=('key00001', 's' * 32)):
        lists = lists if lists is not None else str(self.subscriber_list.id)
        csv_file = SimpleUploadedFile('subscribers.csv', content.encode('utf-8'), content_type='text/csv')
        return self.client.post(IMPORT_URL, data={'file': csv_file, 'lists': lists}, **hmac_headers(*key))

    def test_import(self):
        response = self.upload(
            'new1@example.com,2020-01-01 10:00:00,,0\n'
            'new2@example.com,,{"name": "Bob"},1,2020-01-02 10:00:00\n')
        self.assertEqual(response.status_code, 200, response.content)
        new2 = Subscriber.objects.get(client=self.client_obj, email='new2@example.com')
        self.assertTrue(new2.opt_in)
        self.assertEqual(new2.info, '{"name": "Bob"}')
        self.assertEqual(list(new2.lists.all()), [self.subscriber_list])
        self.assertTrue(Subscriber.objects.filter(email='new1@example.com').exists())

    def test_existing_subscriber_added_to_new_list(self):
        other_list = SubscriberList.objects.create(client=self.client_obj, name='Other')
        response = self.upload('reader@example.com,,,0\n', lists=str(other_list.id))
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(Subscriber.objects.filter(email='reader@example.com').count(), 1)
        self.assertIn(other_list, self.subscriber.lists.all())

    def test_invalid_row_rolls_back(self):
        response = self.upload('ok@example.com,,,0\nnot-an-email,,,0\n')
        self.assertEqual(response.status_code, 400)
        self.assertFalse(Subscriber.objects.filter(email='ok@example.com').exists())

    def test_cannot_import_into_other_client_list(self):
        response = self.upload('x@example.com,,,0\n', key=('key00002', 't' * 32))
        self.assertEqual(response.status_code, 400)
        self.assertFalse(Subscriber.objects.filter(email='x@example.com').exists())


class SubscriberApiTest(NewsletterTestCase):
    def test_list_isolated_per_client(self):
        response = self.client.get('/api/v1/newsletter/subscriber/', **hmac_headers('key00002', 't' * 32))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [])

    def test_cannot_read_other_client_subscriber(self):
        response = self.client.get(
            '/api/v1/newsletter/subscriber/%s/' % self.subscriber.id, **hmac_headers('key00002', 't' * 32))
        self.assertEqual(response.status_code, 404)

    def test_read_own_subscriber(self):
        response = self.client.get(
            '/api/v1/newsletter/subscriber/%s/' % self.subscriber.id, **hmac_headers('key00001', 's' * 32))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['email'], 'reader@example.com')
