# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone
from django.utils.formats import date_format
from django.utils.safestring import mark_safe
from mailqueue.models import MailerMessage


class Client(models.Model):
    user = models.OneToOneField(
        User, verbose_name='utente', on_delete=models.CASCADE)
    name = models.CharField('nome', max_length=50)
    slug = models.SlugField('slug')
    domain = models.CharField('dominio', max_length=100)
    id_key = models.CharField(
        'id key', max_length=8, unique=True, blank=True, null=True)
    secret_key = models.CharField(
        'secret key', max_length=32, unique=True, blank=True, null=True)

    class Meta:
        verbose_name = "client"
        verbose_name_plural = "client"

    def __str__(self):
        return self.name


class SubscriberList(models.Model):
    client = models.ForeignKey(
        Client, verbose_name='client', on_delete=models.CASCADE)
    name = models.CharField('nome', max_length=50)

    class Meta:
        verbose_name = "lista iscritti"
        verbose_name_plural = "liste iscritti"

    def __str__(self):
        return '%s (%s iscritti)' % (self.name, self.subscriber_set.count())


class Subscriber(models.Model):
    client = models.ForeignKey(
        Client, verbose_name='client', on_delete=models.CASCADE)
    email = models.EmailField('e-mail')
    subscription_datetime = models.DateTimeField(
        'data sottoscrizione', auto_now_add=True)
    info = models.TextField('info', blank=True, null=True)
    lists = models.ManyToManyField(SubscriberList, verbose_name='liste')
    opt_in = models.BooleanField('accettazione GDPR', default=False)
    opt_in_datetime = models.DateTimeField(
        'data accettazione GDPR', blank=True, null=True)

    class Meta:
        verbose_name = "iscritto"
        verbose_name_plural = "iscritti"
        unique_together = (
            'client',
            'email',
        )
        ordering = ('email', )

    def __str__(self):
        return self.email


class Topic(models.Model):
    client = models.ForeignKey(
        Client, verbose_name='client', on_delete=models.CASCADE)
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
        '''))

    class Meta:
        verbose_name = "topic"
        verbose_name_plural = "topic"

    def __str__(self):
        return self.name


class Campaign(models.Model):
    client = models.ForeignKey(
        Client, verbose_name='client', on_delete=models.CASCADE)
    name = models.CharField('nome', max_length=50)
    slug = models.SlugField('slug')
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE)
    insertion_datetime = models.DateTimeField(
        auto_now_add=True, verbose_name='inserimento')
    last_edit_datetime = models.DateTimeField(
        auto_now=True, verbose_name='ultima modifica')

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
        verbose_name = "campagna"
        verbose_name_plural = "campagne"
        ordering = ('-id', )

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse(
            'newsletter-campaign-detail',
            args=[
                self.client.slug,
                str(self.insertion_datetime.year),
                self.insertion_datetime.strftime("%m"),
                self.insertion_datetime.strftime("%d"), self.slug
            ])


class Planning(models.Model):
    campaign = models.ForeignKey(
        Campaign, verbose_name='campagna', on_delete=models.CASCADE)
    lists = models.ManyToManyField(SubscriberList, verbose_name='liste')
    schedule = models.DateTimeField('data e ora')
    sent = models.BooleanField('inviata', default=False)

    class Meta:
        verbose_name = "planning"
        verbose_name_plural = "planning"

    def __str__(self):
        return 'Planngin %s' % self.campaign.name


class Dispatch(models.Model):
    campaign = models.ForeignKey(
        Campaign, verbose_name='campagna', on_delete=models.CASCADE)
    lists = models.ManyToManyField(SubscriberList, verbose_name='liste')
    started_at = models.DateTimeField('inizio')
    finished_at = models.DateTimeField('fine', blank=True, null=True)
    error = models.BooleanField('errore', default=False)
    error_message = models.TextField(
        'messaggio di errore', blank=True, null=True)
    success = models.BooleanField('successo', default=False)
    open_statistics = models.BooleanField(
        'statistiche apertura', default=False)
    click_statistics = models.BooleanField('statistiche click', default=False)
    sent = models.IntegerField('e-mail inviate', blank=True, null=True)
    error_recipients = models.TextField(
        'indirizzi in errore', blank=True, null=True)

    class Meta:
        verbose_name = 'invio'
        verbose_name_plural = 'invii'

    def __str__(self):
        return '%s - %s - %s' % (self.id, self.campaign,
                                 date_format(
                                     timezone.localtime(self.started_at),
                                     'DATETIME_FORMAT'))  # noqa

    def open_rate(self):
        if self.error or not self.open_statistics:
            return None
        trackings = Tracking.objects.filter(
            dispatch=self, type=Tracking.OPEN_TYPE).count()  # noqa
        perc = round(100 * trackings / float(self.sent), 1)
        return perc

    def unopen_rate(self):
        if self.open_rate() is None:
            return None
        return round(100 - float(self.open_rate()), 1)

    def click_rate(self):
        if self.error or not self.click_statistics:
            return None
        clicks_s = Tracking.objects.filter(
            dispatch=self, type=Tracking.CLICK_TYPE).values(
                'subscriber').distinct().count()  # noqa
        perc = round(100 * clicks_s / float(self.sent), 1)
        return perc

    def unclick_rate(self):
        if self.click_rate() is None:
            return None
        return round(100 - float(self.click_rate()), 1)


class Tracking(models.Model):
    OPEN_TYPE = 1
    CLICK_TYPE = 2
    TYPE_CHOICES = (
        (OPEN_TYPE, 'apertura'),
        (CLICK_TYPE, 'click'),
    )
    datetime = models.DateTimeField(auto_now_add=True)
    type = models.IntegerField('tipo', choices=TYPE_CHOICES)
    dispatch = models.ForeignKey(
        Dispatch, verbose_name='invio', on_delete=models.CASCADE)
    subscriber = models.ForeignKey(
        Subscriber, verbose_name='iscritto', on_delete=models.CASCADE)
    notes = models.CharField('note', max_length=255, blank=True, null=True)

    class Meta:
        verbose_name = "tracking"
        verbose_name_plural = "tracking"

    def __str__(self):
        return 'tracking ID %s' % str(self.id)


class UserMailerMessage(MailerMessage):
    class Meta:
        proxy = True
        verbose_name = 'log invio'
        verbose_name_plural = 'log invii'


class FailedEmail(models.Model):
    client = models.ForeignKey(
        Client, verbose_name='client', on_delete=models.CASCADE)
    dispatch = models.ForeignKey(
        Dispatch,
        verbose_name='invio',
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name='failedemails')
    datetime = models.DateTimeField('data e ora')
    from_email = models.EmailField('indirizzo from')
    subscriber = models.ForeignKey(
        Subscriber,
        verbose_name='iscritto',
        on_delete=models.CASCADE,
        related_name='failedemails')
    message = models.TextField(blank=True, null=True)
    status = models.CharField('status', max_length=50, blank=True, null=True)
    email_id = models.CharField('id email', max_length=50, unique=True)

    class Meta:
        verbose_name = "bounce"
        verbose_name_plural = "bounces"

    def __str__(self):
        return super(FailedEmail, self).__str__()
