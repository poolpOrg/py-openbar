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
logging interface
"""

import logging
import logging.config
import os.path
import socket
import traceback

_RUNINFO = {}
_LOGGER = logging.getLogger("openbar")

def debug(*args):
    """
    log with DEBUG
    """
    try:
        _LOGGER.debug(*args)
    except:
        error('LOG DEBUG FAILURE: %r', args)
        raise

def info(*args):
    """
    log with INFO
    """
    try:
        _LOGGER.info(*args)
    except:
        error('LOG INFO FAILURE: %r', args)
        raise

def warn(*args):
    """
    log with WARN
    """
    try:
        _LOGGER.warning(*args)
    except:
        error('LOG WARN FAILURE: %r', args)
        raise

def error(*args):
    """
    log with ERROR
    """
    try:
        _LOGGER.error(*args)
    except:
        error('LOG ERROR FAILURE: %r', args)
        raise

def exception(*args):
    """
    log exceptions as ERROR (best effort)
    """
    trace = traceback.format_exc()
    if args:
        ctx = args[0] % tuple(args[1:])
        trace = ctx + "\n---\n" + trace
    _LOGGER.error("Exception: %r", trace)


def setup(procname, debugging=False):
    """
    initialize the logging facility
    """
    _RUNINFO['service'] = procname
    _RUNINFO['host'] = socket.gethostname()
    _RUNINFO['debug'] = debugging

    logging.config.dictConfig({
        "version": 1,
        "formatters": {
            "default": {
                "format": " ".join(["%s[%%(process)s]:" % (procname, ),
                                    "%(levelname)s:",
                                    "%(message)s"]),
                "datefmt": "%Y/%m/%d %H:%M:%S",
            },
            "exception": {
                "format": "".join(["-" * 72 + "\n",
                                   "%(asctime)s",
                                   " %s[%%(process)s]:" % (procname, ),
                                   " %(levelname)s:",
                                   " %(message)s"]),
                "datefmt": "%Y/%m/%d %H:%M:%S",
            },
        },
        "handlers": {
            "syslog": {
                "class": "logging.handlers.SysLogHandler",
                "formatter": "default",
                "level": debug and "DEBUG" or "INFO",
                "address": "/dev/log" if os.path.exists("/dev/log") else "/var/run/syslog",
            },
            "stdout": {
                "class": "logging.StreamHandler",
                "formatter": "default",
                "level": debug and "DEBUG" or "INFO",
            },
            "null": {
                "class" : "logging.NullHandler",
                "formatter": "exception",
            }
        },
        "loggers": {
            "openbar": {
                "handlers" : [debug and "stdout" or "syslog"],
                "level": debug and "DEBUG" or "INFO",
                "propagate": False,
            },
        },
        "root": {
            "handlers": [debug and "stdout" or "syslog"],
            "level": "INFO",
        }
    })
