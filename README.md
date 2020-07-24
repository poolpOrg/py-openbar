README (for developers)
=======================

Environment
-----------
openbar is designed to work on Linux and BSD systems.
It is known to work on OpenBSD, Debian, Ubuntu, CentOS and OSX.

Requirements
------------
openbar assumes Python 3.4 or higher.


Initial setup
-------------
openbar requires being started as root but will then drop to an unprivileged user.

```
$ sudo useradd -s /sbin/nologin -d /var/openbar -m _openbar
```

Virtual environment
-------------------
The virtual environment ensures that dependencies are frozen and that openbar is
running with its dependencies and not ones overriden by system upgrades.

During development:
```
# virtualenv /venv
# /venv/bin/pip install /path/to/openbar/checkout
```

When changes are made to the code, perform an upgrade:
```
# /venv/bin/pip install --upgrade /path/to/openbar/checkout
```

Configuration
-------------
Sample configuration files are available in the etc/ subdirectory of the package.
They must be moved to /etc, by default openbar will search for an /etc/openbar.conf unless overriden.


Running and stopping
--------------------
openbar has two components, the frontend and the backend.
They are controlled through the `openbarctl` utility installed in the virtualenv.

To start openbar:
```
# /venv/bin/openbarctl frontend start
# /venv/bin/openbarctl backend start
```

To stop openbar:
```
# /venv/bin/openbarctl frontend stop
# /venv/bin/openbarctl backend stop
```

During development, the components may be started in foreground:
```
# /venv/bin/openbarctl -d frontend start
# /venv/bin/openbarctl -d backend start
```

When running in foreground, logs are written to stdout, otherwise they are sent to the syslog daemon.
