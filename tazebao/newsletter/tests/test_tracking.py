import html
from urllib.parse import quote_plus

from django.core.signing import Signer
from django.test import override_settings
from django.urls import reverse
from django.utils import timezone

from newsletter.models import Dispatch, Subscriber, Tracking
from newsletter.templatetags.newsletter_tags import encrypt

from .base import NewsletterTestCase

# Signatures produced by Django 2.2 (Signer with sha1) for SECRET_KEY
# "tazebao-test-secret-key". They are embedded in newsletters that were
# already sent: they must keep working after the upgrade.
LEGACY_IDS = (900001, 900002)
LEGACY_OPEN_SIG = 'wE3h6UZtqIbalFzA5YH_yjk4KQM'
LEGACY_CLICK_URL = 'https://example.com/page?a=1'
LEGACY_CLICK_SIG = 'XZg93wPuoujuaEJyWrZn0rFUoFE'


@override_settings(SECRET_KEY='tazebao-test-secret-key')
class TrackingTest(NewsletterTestCase):
    def setUp(self):
        self.campaign = self.make_campaign()
        self.dispatch = self.make_dispatch(self.campaign)

    def legacy_objects(self):
        dispatch = Dispatch.objects.create(
            id=LEGACY_IDS[0], campaign=self.campaign, started_at=timezone.now(), sent=1)
        subscriber = Subscriber.objects.create(
            id=LEGACY_IDS[1], client=self.client_obj, email='legacy@example.com')
        return dispatch, subscriber

    def open_url(self, dispatch_id, subscriber_id, sig):
        return reverse('newsletter-email-tracking', args=[dispatch_id, subscriber_id]) + '?s=' + sig

    def click_url(self, dispatch_id, subscriber_id, url, sig):
        return (reverse('newsletter-click-tracking', args=[dispatch_id, subscriber_id])
                + '?url=' + url + '&s=' + sig)

    # open tracking pixel

    def test_open_pixel_with_current_signature(self):
        sig = Signer().sign('%s-%s' % (self.dispatch.id, self.subscriber.id)).split(':')[1]
        response = self.client.get(self.open_url(self.dispatch.id, self.subscriber.id, sig))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'image/gif')
        self.assertEqual(Tracking.objects.filter(
            dispatch=self.dispatch, subscriber=self.subscriber, type=Tracking.OPEN_TYPE).count(), 1)

    def test_open_pixel_counts_once(self):
        sig = Signer().sign('%s-%s' % (self.dispatch.id, self.subscriber.id)).split(':')[1]
        url = self.open_url(self.dispatch.id, self.subscriber.id, sig)
        self.client.get(url)
        self.client.get(url)
        self.assertEqual(Tracking.objects.filter(type=Tracking.OPEN_TYPE).count(), 1)

    def test_open_pixel_with_legacy_sha1_signature(self):
        dispatch, subscriber = self.legacy_objects()
        response = self.client.get(self.open_url(dispatch.id, subscriber.id, LEGACY_OPEN_SIG))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Tracking.objects.filter(dispatch=dispatch, subscriber=subscriber).exists())

    def test_open_pixel_bad_signature(self):
        response = self.client.get(self.open_url(self.dispatch.id, self.subscriber.id, 'forged'))
        self.assertEqual(response.status_code, 404)
        self.assertFalse(Tracking.objects.exists())

    # click tracking

    def test_click_with_current_signature(self):
        url = 'https://example.com/page?a=1'
        sig = Signer().sign('%s-%s-%s' % (self.dispatch.id, self.subscriber.id, url)).rsplit(':', 1)[1]
        response = self.client.get(self.click_url(self.dispatch.id, self.subscriber.id, url, sig))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], url)
        tracking = Tracking.objects.get(type=Tracking.CLICK_TYPE)
        self.assertEqual(tracking.notes, url)

    def test_click_with_legacy_sha1_signature(self):
        dispatch, subscriber = self.legacy_objects()
        response = self.client.get(self.click_url(dispatch.id, subscriber.id, LEGACY_CLICK_URL, LEGACY_CLICK_SIG))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], LEGACY_CLICK_URL)

    def test_click_bad_signature(self):
        response = self.client.get(
            self.click_url(self.dispatch.id, self.subscriber.id, 'https://evil.example.com/', 'forged'))
        self.assertEqual(response.status_code, 404)

    def render_link(self):
        from django import template
        tpl = template.Template('{% load newsletter_tags %}{% link "https://example.com/page?a=1" %}')
        rendered = tpl.render(template.Context({
            'dispatch_id': self.dispatch.id, 'subscriber_id': self.subscriber.id}))
        return rendered.split('example.com', 1)[1]  # strip scheme and site domain

    def test_link_tag_round_trip_html(self):
        """In an HTML href the mail client decodes &amp; to &."""
        response = self.client.get(html.unescape(self.render_link()))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], 'https://example.com/page?a=1')

    def test_link_tag_round_trip_plain_text(self):
        """In the plain text part the link keeps the literal "&amp;s="."""
        path = self.render_link()
        self.assertIn('&amp;s=', path)
        response = self.client.get(path)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], 'https://example.com/page?a=1')


class UnsubscribeTest(NewsletterTestCase):
    def test_unsubscribe_with_valid_signature(self):
        sid = self.subscriber.id
        sig = encrypt({'client': self.client_obj}, str(sid) + self.subscriber.email)
        response = self.client.get(
            reverse('newsletter-unsubscribe') + '?id=%s&email=%s&sig=%s' % (sid, quote_plus(self.subscriber.email), sig))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Subscriber.objects.filter(id=sid).exists())

    def test_unsubscribe_bad_signature(self):
        response = self.client.get(
            reverse('newsletter-unsubscribe') + '?id=%s&email=%s&sig=forged' % (self.subscriber.id, self.subscriber.email))
        self.assertEqual(response.status_code, 404)
        self.assertTrue(Subscriber.objects.filter(id=self.subscriber.id).exists())

    def test_encrypt_is_stable(self):
        """HMAC-sha256 of the client secret: used in unsubscribe URLs already sent."""
        sig = encrypt({'client': self.client_obj}, '42', 'reader@example.com')
        self.assertEqual(sig, quote_plus('7If8FvmnD+DJR8UVrSxBeyokjOgzpJ5oqbx8lzoi054='))
