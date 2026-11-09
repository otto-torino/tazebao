import re
from html import unescape

from django.core import mail
from django.urls import reverse

from mailqueue.models import MailerMessage
from newsletter.models import Dispatch, Subscriber, Tracking
from newsletter.tasks import send_campaign, test_campaign

from .base import NewsletterTestCase


class SendCampaignTest(NewsletterTestCase):
    def setUp(self):
        self.campaign = self.make_campaign()
        second = Subscriber.objects.create(client=self.client_obj, email='second@example.com')
        second.lists.add(self.subscriber_list)

    def test_send_queues_one_message_per_subscriber(self):
        sent = send_campaign([self.subscriber_list.id], self.campaign.id)
        self.assertEqual(sent, 2)
        dispatch = Dispatch.objects.get(campaign=self.campaign)
        self.assertTrue(dispatch.success, dispatch.error_message)
        self.assertFalse(dispatch.error)
        self.assertEqual(dispatch.sent, 2)
        self.assertTrue(dispatch.open_statistics)
        self.assertTrue(dispatch.click_statistics)
        messages = MailerMessage.objects.filter(app=str(dispatch.id))
        self.assertEqual(sorted(m.to_address for m in messages), ['reader@example.com', 'second@example.com'])
        message = messages.get(to_address='reader@example.com')
        self.assertEqual(message.subject, 'Hello')
        self.assertEqual(message.from_address, 'Example News <news@example.com>')
        self.assertEqual(message.content, 'Hello reader@example.com')

    def test_tracking_links_in_sent_message_work(self):
        send_campaign([self.subscriber_list.id], self.campaign.id)
        dispatch = Dispatch.objects.get(campaign=self.campaign)
        html = MailerMessage.objects.get(app=str(dispatch.id), to_address='reader@example.com').html_content

        pixel = re.search(r'<img src="http://[^/]+(/newsletter/tracking/[^"]+)"', html).group(1)
        self.assertEqual(self.client.get(pixel).status_code, 200)

        click = unescape(re.search(r'href="http://[^/]+(/newsletter/tracking/click/[^"]+)"', html).group(1))
        response = self.client.get(click)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], 'https://example.com/page?a=1')

        self.assertEqual(Tracking.objects.filter(dispatch=dispatch, subscriber=self.subscriber).count(), 2)

    def test_test_campaign_sends_immediately(self):
        sent = test_campaign([self.subscriber_list.id], self.campaign.id)
        self.assertEqual(sent, 2)
        dispatch = Dispatch.objects.get(campaign=self.campaign)
        self.assertTrue(dispatch.test)
        self.assertTrue(dispatch.success, dispatch.error_message)
        self.assertEqual(len(mail.outbox), 2)
        self.assertEqual(mail.outbox[0].subject, 'Hello')
        self.assertIn('/newsletter/tracking/', mail.outbox[0].alternatives[0][0])

    def test_view_online_url(self):
        url = self.campaign.get_absolute_url()
        self.assertEqual(url, reverse('newsletter-campaign-detail', args=[
            'client-1', str(self.campaign.insertion_datetime.year),
            self.campaign.insertion_datetime.strftime('%m'),
            self.campaign.insertion_datetime.strftime('%d'), 'campaign']))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Hello', response.content)
