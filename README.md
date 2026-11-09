![image](https://raw.githubusercontent.com/otto-torino/tazebao/master/tazebao/core/static/core/img/logo.png "Logo")

Otto srl newsletter web application.

## Table of Contents

* [What?](#what)
* [Setup](#setup)
* [REST Web Service](#rest-webservice)
    * [REST Service Authentication](#rest-authentication)
    * [Pagination, filtering and sorting](#rest-pagination)
    * [REST resources](#rest-resources)
* [Unsubscription](#unsubscription)
* [Subscription forms](#subscription-forms)
* [Mosaico Integration](#mosaico-integration)
* [Getting Started](#getting-started)
* [Scheduled jobs](#scheduled-jobs)
* [Remote setup](#remote-setup)
* [Deploy and Stuff](#deploy)
    * [Upgrade to Python 3.12 / Django 5.2 (one-time)](#upgrade-2026)
* [Related repositories](#related-repositories)

## <a name="what"></a>What?

Tazebao is a web application which aims to provide a newsletter service to other sites/applications.

Every platform __User__ can be associated to one __Client__ and manage a newsletter. The platform provides an administrative area where the client user can manage its data.

Tazebao provides the following entities:

- subscriber
- list of subscribers
- topic
- template
- campaign
- planning
- dispatch
- dispatch queue log
- tracking
- bounce (failed e-mail)
- unsubscription
- subscription form
- system message

Each __Subscriber__ must belong to one or more lists (__SubscriberList__). Subscriber's e-mail must be unique for each client.
Each __Campaign__ must belong to a __Topic__, which stores the information about the sender name and address, and the unsubscription url.
Tazebao integrates [mosaico](https://github.com/voidlabs/mosaico/), a responsive e-mail template generator. The generated template can be included in the campaign.
The newsletter is sent creating a __Dispatch__, where the user chooses one or more lists of subscribers which will receive the e-mail. Newsletter can be scheduled (__Planning__), planning the effective dispatch.
If the html template of the email contains the closing body tag, then a tracking code is added automatically in order to track if the user opens the e-mail.
These statistics are inaccurate, because the tracking code works only if the user loads the e-mail images.
Tazebao provides a __link__ templatetag which can be used to track user clicks (the destination url is transformed in a Tazebao url, which executes a view which detects the event and redirects the user to the original url).

The __Subscriber__ has an __info__ text field which can be used to store additional information, for example in a json format, an __opt_in__ / __opt_in_datetime__ pair which stores the GDPR acceptance, and a __pix_track__ boolean flag (tracking pixel).

E-mails are prepared asynchronously through a celery task, queued and sent in blocks. The sending must be scheduled with a crontab (see [Scheduled jobs](#scheduled-jobs)), Tazebao uses the [django-mail-queue application](https://github.com/dstegelman/django-mail-queue/) in order to manage this stuff.

Tazebao provides a REST webservice in order to retrieve, create, edit and delete subscribers, lists and the other entities. Each Client can then implement its own registration form and use the provided API to update Tazebao DB, or use the [subscription forms](#subscription-forms) hosted by Tazebao.
Unsubscription can be managed directly by Tazebao or by the Client application, see [Unsubscription](#unsubscription).

Bounces are collected from the mail server (postfix) through a dedicated API endpoint, and can be used to clean up the subscribers lists.

## <a name="setup"></a>Setup

As superuser you can create clients, which are users that receive a set of keys necessary for communicating with the REST Web Service.
You should also create a Client's Group, associated with each Client user, with the following permissions:

- mosaico | template | Can add template
- mosaico | template | Can change template
- mosaico | template | Can delete template
- mosaico | upload | Can add upload
- mosaico | upload | Can change upload
- mosaico | upload | Can delete upload
- newsletter | Campagna | Can add Campagna
- newsletter | Campagna | Can change Campagna
- newsletter | Campagna | Can delete Campagna
- newsletter | Client | Can change Client
- newsletter | Invio | Can change Invio
- newsletter | Invio | Can delete Invio
- newsletter | Iscritto | Can add Iscritto
- newsletter | Iscritto | Can change Iscritto
- newsletter | Iscritto | Can delete Iscritto
- newsletter | Lista iscritti | Can add Lista iscritti
- newsletter | Lista iscritti | Can change Lista iscritti
- newsletter | Lista iscritti | Can delete Lista iscritti
- newsletter | Planning | Can add Planning
- newsletter | Planning | Can change Planning
- newsletter | Planning | Can delete Planning
- newsletter | Topic | Can add Topic
- newsletter | Topic | Can change Topic
- newsletter | Topic | Can delete Topic
- newsletter | Tracking | Can change Tracking
- newsletter | Tracking | Can delete Tracking
- newsletter | Log coda di invio | Can change Log coda di invio
- newsletter | Log coda di invio | Can delete Log coda di invio

so that clients can manage their account through the admin interface.

Each Client also has a `suggestions_per_day` field (default 3) which limits the number of AI subject suggestions it can request every day.

## <a name="rest-webservice"></a>REST Web Service

All the endpoints live under `/api/v1/`. The admin application authentication is a session based authentication, while the web service supports two methods:

- HMAC signature (Keyed-Hash Message Authentication Code), meant for server to server communication;
- JWT, meant for frontend applications (i.e. the client web app and the desktop app).

### <a name="rest-authentication"></a>REST Service Authentication

#### HMAC signature

Each Client gets an ID_KEY and a SECRET_KEY through which authenticate to Tazebao. Tazebao uses [django-rest-framework-httpsignature](https://github.com/etoccalino/django-rest-framework-httpsignature) to manage this stuff.

In order to perform valid requests to the REST resources, every request must be signed in the HTTP header, and the ID_KEY must be passed in the `X-Api-Key` header.
The signature must be calculated this way:

    SIGNATURE = Base64(Hmac('SECRET_KEY', "date: DATETIME", 'sha256'))

And the request should be:

    ~$ curl -v -H 'Date: "DATETIME"' -H 'X-Api-Key: ID_KEY' -H 'Authorization: Signature keyId="ID_KEY",algorithm="hmac-sha256",headers="date",signature="SIGNATURE"'

this was descriptive code, take a look at the [client repository](https://github.com/otto-torino/tazebao-client) to see how to implement this stuff in real languages.

#### JWT

    POST /api/v1/login/

with `username` and `password` returns a token, which must be passed in the `Authorization` header of the following requests:

    Authorization: JWT <TOKEN>

The token expires after 60 minutes and can be refreshed:

    POST /api/v1/refresh-token/

with the `token` field.

    GET /api/v1/whoami/

returns the authenticated user data, including the client keys.

### <a name="rest-pagination"></a>Pagination, filtering and sorting

List endpoints use a dynamic pagination:

- if the `page_size` query parameter is passed, results are paginated with that page size;
- if it is not passed and the client has fewer records than a threshold (100 for campaigns, 1000 for bounces, 8000 for subscribers and mailer messages, 10000 for the other resources), the whole result set is returned as a plain array, without pagination;
- otherwise results are paginated, 10 per page.

The paginated response has the following format:

    {
        "count": 300,
        "next": "http://localhost:8000/api/v1/newsletter/subscriber/?page=2&page_size=10",
        "previous": null,
        "results": [ ... ]
    }

Most list endpoints accept:

- `q`: a free text search (the searched fields depend on the resource)
- `sort`: the field used to sort results (default `-id`)
- `sort_direction`: `asc` or `desc`

### <a name="rest-resources"></a>REST resources

#### Subscribers Lists

This section describes possible CRUD requests to manage subscribers's lists. `q` searches in the list name.

##### Retrieve lists

    GET http://localhost:8000/api/v1/newsletter/subscriberlist/

returns the subscribers' lists associated to the authenticated client, i.e.:

    [{"id":1,"name":"Journalists","tot_subscribers":120},{"id":8,"name":"ACABS","tot_subscribers":32}]

##### Get a list

    GET http://localhost:8000/api/v1/newsletter/subscriberlist/<LIST_ID>/

returns the list object represented by LIST_ID, i.e.:

    {"id":1,"name":"Journalists","tot_subscribers":120}

##### Add a list

    POST http://localhost:8000/api/v1/newsletter/subscriberlist/

the POST data should be a json containing the name field, i.e.:

    "{"name":"Journalists"}"

for example with PHP:

    $post_data = json_encode(array('name' => 'Journalists'))

##### Edit a list

    PUT http://localhost:8000/api/v1/newsletter/subscriberlist/<LIST_ID>/

the submitted data should be a json containing the name field, i.e.:

    "{"name":"Journalists"}"

##### Delete a list

    DELETE http://localhost:8000/api/v1/newsletter/subscriberlist/<LIST_ID>/

#### Subscribers

This section describes possible CRUD requests to manage subscribers.

##### Retrieve subscribers

    GET http://localhost:8000/api/v1/newsletter/subscriber/

returns the subscribers associated to the authenticated client (see [pagination](#rest-pagination)), i.e.:

    {
        "count": 300,
        "next": "http://localhost:8000/api/v1/newsletter/subscriber/?page=2&page_size=10",
        "previous": null,
        "results": [
            {
                "id":1,
                "client":1,
                "email":"email@example.com",
                "subscription_datetime":"2016-09-08T14:49:58.860948Z",
                "info":"custom stuff",
                "lists":[1],
                "opt_in":true,
                "opt_in_datetime":"2016-09-08T14:49:58.860948Z",
                "pix_track":false
            },
            // ... more
        ]
    }

additional filters:

- `email`: e-mail contains
- `info`: info contains
- `lists`: subscribers belonging to the given list id
- `q`: e-mail or info contains

##### Get a subscriber

    GET http://localhost:8000/api/v1/newsletter/subscriber/<SUBSCRIBER_ID>/

returns the subscriber object represented by SUBSCRIBER_ID, i.e.:

    {
        "id":2,
        "client":1,
        "email":"email2@example.com",
        "subscription_datetime":"2016-09-08T14:59:58.860948Z",
        "info":"",
        "lists":[1, 2],
        "opt_in":false,
        "opt_in_datetime":null,
        "pix_track":false
    }

##### Add a subscriber

    POST http://localhost:8000/api/v1/newsletter/subscriber/

the POST data should be a json of the following format:

    "{"email":"xxx@abidibo.net","info":"\"firstname=\"meow\"\"","lists":["1"],"opt_in":true,"opt_in_datetime":"2019-06-06T10:28:34+02:00"}"

email and lists fields are required. If you try to add a subscriber with an email address already associated to the client, you get a 400 response describing the error.

##### Edit a subscriber

    PUT http://localhost:8000/api/v1/newsletter/subscriber/<SUBSCRIBER_ID>/

the PUT data should be a json of the same format used to add a subscriber. email and lists fields are required.

##### Delete a subscriber

    DELETE http://localhost:8000/api/v1/newsletter/subscriber/<SUBSCRIBER_ID>/

##### Bulk actions

All these actions accept a json POST body:

- `POST /api/v1/newsletter/subscriber/add_list/` `{"subscribers": [1, 2], "lists": [3]}` adds the subscribers to the lists
- `POST /api/v1/newsletter/subscriber/remove_list/` `{"subscribers": [1, 2], "lists": [3]}` removes the subscribers from the lists
- `POST /api/v1/newsletter/subscriber/delete_many/` `{"ids": [1, 2]}` deletes the subscribers
- `POST /api/v1/newsletter/subscriber/delete_from_bounces/` `{"bounces": [10, 11]}` deletes the subscribers related to the given bounces
- `POST /api/v1/newsletter/subscriber/delete_from_mailermessages/` `{"mailermessages": [10, 11]}` deletes the subscribers related to the given mailer messages, and the messages themselves

##### Import subscribers from CSV

    POST http://localhost:8000/api/v1/newsletter/subscriber/import/

multipart request with the following fields:

- `file`: a CSV file, without header row, with the columns `email`, `subscription_datetime`, `info`, `opt_in`, `opt_in_datetime`
    - `subscription_datetime` can be empty (now is used)
    - `info` can be empty, otherwise it must be a valid json
    - `opt_in` is `0` or `1`, if `1` then `opt_in_datetime` is required
- `lists`: comma separated list ids the subscribers will be added to

At most 1000 rows can be imported at once. The import is atomic: if a row is invalid nothing is imported and a 400 response describes the error. Already existing subscribers are just added to the lists.

#### Topics

    GET|POST http://localhost:8000/api/v1/newsletter/topic/
    GET|PUT|DELETE http://localhost:8000/api/v1/newsletter/topic/<TOPIC_ID>/

Topic fields: `id`, `name`, `sending_address`, `sending_name`, `unsubscribe_url`. `q` searches in the topic name.

#### Campaigns

This resource is useful in order to display the newsletter content in your own application, or to create
a newsletter archive. It also supports create, update and delete operations, used by the Tazebao frontend.

##### Retrieve campaigns

    GET http://localhost:8000/api/v1/newsletter/campaign/

returns the campaigns associated to the authenticated client (see [pagination](#rest-pagination)), i.e.:

    {
        "count": 2,
        "next": "http://localhost:8000/api/v1/newsletter/campaign/?page=2&page_size=10",
        "previous": null,
        "results": [
            {
                "id": 1,
                "topic_id": 1,
                "topic": "New Articles",
                "name": "Let's talk about birds!",
                "insertion_datetime": "2016-09-08T14:51:06.980733Z",
                "last_edit_datetime": "2016-09-22T11:42:30.398038Z",
                "subject": "A new article on birds.com!",
                "plain_text": "plain bla bla",
                "html_text": "html bla bla",
                "view_online": true,
                "url": "http://localhost:8000/newsletter/client-slug/2016/09/08/campaign-slug/",
                "template": 1,
                "last_dispatch": "2016-09-22T12:00:00Z",
                "last_not_test_dispatch": "2016-09-22T12:00:00Z"
            }
            // ... more
        ]
    }

additional filters can be used to retrieve campaigns:

- `date_from` in the format `YYYY-MM-DD` (last edit date)
- `date_to` in the format `YYYY-MM-DD` (last edit date)
- `subject`: subject contains
- `text`: html text contains
- `topic`: topic id
- `view_online`: `1` or `0`
- `dispatched`: if present, only campaigns which have been actually sent (not as a test)
- `q`: name contains

just add them in the query string, i.e.

    http://localhost:8000/api/v1/newsletter/campaign/?subject=foo&date_from=2018-09-12

##### Get a campaign

    GET http://localhost:8000/api/v1/newsletter/campaign/<CAMPAIGN_ID>/

returns the campaign object represented by CAMPAIGN_ID, with the same format of the list items.

##### Campaign actions

- `GET /api/v1/newsletter/campaign/<CAMPAIGN_ID>/get_template/` returns the mosaico template of the campaign
- `GET /api/v1/newsletter/campaign/<CAMPAIGN_ID>/dispatches/` returns the dispatches of the campaign
- `POST /api/v1/newsletter/campaign/<CAMPAIGN_ID>/send/` `{"lists": [1, 2]}` queues the sending of the campaign to the given lists; add `?test=1` to mark the dispatch as a test
- `POST /api/v1/newsletter/campaign/<CAMPAIGN_ID>/test/` `{"lists": [1, 2]}` sends a test e-mail immediately to the given lists (at most 50 recipients)
- `POST /api/v1/newsletter/campaign/<CAMPAIGN_ID>/duplicate/` duplicates the campaign and its template, returns the new campaign id

#### Plannings

    GET|POST http://localhost:8000/api/v1/newsletter/planning/
    GET|PUT|DELETE http://localhost:8000/api/v1/newsletter/planning/<PLANNING_ID>/

Planning fields: `id`, `campaign`, `campaign_name`, `lists`, `schedule`, `sent`. `q` searches in the campaign name.
Planned dispatches are launched by the `dispatch_planned_campaigns` command (see [Scheduled jobs](#scheduled-jobs)).

#### Dispatches

Dispatch models are readonly, so you can only retrieve a list of dispatches, or a single dispatch.

##### Retrieve dispatches

    GET http://localhost:8000/api/v1/newsletter/dispatch/

returns the dispatches associated to the authenticated client (see [pagination](#rest-pagination)), i.e.:

    {
        "count": 2,
        "next": "http://localhost:8000/api/v1/newsletter/dispatch/?page=2&page_size=10",
        "previous": null,
        "results": [
            {
                "id": 800,
                "campaign": 387,
                "campaign_name": "Let's talk about birds!",
                "test": false,
                "lists": [
                    23
                ],
                "started_at": "2019-06-06T10:28:34+02:00",
                "finished_at": "2019-06-06T10:28:34+02:00",
                "error": false,
                "error_message": null,
                "success": true,
                "open_statistics": true,
                "click_statistics": false,
                "sent": 1,
                "error_recipients": "",
                "open_rate": 100,
                "click_rate": 100,
                "trackings": [
                    {
                        "id": 159589,
                        "datetime": "2019-06-06T16:46:40+02:00",
                        "type": "apertura",
                        "subscriber_email": "xxx@otto.to.it",
                        "notes": null
                    },
                    {
                        "id": 159590,
                        "datetime": "2019-06-06T17:50:54+02:00",
                        "type": "click",
                        "subscriber_email": "yyy@otto.to.it",
                        "notes": "http:\/\/www.google.it"
                    }
                ],
                "bounces": [
                    {
                        "id": 1,
                        "datetime": "2019-10-18T15:40:19+02:00",
                        "dispatch": 800,
                        "campaign_name": "Let's talk about birds!",
                        "from_email": "test@otto.to.it",
                        "subscriber_email": "xxx@gmail.com",
                        "subscriber_id": 12,
                        "message": "host gmail-smtp-in.l.google.com[108.177.15.26] said: 550-5.1.1 The email account that you tried to reach does not exist. [...]",
                        "status": "bounced"
                    }
                ]
            },
            // ... more
        ]
    }

additional filters can be used to retrieve dispatches:

- `date_from` in the format `YYYY-MM-DD` (start date)
- `date_to` in the format `YYYY-MM-DD` (start date)
- `campaign`: campaign id

just add them in the query string, i.e.

    http://localhost:8000/api/v1/newsletter/dispatch/?campaign=387&date_from=2018-09-12

##### Get a dispatch

    GET http://localhost:8000/api/v1/newsletter/dispatch/<DISPATCH_ID>/

returns the dispatch object represented by DISPATCH_ID, with the same format of the list items.

#### Bounces

    GET http://localhost:8000/api/v1/newsletter/bounces/
    GET|DELETE http://localhost:8000/api/v1/newsletter/bounces/<BOUNCE_ID>/

returns the failed e-mails of the authenticated client, with the same format of the dispatch `bounces` items. `q` searches in the subscriber e-mail and in the campaign name.

Bounces are inserted by the mail server through:

    POST http://localhost:8000/api/v1/newsletter/failedemail/

this endpoint is HMAC signed with the `POSTFIX_CLIENT_ID` and `POSTFIX_CLIENT_SECRET` credentials (see the environment variables in [Getting Started](#getting-started)), and accepts a json body with the fields `datetime` (`YYYY-MM-DD HH:MM:SS`), `from_email`, `email`, `email_id`, `status`, `message`.

#### Mailer messages

    GET http://localhost:8000/api/v1/newsletter/mailermessage/
    GET|DELETE http://localhost:8000/api/v1/newsletter/mailermessage/<MESSAGE_ID>/

the queued/sent e-mails of the client dispatches (`id`, `created`, `subject`, `to_address`, `from_address`, `app`, `sent`, `last_attempt`). `q` searches in the recipient address.

    GET http://localhost:8000/api/v1/newsletter/mailermessage/unsent/

returns the total number of messages still in the shared sending queue, i.e. of all clients: `{"unsent": 120}`. It is meant to give an idea of the queue length before the client's own messages are sent. The number of unsent messages of the authenticated client is the `dispatching` field of the [statistics](#statistics) endpoint.

#### Subscription forms

    GET|POST http://localhost:8000/api/v1/newsletter/subscriptionform/
    GET|PUT|DELETE http://localhost:8000/api/v1/newsletter/subscriptionform/<FORM_ID>/

Subscription form fields: `id`, `created`, `last_edited`, `name`, `content`, `privacy_disclaimer`, `code`, `success_url`, `error_url`, `lists`, `standalone_link`. See [Subscription forms](#subscription-forms).

#### System messages

    GET http://localhost:8000/api/v1/newsletter/systemmessages/

returns the unread system messages addressed to the client (or to all clients): `id`, `title`, `html`, `datetime`.

    POST http://localhost:8000/api/v1/newsletter/systemmessages/<MESSAGE_ID>/mark_as_read/

marks a message as read.

#### Statistics

    GET http://localhost:8000/api/v1/newsletter/stats/

returns a summary of the client account:

    {
        "subscribers": 300,
        "bounces": 12,
        "dispatching": 0,
        "lastMonthUnsubscriptions": 2,
        "lastMonthSubscribers": 15,
        "lastDispatch": { ... dispatch object ... },
        "nextPlanning": { ... planning object ... }
    }

    GET http://localhost:8000/api/v1/newsletter/subscriptions/stats/

returns the number of subscriptions and unsubscriptions per day:

    {
        "subscriptions_stats": [{"subscription_datetime__date": "2023-02-27", "cnt": 3}],
        "unsubscriptions_stats": [{"datetime__date": "2023-02-27", "cnt": 1}]
    }

    GET http://localhost:8000/api/v1/newsletter/dispatches/stats/?ids=1-2-3

returns `{"dispatches": [...]}`, the non test dispatches of the given campaigns (dash separated campaign ids).

#### Subject suggestions

    POST http://localhost:8000/api/v1/newsletter/suggestions/subject/

with a json body `{"topic": "birds", "mean_age": 40}` asks an AI model (OpenAI `gpt-4o-mini`) for 5 newsletter subjects about the topic, for an audience of the given mean age. Returns `{"text": "..."}` with one subject per line.
Each client can perform at most `suggestions_per_day` requests per day. Requires the `AI_API_KEY` and `AI_ORGANIZATION` environment variables.

## <a name="unsubscription"></a>Unsubscription

The unsubscription url is configured in the __Topic__ (`unsubscribe_url` field) and is available in the campaign texts as `{{ unsubscribe_url }}`. The url is a template which can use the `{{ id }}`, `{{ email }}` and `{{ subscription_datetime }}` variables of the subscriber, and the `{% encrypt id email %}` tag, which generates an HMAC signature (with the client SECRET_KEY) of the concatenation of id and email.

There are two options:

- let Tazebao manage the unsubscription, using this url:

        https://www.tazebao.email/newsletter/unsubscribe/?id={{ id }}&email={{ email }}&sig={% encrypt id email %}

    Tazebao checks the signature, deletes the subscriber and shows a confirmation page.

- manage it in your own application: point the url to your application, check the signature there and, if it matches, call the delete action of the API.

## <a name="subscription-forms"></a>Subscription forms

Clients can create subscription forms (through the API or the admin) which are hosted by Tazebao at:

    /newsletter/subscribe/<CODE>/

the full url is returned in the `standalone_link` field. Subscribers registered through the form are created with `opt_in` set to true and added to the lists of the form. After the subscription the user is redirected to `success_url`, if set.

## <a name="mosaico-integration"></a>Mosaico Integration

Tazebao relies on [mosaico](https://github.com/voidlabs/mosaico/) in order to provide a template generator engine.
The mosaico core lib has been touched only to prevent url encoding of django template tags and variables. The e-mail templates have been hacked in order to integrate some Tazebao functionalities.

## <a name="getting-started"></a>Getting Started

Requirements: Python 3.12 (see `.python-version`), MySQL 8, Redis (celery broker).

To be up and running for local development just follow these steps:

- clone the repository    
  `$ git clone https://github.com/otto-torino/tazebao.git`
- cd the new project    
  `$ cd tazebao`
- create a virtualenv    
  `$ python3.12 -m venv .venv312`
- activate it    
  `$ source .venv312/bin/activate`
- install requirements    
  `$ pip install -r tazebao/requirements/local.txt`
- create the `.env` file inside the django project folder (`tazebao/tazebao/.env`, not the repository root)    
  `$ cd tazebao && touch .env`
- config environment    
  `$ dotenv set DJANGO_SETTINGS_MODULE core.settings.local`    
  `$ dotenv set DB_PASSWORD <whatever>`    
  `$ dotenv set SECRET_KEY <whatever>`    
  `$ cd ..`
- run the server    
  `$ bin/runserver`
- enjoy    
  `http://localhost:8000`

Available environment variables:

| Variable | Description |
| --- | --- |
| `DJANGO_SETTINGS_MODULE` | `core.settings.local` or `core.settings.production` |
| `SECRET_KEY` | django secret key |
| `DB_NAME` | database name (default `dbtazebao`) |
| `DB_HOST` | database host (default `localhost`) |
| `DB_USER` | database user (default `tazebao`) |
| `DB_PASSWORD` | database password (required) |
| `POSTFIX_CLIENT_ID` | key used by the mail server to post bounces |
| `POSTFIX_CLIENT_SECRET` | secret used by the mail server to post bounces |
| `AI_API_KEY` | OpenAI api key, used by the subject suggestions |
| `AI_ORGANIZATION` | OpenAI organization, used by the subject suggestions |
| `REMOTE_DB_PWD` | remote db password, used by the fab commands |
| `REMOTE_USER_PWD` | remote user password, used by the fab commands |

Dependencies: `tazebao/requirements/common.in` lists the direct dependencies, `common.txt` is the frozen full set generated from it. To upgrade, edit `common.in`, install it in a clean Python 3.12 virtualenv and regenerate `common.txt` with `pip freeze`.

### Tests

The test suite pins the behaviour seen by external clients (HMAC and JWT API, Postfix bounces, tracking links in e-mails already sent, campaign sending, admin pages). It needs a throwaway MySQL server, by default on `127.0.0.1:3317`:

    $ docker run -d --name tazebao_test_mysql -e MYSQL_ROOT_PASSWORD=tazebao -p 127.0.0.1:3317:3306 mysql:8.0
    $ cd tazebao
    $ python manage.py test --settings=core.settings.test

Host, port and credentials can be changed with the `TEST_DB_HOST`, `TEST_DB_PORT`, `TEST_DB_USER`, `TEST_DB_PASSWORD` environment variables.

E-mails are queued and sent in blocks. The scheduling is managed with crontab, but the queue preparation is managed asynchronously with a celery task. That's because preparing thousand of e-mails for sending is a dispendious job to do within a request, and it would require a not-pleasant timeout setting.

To start celery services (first edit the paths in the `[program:tazebao-workers]` section of `supervisord.conf.local` to match your local setup):

- `supervisord -c supervisord.conf.local`

To monitor celery workers:

- `supervisorctl -c supervisord.conf.local`    
  inside the prompt start, stop and see the status:    
  - start all
  - stop all
  - status

## <a name="scheduled-jobs"></a>Scheduled jobs

Two management commands must be scheduled with a crontab:

    $ python manage.py send_queued_messages [--limit N]

sends the queued e-mails (in blocks of N e-mails if `--limit` is given), and

    $ python manage.py dispatch_planned_campaigns

launches the planned dispatches whose schedule date has passed.

## <a name="remote-setup"></a>Remote setup

Remote setup is done with ansible, using the root user, the scripts are configured for debian based distros.    
First you need to configure your remote host inventory and variables.

Create a file `provisioning/ansible_remote_inventory` with the following content:

    remote ansible_ssh_host=<YOUR_DOMAIN_HERE>

then create a `provisioning/ansible_remote_variables` file:

    ---
    provisioning: 'remote'
    domain: '<YOUR_DOMAIN_HERE>'
    mysql_root_password: '<MYSQL_ROOT_PWD>'
    db_user: '<CHOOSE_A_DB_USER>'
    db_password: '<CHOOSE_A_DB_PWD>'
    db_name: '<CHOOSE_A_DB_NAME>'
    user: '<CHOOSE_THE_REMOTE_USER_TIED_TO_THE_APP>'
    password: '<..AND_ITS_PWD>'
    webapp_dir: '<REMOTE_WEBAPP_DIR>'

Ok you're ready for the provisioning phase, launch

    $ bin/ansible_remote

and provide the remote root password when prompted.

If all goes well, now you should have your remote machine ready for deploy.
Visit your domain and you should see a maintenance page already there.

A staging environment can be provisioned the same way, creating the `provisioning/ansible_staging_inventory` and `provisioning/ansible_staging_variables` files and launching

    $ bin/ansible_staging

### Celery configuration

Celery has a production ready configuration file you find in the ROOT of the repository:

`supervisord.conf.production`

It is configured for the production server (user __otto__, webapp dir `/home/otto/www/tazebao`, virtualenv `.venv312`); customize the following section to match a different remote user and remote paths:

    [program:tazebao-workers]
    command=/home/otto/www/tazebao/.venv312/bin/celery --app=core.celery:app worker --loglevel=INFO
    directory=/home/otto/www/tazebao/releases/current
    user=otto
    numprocs=1
    stdout_logfile=/home/otto/www/tazebao/logs/celery-worker.log
    stderr_logfile=/home/otto/www/tazebao/logs/celery-worker.log
    autostart=true
    autorestart=true
    startsecs=10

(leave the nested parts of the paths as they are, or it'll not work).

As for now it is not uploaded during the provisioning phase with ansible, so you have to do it manually:

    $ scp supervisord.conf.production USER@HOST:/PATH/TO/REMOTE/WEBAPP/DIR

### Troubleshooting

#### SSH connection error
If you see this error

    fatal: [remote] => Using a SSH password instead of a key is not possible because Host Key checking is enabled and sshpass does not support this.  Please add this host's fingerprint to your known_hosts file to manage this host.

means you missed adding an entry for one or more hosts in the `~/.ssh/known_hosts` file, it's enough to connect once to the host via ssh and accept its fingerprint.

#### DB task error
If an error occurs in the create db user task:

    msg: (1396, "Operation CREATE USER failed for ...

maybe you're trying to create a user which already existed and was delete. In this case just run this sql in the mysql database:

    FLUSH PRIVILEGES;

see [this answer on stack overflow](http://stackoverflow.com/questions/5555328/error-1396-hy000-operation-create-user-failed-for-jacklocalhost)


## <a name="deploy"></a>Deploy and Stuff

Deploy is done with [fabric](https://www.fabfile.org/) 3 (installed by `requirements/local.txt`). Two environments are configured in `tazebao/fabfile.py`:

- `production`: `otto@tazebao.email`, webapp dir `/home/otto/www/tazebao`
- `staging`: `otto@tazebao.sqrt64.it`, webapp dir `/home/otto/www/tazebao`

The fab commands read the `REMOTE_DB_PWD` and `REMOTE_USER_PWD` variables from the `.env` file.

In the deployment process, the last revision of the git repository is deployed to the remote server.
So be sure to have committed all your changes:

    $ git add --all
    $ git commit -a -m "first commit"

Be sure the provided remote user has ssh access to the remote host, then deploy should be as easy as:

    $ cd tazebao
    $ fab production deploy

launched from the repository root after moving into the django project folder (where `fabfile.py` lives). Use `fab staging deploy` to deploy to staging. This command does the following things:

- create an archive of the last repository revision
- upload it to the server
- untar it in a folder "app-revision\_id" inside the releases folder
- copy the .env file inside this folder
- upgrade the virtualenv (`.venv312` in the webapp dir, created with `/usr/bin/python3.12` if missing)
- collectstatic
- migrations
- move the current release in the previous release (releases/previous)
- link the releases/current folder to the new release folder
- restart uwsgi and reload nginx
- open a shell in the remote

When performing the first deploy you can create a superuser account using the shell which the script leaves open at the end.

When deploying the first time you need also to start celery workers, so inside the open shell session:

    $ supervisord -c ../../supervisord.conf.production

As in locale you can monitor the supervisor status and start and stop processes:

    $ supervisorctl -c ../../supervisord.conf.production

When you deploy again it won't be necessary to repeat the command above, because the processes are already running. But if you changed the configuration or the tasks you may need to restart this stuff, so:


    $ supervisorctl -c ../../supervisord.conf.production
    $ > stop all
    $ > exit
    $ supervisord -c ../../supervisord.conf.production

Then just check with `ps ax | grep supervisor` and `ps ax | grep celery` if all is ok, if not just `kill -9` the processes and restart supervisord.

### <a name="upgrade-2026"></a>Upgrade to Python 3.12 / Django 5.2 (one-time)

Until November 2026 production ran Python 3.8 / Django 2.2 from the `.virtualenv` virtualenv. The new code runs on the system Python 3.12 of the server (Ubuntu 24.04) in a new virtualenv, `.venv312`; the old one stays untouched for the rollback. No system package is needed: `python3.12-venv`, `python3.12-dev`, `libmysqlclient-dev` and `pkg-config` are already installed.

uWSGI is switched by `fab production deploy`, while the celery workers and the crontab of `otto` still point to `.virtualenv`: once `releases/current` points to the new code they would fail, so they must be switched in the same session.

Before the deploy:

- check that the mosaico templates contain valid JSON (migration `mosaico.0017` converts the columns from `longtext` to `json`):

      SELECT id FROM mosaico_template WHERE NOT JSON_VALID(template_data) OR NOT JSON_VALID(meta_data);

  must return no rows
- dump the database (`fab production dumpDbSnapshot`): the migrations are not reversible for free
- tell the web app and desktop app users they will have to log in again: tokens issued by the old JWT library are not valid anymore (login, refresh and the `Authorization: JWT <token>` header did not change)

Deploy, on the server as `otto`:

- comment out the tazebao lines in the crontab (`crontab -e`)
- stop the celery workers: `supervisorctl -c supervisord.conf.production stop all`
- from the local machine: `fab production deploy`
- copy the new `supervisord.conf.production` to `/home/otto/www/tazebao/` and restart supervisord with it (`supervisorctl -c supervisord.conf.production shutdown`, then `supervisord -c supervisord.conf.production`)
- in the crontab replace `/home/otto/www/tazebao/.virtualenv/` with `/home/otto/www/tazebao/.venv312/` and uncomment the lines
- check: `ps ax | grep -E "uwsgi|celery"` shows the `.venv312` paths, `logs/cron_mail.log` and `logs/celery-worker.log` have no errors, a test campaign is delivered

Rollback: restore the database dump, `fab production rollback`, then point supervisord and the crontab back to `.virtualenv` and restart uWSGI with `/home/otto/www/tazebao/.virtualenv/bin/uwsgi -H /home/otto/www/tazebao/.virtualenv --ini /home/otto/www/tazebao/releases/current/uwsgi.ini`.

### Other useful fab commands

Run `fab -l` to list all the available commands.

#### rollback

    $ fab production rollback

If the deploy revision is broken, or introduces unexpected errors, with this command
it is possible to rollback to the previous revision. Launching it another time will swap between the two revisions.

#### restart-uwsgi

    $ fab production restart-uwsgi

Restarts the uwsgi service

#### reloadServer

    $ fab production reloadServer

Reloads the web server (nginx)

#### restart

    $ fab production restart

Restarts the uwsgi service and reloads the web server

#### offline / online

    $ fab production offline
    $ fab production online

Puts the site in maintenance mode / exits from maintenance mode

#### getRemoteRevision

    $ fab production getRemoteRevision

Shows the revision currently deployed on the remote server

#### dumpDbSnapshot

    $ fab production dumpDbSnapshot

Downloads the production current db snapshot in the backups folder. The dumped file has the remote current revision name.

Requires the remote db user password.

#### loadDbSnapshot

    $ fab production loadDbSnapshot

Dumps the current remote db snapshot, downloads it and loads it in the local db (the local db is reset).

Requires the remote db user password.

#### loadDb

    $ fab production loadDb

Loads an already downloaded db snapshot in the local db.

## <a name="related-repositories"></a>Related repositories

- [tazebao-client](https://github.com/otto-torino/tazebao-client): client libraries for the REST web service
- [tazebao-desktop](https://github.com/otto-torino/tazebao-desktop): desktop application
