#
# Copyright (c) 2013 Eric Faurot <eric@faurot.net>
# Copyright (c) 2013,2017 Gilles Chehade <gilles@poolp.org>
#
# Permission to use, copy, modify, and distribute this software for any
# purpose with or without fee is hereby granted, provided that the above
# copyright notice and this permission notice appear in all copies.
#
# THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
# WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
# MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
# ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
# WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
# ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
# OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
#
"""
interface to create a daemonized running process
"""

import atexit
import errno
import grp
import os
import pwd
import signal
import sys
import time
import importlib

import bottle
from bottle.ext import beaker

import openbar.log
import openbar.routes
import openbar.templates

VERBOSE = 0
DAEMONIZE = 1

try:
    from setproctitle import setproctitle
except ImportError:
    def setproctitle(name):
        """
        stub for systems not supporting the setproctitle() function
        """
        _ = name

def _mkdir_p(*path):
    try:
        os.makedirs(os.path.join(*path))
    except OSError as exc:
        if exc.errno != errno.EEXIST:
            raise

class _Daemon(object):
    """
    A generic daemon class.

    Usage: subclass the Daemon class and override the run() method
    """
    def __init__(self,
                 procname,
                 username=None,
                 syslog=True,
                 pidfile=None):
        self.procname = procname
        self.syslog = syslog
        self.pidfile = pidfile
        self.username = username
        self.pwd = None
        self.run = None
        self.terminate = None

    def _open_log(self, debug=None):
        openbar.log.setup(self.procname, debugging=debug)

    def _write_pid(self):
        pid = self._get_pid()
        if pid is not None:
            if self._is_running(pid):
                message = "Error: process \"%s\" is already running with pid %i\n"
                sys.stderr.write(message % (self.procname, pid))
                sys.exit(1)
            else:
                message = "Warning: overwriting stale pidfile %s with pid %i\n"
                sys.stderr.write(message % (self.pidfile, pid))

        def _del_pid():
            os.remove(self.pidfile)
        atexit.register(_del_pid)
        _mkdir_p(os.path.dirname(self.pidfile))
        open(self.pidfile, 'w').write("%i\n" % os.getpid())

    def _drop_priv(self):
        if os.getuid() != 0:
            return
        groups = list(set([g.gr_gid for g in grp.getgrall() \
                           if self.pwd.pw_name in g.gr_mem] + [self.pwd.pw_gid]))
        os.setgroups(groups)
        try:
            os.setresgid(self.pwd.pw_gid, self.pwd.pw_gid, self.pwd.pw_gid)
            os.setresuid(self.pwd.pw_uid, self.pwd.pw_uid, self.pwd.pw_uid)
        except:
            os.setgid(self.pwd.pw_gid)
            os.setuid(self.pwd.pw_uid)

    def _daemonize(self):
        if DAEMONIZE == 2:
            return
        try:
            pid = os.fork()
            if pid > 0:
                sys.exit(0)
        except OSError as exc:
            sys.stderr.write("Cannot fork: %d (%s)\n" % (exc.errno, exc.strerror))
            sys.exit(1)

        os.setsid()
        #os.chdir("/")
        #os.umask(0)

        # do second fork
        try:
            pid = os.fork()
            if pid > 0:
                sys.exit(0)
        except OSError as exc:
            sys.stderr.write("Cannot fork: %d (%s)\n" % (exc.errno, exc.strerror))
            sys.exit(1)

        def _handler(signum, frame):
            if self.terminate:
                self.terminate()
            else:
                openbar.log.info("Got signal %i. Exiting", signum)
                sys.exit(0)
        signal.signal(signal.SIGTERM, _handler)

    def _start(self, foreground=True):
        if self.username is None:
            if os.getuid() == 0:
                sys.stderr.write("Refusing to run as superuser\n")
                sys.exit(1)
            self.pwd = pwd.getpwuid(os.getuid())
        else:
            self.pwd = pwd.getpwnam(self.username)
            if os.getuid() not in (0, self.pwd.pw_uid):
                sys.stderr.write("Cannot run as user \"%s\"\n" % (self.username, ))
                sys.exit(1)

        setproctitle(self.procname)

        if not foreground:
            self._drop_priv()
            self._pre_daemonize()
            self._daemonize()
            if self.pidfile:
                self._write_pid()
            self._open_log()
        else:
            self._drop_priv()
            self._pre_daemonize()
            self._open_log(debug=True)

        self.run()


    setup = None
    def _pre_daemonize(self):
        if self.setup:
            self.setup()

    def _get_pid(self):
        try:
            return int(open(self.pidfile).read())
        except IOError as exc:
            if exc.errno == errno.ENOENT:
                return
            raise

    def _is_running(self, pid=None):
        if pid is None:
            pid = self._get_pid()
        if pid is None:
            return False
        procname = self.procname.split('openbar-')[-1]

        for line in os.popen("ps aux").read().split("\n"):
            parts = line.split()
            if not parts:
                continue
            if parts[0] != self.username:
                continue
            try:
                ppid = int(parts[1])
            except:
                continue
            if ppid != pid:
                continue
            if procname in parts:
                return True
        return False

    def status(self):
        """
        check if daemonized process is running
        """
        return self._is_running() is not None

    def _kill(self, sig, wait=None):
        pid = self._get_pid()
        if pid is None:
            message = "Process \"%s\" is not running\n"
            sys.stderr.write(message % (self.procname))
            return

        if not self._is_running(pid):
            message = "Process \"%s\" is not running (stale pidfile %s with pid %i)\n"
            sys.stderr.write(message % (self.procname, self.pidfile, pid))
            return

        os.kill(pid, sig)
        timer0 = time.time()
        if wait:
            while self._is_running(pid):
                if time.time() - timer0 >= 10:
                    message = "Warning: process \"%s\" is still running\n"
                    sys.exit(1)
                time.sleep(.1)

    def stop(self):
        """
        stop daemonized process gracefully
        """
        self._kill(signal.SIGTERM, wait=True)

    def kill(self):
        """
        kill daemonized process
        """
        self._kill(signal.SIGKILL)

    def start(self, start, stop=None, setup=None, foreground=None):
        """
        start daemonized process
        """
        if foreground is None:
            foreground = not DAEMONIZE

        if self.pidfile and self._is_running():
            message = "Error: process \"%s\" is already running with pid %i\n"
            sys.stderr.write(message % (self.procname, self._get_pid()))
            sys.exit(1)

        self.run = start
        self.setup = setup
        self.terminate = stop
        self._start(foreground=foreground)

def daemon(*args, **kwargs):
    """
    public interface to instantiate a daemonized process
    """
    return _Daemon(*args, **kwargs)

#
# bottle runs
#
class _LogMiddleware(object):
    def __init__(self, app):
        self.app = app

    def __call__(self, environ, handler):

        def remote():
            forwarded_for = bottle.request.environ.get("HTTP_X_FORWARDED_FOR", None)
            if not forwarded_for:
                forwarded_for = bottle.request.environ.get("REMOTE_ADDR")
            return forwarded_for

        timer0 = time.time()
        environ['wsgi.errors'] = self
        ret = self.app(environ, handler)
        openbar.log.info("%.3f %s %s %i %i %s",
                          time.time() - timer0,
                          remote(),
                          bottle.request.method,
                          bottle.response.status_code,
                          bottle.response.content_length,
                          bottle.request.path)
        return ret

    def write(self, err):
        openbar.log.exception(err)

def run_bottle(action, host, port, packages, **kwargs):
    def _start():
        for package in packages:
            print(package)
            importlib.import_module(package)

        openbar.log.info("Started")
        openbar.log.info("Config: host=%s:%i", host, port)
        bottle.BaseRequest.MEMFILE_MAX = 10 * 1024 * 1024
        bottle._stdout = sys.stdout.write
        bottle._stderr = sys.stderr.write
        app = bottle.app()

        openbar.routes.install_routes(app)

        session_opts = {
            'session.type': 'file',
            'session.data_dir': '/tmp',
            'session.auto': True
        }
        app = beaker.middleware.SessionMiddleware(app, session_opts)
        bottle.run(app=_LogMiddleware(app),
                   host=host,
                   port=port,
                   server="cherrypy",
                   quiet=True)

    def _stop():
        openbar.log.info("Stopped")
        sys.exit(0)

    runner = openbar.run.daemon(**kwargs)
    if action == "restart":
        runner.stop()
        runner.start(_start, _stop)
    elif action == 'start':
        runner.start(_start, _stop)
    elif action == 'stop':
        runner.stop()
    elif action == 'status':
        sys.exit(1 - int(daemon.status()))
    elif action == 'kill':
        runner.kill()
    else:
        raise ValueError(action)

def run_backend(procname, action="start"):
    config = openbar.config.get(procname)
    packages = [_ for _ in config.get('packages').split() if _]
    openbar.run.run_bottle(action,
                            host = config.get('host'),
                            port = config.get('port'),
                            packages = packages,
                            procname=procname,
                            username=config.get('user'),
                            pidfile=config.get('pidfile'))

def run_frontend(procname, action="start"):
    config = openbar.config.get(procname)
    packages = [_ for _ in config.get('packages').split() if _]

    openbar.templates.set_path(config.get('templates'))

    openbar.run.run_bottle(action,
                            host = config.get('host'),
                            port = config.get('port'),
                            packages = packages,
                            procname=procname,
                            username=config.get('user'),
                            pidfile=config.get('pidfile'))