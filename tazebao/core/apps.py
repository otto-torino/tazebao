from suit.apps import DjangoSuitConfig
from suit.menu import ParentItem, ChildItem


class SuitConfig(DjangoSuitConfig):
    admin_name = 'Tazebao'
    menu = (
        ParentItem('Autenticazione', children=[
            ChildItem(model='auth.user'),
            ChildItem(model='auth.group'),
        ]),
        ParentItem('Configurazione domini', children=[
            ChildItem(model='sites.site'),
        ]),
        ParentItem('Pagine', children=[
            ChildItem('Statiche', model='flatpages.flatpage'),
        ]),
        ParentItem('Newsletter', children=[
            ChildItem(model='newsletter.client'),
            ChildItem(model='newsletter.subscriberlist'),
            ChildItem(model='newsletter.subscriber'),
            ChildItem(model='newsletter.topic'),
            ChildItem('Template', model='mosaico.template'),
            ChildItem(model='newsletter.campaign'),
            ChildItem(model='newsletter.dispatch'),
            ChildItem(model='newsletter.tracking'),
            ChildItem(model='newsletter.usermailermessage'),
        ]),
        ParentItem('Aiuto!', url='/help/', align_right=True),
    )
