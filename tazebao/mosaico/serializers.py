from django import template
from rest_framework import serializers

from .models import (Template)


class TemplateSerializer(serializers.ModelSerializer):
    """ Template Serializer """

    class Meta:
        model = Template
        fields = (
            'id',
            'client',
            'key',
            'name',
            'template_data',
            'meta_data'
        )
        read_only_fields = ('client', )
