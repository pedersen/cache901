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

from decimal import Decimal
from xml.etree import cElementTree

import cache901

from cache901.sadbobjects import *

class XMLParser(object):
    def __init__(self):
        self.ccount = 0

    def parse(self, data, maint=True):
        if (type(data) is str):
            parsed = cElementTree.fromstring(data)
        else:
            parsed = cElementTree.parse(data)
        # manage the parsed data here
        for wpt in parsed.findall('{http://www.topografix.com/GPX/1/0}wpt'):
            cachedata = wpt.find('{http://www.groundspeak.com/cache/1/0}cache')
            if cachedata:
                cache_id = int(cachedata.get('id'))
                cache = cache901.db().query(Caches).filter(Caches.cache_id == cache_id).first()
                if not cache:
                    cache = Caches()
                cache.available = (cachedata.get('available').lower() == 'true')
                cache.archived = (cachedata.get('archived').lower() == 'true')
                for node in cachedata.getchildren():
                    if node.tag.endswith('}placed_by'): cache.placed_by = node.text
                    elif node.tag.endswith('}owner'):
                        cache.owner_name = node.text
                        cache.owner_id = node.get('id')
                    elif node.tag.endswith('}container'): cache.container = node.text
                    elif node.tag.endswith('}country'): cache.country = node.text
                    elif node.tag.endswith('}state'): cache.state = node.text
                    elif node.tag.endswith('}short_description'):
                        cache.short_desc = node.text
                        cache.short_desc_html = (node.get('html').lower() == 'true')
                    elif node.tag.endswith('}long_description'):
                        cache.long_desc = node.text
                        cache.long_desc_html = (node.get('html').lower() == 'true')
                    elif node.tag.endswith('}difficulty'): cache.difficulty = Decimal(node.text)
                    elif node.tag.endswith('}terrain'): cache.terrain = Decimal(node.text)
                    elif node.tag.endswith('}encoded_hints'):
                        hint = cache901.db().query(Hints).filter(Hints.cache_id == cache_id).first()
                        if not hint:
                            hint = Hints()
                            cache901.db().add(hint)
                            cache.hint.append(hint)
                        cache.hint[0].hint = node.text
                    elif node.tag.endswith('}travelbugs'):
                        for bugnode in node.findall('{http://www.groundspeak.com/cache/1/0}travelbug'):
                            ref = bugnode.get('ref')
                            bug = cache901.db().query(TravelBugs).filter(TravelBugs.ref == ref).first()
                            if not bug:
                                bug = TravelBugs()
                                cache901.db().add(bug)
                            bug.cache_id = cache_id
                            bug.ref = ref
                            bug.id = int(bugnode.get('id'))
                            bug.name = bugnode.find('{http://www.groundspeak.com/cache/1/0}name').text
            else:
                cache = Locations()
                cache.loc_type = 1
                cache.refers_to = -1
            cache.lat = Decimal(wpt.get('lat'))
            cache.lon = Decimal(wpt.get('lon'))
            for node in wpt.getchildren():
                if node.tag.endswith('}name'): cache.name = node.text
                elif node.tag.endswith('}time'):
                    (year, mon, day)=map(lambda x: int(x), node.text.split('T')[0].split('-'))
                    d = datetime.datetime(year, mon, day, 0, 0, 0)
                    hidden = time.mktime(d.timetuple())
                    if time.daylight:
                        hidden -= time.altzone
                    else:
                        hidden -= time.timezone
                    cache.hidden = hidden
                elif node.tag.endswith('}cmt'): cache.comment = node.text
                elif node.tag.endswith('}desc'):
                    cache.desc = node.text
                    cache.url_desc = node.text
                elif node.tag.endswith('}url'): cache.url = node.text
                elif node.tag.endswith('}urlname'):
                    cache.url_name = node.text
                    if self.ccount == 0:
                        cache901.notify("Processing %s" % cache901.util.forceAscii(cache.url_name))
                    self.ccount = (self.ccount + 1) % 5
                elif node.tag.endswith('}sym'): cache.sym = node.text
                elif node.tag.endswith('}type'): cache.type = node.text
            cache901.db().add(cache)
        cache901.db().commit()
        if maint:
            cache901.db().maintdb()

class XMLHandler(xml.sax.handler.ContentHandler):
    def startElement(self, name, attrs):
        if name == 'wpt':
            pass
        elif name == 'groundspeak:log':
            self.read = 2
            self.log.id = int(attrs['id'])
        elif name == 'groundspeak:finder':
                self.log.finder_id = int(attrs['id'])
        elif name == 'groundspeak:text':
                self.log.log_entry_encoded = (attrs['encoded'].lower() == 'true')


    def endElement(self, name):
        if self.read:
            self.chdata = self.chdata.strip()
            if self.read in (1,5):
                if self.read == 1:
                    wpt = self.wpt
                elif 1==1:
                    wpt = self.logwpt
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
