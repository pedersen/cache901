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

def parse(data, maint=True):
    if (type(data) is str):
        parsed = cElementTree.fromstring(data)
    else:
        parsed = cElementTree.parse(data)
    # manage the parsed data here
    cache_counter = 0
    for wpt in parsed.findall('{http://www.topografix.com/GPX/1/0}wpt'):
        cachedata = wpt.find('{http://www.groundspeak.com/cache/1/0}cache')
        if cachedata:
            cache_id = int(cachedata.get('id'))
            cache = cache901.db().query(Caches).get(cache_id)
            if not cache:
                cache = Caches()
                cache901.db().add(cache)
            cache.cache_id = cache_id
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
                    hint = cache901.db().query(Hints).get(cache_id)
                    if not hint:
                        hint = Hints()
                        cache.hint.append(hint)
                    hint.hint = node.text
                    hint.cache_id = cache.cache_id
                elif node.tag.endswith('}travelbugs'):
                    for bugnode in node.findall('{http://www.groundspeak.com/cache/1/0}travelbug'):
                        ref = bugnode.get('ref')
                        bug = cache901.db().query(TravelBugs).filter(TravelBugs.ref == ref).first()
                        if not bug:
                            bug = TravelBugs()
                            cache.travelbugs.append(bug)
                        bug.ref = ref
                        bug.id = int(bugnode.get('id'))
                        bug.cache_id = cache.cache_id
                        bug.name = bugnode.find('{http://www.groundspeak.com/cache/1/0}name').text
                elif node.tag.endswith('}logs'):
                    for lognode in node.findall('{http://www.groundspeak.com/cache/1/0}log'):
                        logid = lognode.get('id')
                        log = cache901.db().query(Logs).get(logid)
                        if not log:
                            log = Logs()
                            cache.logs.append(log)
                        log.id = logid
                        log.cache_id = cache.cache_id
                        logfindernode = lognode.find('{http://www.groundspeak.com/cache/1/0}finder')
                        log.finder_id = logfindernode.get('id')
                        log.finder = logfindernode.text
                        logtextnode = lognode.find('{http://www.groundspeak.com/cache/1/0}text')
                        log.log_entry_encoded = (logtextnode.get('encoded').lower() == 'true')
                        log.log_entry = logtextnode.text
                        log.type = lognode.find('{http://www.groundspeak.com/cache/1/0}type').text
                        logdatenode = lognode.find('{http://www.groundspeak.com/cache/1/0}date')
                        (year, mon, day)=map(lambda x: int(x), logdatenode.text.split('T')[0].split('-'))
                        d = datetime.datetime(year, mon, day, 0, 0, 0)
                        log.date = time.mktime(d.timetuple())
                        if time.daylight:
                            log.date -= time.altzone
                        else:
                            log.date -= time.timezone
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
                if cache_counter == 0:
                    cache901.notify("Processing %s" % cache901.util.forceAscii(cache.url_name))
                cache_counter = (cache_counter + 1) % 5
            elif node.tag.endswith('}sym'): cache.sym = node.text
            elif node.tag.endswith('}type'): cache.type = node.text
        cache901.db().add(cache)
    cache901.db().commit()
    if maint:
        cache901.db().maintdb()
