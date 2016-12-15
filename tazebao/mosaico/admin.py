from django.contrib import admin
from django.utils.safestring import mark_safe

from newsletter.admin import DisplayOnlyIfAdminOrHasClient, ManageOnlyClientsRows, ClientReadOnly, SaveClientFromUser # noqa

from .models import Upload, Template


class TemplateAdmin(admin.ModelAdmin):
    list_display = ('name', 'key', 'last_modified', 'create_campaign', )

    def get_queryset(self, request):
        """ Let the user see only related templates
        """
        qs = super(TemplateAdmin, self).get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(client__user=request.user)

    def create_campaign(self, obj):
        return mark_safe(
            '<a class="btn btn-primary" href="%s">crea campagna</a>' % (
                '/admin/newsletter/campaign/add/#' + str(obj.id)
            )
        )
    create_campaign.short_description = 'Azioni'

admin.site.register(Template, TemplateAdmin)


class UploadAdmin(DisplayOnlyIfAdminOrHasClient,
                  ManageOnlyClientsRows,
                  ClientReadOnly,
                  SaveClientFromUser,):
    list_display = ('name', 'url', )

    def url(self, obj):
        return mark_safe(
            '<a href="%s" target="_blank">%s</a>' % (obj.image.url, obj.image.url) # noqa
        )

admin.site.register(Upload, UploadAdmin)
