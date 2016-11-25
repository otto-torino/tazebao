from django.contrib import admin
from django.utils.crypto import get_random_string
from django.shortcuts import get_object_or_404, render
from django.utils.safestring import mark_safe
from django.core.urlresolvers import reverse
from django import forms
from django.http.response import HttpResponseRedirect

from .models import Client, SubscriberList, Subscriber
from .models import Topic, Campaign, Dispatch, Tracking
from .models import UserMailerMessage
# send campaign
from .tasks import send_campaign


class DisplayOnlyIfAdminOrHasClient(admin.ModelAdmin):
    def get_model_perms(self, request):
        """ Hides the model if user has no clients and is not admin """
        has_clients = Client.objects.filter(user=request.user).count()

        if not has_clients and not request.user.is_superuser:
            return {}

        return super(DisplayOnlyIfAdminOrHasClient, self).get_model_perms(request) # noqa


class ManageOnlyClientsRows(admin.ModelAdmin):
    def get_queryset(self, request):
        """ Let no admin user see only related clients """
        qs = super(ManageOnlyClientsRows, self).get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(client__user=request.user)


class ClientReadOnly(admin.ModelAdmin):
    def get_readonly_fields(self, request, obj=None):
        """ Let no admin user only read client field """
        if request.user.is_superuser:
            return super(ClientReadOnly, self).get_readonly_fields(request, obj) # noqa
        else:
            return super(ClientReadOnly, self).get_readonly_fields(request, obj) + ('client', ) # noqa


class ClientOnlyAdminListDisplay(admin.ModelAdmin):
    def get_list_display(self, request):
        list_display = super(ClientOnlyAdminListDisplay, self).get_list_display(request) # noqa
        if request.user.is_superuser:
            list_display += ('client', )
        return list_display


class SaveClientFromUser(admin.ModelAdmin):
    def save_model(self, request, obj, form, change):
        """ Automatically saves the client if no admin """
        if not change and not request.user.is_superuser:
            obj.client = request.user.client
        obj.save()


class ClientAdmin(DisplayOnlyIfAdminOrHasClient):
    list_display = ('name', 'user', 'domain', 'id_key', )
    readonly_fields = ('id_key', 'secret_key', )
    prepopulated_fields = {'slug': ('name',), }

    def get_actions(self, request):
        # Disable delete
        actions = super(ClientAdmin, self).get_actions(request)
        if not request.user.is_superuser:
            del actions['delete_selected']
        return actions

    def has_delete_permission(self, request, obj=None):
        # Disable delete
        if request.user.is_superuser:
            return True
        return False

    def has_add_permission(self, request):
        """ User can't create new clients """
        if request.user.is_superuser:
            return True
        return False

    def get_queryset(self, request):
        """ Let the user see only related clients """
        qs = super(ClientAdmin, self).get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(user=request.user)

    def get_readonly_fields(self, request, obj=None):
        if request.user.is_superuser:
            return super(ClientAdmin, self).get_readonly_fields(request, obj)
        else:
            return ('user', 'id_key', 'secret_key', )

    def save_model(self, request, obj, form, change):
        """ Generates an id key and a secret key """
        if not change:
            obj.id_key = get_random_string(length=8)
            obj.secret_key = get_random_string(length=32)
        obj.save()

admin.site.register(Client, ClientAdmin)


class SubscriberListAdmin(DisplayOnlyIfAdminOrHasClient,
                          ManageOnlyClientsRows,
                          ClientReadOnly,
                          ClientOnlyAdminListDisplay,
                          SaveClientFromUser):
    list_display = ('name', 'subscribers', )
    list_filter = (
        ('client', admin.RelatedOnlyFieldListFilter),
    )

    def subscribers(self, obj):
        return obj.subscriber_set.all().count()
    subscribers.short_description = 'numero iscritti'

admin.site.register(SubscriberList, SubscriberListAdmin)


class SubscriberAdmin(DisplayOnlyIfAdminOrHasClient,
                      ManageOnlyClientsRows,
                      ClientReadOnly,
                      ClientOnlyAdminListDisplay,
                      SaveClientFromUser):
    list_display = ('email', 'subscription_datetime',
                    'lists_string', 'info', )
    list_filter = (
        ('client', admin.RelatedOnlyFieldListFilter),
        'subscription_datetime',
    )
    search_fields = ('email', 'info', )
    actions = ['action_add_to_list', 'action_remove_from_list', ]

    def get_actions(self, request):
        """ admin cant add to lists or remove to lists because
            could mix clients lists and subscribers """
        actions = super(SubscriberAdmin, self).get_actions(request)
        if request.user.is_superuser:
            del actions['action_add_to_list']
            del actions['action_remove_from_list']
        return actions

    def lists_string(self, obj):
        return ', '.join([x.name for x in obj.lists.all()])
    lists_string.short_description = 'liste'

    def get_raw_id_fields(self, request):
        fields = CampaignAdmin.raw_id_fields
        if request.user.is_superuser:
            fields += ('lists', )
        return fields

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        """ No admin user can select only its lists """
        self.raw_id_fields = self.get_raw_id_fields(request)
        if db_field.name == "lists" and not request.user.is_superuser:
            kwargs["queryset"] = SubscriberList.objects.filter(
                client__user=request.user)
        return super(SubscriberAdmin, self).formfield_for_manytomany(
            db_field, request, **kwargs)

    def action_add_to_list(self, request, queryset):
        """ Adds selected subscribers to choosen lists
        """
        # http://www.b-list.org/weblog/2008/nov/09/dynamic-forms/
        def _make_add_to_list_form():
            fields = {
                'lists': forms.ModelMultipleChoiceField(
                    queryset=SubscriberList.objects.filter(
                        client__user=request.user
                    ),
                    label=u'liste iscritti'
                ),
            }

            return type(
                'AddToListForm',
                (forms.BaseForm,),
                {'base_fields': fields}
            )

        form = _make_add_to_list_form()(request.POST or None)

        if 'send_submit' in request.POST:
            if form.is_valid():
                info = self.model._meta.app_label, self.model._meta.model_name

                try:
                    for l in form.cleaned_data['lists']:
                        # http://stackoverflow.com/questions/19371677/django-add-into-many-to-many-field-for-each-item-in-a-queryset
                        Subscriber.lists.through.objects.bulk_create(
                            [Subscriber.lists.through(subscriber_id=s.pk, subscriberlist_id=l.pk) for s in queryset] # noqa
                        )
                except Exception, e:
                    return render(
                        request,
                        'admin/newsletter/subscriber/add_to_list.html', {
                            'form': form,
                            'queryset': queryset,
                            'error': True,
                            'exception': str(e),
                            # just to extend change_list without problems
                            'opts': self.model._meta,
                            'change': True,
                            'is_popup': False,
                            'save_as': False,
                            'has_delete_permission': False,
                            'has_add_permission': False,
                            'has_change_permission': False,
                        })

                return HttpResponseRedirect(
                    reverse('admin:%s_%s_changelist' % info)
                )

        return render(
            request,
            'admin/newsletter/subscriber/add_to_list.html', {
                'form': form,
                'queryset': queryset,
                'error': False,
                # just to extend change_list without problems
                'opts': self.model._meta,
                'change': True,
                'is_popup': False,
                'save_as': False,
                'has_delete_permission': False,
                'has_add_permission': False,
                'has_change_permission': False,
            })
    action_add_to_list.short_description = 'Aggiungi Iscritti selezionati a liste' # noqa

    def action_remove_from_list(self, request, queryset):
        """ Removes selected subscribers to choosen lists
        """
        # http://www.b-list.org/weblog/2008/nov/09/dynamic-forms/
        def _make_remove_from_list_form():
            fields = {
                'lists': forms.ModelMultipleChoiceField(
                    queryset=SubscriberList.objects.filter(
                        client__user=request.user
                    ),
                    label=u'liste iscritti'
                ),
            }

            return type(
                'RemoveFromListForm',
                (forms.BaseForm,),
                {'base_fields': fields}
            )

        form = _make_remove_from_list_form()(request.POST or None)

        if 'send_submit' in request.POST:
            if form.is_valid():
                info = self.model._meta.app_label, self.model._meta.model_name

                try:
                    # http://stackoverflow.com/questions/26839115/django-removing-item-from-many-to-many-relation-more-efficiently
                    Subscriber.lists.through.objects.filter(
                        subscriberlist_id__in=[x.pk for x in form.cleaned_data['lists']], # noqa
                        subscriber_id__in=[x.pk for x in queryset]).delete()
                except Exception, e:
                    return render(
                        request,
                        'admin/newsletter/subscriber/remove_from_list.html', {
                            'form': form,
                            'queryset': queryset,
                            'error': True,
                            'exception': str(e),
                            # just to extend change_list without problems
                            'opts': self.model._meta,
                            'change': True,
                            'is_popup': False,
                            'save_as': False,
                            'has_delete_permission': False,
                            'has_add_permission': False,
                            'has_change_permission': False,
                        })

                return HttpResponseRedirect(
                    reverse('admin:%s_%s_changelist' % info)
                )

        return render(
            request,
            'admin/newsletter/subscriber/remove_from_list.html', {
                'form': form,
                'queryset': queryset,
                'error': False,
                # just to extend change_list without problems
                'opts': self.model._meta,
                'change': True,
                'is_popup': False,
                'save_as': False,
                'has_delete_permission': False,
                'has_add_permission': False,
                'has_change_permission': False,
            })
    action_remove_from_list.short_description = 'Rimuovi Iscritti selezionati da liste' # noqa

admin.site.register(Subscriber, SubscriberAdmin)


class TopicAdmin(DisplayOnlyIfAdminOrHasClient,
                 ManageOnlyClientsRows,
                 ClientReadOnly,
                 ClientOnlyAdminListDisplay,
                 SaveClientFromUser):
    list_display = ('name', 'sending_name', 'sending_address', )
    list_filter = (
        ('client', admin.RelatedOnlyFieldListFilter),
    )

admin.site.register(Topic, TopicAdmin)


class CampaignAdmin(DisplayOnlyIfAdminOrHasClient,
                    ManageOnlyClientsRows,
                    ClientReadOnly,
                    ClientOnlyAdminListDisplay,
                    SaveClientFromUser):
    list_display = ('name', 'topic', 'last_edit_datetime', 'view_online',
                    'last_dispatch', )
    list_filter = (
        ('client', admin.RelatedOnlyFieldListFilter),
        ('topic', admin.RelatedOnlyFieldListFilter),
    )
    search_fields = ('name', )
    prepopulated_fields = {'slug': ('name',), }

    def get_list_display(self, request):
        list_display = super(CampaignAdmin, self).get_list_display(request)
        list_display += ('send_campaign_btn', )
        return list_display

    def get_raw_id_fields(self, request):
        fields = CampaignAdmin.raw_id_fields
        if request.user.is_superuser:
            fields += ('topic', )
        return fields

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """ No admin user can select only its topics """
        self.raw_id_fields = self.get_raw_id_fields(request)
        if db_field.name == "topic" and not request.user.is_superuser:
            kwargs["queryset"] = Topic.objects.filter(
                client__user=request.user)
        return super(CampaignAdmin, self).formfield_for_foreignkey(
            db_field, request, **kwargs)

    def last_dispatch(self, obj):
        try:
            dispatch = Dispatch.objects.filter(
                campaign=obj
            ).order_by('-started_at').first()
            return dispatch.started_at
        except:
            return 'nessun invio'
    last_dispatch.short_description = 'ultimo invio'

    def send_campaign_btn(self, obj):
        info = self.model._meta.app_label, self.model._meta.model_name
        return mark_safe(
            '<a href="%s" class="btn btn-success">invia</a>' % reverse(
                'admin:%s_%s_send_campaign' % info, args=[obj.id, ]
            )
        )
    send_campaign_btn.short_description = 'invio'

    def get_urls(self):
        """ adds the url to send the campaign
        """
        from django.conf.urls import url
        original_urls = super(CampaignAdmin, self).get_urls()

        info = self.model._meta.app_label, self.model._meta.model_name

        my_urls = [
            url(r'^send/(?P<campaign_pk>\d+)/$',
                self.admin_site.admin_view(self.view_send_campaign),
                name='%s_%s_send_campaign' % info),
        ]

        return my_urls + original_urls

    def view_send_campaign(self, request, campaign_pk):
        """ Send campaign view """
        campaign = get_object_or_404(self.model, pk=campaign_pk)

        # http://www.b-list.org/weblog/2008/nov/09/dynamic-forms/
        def _make_dispatch_form():
            fields = {
                'lists': forms.ModelMultipleChoiceField(
                    queryset=SubscriberList.objects.filter(
                        client=campaign.client
                    ),
                    label=u'liste iscritti'
                ),
            }

            return type(
                'DispatchForm',
                (forms.BaseForm,),
                {'base_fields': fields}
            )

        form = _make_dispatch_form()(request.POST or None)

        if form.is_valid():
            info = self.model._meta.app_label, self.model._meta.model_name
            lists_ids = [x.pk for x in form.cleaned_data['lists']]
            send_campaign.delay(lists_ids, campaign_pk)
            return HttpResponseRedirect(
                reverse('admin:%s_%s_changelist' % info)
            )

        return render(
            request,
            'admin/newsletter/campaign/send.html', {
                'campaign': campaign,
                'form': form,
                # just to extend change_list without problems
                'opts': self.model._meta,
                'change': True,
                'is_popup': False,
                'save_as': False,
                'has_delete_permission': False,
                'has_add_permission': False,
                'has_change_permission': False,
            })

admin.site.register(Campaign, CampaignAdmin)


class DispatchAdmin(DisplayOnlyIfAdminOrHasClient):
    list_display = ('id', 'campaign', 'started_at', 'finished_at',
                    'error', 'success', 'sent', 'open_rate', 'click_rate', ) # noqa
    list_filter = (
        ('campaign__client', admin.RelatedOnlyFieldListFilter),
        ('campaign', admin.RelatedOnlyFieldListFilter),
    )

    readonly_fields = [f.name for f in Dispatch._meta.fields] + ['lists', ] # noqa

    def has_add_permission(self, request):
        """ User can't create dispatches """
        return False

    def get_list_display(self, request):
        if request.user.is_superuser:
            return self.list_display + ('client', )
        return self.list_display

    def client(self, obj):
        return obj.campaign.client

    def get_queryset(self, request):
        """ Let no admin user see only related dispatches """
        qs = super(DispatchAdmin, self).get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(campaign__client__user=request.user)

    def open_rate(self, obj):
        if obj.error:
            return ''
        elif not obj.open_statistics:
            return 'N.D.'
        trackings = Tracking.objects.filter(dispatch=obj, type=Tracking.OPEN_TYPE).count() # noqa
        perc = round(100 * trackings / float(obj.sent), 1)
        return mark_safe(
            '<span style="font-weight: bold;color: %s">%s%%</span> (%s/%s)' %
            (
            '#00aa00' if perc >= 50 else 'red',
             perc,
             trackings,
             obj.sent)) # noqa
    open_rate.short_description = 'percentuale apertura'

    def click_rate(self, obj):
        if obj.error:
            return ''
        elif not obj.click_statistics:
            return 'N.D.'
        clicks = Tracking.objects.filter(dispatch=obj, type=Tracking.CLICK_TYPE).count() # noqa
        clicks_s = Tracking.objects.filter(dispatch=obj, type=Tracking.CLICK_TYPE).values('subscriber').distinct().count() # noqa

        perc = round(100 * clicks_s / float(obj.sent), 1)

        return mark_safe(
            '<span style="font-weight: bold;color: %s">%s%%</span> (%s/%s), totali: %s' % # noqa
            (
            '#00aa00' if perc >= 50 else 'red',
             perc,
             clicks_s,
             obj.sent,
             clicks)) # noqa
    click_rate.short_description = 'click'

admin.site.register(Dispatch, DispatchAdmin)


class TrackingAdmin(DisplayOnlyIfAdminOrHasClient):
    list_display = ('datetime', 'type', 'dispatch', 'subscriber', 'notes', )
    search_fields = ('dispatch__id', 'dispatch__campaign__name', 'notes', )
    list_filter = (
        ('dispatch__campaign__client', admin.RelatedOnlyFieldListFilter),
        ('dispatch__campaign', admin.RelatedOnlyFieldListFilter),
        'datetime',
        'type',
    )
    readonly_fields = [f.name for f in Tracking._meta.fields]

    def has_add_permission(self, request):
        """ User can't create trackings """
        return False

    def get_queryset(self, request):
        """ Let the user see only related trackings
        """
        qs = super(TrackingAdmin, self).get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(dispatch__campaign__client__user=request.user)

    def get_list_display(self, request):
        if request.user.is_superuser:
            return self.list_display + ('client', )
        return self.list_display

    def client(self, obj):
        return obj.dispatch.campaign.client

admin.site.register(Tracking, TrackingAdmin)


class UserMailerMessageAdmin(admin.ModelAdmin):
    list_display = ('subject', 'to_address', 'dispatch', 'sent',
                    'last_attempt', 'reply_to')
    list_filter = ('sent', )
    search_fields = ['to_address', 'subject', 'app', 'bcc_address',
                     'reply_to', 'app', ]
    readonly_fields = ('subject', 'to_address', 'bcc_address', 'from_address',
                       'reply_to', 'content', 'html_content', 'app', )
    actions = ['send_failed']

    def dispatch(self, obj):
        return '%s' % (Dispatch.objects.get(pk=int(obj.app)))
    dispatch.short_description = 'App: Invio ID - DATA CAMPAGNA'

    def has_add_permission(self, request):
        """ User can't create mailer messages """
        return False

    def get_queryset(self, request):
        """ Let the user see only related logs
        """
        qs = super(UserMailerMessageAdmin, self).get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(app__in=[str(d.pk) for d in Dispatch.objects.filter(
            campaign__client__user=request.user)])

    def send_failed(self, request, queryset):
        emails = queryset.filter(sent=False)
        for email in emails:
            email.send_mail()
        self.message_user(request, "E-mails accodate.")
    send_failed.short_description = "Invia e-mail fallite"

admin.site.register(UserMailerMessage, UserMailerMessageAdmin)
