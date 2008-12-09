# -*- coding: latin-1 -*-
"""
Cache901 - GeoCaching Software for the Asus EEE PC 901
Copyright (C) 2007, Michael J. Pedersen <m.pedersen@icelus.org>

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

import math
import os
import os.path
import serial
import sys
import wx

from decimal import Decimal, InvalidOperation

import cache901
import cache901.dbobjects
import gpsbabel

degsym = u'\u00B0'

def distance_exact(lat1, lon1, lat2, lon2):
    return 3958.75 * math.acos(math.sin(lat1/57.2958) *
          math.sin(lat2/57.2958) + 
          math.cos(lat1/57.2958) * 
          math.cos(lat2/57.2958) * 
          math.cos(lon2/57.2958 - lon1/57.2958))

def decToD(decDegree):
    plus = (decDegree >= 0)
    decDegree = abs(decDegree)
    return (plus, "%s%s" % (decDegree, degsym))

def decToDM(decDegree):
    plus = (decDegree >= 0)
    decDegree = abs(decDegree)
    d = int(decDegree)
    m = (decDegree - d) * 60
    return (plus, "%3d%s %2d'" % (d, degsym, m,))

def decToDMS(decDegree):
    plus = (decDegree >= 0)
    decDegree = abs(decDegree)
    d = int(decDegree)
    r = (decDegree - d) * 60
    m = int(r)
    r = r - m
    s = "%3.04f" % (r*60)
    return (plus, "%3d%s %2d' %s%s" % (d, degsym, m, s, '"'))

def dmsToDec(dmsstr):
    deg = Decimal("0.00")
    mins = Decimal("0.00")
    secs = Decimal("0.00")
    dmsstr = dmsstr.strip()
    localdmsstr = dmsstr
    if localdmsstr[0].lower() not in ['n', 's', 'e', 'w']:
        try:
            deg = Decimal(localdmsstr)
            return deg
        except InvalidOperation:
            raise InvalidDegFormat("Invalid direction (not NSEW): %s" % dmsstr)
    mult = 1 if localdmsstr[0].lower() in ['n', 'e'] else -1
    loc = localdmsstr.find(degsym)
    if loc >= 0: # found degree symbol
        try:
            deg = Decimal(localdmsstr[1:loc].strip())
            localdmsstr = localdmsstr[loc+1:].strip()
        except InvalidOperation:
            raise InvalidDegFormat("Invalid degree specification in %s (%s)" % (dmsstr, localdmsstr[1:loc]))
    else: # no degree symbol found, assuming spaces
        loc = localdmsstr.find(' ')
        if loc >= 0: # found space, proceed
            try:
                deg = Decimal(localdmsstr[1:loc].strip())
                localdmsstr = localdmsstr[loc:].strip()
            except InvalidOperation:
                raise InvalidDegFormat("Invalid degrees specification in %s (%s)" % (dmsstr, localdmsstr[1:loc].strip()))
        else:
            try:
                deg = Decimal(localdmsstr)
                return deg
            except InvalidOperation:
                raise InvalidDegFormat("No spaces, no degree symbol, or invalid symbol in %s" % dmsstr)
    if len(localdmsstr) > 0:
        loc = localdmsstr.find("'")
        if loc >= 0: # minutes mark found
            try:
                mins = Decimal(localdmsstr[:loc].strip()) / Decimal("60.0")
                localdmsstr = localdmsstr[loc+1:].strip()
            except InvalidOperation:
                raise InvalidDegFormat("Invalid minutes specification in %s (%s)" % (dmsstr, localdmsstr[:loc]))
        else:
            loc = localdmsstr.find(' ')
            if loc >= 0: # space found, up to space is minutes
                mins = Decimal(localdmsstr[:loc].strip()) / Decimal("60.0")
                localdmsstr = localdmsstr[loc:].strip()
            else:
                try:
                    mins = Decimal(localdmsstr) / Decimal("60.0")
                    return deg+mins
                except InvalidOperation:
                    raise InvalidDegFormat("Invalid minutes specification in %s" % dmsstr)
    if len(localdmsstr) > 0:
        loc = localdmsstr.find('"')
        if loc >= 0: # seconds mark found, remove it
            localdmsstr = localdmsstr[:loc].strip()
        secs = Decimal(localdmsstr) / Decimal("3600.0")
    return mult * (deg + mins + secs)

def displayDMS(dec):
    cfg = wx.Config.Get()
    isinstance(cfg, wx.Config)
    cfg.SetPath('/PerMachine')
    idx = ['deg min sec', 'deg min', 'deg'].index(cfg.Read('degDisplay', 'deg min sec'))
    if idx == 0:
        return decToDMS(dec)
    elif idx == 1:
        return decToDM(dec)
    else:
        return decToD(dec)

def latToDMS(decDegree):
    plus, val = displayDMS(decDegree)
    if plus: lat="N"
    else: lat = "S"
    return "%s%s" % (lat, val)

def lonToDMS(decDegree):
    plus, val = displayDMS(decDegree)
    if plus: lat="E"
    else: lat = "W"
    return "%s%s" % (lat, val)

def forceAscii(s):
    return filter(lambda x: ord(x) < 128 and ord(x) > 26, s)

def which(cmd):
    if sys.platform == 'win32':
        for d in os.environ['PATH'].split(';'):
            t = os.sep.join([d, cmd])
            for ext in ['exe', 'bat', 'com']:
                f = "%s.%s" % (t, ext)
                if os.path.exists(f) and os.access(f, os.X_OK):
                    return f
    else:
        for d in os.environ['PATH'].split(':'):
            f = os.sep.join([d, cmd])
            if os.path.exists(f) and os.access(f, os.X_OK):
                return f
    return None

def scanForSerial():
    if sys.platform == "win32":
        # @todo: Fix the scanning on Windows
        pass
    else:
        available = []
        for i in range(256):
            try:
                s = serial.Serial(i)
                available.append(s.portstr)
                s.close()   #explicit close 'cause of delayed GC in java
            except serial.SerialException:
                pass
        for i in range(256):
            try:
                s = serial.Serial('/dev/ttyUSB%d' % i)
                available.append(s.portstr)
                s.close()   #explicit close 'cause of delayed GC in java
            except serial.SerialException:
                pass
    return available

def getWaypoints(searchpat=None):
    if searchpat in (None, "", "*") or len(searchpat) < 2:
        where = "where loc_type = 1"
        params = ()
    else:
        where = "where loc_type = 1 and (lower(name) like ? or lower(desc) like ?)"
        params = (searchpat, searchpat)
    query = "%s %s %s" % ("select wpt_id, name, desc from locations", where, "order by name")
    cur = cache901.db().cursor()
    cur.execute(query, params)
    for row in cur:
        yield row

def getSearchLocs(searchpat=None):
    if searchpat in (None, "", "*") or len(searchpat) < 2:
        where = "where loc_type = 2"
        params = ()
    else:
        where = "where loc_type = 2 and (lower(name) like ? or lower(desc) like ?)"
        params = (searchpat, searchpat)
    query = "%s %s %s" % ("select wpt_id, name, desc from locations", where, "order by name")
    cur = cache901.db().cursor()
    cur.execute(query, params)
    for row in cur:
        yield row

def CacheToGPX(cache):
    gpx = gpsbabel.GPXData()
    wpt = gpsbabel.GPXWaypoint()
    wpt.lat = cache.lat
    wpt.lon = cache.lon
    wpt.name = cache.name
    wpt.cmt = cache.name
    wpt.desc = cache.name
    gpx.wpts.append(wpt)
    return gpx

def CacheDayToGPX(cacheday):
    isinstance(cacheday, cache901.dbobjects.CacheDay)
    gpx = gpsbabel.GPXData()
    route = gpsbabel.GPXRoute()
    route.name = cacheday.dayname
    for wptdata in cacheday.caches:
        wpt = gpsbabel.GPXWaypoint()
        wpt.lat = wptdata.lat
        wpt.lon = wptdata.lon
        wpt.cmt = wptdata.name
        wpt.desc = wptdata.name
        wpt.name = wptdata.name
        route.rtepts.append(wpt)
        gpx.wpts.append(wpt)
    gpx.rtes.append(route)
    return gpx
        
class InvalidDegFormat(Exception):
    pass
