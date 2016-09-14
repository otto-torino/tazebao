from __future__ import unicode_literals

from django.db import models
from django.contrib.auth.models import User
from django.utils.safestring import mark_safe

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
            variabili disponibili per il testo e testo html<br/>
            - <code>{{ email }}</code> e-mail iscritto<br />
            - <code>{{ view_online_url }}</code> url relativo della newsletter
                 online<br />
            - <code>{{ site_url }}</code> url applicazione senza
                 protocollo<br />
            per ottenere l'url completo della newsletter online<br />
            <code>http://{{ site_url }}{{ view_online_url }}</code>
        '''))
    html_text = models.TextField('testo html', blank=True, null=True)
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
    started_at = models.DateTimeField()
    finished_at = models.DateTimeField(blank=True, null=True)
    error = models.BooleanField('errore', default=False)
    success = models.BooleanField('successo', default=False)
    sent = models.IntegerField('e-mail inviate', blank=True, null=True)
    sent_recipients = models.TextField('indirizzi', blank=True, null=True)
    error_recipients = models.TextField('indirizzi in errore', blank=True,
                                        null=True)

    class Meta:
        verbose_name = "Invio"
        verbose_name_plural = "Invii"

    def __unicode__(self):
        return '%s - %s' % (str(self.started_at), str(self.campaign))


# proxies
class UserClient(Client):
    class Meta:
        proxy = True
        verbose_name = 'User - Client'
        verbose_name_plural = 'User - Client'


class UserSubscriberList(SubscriberList):
    class Meta:
        proxy = True
        verbose_name = 'User - Lista iscritti'
        verbose_name_plural = 'User - Liste iscritti'


class UserSubscriber(Subscriber):
    class Meta:
        proxy = True
        verbose_name = 'User - Iscritto'
        verbose_name_plural = 'User - Iscritti'


class UserTopic(Topic):
    class Meta:
        proxy = True
        verbose_name = 'User - Topic'
        verbose_name_plural = 'User - Topic'


class UserCampaign(Campaign):
    class Meta:
        proxy = True
        verbose_name = 'User - Campagna'
        verbose_name_plural = 'User - Campagne'


class UserDispatch(Dispatch):
    class Meta:
        proxy = True
        verbose_name = 'User - Invio Campagna'
        verbose_name_plural = 'User - Invii Campagne'


class UserMailerMessage(MailerMessage):
    class Meta:
        proxy = True
        verbose_name = 'User - Log coda di invio'
        verbose_name_plural = 'User - Log code di invio'
