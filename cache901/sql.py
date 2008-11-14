"""
Cache901 - GeoCaching Software for the Asus EEE PC 901
Copyright (C) 2008, Michael J. Pedersen <m.pedersen@icelus.org>

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License along
with this program; if not, write to the Free Software Foundation, Inc.,
51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
"""

try:
    from pysqlite2 import dbapi2 as sqlite
except ImportError, e:
    import sqlite3 as sqlite

import cache901.util
import cache901.sql

statements_v001 = [
    "CREATE TABLE version (version integer)",
    "INSERT INTO version(version) values(1)",
    """
    CREATE TABLE categories (
        catid integer primary key autoincrement,
        catname text
        )
    """,
    """
    CREATE TABLE attributes (
        cache_id integer primary key autoincrement,
        attribute text
        )
    """,
    # locations.loc_type: 1=waypoint, 2=manually entered/search origin spot
    # locations.refers_to: the id of the log, or -1 if not from a log
    """
    CREATE TABLE locations (
        wpt_id integer primary key autoincrement,
        loc_type integer,
        refers_to integer,
        name text,
        desc text,
        comment text,
        lat real,
        lon real
    )
    """,
    "CREATE INDEX locations_refers_to ON locations(refers_to)",
    "CREATE INDEX locations_name ON locations(name)",
    # caches.cache_id: unique int (comes from groundspeak:cache tag, id attribute)
    # caches.catid: the id of the category for this cache. comes from table category.catid
    # caches.available: boolean
    # caches.archived: boolean
    # caches.short_desc_html: boolean
    # caches.long_desc_html: boolean
    # caches.found: boolean
    """
    CREATE TABLE caches (
        cache_id integer primary key,
        catid integer,
        name text,
        lat real,
        lon real,
        url text,
        url_name text,
        url_desc text,
        sym text,
        type text,
        available integer,
        archived integer,
        placed_by text,
        owner_id integer,
        owner_name text,
        container text,
        difficulty real,
        terrain real,
        country text,
        state text,
        short_desc text,
        short_desc_html integer,
        long_desc text,
        long_desc_html integer
        )
    """,
    "CREATE INDEX caches_name ON caches(name)",
    "CREATE INDEX caches_url_name ON caches(url_name)",
    #hints.cache_id: int, links to tbl cache.cache_id
    """
    CREATE TABLE hints (
        cache_id integer,
        hint text
        )
    """,
    "CREATE INDEX hints_cache_id ON hints(cache_id)",
    #logs.cache_id: int, links to tbl cache.cache_id
    #logs.log_entry_encoded: boolean
    #logs.my_log: boolean
    #logs.my_log_found: boolean
    #logs.date: datetime
    """
    CREATE TABLE logs (
        id integer primary key,
        cache_id integer,
        date integer,
        type text,
        finder text,
        finder_id integer,
        log_entry text,
        log_entry_encoded integer,
        my_log integer,
        my_log_found integer,
        my_log_uploaded integer
        )
    """,
    "CREATE INDEX logs_cache_id ON logs(cache_id)",
    #travelbugs.cache_id: int, links to tbl cache.cache_id
    #travelbugs.id: unique int, from xml
    #travelbugs.ref: like "TB3D64"
    """
    CREATE TABLE travelbugs (
        id integer primary key,
        cache_id integer,
        name text,
        ref text
        )
    """,
    "CREATE INDEX travelbugs_cache_id ON travelbugs(cache_id)",
    """
    CREATE TABLE accounts (
        sitename text,
        username text,
        password text,
        type integer
        )
    """
    ]

statements_v002 = [
    """
    CREATE TABLE searches (
        name  text,
        param text,
        value text
        )
    """,
    "CREATE INDEX searches_name ON searches(name)",
    "DELETE FROM version",
    "INSERT INTO version(version) values(2)"
    ]

allstatements = sorted(filter(lambda x: x.startswith("statements_v"), globals()))

def sqlexec(con, statements, debug=False):
    cur = con.cursor()
    for stmt in statements:
        if debug:
            print "---------------------------------"
            print stmt
            print "---------------------------------"
        cur.execute(stmt)

def prepdb(dbname, debug=False):
    con = sqlite.connect(database=dbname, timeout=1.0)
    con.create_function("distance", 4, cache901.util.distance_exact)
    cur = con.cursor()
    try:
        cur.execute("select version from version")
        row = cur.fetchone()
        vname = 'statements_v%03d' % row[0]
        for stgrp in allstatements[allstatements.index(vname)+1:]:
            stmts = globals()[stgrp]
            sqlexec(con, stmts, debug)
    except sqlite.OperationalError:
        for stgrp in allstatements:
            sqlexec(con, stgrp, debug)
    cur.execute("vacuum")
    cur.execute("analyze")
    return con
