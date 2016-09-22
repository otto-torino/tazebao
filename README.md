![image](https://raw.githubusercontent.com/otto-torino/tazebao/master/tazebao/core/static/core/img/logo.png "Logo")

Otto srl newsletter web application.

## Table of Contents

* [What?](#what)
* [REST Web Service](#rest-webservice)
    * [REST Service Authentication](#rest-authentication)
    * [REST resources](#rest-resources)
* [Getting Started](#getting-started)
* [Remote setup](#remote-setup)
* [Deploy and Stuff](#deploy)

## <a name="what"></a>What?

Tazebao is a web application which aims to provide a newsletter service to other sites/applications.

Every platform __User__ can be associated to one __Client__ and manage a newsletter. The platform provides an administrative area where the client user can manage its data.

Tazebao provides the following entities:

- subscriber
- list of subscribers
- topic
- campaign
- dispatch
- dispatch queue log

Each __Subscriber__ must belong to one or more lists (__SubscriberList__). Subscriber's e-mail must be unique for each client.
Each __Campaign__ must belong to a __Topic__, which stores the information about the sender name and address.
The newsletter is sent creating a __Dispatch__, where the user chooses one or more lists of subscribers which will receive the e-mail.

The __Subscriber__ has an __info__ text field which can be used to store additional information, for example in a json format.

E-mails are prepared asynchronously through a celery task, queued and sent in blocks. The scheduling must be set with a crontab, Tazebao uses the [django-mail-queue application](https://github.com/dstegelman/django-mail-queue/) in order to manage this stuff.    
Just set a crontab which calls 

    $ python manage.py send_queued_messages

Tazebao provides a REST webservice in order to retrieve, create, edit and delete subscribers and lists. Each Client can then implement its own registration form and use the provided API to update Tazebao DB. Also the unsubscription feature must be implemented by the Client, which will then use the API to delete the record from Tazebao. Tazebao provides a functionality which can be used to create a signed string of subscriber's data used to generate the unsubscription url.
Unsubscription text is managed in the Topic section of Tazebao. For example you can generate a URL which includes a signature of the ID and EMAIL of the subscriber, then you can check the signature in your own application, and if matches call the delete action of the API.

## <a name="rest-webservice"></a>REST Web Service

The admin application authentication is a session based authentication, while the web service uses HMAC (Keyed-Hash Message Authentication Code).

Each Client gets an ID_KEY and a SECRET_KEY through which authenticate to Tazebao. The Signature must be passed in the HTTP header of every request, Tazebao uses [django-rest-framework-httpsignature](https://github.com/etoccalino/django-rest-framework-httpsignature) to manage this stuff.

### <a name="rest-authentication"></a>REST Service Authentication

In order to perform valid requests to the REST resources, every request must be signed in the HTTP header.
The signature must be calculated this way:

    SIGNATURE = Base64(Hmac('SECRET_KEY', "date: DATETIME", 'sha256'))

And the request should be:

    ~$ curl -v -H 'Date: "DATETIME"' -H 'Authorization: Signature keyId="ID_KEY",algorithm="hmac-sha256",headers="date",signature="SIGNATURE"'

this was descriptive code, take a look at the [client repository](https://github.com/otto-torino/tazebao-client) to see how to implement this stuff in real languages.

### <a name="rest-resources"></a>REST resources

Tazebao provides a REST Web Service which allows to manage subscribers and lists data.

#### Subscribers Lists

This section describes possible CRUD requests to manage subscribers's lists.

##### Retrieve lists

    GET http://localhost:8000/api/v1/newsletter/subscriberlist/

returns a list of subscribers' lists associated to the authenticated client, i.e.:

    [{"id":1,"name":"Journalists"},{"id":8,"name":"ACABS"}]

##### Get a list

    GET http://localhost:8000/api/v1/newsletter/subscriberlist/<LIST_ID>/

returns the list object represented by LIST_ID, i.e.:

    {"id":1,"name":"Journalists"}

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

returns a paginated (200 for page) list of subscribers associated to the authenticated client, i.e.:

    {
        "count": 300,
        "next": "http://localhost:8000/api/v1/newsletter/subscriber/?page=2",
        "previous": null,
        "results": [
            {
                "id":1,
                "client":1,
                "email":"email@example.com",
                "subscription_datetime":"2016-09-08T14:49:58.860948Z",
                "info":"custom stuff",
                "lists":[1]
            },
            {
                "id":2,
                "client":1,
                "email":"email2@example.com",
                "subscription_datetime":"2016-09-08T14:59:58.860948Z",
                "info":"",
                "lists":[1, 2]
            },
            // ... 198 more
        ]
    }

##### Get a subscriber

    GET http://localhost:8000/api/v1/newsletter/subscriber/<SUBSCRIBER_ID>/

returns the subscriber object represented by SUBSCRIBER_ID, i.e.:

    {
        "id":2,
        "client":1,
        "email":"email2@example.com",
        "subscription_datetime":"2016-09-08T14:59:58.860948Z",
        "info":"",
        "lists":[1, 2]
    }

##### Add a subscriber

    POST http://localhost:8000/api/v1/newsletter/subscriber/

the POST data should be a json of the following format:

    "{"email":"xxx@abidibo.net","info":"\"firstname=\"meow\"\"","lists":["1"]}" 

email and lists fields are required.

##### Edit a subscriber

    PUT http://localhost:8000/api/v1/newsletter/subscriber/<SUBSCRIBER_ID>/

the POST data should be a json of the following format:

    "{"email":"xxx@abidibo.net","info":"\"firstname=\"meow\"\"","lists":["1"]}" 

email and lists fields are required.

##### Delete a subscriber

    DELETE http://localhost:8000/api/v1/newsletter/subscriber/<SUBSCRIBER_ID>/

#### Campaigns

Campaign models are readonly, so you can only retrieve a list of paginated campaigns, or a single campaign.
This resource is usefull in order to display the newsletter content on your own application, or to create
a newsletter archive.

##### Retrieve campaigns

    GET http://localhost:8000/api/v1/newsletter/campaign/

returns a paginated (20 for page) list of campaigns associated to the authenticated client, i.e.:

    {
        "count": 2,
        "next": "http://localhost:8000/api/v1/newsletter/campaign/?page=2",
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
                "url": "http://localhost:8000/newsletter/client-slug/2016/09/08/campaign-slug/"
            }
            // ... 19 more
        ]
    }

##### Get a campaign

    GET http://localhost:8000/api/v1/newsletter/campaign/<CAMPAIGN_ID>/

returns the campaign object represented by CAMPAIGN_ID, i.e.:

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
        "url": "http://localhost:8000/newsletter/client-slug/2016/09/08/campaign-slug/"
    }



## <a name="getting-started"></a>Getting Started

To be up and running for local development just follow these steps:

- clone the repository    
  `$ git clone https://github.com/otto-torino/tazebao.git`
- cd the new project    
  `$ cd [repo_name]`
- create a virtualenv    
  `$ virtualenv --no-site-packages .virtualenv`
- activate it    
  `$ source .virtualenv/bin/activate`
- install requirements    
  `$ pip install -r [repo_name]/requirements/local.txt`
- create a .env file    
  `$ touch .env`
- config environment    
  `$ dotenv set DJANGO_SETTINGS_MODULE core.settings.local`    
  `$ dotenv set DB_PASSWORD <whatever>`
  `$ dotenv set SECRET_KEY <whatever>`
- run the server    
  `$ bin/runserver`
- enjoy    
  `http://localhost:8000`

E-mails are queued and sent in blocks. The scheduling is managed with crontab, but the queue preparation is managed asynchronously with a celery task. That's because preparing thousand of e-mails for sending is a dispendious job to do within a request, and it would require a not-pleasant timeout setting.

To start celery services:

- `supervisord -c supervisord.conf.local`

To monitor celery workers:

- `supervisorctl -c supervisord.conf.local`    
  inside the prompt start, stop and see the status:    
  - start all
  - stop all
  - status

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

### Celery configuration

Celery has a production ready configuration file you find in the ROOT of the repository:

`supervisord.conf.production`

You need to customize it in order to match your remote user and rempte paths, just edit the following section:

    [program:tazebao-workers]
    command=/home/tazebao/www/tazebao/.virtualenv/bin/celery --app=core.celery:app worker --loglevel=INFO
    directory=/home/tazebao/www/tazebao/releases/current
    user=tazebao
    numprocs=1
    stdout_logfile=/home/tazebao/www/tazebao/logs/celery-beat.log
    stderr_logfile=/home/tazebao/www/tazebao/logs/celery-beat.log
    autostart=true
    autorestart=true
    startsecs=10

(in this case the user is __tazebao__ and the webapp remote dir is `/home/tazebao/www/tazebao`, leave the nested parts of the paths as they are, or it'll not work).

As for now it is not uploaded during the provisioning phase with ansible, so you have to do it manually:

    $ scp supervisord.conf.production USER@HOST:/PATH/TO/REMOTE/WEBAPP/DIR

### Troubleshooting

#### SSH connection error
If you see this error

    fatal: [remote] => Using a SSH password instead of a key is not possible because Host Key checking is enabled and sshpass does not support this.  Please add this host's fingerprint to your known_hosts file to manage this host.

means you missed adding an entry for one or more hosts in the ~/.ssh/known_hosts file, it's enough to 

#### DB task error
If an error occurs in the create db user task:

    msg: (1396, "Operation CREATE USER failed for ...

maybe you're trying to create a user which already existed and was delete. In this case just run this sql in the mysql database:

    FLUSH PRIVILEGES;

see [this answer on stack overflow](http://stackoverflow.com/questions/5555328/error-1396-hy000-operation-create-user-failed-for-jacklocalhost])


## <a name="deploy"></a>Deploy and Stuff

In the deployment process, the last revision of the git repository is deployed to the remote server.
So be sure to have committed all your changes:

    $ git add --all
    $ git commit -a -m "first commit"

Be sure the provided remote user has ssh access to the remote host, then deploy should be as easy as:

    $ cd [repo_name]
    $ fab production deploy

launched inside the root/repo\_name folder. This command does the following things:

- create an archive of the last repository revision
- upload it to the server
- untar it in a folder "app-revision\_id" inside the releases folder
- copy the .env file inside this folder
- upgrade the virtualenv
- collectstatic
- migrations
- move the current release in the previous release (releases/previous)
- link the releases/current folder to the new release folder
- restart uwsgi and nginx
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

### Other useful fab commands

#### rollback

    $ fab production rollback

If the deploy revision is broken, or introduces unexpected errors, with this command
it is possible to rollback to the previous revision. Launching it another time will swap between the two revisions.

#### restart\_uwsgi

    $ fab production restart_uwsgi

Restarts the uwsgi service

#### restart\_server

    $ fab production restart_server

Restarts the web server

#### restart

    $ fab production restart

Restarts the uwsgi service and the web server

#### dump\_db\_snapshot

    $ fab production dump_db_snapshot

Downloads the production current db snapshot in the backup folders. The dumped file has the remote current revision name.

Requires the remote db user password.

#### load\_db\_snapshot

    $ fab production load_db_snapshot

Loads the current remote db snapshot in the local db.

Requires the remote db user password.
