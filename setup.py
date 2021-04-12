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
"""
setup script for the openbar project
"""

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

CONFIGURATION = {
    'description':      'openbar is a framework to build solid frontend/backend projects',
    'author':           'Gilles Chehade',
    'url':              '',
    'download_url':     '',
    'author_email':     'gilles@poolp.org',
    'version':          '0.1',
    'install_requires': [
        'appdirs==1.4.3',
        'bottle==0.12.19',
	    'bottle-beaker==0.1.3',
	    'CherryPy==3.3.0',
        'nose==1.3.7',
        'packaging==16.8',
        'pyparsing==2.2.0',
        'requests==2.20.0',
        'six==1.10.0',
	'jinja2==2.11.2',
    'psycopg2-binary',
    ],
    'packages':         ['openbar'],
    'package_data':     {'openbar' : [
    ]},
    'scripts':          ['scripts/openbarctl'],
    'name':             'py-openbar'
}

setup(**CONFIGURATION)
