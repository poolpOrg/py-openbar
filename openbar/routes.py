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
plumbing for setting up routes
"""

import bottle

import openbar.log


##
## Routes registration
##
_ROUTES = {}

def _setup_route(app, version, name):
    data = _ROUTES[(version, name)]
    for parent in data['override']:
        _setup_route(app, parent, name)
    data['setup'](app)

def install_routes(root):
    for (version, name) in sorted(_ROUTES):
        mount_point = '/%s/%s/' % (version, name)
        openbar.log.info('Installing %s at %s', version, mount_point)
        app = bottle.Bottle()
        _setup_route(app, version, name)
        root.mount(mount_point, app)

def register(version, name, override=()):
    if isinstance(override, str):
        override = (override, )
    def _(setup):
        _ROUTES[(version, name)] = {'setup': setup, 'override' : override}
    return _
