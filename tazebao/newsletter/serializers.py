from django import template
from django.contrib.sites.models import Site

from rest_framework import serializers

from .models import Subscriber, SubscriberList, Campaign
from .context import get_campaign_context

class ClientFilteredPrimaryKeyRelatedField(serializers.PrimaryKeyRelatedField): # noqa
    def get_queryset(self):
        request = self.context.get('request', None)
        queryset = super(ClientFilteredPrimaryKeyRelatedField, self).get_queryset() # noqa
        if not request or not queryset:
            return None
        return queryset.filter(client__user__id=request.user.id)


class SubscriberListSerializer(serializers.ModelSerializer):
    """ SubscriberList Serializer """
    class Meta:
        model = SubscriberList
        fields = ('id', 'name', )
        read_only_fields = ('client', )


class SubscriberSerializer(serializers.ModelSerializer):
    """ Subscriber Serializer
        m2m lists is not a SubscriberList serializer because I don't want to
        pass the whole object to associate a list.
        This way you can set lists only passing an array of ids.
    """
    lists = ClientFilteredPrimaryKeyRelatedField(
        many=True,
        queryset=SubscriberList.objects.all())

    class Meta:
        model = Subscriber
        fields = ('id', 'client', 'email', 'subscription_datetime',
                  'info', 'lists', 'opt_in', 'opt_in_datetime', )
        read_only_fields = ('client', )


class CampaignSerializer(serializers.ModelSerializer):
    """ Campaign Serializer """
    topic = serializers.SerializerMethodField("topic_fn")
    topic_id = serializers.SerializerMethodField("topic_id_fn")
    plain_text = serializers.SerializerMethodField("plain_text_fn")
    html_text = serializers.SerializerMethodField("html_text_fn")
    url = serializers.SerializerMethodField("url_fn")

    class Meta:
        model = Campaign
        fields = ('id', 'topic_id', 'topic', 'name',
                  'insertion_datetime', 'last_edit_datetime', 'subject',
                  'plain_text', 'html_text', 'view_online', 'url', )
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
        tpl = template.Template('{% load newsletter_tags %}' + obj.html_text) # noqa
        context = template.Context({})
        context.update(get_campaign_context(obj))
        return tpl.render(context)

    def url_fn(self, obj):
        return ''.join([
            'http://',
            str(Site.objects.get_current()),
            obj.get_absolute_url()
        ])
