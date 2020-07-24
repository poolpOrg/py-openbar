#
# Copyright (c) 2013,2017 Gilles Chehade <gilles@poolp.org>
# Copyright (c) 2013 Eric Faurot <eric@faurot.net>
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
plumbing for setting up backend
"""

import http.client
import json as pyjson

import bottle

_MANDATORY = object()
_UNSET = object()

class Parameters(object):
    """
    class to abstract parameters validation
    """
    def __init__(self, parameters):
        #print json.dumps(params, indent = 4, sort_keys = True)
        self.params = parameters

    def __enter__(self):
        return self

    def __exit__(self, type_, value, traceback):
        if (type_, value, traceback) == (None, None, None):
            if self.params:
                error(400, 'unexpected parameter: %s' % ', '.join(self.params.keys()))

    def get(self, name, default, validate):
        value = self.params.pop(name, _UNSET)

        if value is _UNSET:
            if default is not _MANDATORY:
                return default
            error(400, 'missing parameter: %s' % (name, ))

        if validate:
            try:
                validate(value)
            except TypeError as exc:
                error(400, 'invalid parameter type: %s: %s' % (name, exc.args[0]))
            except ValueError as exc:
                error(400, 'invalid parameter value: %s: %s' % (name, exc.args[0]))
            except:
                error(400, 'bad parameter: %s' % (name, ))

        return value

    def get_list(self, name, default, validate, maxlen):
        def _(val):
            if not isinstance(val, list):
                raise TypeError('expect list')
            if maxlen is not None and len(val) > maxlen:
                raise ValueError('list too long')
            if validate:
                for elm in val:
                    validate(elm)
        return self.get(name, default, _)

    def any(self, name, default=_MANDATORY, validate=None):
        return self.get(name, default, validate)

    def string(self, name, default=_MANDATORY, choice=None):
        def _(val):
            if not isinstance(val, str):
                raise TypeError('expect string')
            if choice is not None and val not in choice:
                raise ValueError('not in set of possible values')
        return self.get(name, default, _)

    def integer(self, name, default=_MANDATORY, minval=None, maxval=None):
        def _(val):
            if not isinstance(val, int):
                raise TypeError('expect integer')
            if minval is not None and val < minval:
                raise ValueError('too small')
            if maxval is not None and val > maxval:
                raise ValueError('too large')
        return self.get(name, default, _)

    def string_list(self, name, default=_MANDATORY, maxlen=None):
        def _(val):
            if not isinstance(val, str):
                raise TypeError('expect list of strings')
        return self.get_list(name, default, _, maxlen)

    def integer_list(self, name, default=_MANDATORY, maxlen=None):
        def _(val):
            if not isinstance(val, int):
                raise TypeError('expect list of integers')
        return self.get_list(name, default, _, maxlen)

    def timestamp(self, name, default=_MANDATORY):
        return self.integer(name, default, minval=0)

    def float(self, name, default=_MANDATORY, minval=None, maxval=None):
        def _(val):
            if not isinstance(val, (int, float)):
                raise TypeError('expect float')
            if minval is not None and val < minval:
                raise ValueError('too small')
            if maxval is not None and val > maxval:
                raise ValueError('too large')
        return float(self.get(name, default, _))

def json():
    return Parameters(bottle.request.json or {})

def no_json():
    if bottle.request.json:
        error(400, 'no json expected')

def error(code, data=None):
    if data is None:
        data = {'error': http.client.responses.get(code, "Error code %i" % code)}
    response = bottle.HTTPResponse(pyjson.dumps(data), code)
    response.set_header('Content-Type', 'application/json')
    raise response
