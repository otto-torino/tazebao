# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from django.contrib.auth.models import User
from django.utils.safestring import mark_safe
from django.utils.formats import date_format
from django.utils import timezone

from mailqueue.models import MailerMessage


class Client(models.Model):
    user = models.OneToOneField(User, verbose_name='utente')
    name = models.CharField('nome', max_length=50)
    slug = models.SlugField('slug')
    domain = models.CharField('dominio', max_length=100)
    id_key = models.CharField('id key', max_length=8, unique=True,
                              blank=True, null=True)
    secret_key = models.CharField('secret key', max_length=32, unique=True,
                                  blank=True, null=True)

    class Meta:
        verbose_name = "Client"
        verbose_name_plural = "Client"

    def __unicode__(self):
        return self.name


class SubscriberList(models.Model):
    client = models.ForeignKey(Client, verbose_name='client')
    name = models.CharField('nome', max_length=50)

    class Meta:
        verbose_name = "Lista iscritti"
        verbose_name_plural = "Liste iscritti"

    def __unicode__(self):
        return '%s (%s iscritti)' % (self.name, self.subscriber_set.count())


class Subscriber(models.Model):
    client = models.ForeignKey(Client, verbose_name='client')
    email = models.EmailField('e-mail')
    subscription_datetime = models.DateTimeField('data sottoscrizione',
                                                 auto_now_add=True)
    info = models.TextField('info', blank=True, null=True)
    lists = models.ManyToManyField(SubscriberList, verbose_name='liste')

    class Meta:
        verbose_name = "Iscritto"
        verbose_name_plural = "Iscritti"
        unique_together = ('client', 'email', )

    def __unicode__(self):
        return self.email


class Topic(models.Model):
    client = models.ForeignKey(Client, verbose_name='client')
    name = models.CharField('nome', max_length=50)
    sending_address = models.EmailField('indirizzo invio')
    sending_name = models.CharField('nome invio', max_length=50)
    unsubscribe_url = models.CharField(
        'url cancellazione registrazione',
        blank=True,
        null=True,
        max_length=255,
        help_text=mark_safe('''
            <p><b>Variabili</b> disponibili</p>
            - <code>{{ id }}</code> id iscritto<br />
            - <code>{{ email }}</code> e-mail iscritto<br />
            - <code>{{ subscription_datetime }}</code> data
                            sottoscrizione<br />
            <p>Per criptare utilizzando la SECRET_KEY:</p>
            <code>{% encrypt id email %}</code>
            <p>genera una stringa criptata della concatenazione di id
                            e email.</p>
        ''')
    )

    class Meta:
        verbose_name = "Topic"
        verbose_name_plural = "Topic"

    def __unicode__(self):
        return self.name


class Campaign(models.Model):
    client = models.ForeignKey(Client, verbose_name='client')
    name = models.CharField('nome', max_length=50)
    slug = models.SlugField('slug')
    topic = models.ForeignKey(Topic)
    insertion_datetime = models.DateTimeField(auto_now_add=True,
                                              verbose_name='inserimento')
    last_edit_datetime = models.DateTimeField(auto_now=True,
                                              verbose_name='ultima modifica')

    subject = models.CharField('oggetto', max_length=255)
    plain_text = models.TextField(
        'testo',
        blank=True,
        null=True,
        help_text=mark_safe('''
            <p><b>Variabili</b> disponibili per il testo e testo html:</p>
            <p>
            - <code>{{ id }}</code> id campagna<br />
            - <code>{{ unsubscribe_url }}</code> url cancellazione
                            sottoscrizione definito nel Topic<br />
            - <code>{{ view_online_url }}</code> url assoluto della newsletter
                 online<br />
            - <code>{{ domain }}</code> dominio applicazione<br />
            - <code>{{ email }}</code> e-mail iscritto<br />
            </p>
            <p>Per criptare utilizzando la SECRET_KEY:<br />
            <code>{% encrypt email %}</code><br />
            genera una stringa criptata della email.</p>
            <p>Per creare un link con tracciamento del click:<br />
            <code>{% link 'http://www.example.com' %}</code><br />
            genera un url che se visitato tiene traccia dell'evento e
            ridirige su http://www.example.com.</p>
        '''))
    html_text = models.TextField(
        'testo html',
        blank=True,
        null=True,
        help_text='''
            <p><b>Variabili</b> disponibili per il testo e testo html:</p>
            <p>
            - <code>{{ id }}</code> id campagna<br />
            - <code>{{ unsubscribe_url }}</code> url cancellazione
                            sottoscrizione definito nel Topic<br />
            - <code>{{ view_online_url }}</code> url assoluto della newsletter
                 online<br />
            - <code>{{ domain }}</code> dominio applicazione</p>
            - <code>{{ email }}</code> e-mail iscritto<br />
            </p>
            <p>Per criptare utilizzando la SECRET_KEY:<br />
            <code>{% encrypt email %}</code><br />
            genera una stringa criptata della email.</p>
            <p>Per creare un link con tracciamento del click:<br />
            <code>{% link 'http://www.example.com' %}</code><br />
            genera un url che se visitato tiene traccia dell'evento e
            ridirige su http://www.example.com.</p>
        ''')
    view_online = models.BooleanField('visualizza online', default=True)

    class Meta:
        verbose_name = "Campagna"
        verbose_name_plural = "Campagne"

    def __unicode__(self):
        return self.name

    def get_absolute_url(self):
        from django.core.urlresolvers import reverse
        return reverse(
            'newsletter-campaign-detail',
            args=[
                self.client.slug,
                str(self.insertion_datetime.year),
                self.insertion_datetime.strftime("%m"),
                self.insertion_datetime.strftime("%d"),
                self.slug
            ])


class Dispatch(models.Model):
    campaign = models.ForeignKey(Campaign, verbose_name='campagna')
    lists = models.ManyToManyField(SubscriberList, verbose_name='liste')
    started_at = models.DateTimeField('inizio')
    finished_at = models.DateTimeField('fine', blank=True, null=True)
    error = models.BooleanField('errore', default=False)
    success = models.BooleanField('successo', default=False)
    open_statistics = models.BooleanField('statistiche apertura',
                                          default=False)
    click_statistics = models.BooleanField('statistiche click',
                                           default=False)
    sent = models.IntegerField('e-mail inviate', blank=True, null=True)
    error_recipients = models.TextField('indirizzi in errore', blank=True,
                                        null=True)

    class Meta:
        verbose_name = 'Invio'
        verbose_name_plural = 'Invii'

    def __unicode__(self):
        return '%s - %s - %s' % (self.id, self.campaign, date_format(timezone.localtime(self.started_at), 'DATETIME_FORMAT')) # noqa

    def open_rate(self):
        if self.error or not self.open_statistics:
            return None
        trackings = Tracking.objects.filter(dispatch=self, type=Tracking.OPEN_TYPE).count() # noqa
        perc = int(round(100 * trackings / self.sent))
        return perc

    def unopen_rate(self):
        if self.open_rate() is None:
            return None
        return 100 - self.open_rate()

    def click_rate(self):
        if self.error or not self.click_statistics:
            return None
        clicks_s = Tracking.objects.filter(dispatch=self, type=Tracking.CLICK_TYPE).values('subscriber').distinct().count() # noqa
        perc = int(round(100 * clicks_s / self.sent))
        return perc

    def unclick_rate(self):
        if self.click_rate() is None:
            return None
        return 100 - self.click_rate()


class Tracking(models.Model):
    OPEN_TYPE = 1
    CLICK_TYPE = 2
    TYPE_CHOICES = (
        (OPEN_TYPE, 'apertura'),
        (CLICK_TYPE, 'click'),
    )
    datetime = models.DateTimeField(auto_now_add=True)
    type = models.IntegerField('tipo', choices=TYPE_CHOICES)
    dispatch = models.ForeignKey(Dispatch, verbose_name='invio')
    subscriber = models.ForeignKey(Subscriber, verbose_name='iscritto')
    notes = models.CharField('note', max_length=255, blank=True, null=True)

    class Meta:
        verbose_name = "Tracking"
        verbose_name_plural = "Tracking"

    def __unicode__(self):
        return 'tracking ID %s' % str(self.id)


# proxies
class UserClient(Client):
    class Meta:
        proxy = True
        verbose_name = 'Client'
        verbose_name_plural = 'Client'


class UserSubscriberList(SubscriberList):
    class Meta:
        proxy = True
        verbose_name = 'Lista iscritti'
        verbose_name_plural = 'Liste iscritti'


class UserSubscriber(Subscriber):
    class Meta:
        proxy = True
        verbose_name = 'Iscritto'
        verbose_name_plural = 'Iscritti'


class UserTopic(Topic):
    class Meta:
        proxy = True
        verbose_name = 'Topic'
        verbose_name_plural = 'Topic'


class UserCampaign(Campaign):
    class Meta:
        proxy = True
        verbose_name = 'Campagna'
        verbose_name_plural = 'Campagne'


class UserDispatch(Dispatch):
    class Meta:
        proxy = True
        verbose_name = 'Invio Campagna'
        verbose_name_plural = 'Invii Campagne'


class UserTracking(Tracking):
    class Meta:
        proxy = True
        verbose_name = 'Traking'
        verbose_name_plural = 'Tracking'


class UserMailerMessage(MailerMessage):
    class Meta:
        proxy = True
        verbose_name = 'Log coda di invio'
        verbose_name_plural = 'Log code di invio'