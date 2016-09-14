# Tazebao

![image](https://raw.githubusercontent.com/otto-torino/tazebao/master/tazebao/core/static/core/img/logo.png "Logo")

Otto srl newsletter web application

## What?

Tazebao is a web application which aims to provide a newsletter service to other sites/applications.

Every platform __User__ can be associated to one __Client__ and manage a newsletter. The platform provides an administrative area where the client user can manage its data.

Tazebao provides these entities:

- subscriber
- list of subscribers
- topic
- campaign
- dispatch

Each __Subscriber__ must belong to one or more lists (__SubscriberList__). Subscriber's e-mail must be unique for each client.
Each __Campaign__ must belong to a __Topic__, which stores the information about the sender name and address.
The newsletter is sent creating a __Dispatch__, where the user chooses one or more lists of subscribers which will receive the e-mail.

The __Subscriber__ has an __info__ text field which can be used to store additional information, for example in a json format.

E-mails are queued and sent in blocks, the scheduling must be set with a crontab, Tazebao uses the [django-mail-queue application](https://github.com/dstegelman/django-mail-queue/) in order to manage this stuff.
Just set a crontab which calls 

    $ python manage.py send_queued_messages

Tazebao provides a REST webservice in order to retrieve, create, edit and delete subscribers and lists. Each Client can then implement its own registration form and use the provided API to update Tazebao DB. Also the unsign feature must be implemented by the Client, which will then use the API to delete the record from Tazebao.

The admin application authentication is a session based authentication, while the web service uses HMAC (Keyed-Hash Message Authentication Code).
Each Client gets an ID_KEY and a SECRET_KEY through which authenticate to Tazebao. The Signature must be passed in the HTTP header of every request, Tazebao uses [django-rest-framework-httpsignature](https://github.com/etoccalino/django-rest-framework-httpsignature) to manage this stuff.

### REST Service Authentication

In order to perform valid requests to the REST Endpoint, every request must be signed in the HTTP header.
The signature must be calculated this way:

    SIGNATURE = Base64(Hmac('SECRET_KEY', "date: DATETIME", 'sha256'))

And the request should be:

    ~$ curl -v -H 'Date: "DATETIME"' -H 'Authorization: Signature keyId="ID_KEY",algorithm="hmac-sha256",headers="date",signature="SIGNATURE"'

this was descriptive code, take a look at the [client repository](https://github.com/otto-torino/tazebao-client) to see how to implement this stuff in real languages.

## REST Web Service

Tazebao provides a REST Web Service which allows to manage subscribers and lists data.

### Subscribers Lists

This section describes possible CRUD requests to manage subscribers's lists.

#### Retrieve lists

    GET http://localhost:8000/api/v1/newsletter/subscriberlist/

returns a list of subscribers' lists associated to the authenticated client, i.e.:

    [{"id":1,"name":"Journalists"},{"id":8,"name":"ACABS"}]

#### Add a list

    POST http://localhost:8000/api/v1/newsletter/subscriberlist/

the POST data should be a json containing the name field, i.e.:

    "{"name":"Journalists"}"

for example with PHP:

    $post_data = json_encode(array('name' => 'Journalists'))

#### Edit a list

    PUT http://localhost:8000/api/v1/newsletter/subscriberlist/<LIST_ID>/

the submitted data should be a json containing the name field, i.e.:

    "{"name":"Journalists"}"

#### Delete a list

    DELETE http://localhost:8000/api/v1/newsletter/subscriberlist/<LIST_ID>/

### Subscribers

This section describes possible CRUD requests to manage subscribers.

#### Retrieve subscribers

    GET http://localhost:8000/api/v1/newsletter/subscriber/

returns a list of subscribers associated to the authenticated client, i.e.:

    [{
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
    }]

#### Add a subscriber

    POST http://localhost:8000/api/v1/newsletter/subscriber/

the POST data should be a json of the following format:

    "{"email":"xxx@abidibo.net","info":"\"firstname=\"meow\"\"","lists":["1"]}" 

email and lists fields are required.

#### Edit a subscriber

    PUT http://localhost:8000/api/v1/newsletter/subscriber/<SUBSCRIBER_ID>/

the POST data should be a json of the following format:

    "{"email":"xxx@abidibo.net","info":"\"firstname=\"meow\"\"","lists":["1"]}" 

email and lists fields are required.

#### Delete a subscriber

    DELETE http://localhost:8000/api/v1/newsletter/subscriber/<SUBSCRIBER_ID>/

## Getting Started

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

## Remote setup

Remote setup is done with ansible, using the root user. Run

    $ bin/ansible_remote

and provide the root password when prompted.

If all goes well now you should have your remote machine ready for deploy.
Visit your domain and you should see a maintenance page already there.

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


## Deploy and Stuff

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

###Other useful fab commands

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
