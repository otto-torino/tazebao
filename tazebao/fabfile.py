"""Deploy and maintenance tasks (fabric 3).

    $ cd tazebao
    $ fab production deploy

Every task runs without prompts, except dumpDbSnapshot (db password) and
reloadServer (sudo password), which are not part of a deploy.

Environment variables (from tazebao/.env or the shell):
    PRODUCTION_HOST   ssh host of the production server (default tazebao.email)
    STAGING_HOST      ssh host of the staging server (default tazebao.sqrt64.it)
    REMOTE_DB_PWD     remote db password, only for dumpDbSnapshot
    REMOTE_USER_PWD   remote user password, only for reloadServer (sudo)
"""
import os
import sys
import time
import threading
import urllib.error
import urllib.request

from dotenv import load_dotenv  # type: ignore
from fabric import Connection, task  # type: ignore
from invoke import Responder  # type: ignore

# virtualenv directory, relative to the project root (local) or to the remote path
VIRTUALENV_DIR = '.venv312'
# interpreter used to create the remote virtualenv (Ubuntu 24.04 system python)
REMOTE_PYTHON = '/usr/bin/python3.12'
# supervisord config, in the remote path (not part of the release)
SUPERVISOR_CONF = 'supervisord.conf.production'
SUPERVISOR_PROGRAM = 'tazebao-workers'


def here(*args):
    return os.path.join(os.path.dirname(os.path.realpath(__file__)), *args)


load_dotenv(here('.env'))


def env(name, default=None):
    return os.environ.get(name, default)


class Spinner:
    busy = False
    delay = 0.1

    @staticmethod
    def spinning_cursor():
        while 1:
            for cursor in '|/-\\':
                yield cursor

    def __init__(self, delay=None):
        self.spinner_generator = self.spinning_cursor()
        if delay and float(delay):
            self.delay = delay

    def spinner_task(self):
        while self.busy:
            sys.stdout.write(next(self.spinner_generator))
            sys.stdout.flush()
            time.sleep(self.delay)
            sys.stdout.write('\b')
            sys.stdout.flush()

    def __enter__(self):
        self.busy = True
        d = threading.Thread(target=self.spinner_task)
        d.start()

    def __exit__(self, exception, value, tb):
        self.busy = False
        time.sleep(self.delay)
        if exception is not None:
            return False


class bcolors:
    HEADER = '\033[1m\033[33m'
    INFO = '\033[94m'
    SUCCESS = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def print_(text, color):
    print(getattr(bcolors, color) + text + bcolors.ENDC + (bcolors.ENDC if color == 'HEADER' else ''))  # noqa


def get_env(ctx, var=None):
    if var is None:
        return ctx.config.run.env
    return ctx.config.run.env[var]


def set_env(ctx, var, val):
    ctx.config.run.env[var] = val


def get_connection(ctx):
    if 'conn' not in ctx.config.run.env:
        print_('Choose an environment first, e.g. "fab production deploy"', 'FAIL')
        sys.exit(1)
    return ctx.config.run.env['conn']


def remote_exists(c, path):
    return c.run(f"test -e {path}", warn=True, hide=True).ok


def remote_path(ctx, *parts):
    return os.path.join(get_env(ctx, 'path'), *parts)


def virtualenv_path(ctx):
    return remote_path(ctx, VIRTUALENV_DIR)


def sudo_responder(ctx):
    return Responder(
        pattern=r'\[sudo\] password',
        response=f"{get_env(ctx, 'sudo_password')}\n"
    )


def db_password_responder(ctx):
    return Responder(
        pattern=r'Enter password',
        response=f"{get_env(ctx, 'db_password')}\n"
    )


def describe_revision(ctx, head='HEAD', log=True):
    """ Describes the current local revision """
    c = get_connection(ctx)
    result = c.local(f"git describe --always {head}", hide=True)
    tag = result.stdout.rstrip()
    if log:
        print(f"Current tag of {head}: {tag}")
    return tag


def get_release_filename(ctx, head='HEAD', log=True):
    return f"{describe_revision(ctx, head, log)}.tar.gz"


def get_release_filepath(ctx, head='HEAD', log=True):
    releases_dir = here('..', 'releases')
    if not os.path.exists(releases_dir):
        os.makedirs(releases_dir)
    return os.path.join(releases_dir, get_release_filename(ctx, head, log))


def check_working_tree(ctx, head):
    """ Only committed code is deployed: warn about local changes """
    c = get_connection(ctx)
    branch = c.local('git rev-parse --abbrev-ref HEAD', hide=True).stdout.strip()
    print(f"Deploying {head} of branch {branch}")
    dirty = c.local('git status --porcelain --untracked-files=no', hide=True).stdout.strip()
    if dirty and head == 'HEAD':
        print_('Uncommitted changes are NOT deployed:', 'WARNING')
        print(dirty)


def sync_virtualenv(ctx, requirements_path):
    """ Creates the virtualenv if missing and installs the requirements """
    c = get_connection(ctx)
    venv = virtualenv_path(ctx)
    if not remote_exists(c, venv):
        print(f"Creating virtualenv {venv} with {REMOTE_PYTHON}")
        c.run(f"{REMOTE_PYTHON} -m venv {venv}")
        c.run(f"{venv}/bin/pip install --upgrade pip", hide='stdout')
    result = c.run(f"{venv}/bin/pip install -r {requirements_path}", hide='stdout')
    changes = [line for line in result.stdout.split('\n')
               if line and not line.startswith('Requirement already satisfied')]
    print('\n'.join(changes) if changes else 'All requirements already satisfied')


def check_site(ctx, attempts=10):
    """ GETs the site url until it answers 200 """
    url = get_env(ctx, 'check_url')
    last = None
    for _ in range(attempts):
        try:
            with urllib.request.urlopen(url, timeout=10) as response:
                if response.status == 200:
                    print_(f"{url} -> 200", 'SUCCESS')
                    return True
        except urllib.error.HTTPError as e:
            last = e.code
        except Exception as e:  # noqa
            last = str(e)
        time.sleep(2)
    print_(f"{url} -> {last}", 'FAIL')
    return False


def get_dump_filepath(ctx, prefix=u'backups', log=True):
    return f"../{prefix}/{getRemoteRevision(ctx, log)}.sql"


def reset_db(ctx):
    """ Resets the local db """
    c = get_connection(ctx)
    print_('Flushing local db', 'INFO')
    c.local(f"source {here('..', VIRTUALENV_DIR, 'bin', 'activate')} && python manage.py flush")
    print_('Done!', 'SUCCESS')


@task
def production(ctx):
    """ Production server settings """
    ctx.config.run.env['path'] = '/home/otto/www/tazebao'
    ctx.config.run.env['conn'] = Connection(host=env('PRODUCTION_HOST', 'tazebao.email'), user='otto')
    ctx.config.run.env['check_url'] = 'https://www.tazebao.email/'
    ctx.config.run.env['db_password'] = env('REMOTE_DB_PWD')
    ctx.config.run.env['sudo_password'] = env('REMOTE_USER_PWD')


@task
def staging(ctx):
    """ Staging server settings """
    ctx.config.run.env['path'] = '/home/otto/www/tazebao'
    ctx.config.run.env['conn'] = Connection(host=env('STAGING_HOST', 'tazebao.sqrt64.it'), user='otto')
    ctx.config.run.env['check_url'] = 'https://tazebao.sqrt64.it/'
    ctx.config.run.env['db_password'] = env('REMOTE_DB_PWD')
    ctx.config.run.env['sudo_password'] = env('REMOTE_USER_PWD')


@task
def createReleaseArchive(ctx, head='HEAD'):
    """ Creates a local release archive """
    print_("Creating release archive", 'INFO')
    c = get_connection(ctx)
    # run from this folder: only the django project is archived
    c.local('cd {0} && git archive --worktree-attributes --format=tar.gz {1} > {2}'.format(  # noqa
        here(), head, get_release_filepath(ctx, head)))
    print_("Done!", 'SUCCESS')


@task(help={
    'head': 'git revision to deploy (default HEAD)',
    'requirements': 'requirements file inside the release',
    'shell': 'open a shell on the server at the end',
})
def deploy(ctx, head='HEAD', requirements='requirements/production.txt', shell=False):
    """ Deploys a git revision: upload, virtualenv, static, migrations, restart """
    print_("Running task 'deploy'", 'HEADER')
    c = get_connection(ctx)
    check_working_tree(ctx, head)

    createReleaseArchive(ctx, head)
    release_filename = get_release_filename(ctx, head, log=False)
    current_version = describe_revision(ctx, head, log=False)

    releases_dir = remote_path(ctx, 'releases')
    release_dir = os.path.join(releases_dir, f"app-{current_version}")
    current_release_dir = os.path.join(releases_dir, 'current')
    previous_release_dir = os.path.join(releases_dir, 'previous')
    venv = virtualenv_path(ctx)
    print(f"Remote release directory: {release_dir}")

    print_('Uploading release', 'INFO')
    with Spinner():
        c.put(get_release_filepath(ctx, head, False), remote=releases_dir + '/')
    print()
    c.run(f"rm -fr {release_dir} && mkdir -p {release_dir}")
    c.run(f"tar xf {os.path.join(releases_dir, release_filename)} -C {release_dir}")
    c.run(f"rm {os.path.join(releases_dir, release_filename)}")
    c.run(f"cp {remote_path(ctx, '.env')} {release_dir}")
    print_('Done!', 'SUCCESS')

    manage = f"cd {release_dir} && {venv}/bin/python manage.py"

    print_('Syncing virtualenv', 'INFO')
    sync_virtualenv(ctx, f"{release_dir}/{requirements}")

    print_('Checking the release', 'INFO')
    c.run(f"{manage} check")

    print_('Collecting static files', 'INFO')
    c.run(f"{manage} collectstatic --noinput", hide='stdout')

    print_('Running migrations', 'INFO')
    c.run(f"{manage} migrate --noinput")

    print_('Setting current/previous releases', 'INFO')
    if remote_exists(c, current_release_dir):
        previous_version = c.run(f"basename $(readlink -f {current_release_dir})", hide=True).stdout.strip()
        if previous_version != f"app-{current_version}":
            c.run(f"rm -f {previous_release_dir} && mv {current_release_dir} {previous_release_dir}")
        else:
            c.run(f"rm {current_release_dir}")
    c.run(f"ln -s {release_dir} {current_release_dir}")
    c.run(f"ls -l {current_release_dir} {previous_release_dir}", warn=True)

    restart(ctx)

    if shell:
        c.run(f"cd {current_release_dir} && source {venv}/bin/activate && /bin/bash", pty=True)


@task
def rollback(ctx):
    """
    Swaps the current and previous releases and restarts.
    The previous release must work with the current virtualenv and db schema.
    """
    print_("Running task 'rollback'", 'HEADER')
    c = get_connection(ctx)
    path = get_env(ctx, 'path')
    c.run(f"cd {path}/releases && mv current _previous && mv previous current && mv _previous previous")
    c.run(f"ls -l {path}/releases/current {path}/releases/previous")
    restart(ctx)


@task
def getRemoteRevision(ctx, log=True):
    """ Returns and prints the current deployed remote revision """
    c = get_connection(ctx)
    current_app_dir = c.run(f"basename $(readlink -f {remote_path(ctx, 'releases', 'current')})", hide=True).stdout.strip()  # noqa
    remote_revision = current_app_dir.split('-', 1)[1] if '-' in current_app_dir else 'unknown'
    if log:
        print(f"Current remote revision: {remote_revision}")
    return remote_revision


@task
def dumpDbSnapshot(ctx):
    """ Dump of the production current db """
    print_("Dumping remote db", 'INFO')
    remote_tmp_file_path = '/tmp/dump_db.sql'
    c = get_connection(ctx)
    c.local(f"mkdir -p {here('..', 'backups')}")
    c.run(f"mysqldump --no-tablespaces --user tazebao --password dbtazebao > {remote_tmp_file_path}",  # noqa
          pty=True,
          watchers=[db_password_responder(ctx)])

    print_('Downloading db snapshot', 'INFO')
    with Spinner():
        c.get(remote_tmp_file_path, local=get_dump_filepath(ctx, log=False))
        print()
        print_('Done!', 'SUCCESS')
    c.run(f"rm {remote_tmp_file_path}")


@task
def loadDbSnapshot(ctx):
    """ Loads the production db snapshot in the local db """
    print_("Running task 'loadDbSnapshot'", 'HEADER')
    dumpDbSnapshot(ctx)
    reset_db(ctx)
    loadDb(ctx)


@task
def loadDb(ctx):
    """ Loads the downloaded production db snapshot in the local db """
    c = get_connection(ctx)
    print_('Loading db snapshot', 'INFO')
    c.local(f"source {here('..', VIRTUALENV_DIR, 'bin', 'activate')} && cat {get_dump_filepath(ctx, log=False)} | python manage.py dbshell")  # noqa
    print_('Done!', 'SUCCESS')


@task
def offline(ctx):
    """ Puts the site offline (manteinance page showed) """
    c = get_connection(ctx)
    c.run(f"touch {remote_path(ctx, 'releases', 'current', '.maintenance')}")
    print_('Site in maintenance mode', 'SUCCESS')


@task
def online(ctx):
    """ Puts the site online (manteinance page removed) """
    c = get_connection(ctx)
    c.run(f"rm -f {remote_path(ctx, 'releases', 'current', '.maintenance')}")
    print_('Site online', 'SUCCESS')


@task
def reloadServer(ctx):
    """ Reload nginx (needs REMOTE_USER_PWD, not needed by deploy) """
    print_("Reloading web server...", 'INFO')
    c = get_connection(ctx)
    c.sudo(
        '/etc/init.d/nginx reload',
        pty=True,
        hide='stdout',
        watchers=[sudo_responder(ctx)])
    print_("Done!", 'SUCCESS')


@task
def restart_uwsgi(ctx):
    """ Stops every uWSGI process of the app (orphans included) and starts it from releases/current """
    print_("Restarting uWSGI...", 'INFO')
    c = get_connection(ctx)
    path = get_env(ctx, 'path')
    venv = virtualenv_path(ctx)
    # "[b]in" so that pgrep does not match the shell running it
    pattern = f"[b]in/uwsgi -H {path}/"
    pids = c.run(f"pgrep -u $(whoami) -f '{pattern}'", warn=True, hide=True).stdout.split()
    if pids:
        print(f"Stopping uWSGI processes: {' '.join(pids)}")
        c.run(f"kill -INT {' '.join(pids)}", warn=True)
        for _ in range(20):
            if not c.run(f"pgrep -u $(whoami) -f '{pattern}'", warn=True, hide=True).ok:
                break
            time.sleep(1)
        else:
            print_('Some uWSGI processes did not stop, killing them', 'WARNING')
            c.run(f"pkill -KILL -u $(whoami) -f '{pattern}'", warn=True)
    c.run(f"rm -f {path}/uwsgi.pid /tmp/project-master_tazebao.pid", warn=True)
    c.run(f"cd {path}/releases/current && {venv}/bin/uwsgi -H {venv} --ini {path}/releases/current/uwsgi.ini")
    for _ in range(15):
        if c.run(f"test -S /tmp/uwsgi_tazebao.sock && kill -0 $(cat {path}/uwsgi.pid)", warn=True, hide=True).ok:
            break
        time.sleep(1)
    else:
        print_(f"uWSGI did not start, see {path}/logs/tazebao.log", 'FAIL')
        sys.exit(1)
    count = c.run(f"pgrep -u $(whoami) -fc '{pattern}'", warn=True, hide=True).stdout.strip()
    print_(f"uWSGI running ({count} processes)", 'SUCCESS')


@task
def restart_workers(ctx):
    """ Restarts the celery workers (starts supervisord if it is not running) """
    print_("Restarting celery workers...", 'INFO')
    c = get_connection(ctx)
    path = get_env(ctx, 'path')
    ctl = f"cd {path} && {virtualenv_path(ctx)}/bin/supervisorctl -c {SUPERVISOR_CONF}"
    if c.run(f"{ctl} pid", warn=True, hide=True).ok:
        c.run(f"{ctl} restart {SUPERVISOR_PROGRAM}")
    else:
        print('supervisord is not running, starting it')
        c.run(f"cd {path} && {virtualenv_path(ctx)}/bin/supervisord -c {SUPERVISOR_CONF}")
        time.sleep(5)
    c.run(f"{ctl} status")


@task
def restart(ctx):
    """ Restarts uWSGI and the celery workers, then checks the site """
    print_("Running task 'restart'", 'HEADER')
    restart_uwsgi(ctx)
    restart_workers(ctx)
    if not check_site(ctx):
        sys.exit(1)


@task
def status(ctx):
    """ Shows the deployed revision, the running processes and the site status """
    c = get_connection(ctx)
    path = get_env(ctx, 'path')
    getRemoteRevision(ctx)
    c.run(f"ls -l {path}/releases/current {path}/releases/previous", warn=True)
    c.run(f"echo uWSGI processes: $(pgrep -u $(whoami) -fc '[b]in/uwsgi -H {path}/')", warn=True)
    c.run(f"cd {path} && {virtualenv_path(ctx)}/bin/supervisorctl -c {SUPERVISOR_CONF} status", warn=True)
    check_site(ctx, attempts=1)


@task(help={'keep': 'how many releases to keep, besides current and previous'})
def cleanReleases(ctx, keep=5):
    """ Removes old release folders, never current and previous """
    c = get_connection(ctx)
    releases_dir = remote_path(ctx, 'releases')
    protected = set(c.run(
        f"basename $(readlink -f {releases_dir}/current); basename $(readlink -f {releases_dir}/previous)",
        hide=True, warn=True).stdout.split())
    folders = c.run(f"ls -1t {releases_dir} | grep '^app-'", hide=True).stdout.split()
    removable = [f for f in folders if f not in protected][int(keep):]
    if not removable:
        print('Nothing to remove')
        return
    print(f"Removing {len(removable)} releases: {' '.join(removable)}")
    c.run(f"cd {releases_dir} && rm -rf {' '.join(removable)}")
