from django.contrib import admin
from django import template
from django.utils.crypto import get_random_string
from django.shortcuts import get_object_or_404, render
from django.utils.safestring import mark_safe
from django.core.urlresolvers import reverse
from django import forms
from django.utils import timezone
from django.http.response import HttpResponseRedirect
# from django.core.mail import EmailMultiAlternatives
from django.template import Context

from mailqueue.models import MailerMessage

from .models import Client, SubscriberList, Subscriber
from .models import Topic, Campaign, Dispatch
from .models import UserClient, UserSubscriberList, UserSubscriber
from .models import UserTopic, UserCampaign, UserDispatch, UserMailerMessage
from .context import get_campaign_context


class DisplayOnlyIfHasClientAdmin(admin.ModelAdmin):
    """ Hides the model if user has no clients """
    def get_model_perms(self, request):
        has_clients = Client.objects.filter(user=request.user).count()

        if not has_clients:
            return {}

        return super(DisplayOnlyIfHasClientAdmin, self).get_model_perms(request) # noqa


class SaveClientAdmin(admin.ModelAdmin):
    """ Saves the client field automatically """
    def save_model(self, request, obj, form, change):
        """ Automatically saves the client """
        if not change:
            obj.client = request.user.client
        obj.save()


class ClientAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'domain', 'id_key', )
    readonly_fields = ('id_key', 'secret_key', )
    prepopulated_fields = {'slug': ('name',), }

    def save_model(self, request, obj, form, change):
        """ Generates an id key and a secret key """
        if not change:
            obj.id_key = get_random_string(length=8)
            obj.secret_key = get_random_string(length=32)
        obj.save()

admin.site.register(Client, ClientAdmin)


class SubscriberListAdmin(admin.ModelAdmin):
    list_display = ('name', 'client', )
    list_filter = ('client', )

admin.site.register(SubscriberList, SubscriberListAdmin)


class SubscriberAdmin(admin.ModelAdmin):
    list_display = ('email', 'client', 'subscription_datetime', 'lists_string')
    list_filter = ('client', 'subscription_datetime', )

    def lists_string(self, obj):
        return ', '.join([x.name for x in obj.lists.all()])
    lists_string.short_description = 'liste'

admin.site.register(Subscriber, SubscriberAdmin)


class TopicAdmin(admin.ModelAdmin):
    list_display = ('name', 'client', )
    list_filter = ('client', )

admin.site.register(Topic, TopicAdmin)


class CampaignAdmin(admin.ModelAdmin):
    list_display = ('name', 'topic', 'last_edit_datetime', 'client', )
    list_filter = ('client', 'topic', )
    prepopulated_fields = {'slug': ('name',), }

admin.site.register(Campaign, CampaignAdmin)


class DispatchAdmin(admin.ModelAdmin):
    list_display = ('campaign', 'started_at', 'finished_at',
                    'error', 'success', 'sent', )
    list_filter = ('campaign__client',)

admin.site.register(Dispatch, DispatchAdmin)


class UserClientAdmin(DisplayOnlyIfHasClientAdmin):
    list_display = ('name', 'domain', 'id_key', 'secret_key', )
    readonly_fields = ('user', 'id_key', 'secret_key', )

    def has_add_permission(self, request):
        """ User can't create new clients, onrtoone relationship """
        return False

    def get_queryset(self, request):
        """ Let the user see only related clients
        """
        qs = super(UserClientAdmin, self).get_queryset(request)
        return qs.filter(user=request.user)

    def save_model(self, request, obj, form, change):
        """ Generates an id key and a secret key """
        if not change:
            obj.user = request.user
            obj.id_key = get_random_string(length=8)
            obj.secret_key = get_random_string(length=32)
        obj.save()

admin.site.register(UserClient, UserClientAdmin)


class UserSubscriberListAdmin(SaveClientAdmin, DisplayOnlyIfHasClientAdmin):
    list_display = ('name', )
    readonly_fields = ('client', )

    def get_queryset(self, request):
        """ Let the user see only related clients
        """
        qs = super(UserSubscriberListAdmin, self).get_queryset(request)
        return qs.filter(client__user=request.user)

admin.site.register(UserSubscriberList, UserSubscriberListAdmin)


class UserSubscriberAdmin(SaveClientAdmin, DisplayOnlyIfHasClientAdmin):
    list_display = ('email', 'subscription_datetime', 'lists_string', 'info', )
    list_filter = ('subscription_datetime', )
    readonly_fields = ('client', )
    search_fields = ('email', )

    def lists_string(self, obj):
        return ', '.join([x.name for x in obj.lists.all()])
    lists_string.short_description = 'liste'

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        """ User can select only its lists """
        if db_field.name == "lists":
            kwargs["queryset"] = SubscriberList.objects.filter(
                client__user=request.user)
        return super(UserSubscriberAdmin, self).formfield_for_manytomany(
            db_field, request, **kwargs)

    def get_queryset(self, request):
        """ Let the user see only related clients
        """
        qs = super(UserSubscriberAdmin, self).get_queryset(request)
        return qs.filter(client__user=request.user)

admin.site.register(UserSubscriber, UserSubscriberAdmin)


class UserTopicAdmin(SaveClientAdmin, DisplayOnlyIfHasClientAdmin):
    list_display = ('name', 'sending_name', 'sending_address', )
    readonly_fields = ('client', )

    def get_queryset(self, request):
        """ Let the user see only related topics
        """
        qs = super(UserTopicAdmin, self).get_queryset(request)
        return qs.filter(client__user=request.user)

admin.site.register(UserTopic, UserTopicAdmin)


class UserCampaignAdmin(SaveClientAdmin, DisplayOnlyIfHasClientAdmin):
    list_display = ('name', 'topic', 'last_edit_datetime', 'view_online',
                    'last_dispatch', 'send_campaign_btn', )
    list_filter = ('topic', )
    readonly_fields = ('client', )
    search_fields = ('name', )
    prepopulated_fields = {'slug': ('name',), }

    def get_queryset(self, request):
        """ Let the user see only related campaigns
        """
        qs = super(UserCampaignAdmin, self).get_queryset(request)
        return qs.filter(client__user=request.user)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """ User can select only its topics """
        if db_field.name == "topic":
            kwargs["queryset"] = Topic.objects.filter(
                client__user=request.user)
        return super(UserCampaignAdmin, self).formfield_for_foreignkey(
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
    send_campaign_btn.short_description = 'azioni'

    def get_urls(self):
        """ adds the url to send the campaign
        """
        from django.conf.urls import url
        original_urls = super(UserCampaignAdmin, self).get_urls()

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
                        client__user=request.user
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
            self.send_campaign(form.cleaned_data, campaign)
            return HttpResponseRedirect(
                reverse('admin:%s_%s_changelist' % info)
            )

        return render(
            request,
            'admin/campaign/send.html', {
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

    def send_campaign(self, cleaned_data, campaign, fail_silently=False):
        """ Dispatches the newsletter """
        dispatch = Dispatch(
            campaign=campaign,
            started_at=timezone.now(),
            error=True,
            success=False
        )
        dispatch.save()
        dispatch.lists = cleaned_data['lists']
        dispatch.save()
        # send
        sent = 0
        used_addresses = []
        error_addresses = []
        # param
        text_template = template.Template(campaign.plain_text)
        html_template = template.Template(campaign.html_text)
        from_header = "%s <%s>" % (
            campaign.topic.sending_name,
            campaign.topic.sending_address
        )
        for subscriber_list in cleaned_data['lists']:
            for subscriber in subscriber_list.subscriber_set.all():
                msg = MailerMessage()
                context = Context()
                context.update({'email': subscriber.email})
                if campaign.view_online:
                    context.update(get_campaign_context(campaign))
                msg.app = dispatch.pk
                msg.subject = campaign.subject
                msg.to_address = subscriber.email
                msg.from_address = from_header
                msg.content = text_template.render(context)
                # msg.body = text_template.render(context)
                if campaign.html_text is not None and campaign.html_text != u"": # noqa
                    html_content = html_template.render(context)
                    # msg.attach_alternative(html_content, 'text/html')
                    msg.html_content = html_content
                try:
                    msg.save()
                    sent += 1
                    used_addresses.append(subscriber.email)
                except:
                    error_addresses.append(subscriber.email)
        dispatch.error = False
        dispatch.success = True
        dispatch.finished_at = timezone.now()
        dispatch.sent = sent
        dispatch.sent_recipients = ','.join(used_addresses)
        dispatch.error_recipients = ','.join(error_addresses)
        dispatch.save()
        return sent

admin.site.register(UserCampaign, UserCampaignAdmin)


class UserDispatchAdmin(DisplayOnlyIfHasClientAdmin):
    list_display = ('id', 'campaign', 'started_at', 'finished_at',
                    'error', 'success', 'sent', )
    list_filter = ('campaign', 'error', 'success', 'started_at', )
    readonly_fields = [f.name for f in UserDispatch._meta.fields] + ['lists', ]

    def has_add_permission(self, request):
        """ User can't create dispatches """
        return False

    def has_delete_permission(self, request, obj=None):
        """ User can't delete dispatches """
        return False

    def get_actions(self, request):
        actions = super(UserDispatchAdmin, self).get_actions(request)
        if 'delete_selected' in actions:
            del actions['delete_selected']
        return actions

    def get_queryset(self, request):
        """ Let the user see only related dispatches
        """
        qs = super(UserDispatchAdmin, self).get_queryset(request)
        return qs.filter(campaign__client__user=request.user)

admin.site.register(UserDispatch, UserDispatchAdmin)


class UserMailerMessageAdmin(admin.ModelAdmin):
    list_display = ('subject', 'to_address', 'dispatch', 'sent',
                    'last_attempt', 'reply_to')
    list_filter = ('app', 'sent', )
    search_fields = ['to_address', 'subject', 'app', 'bcc_address',
                     'reply_to']
    readonly_fields = ('subject', 'to_address', 'bcc_address', 'from_address',
                       'reply_to', 'content', 'html_content', 'app', )
    actions = ['send_failed']

    def dispatch(self, obj):
        return '%s - %s ' % (obj.app, Dispatch.objects.get(pk=int(obj.app)))
    dispatch.short_description = 'App: Invio ID - DATA CAMPAGNA'

    def has_add_permission(self, request):
        """ User can't create mailer messages """
        return False

    def get_queryset(self, request):
        """ Let the user see only related logs
        """
        qs = super(UserMailerMessageAdmin, self).get_queryset(request)
        return qs.filter(app__in=[str(d.pk) for d in Dispatch.objects.filter(
            campaign__client__user=request.user)])

    def send_failed(self, request, queryset):
        emails = queryset.filter(sent=False)
        for email in emails:
            email.send_mail()
        self.message_user(request, "Emails queued.")
    send_failed.short_description = "Send failed"

admin.site.register(UserMailerMessage, UserMailerMessageAdmin)
