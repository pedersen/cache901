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

import os
import os.path
import sqlite3

import cache901

class Database(object):
    __shared_state = {}
    def __init__(self, debugging=False):
        self.__dict__ = self.__shared_state
        if not hasattr(self, "allstatements"):
            self.allstatements = sorted(filter(lambda x: x.startswith("statements_v"), Database.__dict__.keys()))
        if not hasattr(self, "database"):
            self.open(cache901.cfg().dbfile, debugging)
    
    def open(self, dbfile=None, debugging=False):
        self.close()
        if debugging:
            self.prepdb(":memory:")
        else:
            if not os.path.isdir(cache901.cfg().dbpath):
                os.makedirs(cache901.cfg().dbpath)
            self.prepdb(cache901.cfg().dbfile)
            cache901.cfg().dbfile = dbfile
    
    def close(self):
        if hasattr(self, "database"):
            self.database.close()
            del self.database
    
    def cursor(self):
        return self.database.cursor()
    
    def commit(self):
        return self.database.commit()
    
    def prepdb(self, dbname, debug=False):
        self.database = sqlite3.connect(database=dbname, timeout=1.0)
        self.database.create_function("distance", 4, cache901.util.distance_exact)
        self.database.row_factory = sqlite3.Row
        cur = self.database.cursor()
        try:
            cur.execute("select version from version")
            row = cur.fetchone()
            vname = 'statements_v%03d' % row[0]
            for stgrp in self.allstatements[self.allstatements.index(vname)+1:]:
                stmts = globals()[stgrp]
                self.sqlexec(stmts, debug)
                vnum = int(stgrp[-3:])
                cur.execute("UPDATE version SET version=?", (vnum, ))
                self.database.commit()
        except sqlite3.OperationalError:
            for stgrp in allstatements:
                stmts = globals()[stgrp]
                self.sqlexec(stmts, debug)
                vnum = int(stgrp[-3:])
                cur.execute("UPDATE version SET version=?", (vnum, ))
                self.database.commit()
    
    def scrub(self):
        maxlogs = cache901.cfg().dbMaxLogs
        cache901.notify('Scrubbing database of old/invalid data')
        if hasattr(self, "database"):
            cur = self.cursor()
            cur.execute("delete from travelbugs where cache_id not in (select cache_id from caches)")
            cur.execute("delete from hints where cache_id not in (select cache_id from caches)")
            cur.execute("delete from logs where cache_id not in (select cache_id from caches)")
            cur.execute("delete from notes where cache_id not in (select cache_id from caches)")
            cur.execute("delete from photos where cache_id not in (select cache_id from caches)")
            cur.execute("delete from cacheday where cache_id not in (select cache_id from caches)")
            cur.execute("delete from alt_coords where cache_id not in (select cache_id from caches)")
            # update logs to show my_log for any logs where finder is in gpx accounts
            cache901.notify('Ensuring my logs are noted properly')
            cur.execute('update logs set my_log=1 where finder in (select username from accounts)')
            # delete logs after maxlogs entries for a given cache, keeping only the newest (and the my_log)
            cur.execute('select distinct id, cache_id, my_log from logs order by cache_id, id desc')
            cache_id = -1
            logcount = 0
            delthese = []
            for row in cur:
                if row['cache_id'] != cache_id:
                    cache_id = row['cache_id']
                    logcount = 0
                logcount += 1
                if logcount > maxlogs and row['my_log'] == 0:
                    delthese.append(str(row['id']))
            cur.execute('delete from logs where id in (%s)' % ",".join(delthese))
            self.commit()
    
    
    def delAllCaches(self):
        cache901.notify("Emptying all caches and waypoints from the database")
        cur=self.cursor()
        cur.execute("delete from caches")
        cur.execute("delete from locations where loc_type=1")
        self.commit()
        self.scrub()


    def sqlexec(self, statements, debug=False):
        cur = self.cursor()
        for stmt in statements:
            if debug:
                print "---------------------------------"
                print stmt
                print "---------------------------------"
            cur.execute(stmt)
    
    def maintdb(self):
        self.scrub()
        cur = self.cursor()
        cache901.notify('Recovering unused disk space')
        cur.execute("vacuum")
        cache901.notify('Rebuilding database indices')
        cur.execute("analyze")
        self.commit()

    
    statements_v001 = [
        "CREATE TABLE version (version integer)",
        "INSERT INTO version(version) VALUES(1)",
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
        """
        CREATE TABLE notes (
            cache_id integer,
            note     text
            )
        """,
        "CREATE INDEX notes_id ON notes(cache_id)",
        """
        CREATE TABLE photos (
            cache_id  integer,
            photofile text
            )
        """,
        "CREATE INDEX photos_id ON photos(cache_id)",
        ]
    
    statements_v003 = [
        # cache_type: 1 for cache, 2 for waypoint
        """
        CREATE TABLE cacheday (
            dayname     text,
            cache_id    integer,
            cache_type  integer,
            cache_order integer
            )
        """,
        "CREATE INDEX cacheday_name ON cacheday(dayname)",
        """
        CREATE TABLE cacheday_names (
            dayname text
            )
        """
        ]
    
    statements_v004 = [
        "DROP TABLE accounts",
        """
        CREATE TABLE accounts (
            accountid integer primary key,
            sitename  text,
            username  text,
            password  text,
            isteam    integer,
            ispremium integer
            )
        """,
        """
        CREATE TABLE emailsources (
            emailid   integer,
            svrtype   text,
            svrname   text,
            svruser   text,
            svrpass   text,
            usessl    integer,
            deffolder text
            )
        """,
        """
        CREATE TABLE gpxfolders (
            foldername text
            )
        """,
        """
        CREATE TABLE watched_waypoints (
            waypoint_name text
            )
        """
        ]
    
    statements_v005 = [
        "ALTER TABLE caches ADD COLUMN hidden integer default 0",
        "ALTER TABLE locations ADD COLUMN hidden integer default 0",
        """
        CREATE TABLE alt_coords (
            cache_id     integer,
            sequence_num integer,
            name         text,
            lat          real,
            lon          real,
            setdefault   integer
            )
        """
        ]
    
    statements_v006 = [
        "DROP TABLE alt_coords",
        """
        CREATE TABLE alt_coords (
            cache_id     integer,
            sequence_num integer,
            name         text,
            lat          text,
            lon          text,
            setdefault   integer
            )
        """,
        "CREATE INDEX alt_coords_cid_seq ON alt_coords(cache_id, sequence_num)"
        ]
    
     