from rest_framework import serializers

from .models import Subscriber, SubscriberList

class ClientFilteredPrimaryKeyRelatedField(serializers.PrimaryKeyRelatedField): # noqa
    def get_queryset(self):
        request = self.context.get('request', None)
        queryset = super(ClientFilteredPrimaryKeyRelatedField, self).get_queryset() # noqa
        if not request or not queryset:
            return None
        return queryset.filter(client__user=request.user)


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
                  'info', 'lists', )
        read_only_fields = ('client', )
