from django import template, http
from django.shortcuts import get_object_or_404


from rest_framework import viewsets

from .models import Campaign, SubscriberList, Subscriber
from .serializers import SubscriberListSerializer, SubscriberSerializer
from .context import get_campaign_context
from .permissions import IsClient


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

        if campaign.html_text is not None and \
                campaign.html_text != u"" and \
                not request.GET.get('txt', False):
            tpl = template.Template(campaign.html_text)
            content_type = 'text/html; charset=utf-8'
        else:
            tpl = template.Template(campaign.plain_text)
            content_type = 'text/plain; charset=utf-8'
        context = template.Context({})
        if campaign.view_online:
            context.update(get_campaign_context(campaign))
        return http.HttpResponse(tpl.render(context),
                                 content_type=content_type)

    raise http.Http404()


# API
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
        return SubscriberList.objects.filter(client__user=self.request.user)

    def perform_create(self, serializer):
        """ Automatically set the client field """
        serializer.save(client=self.request.user.client)


class SubscriberViewSet(viewsets.ModelViewSet):
    """ Subscriber CRUD
    """
    lookup_field = 'pk'
    queryset = Subscriber.objects.all()
    serializer_class = SubscriberSerializer

    def get_permissions(self):
        """ Only client users can perform object actions
        """
        return [IsClient(), ]

    def get_queryset(self):
        """ Retrieves only clients subscribers
        """
        return Subscriber.objects.filter(client__user=self.request.user)

    def perform_create(self, serializer):
        """ Automatically set the client field """
        serializer.save(client=self.request.user.client)
