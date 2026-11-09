import json
from datetime import datetime, timedelta

from django.test import override_settings
from django.utils import timezone

from newsletter.models import FailedEmail

from .base import NewsletterTestCase, hmac_headers

LISTS_URL = '/api/v1/newsletter/subscriberlist/'
BOUNCE_URL = '/api/v1/newsletter/failedemail/'


class ClientHmacAuthTest(NewsletterTestCase):
    def test_valid_signature(self):
        response = self.client.get(LISTS_URL, **hmac_headers('key00001', 's' * 32))
        self.assertEqual(response.status_code, 200)
        self.assertEqual([item['name'] for item in response.json()], ['Main'])

    def test_sees_only_own_data(self):
        response = self.client.get(LISTS_URL, **hmac_headers('key00002', 't' * 32))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [])

    def test_create_assigns_client(self):
        response = self.client.post(
            LISTS_URL, data=json.dumps({'name': 'New list'}), content_type='application/json',
            **hmac_headers('key00001', 's' * 32))
        self.assertEqual(response.status_code, 201)
        self.assertEqual(self.client_obj.subscriberlist_set.filter(name='New list').count(), 1)

    def test_wrong_secret(self):
        response = self.client.get(LISTS_URL, **hmac_headers('key00001', 'wrong'))
        self.assertEqual(response.status_code, 401)

    def test_unknown_key(self):
        response = self.client.get(LISTS_URL, **hmac_headers('nokey000', 's' * 32))
        self.assertEqual(response.status_code, 401)

    def test_signature_for_other_date(self):
        headers = hmac_headers('key00001', 's' * 32)
        headers['HTTP_DATE'] = 'Tue, 10 Nov 2026 10:00:00 GMT'
        response = self.client.get(LISTS_URL, **headers)
        self.assertEqual(response.status_code, 401)

    def test_no_credentials(self):
        response = self.client.get(LISTS_URL)
        self.assertEqual(response.status_code, 401)


@override_settings(POSTFIX_CLIENT_ID='postfix-id', POSTFIX_CLIENT_SECRET='postfix-secret')
class PostfixBounceTest(NewsletterTestCase):
    def setUp(self):
        self.campaign = self.make_campaign()
        self.dispatch = self.make_dispatch(self.campaign, finished_at=timezone.now() - timedelta(hours=1))

    def payload(self, **kwargs):
        data = {
            'datetime': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'from_email': 'news@example.com',
            'email': 'reader@example.com',
            'status': 'bounced',
            'message': '550 5.1.1 user unknown',
            'email_id': 'ABC123',
        }
        data.update(kwargs)
        return json.dumps(data)

    def post(self, body, headers):
        return self.client.post(BOUNCE_URL, data=body, content_type='application/json', **headers)

    def test_valid_bounce(self):
        response = self.post(self.payload(), hmac_headers('postfix-id', 'postfix-secret'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b'failed email correctly inserted')
        failed = FailedEmail.objects.get(email_id='ABC123')
        self.assertEqual(failed.client, self.client_obj)
        self.assertEqual(failed.subscriber, self.subscriber)
        self.assertEqual(failed.dispatch, self.dispatch)
        self.assertEqual(failed.status, 'bounced')

    def test_missing_field(self):
        response = self.post(json.dumps({'from_email': 'news@example.com'}), hmac_headers('postfix-id', 'postfix-secret'))
        self.assertEqual(response.status_code, 400)

    def test_client_credentials_are_not_postfix(self):
        response = self.post(self.payload(), hmac_headers('key00001', 's' * 32))
        self.assertEqual(response.status_code, 403)
        self.assertFalse(FailedEmail.objects.exists())

    def test_bad_signature(self):
        response = self.post(self.payload(), hmac_headers('postfix-id', 'wrong'))
        self.assertEqual(response.status_code, 403)
        self.assertFalse(FailedEmail.objects.exists())

    def test_no_signature(self):
        response = self.post(self.payload(), {})
        self.assertEqual(response.status_code, 403)
        self.assertFalse(FailedEmail.objects.exists())
