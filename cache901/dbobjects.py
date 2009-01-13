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

import pysqlite2
import sys

import cache901

minint = 0-sys.maxint

class Cache(object):
    def __init__(self, cid=minint):
        cur=cache901.db().cursor()
        if cid < 0:
            cur.execute('select cache_id from caches where cache_id=?', (cid, ))
            if cur.fetchone() is None:
                cur.execute('select min(cache_id) from caches')
                row = cur.fetchone()
                if row[0] is None:
                    cid = -1
                else:
                    cid = min(row[0]-1, -1)
                cur.execute("insert into caches(cache_id, url, url_name, url_desc, name, sym, type, available, archived, placed_by, owner_id, owner_name, container, difficulty, terrain, country, state, short_desc, long_desc, lat, lon, short_desc_html, long_desc_html) values(?,'','','','','','',1,0,'',0,'','',1.0,1.0,'','','','',0.0,0.0,0,0)", (cid,))
        cur.execute("select cache_id, url, url_name, url_desc, name, sym, type, available, archived, placed_by, owner_id, owner_name, container, difficulty, terrain, country, state, short_desc, long_desc, lat, lon, short_desc_html, long_desc_html, hidden from caches where cache_id=?", (cid, ))
        row = cur.fetchone()
        if type(row) is not pysqlite2.dbapi2.Row:
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
        self.hidden          = row['hidden']

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
        cur.execute("insert into caches(cache_id, name, lat, lon, url, url_name, url_desc, sym, type, available, archived, placed_by, owner_id, owner_name, container, difficulty, terrain, country, state, short_desc, short_desc_html, long_desc, long_desc_html, hidden) values (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", (self.cache_id, self.name, self.lat, self.lon, self.url, self.url_name, self.url_desc, self.sym, self.type, self.available, self.archived, self.placed_by, self.owner_id, self.owner_name, self.container, self.difficulty, self.terrain, self.country, self.state, self.short_desc, self.short_desc_html, self.long_desc, self.long_desc_html, self.hidden))
        cache901.db().commit()

    def Delete(self):
        cur = cache901.db().cursor()
        cur.execute("delete from caches where cache_id=?", (self.cache_id, ))
        cache901.db().commit()
        
class Waypoint(object):
    def __init__(self, cid=minint):
        cur=cache901.db().cursor()
        if cid < 0:
            cur.execute('select wpt_id from locations where wpt_id=?', (cid, ))
            if cur.fetchone() is None:
                cur.execute('select wpt_id from locations where wpt_id=?', (cid, ))
                row = cur.fetchone()
                if row is None or row[0] is None:
                    cur.execute('select min(wpt_id) from locations')
                    row = cur.fetchone()
                    if row is None or row[0] is None:
                        cid = -1
                    else:
                        cid = min(row[0]-1, -1)
                    cur.execute("insert into locations(wpt_id, loc_type, refers_to, name, desc, comment, lat, lon) values(?,0,-1,'','','',0.0,0.0)", (cid, ))
        cur.execute('select loc_type, refers_to, name, desc, comment, lat, lon, hidden from locations where wpt_id=?', (cid, ))
        row = cur.fetchone()
        if type(row) is pysqlite2.dbapi2.Row:
            self.wpt_id = cid
            self.loc_type = row[0]
            self.refers_to = row[1]
            self.name = row[2]
            self.desc = row[3]
            self.comment = row[4]
            self.lat = row[5]
            self.lon = row[6]
            self.hidden = row[7]
        else:
            raise cache901.InvalidID('Invalid waypoint ID: %d', cid)

    def Save(self):
        cur = cache901.db().cursor()
        cur.execute('delete from locations where wpt_id=?', (self.wpt_id,))
        cur.execute("insert into locations(wpt_id, loc_type, refers_to, name, desc, comment, lat, lon, hidden) values(?,?,?,?,?,?,?,?,?)", (self.wpt_id, self.loc_type, self.refers_to, self.name, self.desc, self.comment, self.lat, self.lon, self.hidden))
        cache901.db().commit()

    def Delete(self):
        cur = cache901.db().cursor()
        cur.execute('delete from locations where wpt_id=?', (self.wpt_id,))
        cache901.db().commit()

class Log(object):
    def __init__(self, lid=minint):
        cur=cache901.db().cursor()
        if lid < 0:
            cur.execute('select id from logs where id=?', (lid, ))
            if cur.fetchone() is None:
                cur.execute('select min(id) from logs')
                row = cur.fetchone()
                if row[0] is None:
                    lid = -1
                else:
                    lid = min(row[0]-1, -1)
                cur.execute("insert into logs(id, cache_id, date, type, finder, finder_id, log_entry, log_entry_encoded, my_log, my_log_found, my_log_uploaded) values(?,-1,0,'','',0,'',0,0,0,0)", (lid, ))
        cur.execute('select id, cache_id, date, type, finder, finder_id, log_entry, log_entry_encoded, my_log, my_log_found, my_log_uploaded from logs where id=?', (lid, ))
        row = cur.fetchone()
        if type(row) is pysqlite2.dbapi2.Row:
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

    def Delete(self):
        cur = cache901.db().cursor()
        cur.execute('delete from logs where id=?', (self.id, ))
        cache901.db().commit()
        
    def Save(self):
        cur = cache901.db().cursor()
        cur.execute('delete from logs where id=?', (self.id, ))
        cur.execute("insert into logs(id, cache_id, date, type, finder, finder_id, log_entry, log_entry_encoded, my_log, my_log_found, my_log_uploaded) values(?,?,?,?,?,?,?,?,?,?,?)", (self.id, self.cache_id, self.date, self.type, self.finder, self.finder_id, self.log_entry, self.log_entry_encoded, self.my_log, self.my_log_found, self.my_log_uploaded))
        cache901.db().commit()

class TravelBug(object):
    def __init__(self, bid=minint):
        cur=cache901.db().cursor()
        if bid < 0:
            cur.execute('select id from travelbugs where id=?', (bid, ))
            if cur.fetchone() is None:
                cur.execute('select min(id) from travelbugs')
                row = cur.fetchone()
                if row[0] is None:
                    bid = -1
                else:
                    bid = min(row[0]-1, -1)
                cur.execute("insert into travelbugs(id, cache_id, name, ref) values(?,-1,'','')", (bid, ))
        cur.execute('select id, cache_id, name, ref from travelbugs where id=?', (bid, ))
        row = cur.fetchone()
        if type(row) is pysqlite2.dbapi2.Row:
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
        cache901.db().commit()

class Note(object):
    def __init__(self, nid=minint):
        cur=cache901.db().cursor()
        if nid < 0:
            cur.execute('select cache_id from notes where cache_id=?', (nid, ))
            if cur.fetchone() is None:
                cur.execute('select min(cache_id) from notes')
                row = cur.fetchone()
                if row[0] is None:
                    nid = -1
                else:
                    nid = min(row[0]-1, -1)
                cur.execute("insert into notes(cache_id, note) values(?,'')", (nid, ))
        cur.execute('select cache_id, note from notes where cache_id=?', (nid, ))
        row = cur.fetchone()
        if type(row) is pysqlite2.dbapi2.Row:
            self.id = nid
            self.note = row[1]
        else:
            raise cache901.InvalidID('Invalid Note ID: %d' % nid)

    def Save(self):
        cur = cache901.db().cursor()
        cur.execute('delete from notes where cache_id=?', (self.id, ))
        cur.execute("insert into notes(cache_id, note) values(?,?)", (self.id, self.note))
        cache901.db().commit()

class Hint(object):
    def __init__(self, hid=minint):
        cur=cache901.db().cursor()
        if hid < 0:
            cur.execute('select cache_id from hints where cache_id=?', (hid, ))
            if cur.fetchone() is None:
                cur.execute('select min(cache_id) from hints')
                row = cur.fetchone()
                if row[0] is None:
                    hid = -1
                else:
                    hid = min(row[0]-1, -1)
                cur.execute("insert into hints(cache_id, hint) values(?,'')", (hid, ))
        cur.execute('select cache_id, hint from hints where cache_id=?', (hid, ))
        row = cur.fetchone()
        if type(row) is pysqlite2.dbapi2.Row:
            self.id = hid
            self.hint = row[1]
        else:
            raise cache901.InvalidID('Invalid Hint ID: %d' % hid)

    def Save(self):
        cur = cache901.db().cursor()
        cur.execute('delete from hints where cache_id=?', (self.id, ))
        cur.execute("insert into hints(cache_id, hint) values(?,?)", (self.id, self.hint))
        cache901.db().commit()

class PhotoList(object):
    def __init__(self, plid=minint):
        self.names = []
        cur=cache901.db().cursor()
        if plid < 0:
            cur.execute('select cache_id from photos where cache_id=?', (plid, ))
            if cur.fetchone() is None:
                cur.execute('select min(cache_id) from photos')
                row = cur.fetchone()
                if row[0] is None:
                    plid = -1
                else:
                    plid = min(row[0]-1, -1)
                cur.execute("insert into photos(cache_id, photofile) values(?,'')", (plid, ))
        cur.execute('select cache_id, photofile from photos where cache_id=? order by photofile', (plid, ))
        rowcount = 0
        for row in cur:
            if type(row) is pysqlite2.dbapi2.Row:
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
        cache901.db().commit()

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
    
    def Rename(self, newname):
        self.Delete()
        self.dayname=newname
        self.Save()

class Account(object):
    def __init__(self, acctid=minint):
        cur = cache901.db().cursor()
        if acctid < 0:
            cur.execute('select accountid from accounts where accountid=?', (acctid, ))
            if cur.fetchone() is None:
                cur.execute('select min(accountid) from accounts')
                row = cur.fetchone()
                if row[0] is None:
                    acctid = -1
                else:
                    acctid = min(row[0]-1, -1)
                cur.execute('insert into accounts(accountid, sitename, username, password, isteam, ispremium) values(?, "", "", "", 0, 0)', (acctid, ))
        cur.execute('select accountid, sitename, username, password, isteam, ispremium from accounts where accountid=?', (acctid, ))
        row = cur.fetchone()
        if type(row) is pysqlite2.dbapi2.Row:
            self.acctid    = row['accountid']
            self.sitename  = row['sitename']
            self.username  = row['username']
            self.password  = row['password']
            self.isteam    = (row['isteam'] == 1)
            self.ispremium = (row['ispremium'] == 1)
        else:
            raise cache901.InvalidID('Invalid Account ID: %d' % acctid)
        
    def Save(self):
        cur = cache901.db().cursor()
        cur.execute('delete from accounts where accountid=?', (self.acctid, ))
        cur.execute('insert into accounts(accountid, sitename, username, password, isteam, ispremium) values(?, ?, ?, ?, ?, ?)', (self.acctid, self.sitename, self.username, self.password, self.isteam, self.ispremium))
        cache901.db().commit()
        
    def Delete(self):
        cur = cache901.db().cursor()
        cur.execute('delete from accounts where accountid=?', (self.acctid, ))
        cache901.db().commit()

class Email(object):
    def __init__(self, acctid=minint):
        cur = cache901.db().cursor()
        if acctid < 0:
            cur.execute('select emailid from emailsources where emailid=?', (acctid, ))
            if cur.fetchone() is None:
                cur.execute('select min(emailid) from emailsources')
                row = cur.fetchone()
                if row[0] is None:
                    acctid = -1
                else:
                    acctid = min(row[0]-1, -1)
                cur.execute('insert into emailsources(emailid, svrtype, svrname, svruser, svrpass, usessl, deffolder) values(?, "pop", "", "", "", 0, "INBOX")', (acctid, ))
        cur.execute('select emailid, svrtype, svrname, svruser, svrpass, usessl, deffolder from emailsources where emailid=?', (acctid, ))
        row = cur.fetchone()
        if type(row) is pysqlite2.dbapi2.Row:
            self.emailid   = row['emailid']
            self.svrtype   = row['svrtype']
            self.svrname   = row['svrname']
            self.username  = row['svruser']
            self.password  = row['svrpass']
            self.usessl    = (row['usessl'] == 1)
            self.deffolder = row['deffolder']
        else:
            raise cache901.InvalidID('Invalid Account ID: %d' % acctid)
        
    def Save(self):
        cur = cache901.db().cursor()
        cur.execute('delete from emailsources where emailid=?', (self.emailid, ))
        cur.execute('insert into emailsources(emailid, svrtype, svrname, svruser, svrpass, usessl, deffolder) values(?, ?, ?, ?, ?, ?, ?)', (self.emailid, self.svrtype, self.svrname, self.username, self.password, self.usessl, self.deffolder))
        cache901.db().commit()
        
    def Delete(self):
        cur = cache901.db().cursor()
        cur.execute('delete from emailsources where emailid=?', (self.emailid, ))
        cache901.db().commit()

    def setPop(self, popval):
        if popval: self.svrtype = 'pop'
        else: self.svrtype = 'imap'
        
    def getPop(self):
        return self.svrtype == 'pop'
    
    def setImap(self, imapval):
        if imapval: self.svrtype = 'imap'
        else: self.svrtype = 'pop'
        
    def getImap(self):
        return self.svrtype == 'imap'
    
    pop=property(getPop, setPop)
    imap=property(getImap, setImap)

class AltCoordsList(object):
    def __init__(self, aclid=minint):
        self.alts = []
        self.cid = aclid
        cur=cache901.db().cursor()
        cur.execute('select cache_id, sequence_num, name, lat, lon, setdefault from alt_coords where cache_id=? order by sequence_num', (aclid, ))
        rowcount = 0
        for row in cur:
            if type(row) is pysqlite2.dbapi2.Row:
                self.alts.append({
                    'name' : row['name'],
                    'lat' : row['lat'],
                    'lon' : row['lon'],
                    'setdefault' : row['setdefault']
                    })

    def Save(self):
        cur = cache901.db().cursor()
        cur.execute('delete from alt_coords where cache_id=?', (self.cid, ))
        for idx, f in enumerate(self.alts):
            cur.execute("insert into alt_coords(cache_id, sequence_num, name, lat, lon, setdefault) values(?,?,?,?,?,?)", (self.cid, idx, f['name'], f['lat'], f['lon'], 1 if f['setdefault'] else 0))
        cache901.db().commit()

        
        