from django.contrib import admin
from django.utils.safestring import mark_safe

from .models import Upload, Template


class TemplateAdmin(admin.ModelAdmin):
    list_display = ('name', 'key', 'last_modified', 'create_campaign', )

    def get_queryset(self, request):
        """ Let the user see only related templates
        """
        qs = super(TemplateAdmin, self).get_queryset(request)
        return qs.filter(client__user=request.user)

    def create_campaign(self, obj):
        return mark_safe(
            '<a class="btn btn-success" href="%s">crea campagna</a>' % (
                '/admin/newsletter/usercampaign/add/#' + str(obj.id)
            )
        )
    create_campaign.short_description = 'Azioni'

admin.site.register(Template, TemplateAdmin)

admin.site.register(Upload)
