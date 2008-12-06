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

class Cache(object):
    def __init__(self, cid):
        if cid < 0:
            cur=cache901.db().cursor()
            cur.execute('select min(cache_id) from caches')
            row = cur.fetchone()
            if row[0] is None:
                cid = -1
            else:
                cid = row[0]-1
            cur.execute("insert into caches(cache_id, url, url_name, url_desc, name, sym, type, available, archived, placed_by, owner_id, owner_name, container, difficulty, terrain, country, state, short_desc, long_desc, lat, lon, short_desc_html, long_desc_html) values(?,'','','','','','',1,0,'',0,'','',1.0,1.0,'','','','',0.0,0.0,0,0)", (cid,))
        cur = cache901.db().cursor()
        cur.execute("select cache_id, url, url_name, url_desc, name, sym, type, available, archived, placed_by, owner_id, owner_name, container, difficulty, terrain, country, state, short_desc, long_desc, lat, lon, short_desc_html, long_desc_html from caches where cache_id=?", (cid, ))
        row = cur.fetchone()
        if type(row) is not tuple:
            raise cache901.InvalidID("Invalid Cache ID: %s" % str(cid))

        self.cache_id        = row[ 0]
        self.url             = row[ 1]
        self.url_name        = row[ 2]
        self.url_desc        = row[ 3]
        self.name            = row[ 4]
        self.sym             = row[ 5]
        self.type            = row[ 6]
        self.available       = (row[ 7] == 1)
        self.archived        = (row[ 8] == 1)
        self.placed_by       = row[ 9]
        self.owner_id        = row[10]
        self.owner_name      = row[11]
        self.container       = row[12]
        self.difficulty      = row[13]
        self.terrain         = row[14]
        self.country         = row[15]
        self.state           = row[16]
        self.short_desc      = row[17]
        self.long_desc       = row[18]
        self.lat             = row[19]
        self.lon             = row[20]
        self.short_desc_html = (row[21] == 1)
        self.long_desc_html  = (row[22] == 1)

        # Load hint information
        try:
            self.hint = cache901.dbobjects.Hint(self.cache_id)
        except cache901.InvalidID:
            pass
        
        # Load note information
        try:
            self.note = cache901.dbobjects.Note(self.cache_id)
        except cache901.InvalidID:
            self.note = cache901.dbobjects.Note(-999999)
            self.note.id = self.cache_id
        
        # Load PhotoList
        try:
            self.photolist = cache901.dbobjects.PhotoList(self.cache_id)
        except:
            self.photolist = cache901.dbobjects.PhotoList(-999999)
            self.photolist.id = self.cache_id
        
        # Load travelbug information
        self.bugs = []
        cur = cache901.db().cursor()
        cur.execute("select id from travelbugs where cache_id=?", (self.cache_id, ))
        for row in cur:
            self.bugs.append(TravelBug(row[0]))
            
        # Load log information
        self.logs = []
        cur = cache901.db().cursor()
        # For some reason, the sqlite engine would not return the logs in 
        # the correct order *unless* date was the first column in the
        # result set *and* was the only column being sorted by
        cur.execute("select date,id from logs where cache_id=? order by date desc", (self.cache_id, ))
        for row in cur:
            self.logs.append(Log(row[1]))

    def Save(self):
        cur = cache901.db().cursor()
        cur.execute("delete from caches where cache_id=?", (self.cache_id, ))
        cur.execute("insert into caches(cache_id, name, lat, lon, url, url_name, url_desc, sym, type, available, archived, placed_by, owner_id, owner_name, container, difficulty, terrain, country, state, short_desc, short_desc_html, long_desc, long_desc_html) values (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", (self.cache_id, self.name, self.lat, self.lon, self.url, self.url_name, self.url_desc, self.sym, self.type, self.available, self.archived, self.placed_by, self.owner_id, self.owner_name, self.container, self.difficulty, self.terrain, self.country, self.state, self.short_desc, self.short_desc_html, self.long_desc, self.long_desc_html))

class Waypoint(object):
    def __init__(self, cid):
        if cid < 0:
            cur=cache901.db().cursor()
            cur.execute('select wpt_id from locations where wpt_id=?', (cid, ))
            row = cur.fetchone()
            if row is None or row[0] is None:
                cur.execute('select min(wpt_id) from locations')
                row = cur.fetchone()
                if row is None or row[0] is None:
                    cid = -1
                else:
                    cid = row[0]-1
                cur.execute("insert into locations(wpt_id, loc_type, refers_to, name, desc, comment, lat, lon) values(?,0,-1,'','','',0.0,0.0)", (cid, ))
        cur = cache901.db().cursor()
        cur.execute('select loc_type, refers_to, name, desc, comment, lat, lon from locations where wpt_id=?', (cid, ))
        row = cur.fetchone()
        if type(row) is tuple:
            self.wpt_id = cid
            self.loc_type = row[0]
            self.refers_to = row[1]
            self.name = row[2]
            self.desc = row[3]
            self.comment = row[4]
            self.lat = row[5]
            self.lon = row[6]
        else:
            raise cache901.InvalidID('Invalid waypoint ID: %d', cid)

    def Save(self):
        cur = cache901.db().cursor()
        cur.execute('delete from locations where wpt_id=?', (self.wpt_id,))
        cur.execute("insert into locations(wpt_id, loc_type, refers_to, name, desc, comment, lat, lon) values(?,?,?,?,?,?,?,?)", (self.wpt_id, self.loc_type, self.refers_to, self.name, self.desc, self.comment, self.lat, self.lon))

class Log(object):
    def __init__(self, lid):
        if lid < 0:
            cur=cache901.db().cursor()
            cur.execute('select min(id) from logs')
            row = cur.fetchone()
            if row[0] is None:
                lid = -1
            else:
                lid = row[0]-1
            cur.execute("insert into logs(id, cache_id, date, type, finder, finder_id, log_entry, log_entry_encoded, my_log, my_log_found, my_log_uploaded) values(?,-1,0,'','',0,'',0,0,0,0)", (lid, ))
        cur = cache901.db().cursor()
        cur.execute('select id, cache_id, date, type, finder, finder_id, log_entry, log_entry_encoded, my_log, my_log_found, my_log_uploaded from logs where id=?', (lid, ))
        row = cur.fetchone()
        if type(row) is tuple:
            self.id = lid
            self.cache_id = row[1]
            self.date = row[2]
            self.type = row[3]
            self.finder = row[4]
            self.finder_id = row[5]
            self.log_entry = row[6]
            self.log_entry_encoded = (row[7] == 1)
            self.my_log = (row[8] == 1)
            self.my_log_found = (row[9] == 1)
            self.my_log_uploaded = (row[10] == 1)
        else:
            raise cache901.InvalidID('Invalid Log ID: %d' % lid)

    def Save(self):
        cur = cache901.db().cursor()
        cur.execute('delete from logs where id=?', (self.id, ))
        cur.execute("insert into logs(id, cache_id, date, type, finder, finder_id, log_entry, log_entry_encoded, my_log, my_log_found, my_log_uploaded) values(?,?,?,?,?,?,?,?,?,?,?)", (self.id, self.cache_id, self.date, self.type, self.finder, self.finder_id, self.log_entry, self.log_entry_encoded, self.my_log, self.my_log_found, self.my_log_uploaded))

class TravelBug(object):
    def __init__(self, bid):
        if bid < 0:
            cur=cache901.db().cursor()
            cur.execute('select min(id) from travelbugs')
            row = cur.fetchone()
            if row[0] is None:
                bid = -1
            else:
                bid = row[0]-1
            cur.execute("insert into travelbugs(id, cache_id, name, ref) values(?,-1,'','')", (bid, ))
        cur = cache901.db().cursor()
        cur.execute('select id, cache_id, name, ref from travelbugs where id=?', (bid, ))
        row = cur.fetchone()
        if type(row) is tuple:
            self.id = bid
            self.cache_id = row[1]
            self.name = row[2]
            self.ref = row[3]
        else:
            raise cache901.InvalidID('Invalid Travel Bug Id: %d' % bid)

    def Save(self):
        cur = cache901.db().cursor()
        cur.execute('delete from travelbugs where id=?', (self.id, ))
        cur.execute("insert into travelbugs(id, cache_id, name, ref) values(?,?,?,?)", (self.id, self.cache_id, self.name, self.ref))

class Note(object):
    def __init__(self, nid):
        if nid < 0:
            cur=cache901.db().cursor()
            cur.execute('select min(cache_id) from notes')
            row = cur.fetchone()
            if row[0] is None:
                nid = -1
            else:
                nid = row[0]-1
            cur.execute("insert into notes(cache_id, note) values(?,'')", (nid, ))
        cur = cache901.db().cursor()
        cur.execute('select cache_id, note from notes where cache_id=?', (nid, ))
        row = cur.fetchone()
        if type(row) is tuple:
            self.id = nid
            self.note = row[1]
        else:
            raise cache901.InvalidID('Invalid Note ID: %d' % nid)

    def Save(self):
        cur = cache901.db().cursor()
        cur.execute('delete from notes where cache_id=?', (self.id, ))
        cur.execute("insert into notes(cache_id, note) values(?,?)", (self.id, self.note))

class Hint(object):
    def __init__(self, hid):
        if hid < 0:
            cur=cache901.db().cursor()
            cur.execute('select min(cache_id) from hints')
            row = cur.fetchone()
            if row[0] is None:
                hid = -1
            else:
                hid = row[0]-1
            cur.execute("insert into hints(cache_id, hint) values(?,'')", (hid, ))
        cur = cache901.db().cursor()
        cur.execute('select cache_id, hint from hints where cache_id=?', (hid, ))
        row = cur.fetchone()
        if type(row) is tuple:
            self.id = hid
            self.hint = row[1]
        else:
            raise cache901.InvalidID('Invalid Hint ID: %d' % hid)

    def Save(self):
        cur = cache901.db().cursor()
        cur.execute('delete from hints where cache_id=?', (self.id, ))
        cur.execute("insert into hints(cache_id, hint) values(?,?)", (self.id, self.hint))

class PhotoList(object):
    def __init__(self, plid):
        self.names = []
        if plid < 0:
            cur=cache901.db().cursor()
            cur.execute('select min(cache_id) from photos')
            row = cur.fetchone()
            if row[0] is None:
                plid = -1
            else:
                plid = row[0]-1
            cur.execute("insert into photos(cache_id, photofile) values(?,'')", (plid, ))
        cur = cache901.db().cursor()
        cur.execute('select cache_id, photofile from photos where cache_id=? order by photofile', (plid, ))
        rowcount = 0
        for row in cur:
            if type(row) is tuple:
                self.id = plid
                rowcount = rowcount + 1
                if row[1] != "":
                    self.names.append(row[1])
        if rowcount <= 0:
            raise cache901.InvalidID('Invalid PhotoList ID: %d' % plid)

    def Save(self):
        cur = cache901.db().cursor()
        cur.execute('delete from photos where cache_id=?', (self.id, ))
        for f in self.names:
            cur.execute("insert into photos(cache_id, photofile) values(?,?)", (self.id, f))

class CacheDay(object):
    def __init__(self, dayname):
        self.caches = []
        self.dayname = dayname
        cur = cache901.db().cursor()
        cur.execute('select dayname, cache_id, cache_type, cache_order from cacheday where dayname=? order by cache_order', (self.dayname, ))
        for row in cur:
            if row[2] == 1:
                self.caches.append(Cache(row[1]))
            elif row[2] == 2:
                self.caches.append(Waypoint(row[1]))
            else:
                raise Exception('Invalid cache type %d' % (row[2], ))
        
    def Save(self):
        cur = cache901.db().cursor()
        cur.execute('delete from cacheday where dayname=?', (self.dayname, ))
        cur.execute('delete from cacheday_names where dayname=?', (self.dayname, ))
        cur.execute('insert into cacheday_names(dayname) values (?)', (self.dayname, ))
        for idx, wpt in enumerate(self.caches):
            if isinstance(wpt, Cache):
                cache_type = 1
                cid = wpt.cache_id
            elif isinstance(wpt, Waypoint):
                cache_type = 2
                cid = wpt.wpt_id
            else: raise Exception('Invalid cache type in cache day at index %d' % (idx, ))
            cur.execute('insert into cacheday(dayname, cache_id, cache_type, cache_order) values (?,?,?,?)', (self.dayname, cid, cache_type, idx))
        cache901.db().commit()
        
    def Delete(self):
        cur = cache901.db().cursor()
        cur.execute('delete from cacheday where dayname=?', (self.dayname, ))
        cur.execute('delete from cacheday_names where dayname=?', (self.dayname, ))
        cache901.db().commit()
