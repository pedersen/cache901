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

import cache901

class xmlWaypointSaver(object):
    def __init__(self):
        self.Clear()

    def isCache(self):
        return self.cache == True

    def Clear(self):
        for strs in ['name', 'desc', 'comment', 'url', 'url_name',
                'url_desc', 'sym', 'type', 'placed_by', 'owner_name',
                'container', 'country', 'state', 'short_desc', 'long_desc']:
            setattr(self, strs, "")
        for ints in ['loc_type', 'refers_to', 'id', 'catid', 'owner_id', 'hidden']:
            setattr(self, ints, 0)
        for floats in ['lat', 'lon', 'difficulty', 'terrain' ]:
            setattr(self, floats, 0.00)
        for bools in ['available', 'archived', 'short_desc_html',
                'long_desc_html', 'cache']:
            setattr(self, bools, False)

    def Save(self):
        cur = cache901.db().cursor()
        ret = -1
        if not self.isCache():
            wpt_id = -1
            cur.execute("delete from locations where name=?", (self.name, ))
            r=cur.execute("insert into locations(loc_type, refers_to, name, desc, comment, lat, lon, hidden) values(?,?,?,?,?,?,?,?)", (self.loc_type, self.refers_to, self.name, self.desc, self.comment, self.lat, self.lon, self.hidden))
            ret=r.lastrowid
        else:
            ret = self.cache_id
            cur.execute("delete from caches where cache_id=?", (self.cache_id, ))
            cur.execute("insert into caches(cache_id, name, lat, lon, url, url_name, url_desc, sym, type, available, archived, placed_by, owner_id, owner_name, container, difficulty, terrain, country, state, short_desc, short_desc_html, long_desc, long_desc_html, hidden) values (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", (self.cache_id, self.name, self.lat, self.lon, self.url, self.url_name, self.url_desc, self.sym, self.type, self.available, self.archived, self.placed_by, self.owner_id, self.owner_name, self.container, self.difficulty, self.terrain, self.country, self.state, self.short_desc, self.short_desc_html, self.long_desc, self.long_desc_html, self.hidden))
        self.Clear()
        return ret

class xmlLogSaver(object):
    def __init__(self):
        self.Clear()

    def Clear(self):
        self.id = -1
        self.cache_id = -1
        self.date = 0
        self.type = ""
        self.finder = ""
        self.finder_id = ""
        self.log_entry = ""
        self.log_entry_encoded = ""
        self.my_log = False
        self.my_log_found = False

    def Save(self):
        cur=cache901.db().cursor()
        cur.execute("delete from logs where id=?", (self.id, ))
        cur.execute("insert into logs(id, finder, log_entry, log_entry_encoded, my_log, my_log_found, cache_id, date, type, finder_id) values(?,?,?,?,0,0,?,?,?,?)", (self.id, self.finder, self.log_entry, self.log_entry_encoded, self.cache_id, self.date, self.type, self.finder_id))
        self.Clear()

class xmlBugSaver(object):
    def __init__(self):
        self.Clear()

    def Clear(self):
        self.id = -1
        self.cache_id = -1
        self.name = ""
        self.ref = ""

    def Save(self):
        ret = self.id
        cur = cache901.db().cursor()
        cur.execute("delete from travelbugs where id=?", (self.id, ))
        r=cur.execute("insert into travelbugs(id, cache_id, name, ref) values(?,?,?,?)", (self.id, self.cache_id, self.name, self.ref))
        self.Clear()
        return ret
