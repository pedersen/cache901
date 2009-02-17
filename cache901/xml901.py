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

import xml.sax
import xml.sax.handler
import datetime
import time

import cache901

class XMLParser(object):
    def __init__(self):
        self.handler = XMLHandler()

    def parse(self, data, maint=True):
        self.handler.reset()
        if (type(data) is str):
            xml.sax.parseString(data, self.handler)
        else:
            xml.sax.parse(data, self.handler)
        cache901.db().commit()
        if maint:
            cache901.db().maintdb()

class XMLHandler(xml.sax.handler.ContentHandler):
    def __init__(self):
       xml.sax.handler.ContentHandler.__init__(self)
       self.reset()

    def reset(self):
        self.ccount  = 0
        self.chdata  = ""
        self.wpt     = xmlWaypointSaver()
        self.log     = xmlLogSaver()
        self.logwpt  = xmlWaypointSaver()
        self.bug     = xmlBugSaver()
        self.hints   = []
        self.read    = 0 # 0=None, 1=Wpt, 2=Log, 3=Bug, 4=Hint, 5=Log Waypoint

    def startElement(self, name, attrs):
        if name == 'wpt':
            if self.read == 0:
                self.read    = 1
            else:
                self.read = 5
            self.wpt.lat = float(attrs['lat'])
            self.wpt.lon = float(attrs['lon'])
            self.chdata  = ""
        elif name == 'groundspeak:cache':
            self.wpt.cache_id  = int(attrs['id'])
            self.wpt.available = (attrs['available'].lower() == 'true')
            self.wpt.archived  = (attrs['archived'].lower() == 'true')
            self.wpt.cache = True
        elif name == 'groundspeak:owner':
            self.wpt.owner_id = int(attrs['id'])
            self.wpt.cache = True
        elif name == 'groundspeak:short_description':
            self.wpt.short_desc_html = (attrs['html'].lower() == 'true')
            self.wpt.cache = True
        elif name == 'groundspeak:long_description':
            self.wpt.long_desc_html = (attrs['html'].lower() == 'true')
            self.wpt.cache = True
        elif name == 'groundspeak:encoded_hints':
            self.read = 4
        elif name == 'groundspeak:travelbug':
            self.read=3
            self.bug.id  = int(attrs['id'])
            self.bug.ref = attrs['ref']
        elif name == 'groundspeak:log':
            self.read = 2
            self.log.id = int(attrs['id'])
        elif name == 'groundspeak:finder':
                self.log.finder_id = int(attrs['id'])
        elif name == 'groundspeak:text':
                self.log.log_entry_encoded = (attrs['encoded'].lower() == 'true')

    def characters(self, ch):
        if self.read:
            self.chdata = "%s%s" % (self.chdata, ch)

    def endElement(self, name):
        if self.read:
            self.chdata = self.chdata.strip()
            if self.read in (1,5):
                if self.read == 1:
                    wpt = self.wpt
                else:
                    wpt = self.logwpt
                if name == 'name':
                    wpt.name = self.chdata
                elif name == 'time':
                    (year, mon, day)=map(lambda x: int(x), self.chdata.split('T')[0].split('-'))
                    d = datetime.datetime(year, mon, day, 0, 0, 0)
                    self.wpt.hidden = time.mktime(d.timetuple())
                    if time.daylight:
                        self.wpt.hidden -= time.altzone
                    else:
                        self.wpt.hidden -= time.timezone
                elif name == 'cmt':
                    wpt.comment = self.chdata
                elif name == 'desc':
                    wpt.desc = self.chdata
                    wpt.url_desc = self.chdata
                elif name == 'url':
                    wpt.url = self.chdata
                elif name == 'urlname':
                    wpt.url_name = self.chdata
                    if self.ccount == 0:
                        cache901.notify("Processing %s" % cache901.util.forceAscii(wpt.url_name))
                    self.ccount = (self.ccount + 1) % 5
                elif name == 'sym':
                    wpt.sym = self.chdata
                elif name == 'type':
                    wpt.type = self.chdata
                elif name == 'groundspeak:placed_by':
                    wpt.placed_by = self.chdata
                    wpt.cache = True
                elif name == 'groundspeak:owner':
                    wpt.owner_name = self.chdata
                    wpt.cache = True
                elif name == 'groundspeak:container':
                    wpt.container = self.chdata
                    wpt.cache = True
                elif name == 'groundspeak:country':
                    wpt.country = self.chdata
                    wpt.cache = True
                elif name == 'groundspeak:state':
                    wpt.state = self.chdata
                    wpt.cache = True
                elif name == 'groundspeak:short_description':
                    wpt.short_desc = self.chdata
                    wpt.cache = True
                elif name == 'groundspeak:long_description':
                    wpt.long_desc = self.chdata
                    wpt.cache = True
                elif name == 'groundspeak:difficulty':
                    wpt.difficulty = float(self.chdata)
                    wpt.cache = True
                elif name == 'groundspeak:terrain':
                    wpt.terrain = float(self.chdata)
                    wpt.cache = True
                elif name == 'wpt':
                    if not self.wpt.isCache():
                        wpt.loc_type = 1
                        if self.read == 5:
                            wpt.refers_to = self.wpt.cache_id
                            self.read = 1
                        else:
                            wpt.refers_to = -1
                            self.read = 0
                    else:
                        self.read = 0
                    wpt.Save()
            elif self.read == 4:
                cur=cache901.db().cursor()
                cur.execute("delete from hints where cache_id=?", (self.wpt.cache_id,))
                cur.execute("insert into hints(cache_id, hint) values(?,?)", (self.wpt.cache_id, self.chdata))
                self.read=1
            elif self.read == 3:
                if name == 'groundspeak:name':
                    self.bug.name = self.chdata
                elif name == 'groundspeak:travelbug':
                    self.bug.cache_id = self.wpt.cache_id
                    self.bug.Save()
                    self.read=1
            elif self.read == 2:
                if name == 'groundspeak:date':
                    (year, mon, day)=map(lambda x: int(x), self.chdata.split('T')[0].split('-'))
                    d = datetime.datetime(year, mon, day, 0, 0, 0)
                    self.log.date = time.mktime(d.timetuple())
                    if time.daylight:
                        self.log.date -= time.altzone
                    else:
                        self.log.date -= time.timezone
                elif name == 'groundspeak:type':
                    self.log.type = self.chdata
                elif name == 'groundspeak:finder':
                    self.log.finder = self.chdata
                elif name == 'groundspeak:text':
                    self.log.log_entry = self.chdata
                elif name == 'groundspeak:log':
                    self.log.cache_id = self.wpt.cache_id
                    self.log.Save()
                    self.read = 1
            self.chdata = ""

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
