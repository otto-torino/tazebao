from django import template
from django.contrib.sites.models import Site
from rest_framework import serializers

from .context import get_campaign_context
from .models import (Campaign, Dispatch, FailedEmail, Planning, Subscriber,
                     SubscriberList, Topic, Tracking)


class ClientFilteredPrimaryKeyRelatedField(
        serializers.PrimaryKeyRelatedField):  # noqa
    def get_queryset(self):
        request = self.context.get('request', None)
        queryset = super(ClientFilteredPrimaryKeyRelatedField,
                         self).get_queryset()  # noqa
        if not request or not queryset:
            return None
        return queryset.filter(client__user__id=request.user.id)


class SubscriberListSerializer(serializers.ModelSerializer):
    """ SubscriberList Serializer """
    tot_subscribers = serializers.SerializerMethodField("tot_subscribers_fn")

    class Meta:
        model = SubscriberList
        fields = (
            'id',
            'name',
            'tot_subscribers'
        )
        read_only_fields = ('client', )

    def tot_subscribers_fn(self, obj):
        return obj.subscriber_set.count()


class SubscriberSerializer(serializers.ModelSerializer):
    """ Subscriber Serializer
        m2m lists is not a SubscriberList serializer because I don't want to
        pass the whole object to associate a list.
        This way you can set lists only passing an array of ids.
    """
    lists = ClientFilteredPrimaryKeyRelatedField(
        many=True, queryset=SubscriberList.objects.all())

    class Meta:
        model = Subscriber
        fields = (
            'id',
            'client',
            'email',
            'subscription_datetime',
            'info',
            'lists',
            'opt_in',
            'opt_in_datetime',
        )
        read_only_fields = ('client', )


class CampaignSerializer(serializers.ModelSerializer):
    """ Campaign Serializer """
    topic = serializers.SerializerMethodField("topic_fn")
    topic_id = serializers.SerializerMethodField("topic_id_fn")
    plain_text = serializers.SerializerMethodField("plain_text_fn")
    html_text = serializers.SerializerMethodField("html_text_fn")
    url = serializers.SerializerMethodField("url_fn")
    last_dispatch = serializers.SerializerMethodField("last_dispatch_fn")

    class Meta:
        model = Campaign
        fields = (
            'id',
            'topic_id',
            'topic',
            'name',
            'insertion_datetime',
            'last_edit_datetime',
            'subject',
            'plain_text',
            'html_text',
            'view_online',
            'url',
            'template',
            'last_dispatch',
        )
        read_only_fields = ('client', )

    def topic_fn(self, obj):
        return obj.topic.name

    def topic_id_fn(self, obj):
        return obj.topic.id

    def plain_text_fn(self, obj):
        tpl = template.Template(obj.plain_text)
        context = template.Context({})
        context.update(get_campaign_context(obj))
        return tpl.render(context)

    def html_text_fn(self, obj):
        tpl = template.Template(
            '{% load newsletter_tags %}' + obj.html_text)  # noqa
        context = template.Context({})
        context.update(get_campaign_context(obj))
        return tpl.render(context)

    def url_fn(self, obj):
        return ''.join([
            'http://',
            str(Site.objects.get_current()),
            obj.get_absolute_url()
        ])

    def last_dispatch_fn(self, obj):
        last = obj.dispatch_set.last()
        if last:
            return last.started_at
        else:
            return None


class FailedEmailSerializer(serializers.ModelSerializer):
    """ Tracking Serializer """
    subscriber_email = serializers.SerializerMethodField("subscriber_email_fn")
    subscriber_id = serializers.SerializerMethodField("subscriber_id_fn")
    campaign_name = serializers.SerializerMethodField("campaign_name_fn")

    class Meta:
        model = FailedEmail
        fields = (
            'id',
            'datetime',
            'dispatch',
            'campaign_name',
            'from_email',
            'subscriber_email',
            'subscriber_id',
            'message',
            'status',
        )

    def subscriber_email_fn(self, obj):
        return obj.subscriber.email

    def subscriber_id_fn(self, obj):
        return obj.subscriber.id

    def campaign_name_fn(self, obj):
        if obj.dispatch:
            return obj.dispatch.campaign.name
        return None


class TrackingSerializer(serializers.ModelSerializer):
    """ Tracking Serializer """
    subscriber_email = serializers.SerializerMethodField("subscriber_email_fn")
    type = serializers.SerializerMethodField("type_fn")

    class Meta:
        model = Tracking
        fields = (
            'id',
            'datetime',
            'type',
            'subscriber_email',
            'notes',
        )

    def subscriber_email_fn(self, obj):
        return obj.subscriber.email

    def type_fn(self, obj):
        return obj.get_type_display()


class DispatchSerializer(serializers.ModelSerializer):
    """ Dispatch Serializer """
    trackings = TrackingSerializer(many=True, read_only=True)
    bounces = FailedEmailSerializer(many=True, read_only=True)
    campaign_name = serializers.SerializerMethodField("campaign_name_fn")

    class Meta:
        model = Dispatch
        fields = (
            'id',
            'campaign',
            'campaign_name',
            'lists',
            'started_at',
            'finished_at',
            'error',
            'error_message',
            'success',
            'open_statistics',
            'click_statistics',
            'sent',
            'error_recipients',
            'open_rate',
            'click_rate',
            'trackings',
            'bounces',
        )

    def campaign_name_fn(self, obj):
        return obj.campaign.name


class PlanningSerializer(serializers.ModelSerializer):
    """ Planning Serializer """
    campaign_name = serializers.SerializerMethodField("campaign_name_fn")

    class Meta:
        model = Planning
        fields = (
            'id',
            'campaign',
            'campaign_name',
            'lists',
            'schedule',
            'sent',
        )

    def campaign_name_fn(self, obj):
        return obj.campaign.name


class TopicSerializer(serializers.ModelSerializer):
    """ Topic Serializer """

    class Meta:
        model = Topic
        fields = (
            'id',
            'name',
            'sending_address',
            'sending_name',
            'unsubscribe_url',
        )
        read_only_fields = ('client', )
