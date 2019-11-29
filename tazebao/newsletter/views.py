import base64
import json
import random
import string
import time
from datetime import date, datetime, timedelta
from urllib.parse import unquote

from dateutil.relativedelta import relativedelta
from django import http, template
from django.core.signing import Signer
from django.db import IntegrityError, transaction
from django.http import (Http404, HttpResponse, HttpResponseBadRequest,
                         HttpResponseRedirect)
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.views import APIView

from mosaico.models import Template
from mosaico.serializers import TemplateSerializer

from .auth import PostfixNewsletterAPISignatureAuthentication
from .context import get_campaign_context
from .models import (Campaign, Client, Dispatch, FailedEmail, Planning,
                     Subscriber, SubscriberList, Topic, Tracking, Unsubscription)
from .permissions import IsClient
from .serializers import (CampaignSerializer, DispatchSerializer,
                          FailedEmailSerializer, PlanningSerializer,
                          SubscriberListSerializer, SubscriberSerializer,
                          TopicSerializer)
from .tasks import send_campaign
from .templatetags.newsletter_tags import encrypt


def random_string(string_length=7):
    """Generate a random string of fixed length """
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for i in range(string_length))


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
    page_size_query_param = 'page_size'


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


class PlanningViewSet(viewsets.ModelViewSet):
    """ SubscriberList CRUD
    """
    lookup_field = 'pk'
    queryset = Planning.objects.all()
    serializer_class = PlanningSerializer

    def get_permissions(self):
        """ Only client users can perform object actions
        """
        return [
            IsClient('campaign'),
        ]

    def get_queryset(self):
        """ Retrieves only clients plannings
        """
        return Planning.objects.filter(
            campaign__client__user__id=self.request.user.id)  # noqa


class FailedEmailViewSet(viewsets.ModelViewSet):
    """ FailedEmail CRUD
    """
    lookup_field = 'pk'
    queryset = FailedEmail.objects.all()
    serializer_class = FailedEmailSerializer

    def get_permissions(self):
        """ Only client users can perform object actions
        """
        return [
            IsClient(),
        ]

    def get_queryset(self):
        """ Retrieves only clients plannings
        """
        return FailedEmail.objects.filter(
            client__user__id=self.request.user.id)  # noqa


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

    @action(detail=False, methods=['post'])
    def add_list(self, request):
        subscribers = request.data.get('subscribers')
        for subscriber_id in subscribers:
            try:
                subscriber = Subscriber.objects.get(id=int(subscriber_id))
                subscriber.lists.add(*request.data.get('lists'))
            except IntegrityError:
                pass
            except Exception as e:
                print(e)
                return HttpResponseBadRequest('unexisting subscriber or list')
        return Response({})

    @transaction.atomic
    @action(detail=False, methods=['post'])
    def remove_list(self, request):
        subscribers = request.data.get('subscribers')
        for subscriber_id in subscribers:
            try:
                subscriber = Subscriber.objects.get(id=int(subscriber_id))
                subscriber.lists.remove(*request.data.get('lists'))
            except Exception as e:
                print(e)
                return HttpResponseBadRequest('unexisting subscriber or list')
        return Response({})

    @action(detail=False, methods=['post'])
    def delete_from_bounces(self, request):
        bounces_ids = request.data.get('bounces')
        try:
            subscribers = Subscriber.objects.filter(
                bounces__id__in=bounces_ids).delete()
            return Response({'detail': 'subscribers deleted'})
        except Exception as e:
            print(e)
            return HttpResponseBadRequest(str(e))


class CampaignViewSet(viewsets.ModelViewSet):
    """ Campaigns CRUD
    """
    lookup_field = 'pk'
    queryset = Campaign.objects.all()
    serializer_class = CampaignSerializer
    pagination_class = LargeResultsSetPagination

    def get_permissions(self):
        """ Only client users can perform object actions
        """
        return [
            IsClient(),
        ]

    def get_queryset(self):
        """ Retrieves only client's campaigns
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
                last_edit_datetime__gte=datetime.strptime(
                    date_from, "%Y-%m-%d"))
        if date_to is not None:
            qs = qs.filter(
                last_edit_datetime__lte=datetime.strptime(date_to, "%Y-%m-%d"))
        return qs

    def perform_create(self, serializer):
        """ Automatically set the client field """
        serializer.save(client=self.request.user.client)

    @action(detail=True, methods=['get'])
    def get_template(self, request, pk=None):
        campaign = self.get_object()
        if not campaign.template:
            raise Http404()
        else:
            tpl = TemplateSerializer(campaign.template)
            return Response(tpl.data)

    @action(detail=True, methods=['get'])
    def dispatches(self, request, pk=None):
        campaign = self.get_object()
        data = DispatchSerializer(campaign.dispatch_set, many=True)
        return Response(data.data)

    @action(detail=True, methods=['post'])
    def send(self, request, pk=None):
        campaign = self.get_object()
        if (campaign.client != request.user.client):
            raise Http404()
        else:
            try:
                send_campaign.delay(request.data.get('lists'), campaign.id)
                return Response({'detail': 'task queued'})
            except Exception as e:
                return HttpResponseBadRequest(
                    'cannot send campaign: %s' % str(e))

    @action(detail=True, methods=['post'])
    def duplicate(self, request, pk=None):
        campaign = self.get_object()
        if (campaign.client != request.user.client):
            raise Http404()
        if not campaign.template:
            raise Http404()
        try:
            new_campaign = Campaign(
                client=campaign.client,
                name=campaign.name + ' (copy)',
                slug=str(int(time.time())),
                topic=campaign.topic,
                subject=campaign.subject,
                plain_text=campaign.plain_text,
                html_text=campaign.html_text,
                view_online=campaign.view_online,
            )
            new_campaign.save()
            new_template = Template(
                client=campaign.template.client,
                campaign=new_campaign,
                key=random_string(),
                name=campaign.template.name,
                html=campaign.template.html,
                template_data=campaign.template.template_data,
                meta_data=campaign.template.meta_data,
            )
            new_template.save()
            return Response({'id': new_campaign.id})
        except Exception as e:
            return HttpResponseBadRequest(
                'cannot duplicate campaign: %s' % str(e))


class DispatchViewSet(viewsets.ReadOnlyModelViewSet):
    """ Dispatches cRud
    """
    lookup_field = 'pk'
    queryset = Dispatch.objects.all()
    serializer_class = DispatchSerializer
    pagination_class = ResultsSetPagination

    def get_permissions(self):
        """ Only client users can perform object actions
        """
        return [
            IsClient('campaign'),
        ]

    def get_queryset(self):
        """ Retrieves only client's dispatches
        """
        qs = Dispatch.objects.filter(
            campaign__client__user__id=self.request.user.id)
        campaign_id = self.request.query_params.get('campaign', None)
        date_from = self.request.query_params.get('date_from', None)
        date_to = self.request.query_params.get('date_to', None)
        if campaign_id is not None:
            qs = qs.filter(campaign__id=campaign_id)
        if date_from is not None:
            qs = qs.filter(
                started_at__gte=datetime.strptime(date_from, "%Y-%m-%d"))
        if date_to is not None:
            qs = qs.filter(
                started_at__lte=datetime.strptime(date_to, "%Y-%m-%d"))
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
            data = json.loads(request.body.decode('utf-8'))
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
                return HttpResponseBadRequest('%s' % str(e))
            # force text plain because on remote server it sends probably
            # binary data
            return HttpResponse(
                'failed email correctly inserted', content_type='text/plain')
        else:
            return http.HttpResponseForbidden()


class TopicViewSet(viewsets.ModelViewSet):
    """ Topic CRUD
    """
    lookup_field = 'pk'
    queryset = Topic.objects.all()
    serializer_class = TopicSerializer

    def get_permissions(self):
        """ Only client users can perform object actions
        """
        return [
            IsClient(),
        ]

    def get_queryset(self):
        """ Retrieves only clients lists
        """
        return Topic.objects.filter(
            client__user__id=self.request.user.id)  # noqa

    def perform_create(self, serializer):
        """ Automatically set the client field """
        serializer.save(client=self.request.user.client)


class StatsApiView(APIView):
    def get(self, request):
        if not request.user.is_authenticated:
            return Response({'description': 'not authenticated'}, status=401)
            response = {}
        else:
            today = date.today()
            last_month = today - relativedelta(months=1)
            tot_subscribers = Subscriber.objects.filter(
                client__user=request.user).count()
            last_month_subscribers = Subscriber.objects.filter(
                client__user=request.user,
                subscription_datetime__gte=last_month).count()
            last_month_unsubscriptions= Unsubscription.objects.filter(
                client__user=request.user,
                datetime__gte=last_month).count()
            last_dispatch = Dispatch.objects.filter(
                campaign__client__user=request.user).last()
            next_planning = Planning.objects.filter(
                campaign__client__user=request.user,
                schedule__gte=datetime.now()).first()
            response = {
                'subscribers': tot_subscribers,
                'lastMonthUnsubscriptions': last_month_unsubscriptions,
                'lastMonthSubscribers': last_month_subscribers,
                'lastDispatch': DispatchSerializer(last_dispatch).data if last_dispatch else None,
                'nextPlanning': PlanningSerializer(next_planning).data if next_planning else None,
            }
        return Response(response)
