"""Shared fixtures for the newsletter test suite.

These tests pin the behaviour seen by external clients (HMAC and JWT API
users, the Postfix bounce script, recipients clicking links in e-mails
already sent) so that it survives the Django/DRF upgrade unchanged.
"""
import base64
import hashlib
import hmac

from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone

from newsletter.models import Campaign, Client, Dispatch, Subscriber, SubscriberList, Topic

PASSWORD = 'secret-password'
HTTP_DATE = 'Mon, 09 Nov 2026 10:00:00 GMT'


def hmac_signature(secret, date=HTTP_DATE):
    """Signature as documented in README: Base64(Hmac(SECRET, "date: DATE", sha256)).

    Deliberately written without the httpsig library, the way a client does it.
    """
    digest = hmac.new(secret.encode('utf-8'), ('date: %s' % date).encode('utf-8'), hashlib.sha256).digest()
    return base64.b64encode(digest).decode('ascii')


def hmac_headers(key_id, secret, date=HTTP_DATE, signature=None):
    """Django test client kwargs for an HMAC signed request."""
    if signature is None:
        signature = hmac_signature(secret, date)
    return {
        'HTTP_DATE': date,
        'HTTP_X_API_KEY': key_id,
        'HTTP_AUTHORIZATION': 'Signature keyId="%s",algorithm="hmac-sha256",headers="date",signature="%s"' % (
            key_id, signature),
    }


class NewsletterTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user('client1', 'client1@example.com', PASSWORD)
        cls.client_obj = Client.objects.create(
            user=cls.user, name='Client 1', slug='client-1', domain='example.com',
            id_key='key00001', secret_key='s' * 32)
        cls.other_user = User.objects.create_user('client2', 'client2@example.com', PASSWORD)
        cls.other_client = Client.objects.create(
            user=cls.other_user, name='Client 2', slug='client-2', domain='example.org',
            id_key='key00002', secret_key='t' * 32)
        cls.topic = Topic.objects.create(
            client=cls.client_obj, name='News', sending_address='news@example.com',
            sending_name='Example News')
        cls.subscriber_list = SubscriberList.objects.create(client=cls.client_obj, name='Main')
        cls.subscriber = Subscriber.objects.create(client=cls.client_obj, email='reader@example.com')
        cls.subscriber.lists.add(cls.subscriber_list)

    def make_campaign(self, **kwargs):
        defaults = dict(
            client=self.client_obj, name='Campaign', slug='campaign', topic=self.topic,
            subject='Hello', plain_text='Hello {{ email }}',
            html_text='<html><body><p>Hello</p><a href="{% link "https://example.com/page?a=1" %}">x</a></body></html>')
        defaults.update(kwargs)
        return Campaign.objects.create(**defaults)

    def make_dispatch(self, campaign, **kwargs):
        defaults = dict(campaign=campaign, started_at=timezone.now(), success=True, sent=1)
        defaults.update(kwargs)
        return Dispatch.objects.create(**defaults)
