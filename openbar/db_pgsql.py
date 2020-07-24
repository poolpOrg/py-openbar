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

import json
import threading

import psycopg2
import psycopg2.extras
import psycopg2.pool

import openbar.log
import openbar.run

def _fail_safe(func, *args, **kwargs):
    try:
        func(*args, **kwargs)
    except:
        pass

class _Connection(object):

    def __init__(self, conn):
        self.conn = conn
        self.cursor = None

    def __enter__(self):
        self.cursor = self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        return self.cursor

    def __exit__(self, etype, value, traceback):
        cursor = self.cursor
        del self.cursor
        cursor.close()
        if (etype, value, traceback) == (None, None, None):
            self.conn.commit()
        else:
            self.conn.rollback()


_POOLS_LOCK = threading.Lock()
_POOLS_DICT = {}

def get_connection_pool(host, port, username, password, dbname, read_only):

    with _POOLS_LOCK:
        pool = _POOLS_DICT.get((host, port, username, dbname, read_only), None)
        if pool is not None:
            return pool
        pool = psycopg2.pool.ThreadedConnectionPool(minconn=1,
                                                    maxconn=100,
                                                    host=host,
                                                    port=port,
                                                    user=username,
                                                    password=password,
                                                    dbname=dbname)
        _POOLS_DICT[(host, port, username, dbname, read_only)] = pool
        return pool


class Connector(object):

    def __init__(self, name, pool, factory):
        self.name = name
        self.pool = pool
        self.factory = factory
        self.conn = None

    @staticmethod
    def _rollback_and_close_conn(conn):
        try:
            conn.rollback()
        except:
            openbar.log.warn("CONNECTION ROLLBACK FAILED!")
        try:
            conn.close()
        except:
            openbar.log.warn("CONNECTION CLOSE FAILED!")

    def __enter__(self):
        self.conn = self.pool.getconn()
        self.conn.set_client_encoding('UTF8')
        return self.factory(self.conn, self.name)

    def __exit__(self, etype, value, traceback):
        conn = self.conn
        del self.conn
        if (etype, value, traceback) == (None, None, None):
            conn.commit()
            self.pool.putconn(conn)
        else:
            openbar.log.warn("CONNECTION EXIT %r", (etype, value, traceback))
            self._rollback_and_close_conn(conn)


class Connected(object):

    _cursor = None

    def __init__(self, conn, name):
        self.conn = conn
        self.name = name

    def __enter__(self):
        assert self._cursor is None
        self._cursor = self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        return self._cursor

    def __exit__(self, etype, value, traceback):
        self._cursor.close()
        del self._cursor
