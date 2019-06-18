import base64
import datetime
import json
from datetime import datetime, timedelta
from urllib.parse import unquote

from django import http, template
from django.core.signing import Signer
from django.db import IntegrityError
from django.http import (HttpResponse, HttpResponseBadRequest,
                         HttpResponseRedirect)
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from rest_framework import viewsets
from rest_framework.exceptions import ValidationError
from rest_framework.pagination import PageNumberPagination

from .auth import PostfixNewsletterAPISignatureAuthentication
from .context import get_campaign_context
from .models import (Campaign, Client, Dispatch, FailedEmail, Subscriber,
                     SubscriberList, Tracking)
from .permissions import IsClient
from .serializers import SubscriberListSerializer  # noqa
from .serializers import CampaignSerializer, SubscriberSerializer
from .templatetags.newsletter_tags import encrypt


def campaign_detail_view(request, client_slug, year, month, day,
                         campaign_slug):
    """ View online the campaign
        only the campaign user can see this if view_online is False
    """

    campaign = get_object_or_404(
        Campaign,
        client__slug=client_slug,
        insertion_datetime__year=year,
        insertion_datetime__month=month,
        insertion_datetime__day=day,
        slug=campaign_slug)

    if request.user == campaign.client.user or campaign.view_online:

        subscriber = None
        dispatch = None
        unsubscribe_url = ''
        if request.GET.get('subscriber', False) and request.GET.get(
                'dispatch', False) and request.GET.get('sig', False):  # noqa
            sig = request.GET['sig']
            signature = unquote(
                encrypt({
                    'client': campaign.client
                },
                        str(request.GET['subscriber']) + str(
                            request.GET['dispatch']))  # noqa
            )
            if (sig == signature):
                subscriber = get_object_or_404(
                    Subscriber, id=int(request.GET['subscriber']))
                dispatch = get_object_or_404(
                    Dispatch, id=int(request.GET['dispatch']))

                unsubscribe_url_template = template.Template(
                    '{% load newsletter_tags %}' +
                    ('' if campaign.topic.unsubscribe_url is None else campaign
                     .topic.unsubscribe_url)  # noqa
                )
                if campaign.topic.unsubscribe_url:
                    ctx = template.Context()
                    ctx.update({'client': campaign.client})
                    ctx.update({'id': subscriber.id})
                    ctx.update({'email': subscriber.email})
                    ctx.update({
                        'subscription_datetime':
                        subscriber.subscription_datetime
                    })  # noqa
                    unsubscribe_url = unsubscribe_url_template.render(ctx)

        if campaign.html_text is not None and \
                campaign.html_text != u"" and \
                not request.GET.get('txt', False):
            tpl = template.Template(
                '{% load newsletter_tags %}' + campaign.html_text)  # noqa
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

        return http.HttpResponse(
            tpl.render(context), content_type=content_type)

    raise http.Http404()


def email_tracking(request, dispatch_id, subscriber_id):
    # check signature
    signer = Signer()
    s = signer.sign(
        '%s-%s' % (str(dispatch_id), str(subscriber_id))).split(':')[1]  # noqa
    if s != request.GET.get('s', ''):
        raise http.Http404()

    dispatch = get_object_or_404(Dispatch, id=dispatch_id)
    subscriber = get_object_or_404(Subscriber, id=subscriber_id)
    tracking = Tracking.objects.filter(
        dispatch=dispatch, subscriber=subscriber, type=Tracking.OPEN_TYPE)
    if not tracking.count():
        new_tracking = Tracking(
            dispatch=dispatch, subscriber=subscriber, type=Tracking.OPEN_TYPE)
        new_tracking.save()

    PIXEL_GIF_DATA = base64.b64decode("""
    R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7
    """.strip())
    return HttpResponse(PIXEL_GIF_DATA, content_type='image/gif')


# add url
def link_tracking(request, dispatch_id, subscriber_id):
    signer = Signer()
    s = signer.sign('%s-%s-%s' % (str(dispatch_id), str(subscriber_id),
                                  request.GET.get('url', ''))).rsplit(':',
                                                                      1)[1]
    if s != request.GET.get('s', ''):
        raise http.Http404()

    dispatch = get_object_or_404(Dispatch, id=dispatch_id)
    subscriber = get_object_or_404(Subscriber, id=subscriber_id)
    tracking, created = Tracking.objects.get_or_create(
        dispatch=dispatch,
        subscriber=subscriber,
        type=Tracking.CLICK_TYPE,
        notes=request.GET.get('url', ''))

    return HttpResponseRedirect(request.GET.get('url'))


# API
class ResultsSetPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'


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
        return [
            IsClient(),
        ]

    def get_queryset(self):
        """ Retrieves only clients lists
        """
        return SubscriberList.objects.filter(
            client__user__id=self.request.user.id)  # noqa

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
        return [
            IsClient(),
        ]

    def get_queryset(self):
        """ Retrieves only clients subscribers
        """
        return Subscriber.objects.filter(client__user__id=self.request.user.id)

    def perform_create(self, serializer):
        """ Automatically set the client field """
        try:
            serializer.save(client=self.request.user.client)
        except IntegrityError:
            raise ValidationError(
                detail={
                    'email':
                    'Esiste già un utente iscritto con questo indirizzo e-mail'
                })


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
        return [
            IsClient(),
        ]

    def get_queryset(self):
        """ Retrieves only clients campaigns
        """
        qs = Campaign.objects.filter(client__user__id=self.request.user.id)
        view_online = self.request.query_params.get('view_online', None)
        subject = self.request.query_params.get('subject', None)
        text = self.request.query_params.get('text', None)
        date_from = self.request.query_params.get('date_from', None)
        date_to = self.request.query_params.get('date_to', None)
        if view_online is not None:
            qs = qs.filter(view_online=True if int(view_online) else False)
        if subject is not None:
            qs = qs.filter(subject__icontains=subject)
        if text is not None:
            qs = qs.filter(html_text__icontains=text)
        if date_from is not None:
            qs = qs.filter(
                last_edit_datetime__gte=datetime.datetime.strptime(
                    date_from, "%Y-%m-%d"))
        if date_to is not None:
            qs = qs.filter(
                last_edit_datetime__lte=datetime.datetime.strptime(
                    date_to, "%Y-%m-%d"))
        return qs


class FailedEmailApiView(View):
    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        # no need for CSRF protection since it is an HMAC request
        return super(FailedEmailApiView, self).dispatch(
            request, *args, **kwargs)

    def post(self, request):
        authentication = PostfixNewsletterAPISignatureAuthentication()
        if (authentication.authenticate(request)):
            try:
                data = json.loads(request.body.decode('utf-8'))  # remote
            except Exception as e:
                data = json.loads(request.body)  # local
            datetime_string = data.get('datetime')
            from_email = data.get('from_email')
            email = data.get('email')
            status = data.get('status')
            message = data.get('message')
            email_id = data.get('email_id')
            if not datetime_string:
                return HttpResponseBadRequest('missing datetime field')
            if not from_email:
                return HttpResponseBadRequest('missing from email field')
            if not email:
                return HttpResponseBadRequest('missing email field')
            if not email_id:
                return HttpResponseBadRequest('missing email id field')
            dt = datetime.strptime(datetime_string, '%Y-%m-%d %H:%M:%S')
            # try to get client
            client = Client.objects.filter(
                topic__sending_address=from_email,
                subscriber__email=email).first()
            if not client:
                return HttpResponseBadRequest('unrecognized client')
            # try to get dispatch
            dispatch = Dispatch.objects.filter(
                campaign__client=client,
                finished_at__range=(dt - timedelta(hours=6), dt)).first()
            subscriber = Subscriber.objects.filter(
                client=client, email=email).first()

            try:
                failed_email = FailedEmail(
                    datetime=dt,
                    client=client,
                    dispatch=dispatch,
                    from_email=from_email,
                    subscriber=subscriber,
                    status=status,
                    message=message,
                    email_id=email_id,
                )
                failed_email.save()
            except Exception as e:
                return HttpResponse('Error: %s' % str(e))
            return HttpResponse('failed email correctly inserted')
        else:
            return http.HttpResponseForbidden()
