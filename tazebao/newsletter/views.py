import urllib

from django import template, http
from django.shortcuts import get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect
from django.core.signing import Signer

from rest_framework import viewsets
from rest_framework.pagination import PageNumberPagination

from .models import Campaign, SubscriberList, Subscriber, Tracking, Dispatch
from .serializers import SubscriberListSerializer, SubscriberSerializer, CampaignSerializer # noqa
from .context import get_campaign_context
from .permissions import IsClient
from .templatetags.newsletter_tags import encrypt


def campaign_detail_view(request, client_slug,
                         year, month, day, campaign_slug):
    """ View online the campaign
        only the campaign user can see this if view_online is False
    """

    campaign = get_object_or_404(
        Campaign,
        client__slug=client_slug,
        insertion_datetime__year=year,
        insertion_datetime__month=month,
        insertion_datetime__day=day,
        slug=campaign_slug
    )

    if request.user == campaign.client.user or campaign.view_online:

        subscriber = None
        dispatch = None
        unsubscribe_url = ''
        if request.GET.get('subscriber', False) and request.GET.get('dispatch', False) and request.GET.get('sig', False): # noqa
            sig = request.GET['sig']
            signature = urllib.unquote(
                encrypt({'client': campaign.client}, str(request.GET['subscriber']) + str(request.GET['dispatch'])) # noqa
            )
            if (sig == signature):
                subscriber = Subscriber.objects.get(id=int(request.GET['subscriber'])) # noqa
                dispatch = Dispatch.objects.get(id=int(request.GET['dispatch'])) # noqa

                unsubscribe_url_template = template.Template(
                    '{% load newsletter_tags %}' + ('' if campaign.topic.unsubscribe_url is None else campaign.topic.unsubscribe_url) # noqa
                )
                if campaign.topic.unsubscribe_url:
                    ctx = template.Context()
                    ctx.update({'client': campaign.client})
                    ctx.update({'id': subscriber.id})
                    ctx.update({'email': subscriber.email})
                    ctx.update({'subscription_datetime': subscriber.subscription_datetime}) # noqa
                    unsubscribe_url = unsubscribe_url_template.render(ctx)

        if campaign.html_text is not None and \
                campaign.html_text != u"" and \
                not request.GET.get('txt', False):
            tpl = template.Template('{% load newsletter_tags %}' + campaign.html_text) # noqa
            content_type = 'text/html; charset=utf-8'
        else:
            tpl = template.Template(campaign.plain_text)
            content_type = 'text/plain; charset=utf-8'
        context = template.Context({})
        context.update(get_campaign_context(campaign, subscriber))
        context.update({'client': campaign.client})
        context.update({'unsubscribe_url': unsubscribe_url})
        if subscriber:
            context.update({'subscriber_id': subscriber.id})
            context.update({'email': subscriber.email})
        if dispatch:
            context.update({'dispatch_id': dispatch.id})

        return http.HttpResponse(tpl.render(context),
                                 content_type=content_type)

    raise http.Http404()


def email_tracking(request, dispatch_id, subscriber_id):
    # check signature
    signer = Signer()
    s = signer.sign('%s-%s' % (str(dispatch_id), str(subscriber_id))).split(':')[1] # noqa
    if s != request.GET.get('s', ''):
        raise http.Http404()

    dispatch = get_object_or_404(Dispatch, id=dispatch_id)
    subscriber = get_object_or_404(Subscriber, id=subscriber_id)
    tracking, created = Tracking.objects.get_or_create(
        dispatch=dispatch,
        subscriber=subscriber,
        type=Tracking.OPEN_TYPE
    )

    PIXEL_GIF_DATA = """
    R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7
    """.strip().decode('base64')
    return HttpResponse(PIXEL_GIF_DATA, content_type='image/gif')


# add url
def link_tracking(request, dispatch_id, subscriber_id):
    signer = Signer()
    s = signer.sign('%s-%s-%s' % (
        str(dispatch_id),
        str(subscriber_id),
        request.GET.get('url', '')
    )).rsplit(':', 1)[1]
    if s != request.GET.get('s', ''):
        raise http.Http404()

    dispatch = get_object_or_404(Dispatch, id=dispatch_id)
    subscriber = get_object_or_404(Subscriber, id=subscriber_id)
    tracking, created = Tracking.objects.get_or_create(
        dispatch=dispatch,
        subscriber=subscriber,
        type=Tracking.CLICK_TYPE,
        notes=request.GET.get('url', '')
    )

    return HttpResponseRedirect(request.GET.get('url'))


# API
class ResultsSetPagination(PageNumberPagination):
    page_size = 1


class LargeResultsSetPagination(PageNumberPagination):
    page_size = 200


class SubscriberListViewSet(viewsets.ModelViewSet):
    """ SubscriberList CRUD
    """
    lookup_field = 'pk'
    queryset = SubscriberList.objects.all()
    serializer_class = SubscriberListSerializer

    def get_permissions(self):
        """ Only client users can perform object actions
        """
        return [IsClient(), ]

    def get_queryset(self):
        """ Retrieves only clients lists
        """
        return SubscriberList.objects.filter(client__user__id=self.request.user.id) # noqa

    def perform_create(self, serializer):
        """ Automatically set the client field """
        serializer.save(client=self.request.user.client)


class SubscriberViewSet(viewsets.ModelViewSet):
    """ Subscriber CRUD
    """
    lookup_field = 'pk'
    queryset = Subscriber.objects.all()
    serializer_class = SubscriberSerializer
    pagination_class = LargeResultsSetPagination

    def get_permissions(self):
        """ Only client users can perform object actions
        """
        return [IsClient(), ]

    def get_queryset(self):
        """ Retrieves only clients subscribers
        """
        return Subscriber.objects.filter(client__user__id=self.request.user.id)

    def perform_create(self, serializer):
        """ Automatically set the client field """
        serializer.save(client=self.request.user.client)


class CampaignViewSet(viewsets.ReadOnlyModelViewSet):
    """ Subscriber cRud
    """
    lookup_field = 'pk'
    queryset = Campaign.objects.all()
    serializer_class = CampaignSerializer
    pagination_class = ResultsSetPagination

    def get_permissions(self):
        """ Only client users can perform object actions
        """
        return [IsClient(), ]

    def get_queryset(self):
        """ Retrieves only clients campaigns
        """
        return Campaign.objects.filter(client__user__id=self.request.user.id)
