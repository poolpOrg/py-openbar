#
# Copyright (c) 2017 Gilles Chehade <gilles@poolp.org>
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
import configparser

import openbar.exceptions

_CONFIGFILE = None
_CONFIG = {}

def parse(filename):
    _CONFIGFILE = filename
    config = configparser.RawConfigParser()
    try:
        config.read(filename)
    except configparser.DuplicateSectionError as exc:
        raise openbar.exceptions.InvalidConfiguration("%s: %s" % (filename, exc))
    except configparser.DuplicateOptionError as exc:
        raise openbar.exceptions.InvalidConfiguration("%s: %s" % (filename, exc))
    if len(config) == 1:
        raise openbar.exceptions.InvalidConfiguration("empty or inexistant configuration file: %s" % filename)

    for section in config:
        if section == "DEFAULT":
            continue
        type_ = config[section].get('type')
        if type_ is None:
            raise openbar.exceptions.InvalidConfiguration("no type for section %s in configuration file: %s" % (section, filename))
        elif type_ == "frontend":
            parse_frontend(filename, section, config[section])
        elif type_ == "backend":
            parse_backend(filename, section, config[section])
        else:
            print(type_)
            raise openbar.exceptions.InvalidConfiguration("unknown section type %s for section %s in configuration file: %s" % (type_, section, filename))


def parse_frontend(filename, section, config):
    tmp = {}
    for key in ['type', 'host', 'port', 'user', 'secret', 'backend', 'packages', 'pidfile', 'templates', 'static', 'sitemap']:
        if config.get(key) is None:
            raise openbar.exceptions.InvalidConfiguration("%s: in section 'frontend': missing key '%s'" % (filename, key))
        tmp[key] = config.get(key)

    try:
        port = config.getint('port')
    except ValueError:
        raise openbar.exceptions.InvalidConfiguration("%s: in section 'frontend': invalid port number '%s'" % (filename, config.get('port')))
    tmp['port'] = port
    _CONFIG[section] = tmp


def parse_backend(filename, section, config):
    tmp = {}
    for key in ['type', 'host', 'port', 'user', 'secret', 'frontend', 'packages', 'pidfile']:
        if config.get(key) is None:
            raise openbar.exceptions.InvalidConfiguration("%s: in section 'backend': missing key '%s'" % (filename, key))
        tmp[key] = config.get(key)

    try:
        port = config.getint('port')
    except ValueError:
        raise openbar.exceptions.InvalidConfiguration("%s: in section 'backend': invalid port number '%s'" % (filename, config.get('port')))
    tmp['port'] = port
    _CONFIG[section] = tmp


def parse_database(filename, section, config):
    tmp = {}
    for key in ['engine', 'host', 'port', 'username', 'password']:
        if config.get(key) is None:
            raise openbar.exceptions.InvalidConfiguration("%s: in section 'database': missing key '%s'" % (filename, key))
        tmp[key] = config.get(key)

    try:
        port = config.getint('port')
    except ValueError:
        raise openbar.exceptions.InvalidConfiguration("%s: in section 'database': invalid port number '%s'" % (filename, config.get('port')))
    tmp['port'] = port
    _CONFIG[section] = tmp

def get(section):
    return _CONFIG.get(section)

def backend(key):
    if 'backend' not in _CONFIG:
        raise openbar.exceptions.InvalidConfiguration("%s: missing section 'backend'" % _CONFIGFILE)
    return _CONFIG.get('backend')[key]

def database(key):
    if 'database' not in _CONFIG:
        raise openbar.exceptions.InvalidConfiguration("%s: missing section 'database'" % _CONFIGFILE)
    return _CONFIG.get('database')[key]

def frontend(key):
    if 'frontend' not in _CONFIG:
        raise openbar.exceptions.InvalidConfiguration("%s: missing section 'frontend'" % _CONFIGFILE)
    return _CONFIG.get('frontend')[key]
