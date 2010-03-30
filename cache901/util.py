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
import shutil
import sys
import tempfile
import wx

from decimal import Decimal, InvalidOperation

from sqlalchemy import func, or_
import cache901
import cache901.kml
from cache901 import sadbobjects
import gpsbabel

degsym = u'\u00B0'

def distance_exact(lat1_in, lon1_in, lat2_in, lon2_in):
    lat1 = float(lat1_in)
    lon1 = float(lon1_in)
    lat2 = float(lat2_in)
    lon2 = float(lon2_in)
    if lat2 > 90 or lat2 < -90 or lon1 > 180 or lon1 < -180:
        return 0.00
    return float('%1.2f' % (3958.75 * math.acos(math.sin(lat1/57.2958) *
          math.sin(lat2/57.2958) + 
          math.cos(lat1/57.2958) * 
          math.cos(lat2/57.2958) * 
          math.cos(lon2/57.2958 - lon1/57.2958))))

def decToD(decDegree):
    plus = (decDegree >= 0)
    decDegree = abs(decDegree)
    return (plus, "%s%s" % (decDegree, degsym))

def decToDM(decDegree):
    plus = (decDegree >= 0)
    decDegree = abs(decDegree)
    d = int(decDegree)
    m = (decDegree - d) * 60
    return (plus, "%3d%s %2.3f'" % (d, degsym, m,))

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
    localdmsstr = localdmsstr[1:].strip()
    loc = localdmsstr.find(degsym)
    if loc >= 0: # found degree symbol
        try:
            deg = Decimal(localdmsstr[:loc].strip())
            localdmsstr = localdmsstr[loc+1:].strip()
        except InvalidOperation:
            raise InvalidDegFormat("Invalid degree specification in %s (%s)" % (dmsstr, localdmsstr[1:loc]))
    else: # no degree symbol found, assuming spaces
        loc = localdmsstr.find(' ')
        if loc >= 0: # found space, proceed
            try:
                deg = Decimal(localdmsstr[:loc].strip())
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
                    return mult * (deg+mins)
                except InvalidOperation:
                    raise InvalidDegFormat("Invalid minutes specification in %s" % dmsstr)
    if len(localdmsstr) > 0:
        loc = localdmsstr.find('"')
        if loc >= 0: # seconds mark found, remove it
            localdmsstr = localdmsstr[:loc].strip()
        secs = Decimal(localdmsstr) / Decimal("3600.0")
    return mult * (deg + mins + secs)

def displayDMS(dec):
    idx = ['deg min sec', 'deg min', 'deg'].index(cache901.cfg().degdisplay)
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
        syspath = ['.']
        syspath.append(cache901.__path__[0].replace('%slibrary.zip' % os.sep, ''))
        syspath = os.environ['PATH'].split(';')
        for d in syspath:
            t = os.sep.join([d, cmd])
            for ext in ['exe', 'bat', 'com']:
                f = "%s.%s" % (t, ext)
                if os.path.exists(f) and os.access(f, os.X_OK) and not os.path.isdir(f):
                    return f
    else:
        for d in os.environ['PATH'].split(':'):
            f = os.sep.join([d, cmd])
            if os.path.exists(f) and os.access(f, os.X_OK) and not os.path.isdir(f):
                return f
    return None

def scanForSerial():
    available = []
    if sys.platform == "win32":
        import cache901.scanwin32
        available.extend(map(lambda x: '%s:' % str(x), cache901.scanwin32.getSerialPorts()))
    else:
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

def getWaypoints(params={}):
    qry = cache901.db().query(sadbobjects.Locations).filter(sadbobjects.Locations.loc_type == 1).order_by(sadbobjects.Locations.name)
    if params.has_key('ids'):
        qry = qry.add_column(sadbobjects.CacheDay.cache_order)
        qry = qry.outerjoin((sadbobjects.CacheDay, sadbobjects.CacheDay.cache_id == sadbobjects.Locations.wpt_id))
        qry = qry.filter(sadbobjects.Locations.loc_type == 1)
        qry = qry.filter(sadbobjects.Locations.wpt_id.in_(params['ids']))
        qry = qry.order_by(sadbobjects.CacheDay.cache_order)
    if params.has_key('searchpat') and len(params['searchpat']) >= 2:
        qry = qry.filter(func.lower(sadbobjects.Locations.name).like(params['searchpat']))
    if params.has_key('addwpts'): # additional waypoints listing
        qry = qry.filter(sadbobjects.Locations.name.in_(params['addwpts']))
    return qry

def getSearchLocs(searchpat=None):
    qry = cache901.db().query(sadbobjects.Locations).filter(sadbobjects.Locations.loc_type == 2)
    if searchpat is not None or len(searchpat) >= 2:
        searchpat = '%%%s%%' % (searchpat.lower())
        qry = qry.filter(or_(
            func.lower(sadbobjects.Locations.name).like(searchpat),
            func.lower(sadbobjects.Locations.desc).like(searchpat)
        ))
    qry = qry.order_by(sadbobjects.Locations.name)
    return qry

def getDefaultCoords(cache):
    for coords in cache.alt_coords:
        if coords.setdefault == 1:
            return (Decimal(dmsToDec(coords.lat)), Decimal(dmsToDec(coords.lon)))
    return (cache.lat, cache.lon)
    

def exportKML(cacheids, outdir=None, confirmDir=True):
    if outdir is None and not confirmDir:
        raise Exception('Never exported KML before, no idea where to write it.')
    if confirmDir:
        outdir = cache901.cfg().lastkmldir
        if outdir is None: outdir = wx.EmptyString
        outdir=wx.DirSelector("Select output directory", outdir, parent=wx.GetApp().GetTopWindow())
        if outdir != "":
            cache901.cfg().lastkmldir = outdir
        else:
            return
    k = cache901.kml.KML()
    k.export(cacheids, outdir)

def exportTomTomPOI(cacheids, outdir=None, confirmDir=True):
    if outdir is None and not confirmDir:
        raise Exception('Never exported TomTom POI before, no idea where to write it.')
    if confirmDir:
        outdir = cache901.cfg().lasttomtompoidir
        if outdir is None: outdir = wx.EmptyString
        outdir=wx.DirSelector("Select output directory", outdir, parent=wx.GetApp().GetTopWindow())
        if outdir != "":
            cache901.cfg().lasttomtompoidir = outdir
        else:
            return
    tmpdir = tempfile.mkdtemp()
    k = cache901.kml.KML()
    k.export(cacheids, tmpdir, True)
    gpsbabel.gps.addInputFile(os.sep.join([tmpdir, "cache901.kml"]), "kml")
    gpsbabel.gps.addOutputFile(os.sep.join([outdir, "Cache901.ov2"]), "tomtom")
    gpsbabel.gps.procWpts = True
    (retcode, output) = gpsbabel.gps.execCmd(parseOutput = False)
    if retcode != 0:
        raise Exception(output)
    shutil.rmtree(tmpdir)
    geoicons = wx.GetApp().GetTopWindow().geoicons
    bmp = geoicons['shield_poi']
    bmp.SaveFile(os.sep.join([outdir, "Cache901.bmp"]), wx.BITMAP_TYPE_BMP)

def getDbList():
    return map(lambda x: os.path.splitext(x)[0], filter(lambda x: x.lower().endswith('.sqlite'), os.listdir(cache901.cfg().dbpath)))

def CacheToGPX(cache):
    gpx = gpsbabel.GPXData()
    wpt = gpsbabel.GPXWaypoint()
    (lat, lon) = getDefaultCoords(cache)
    wpt.lat = lat
    wpt.lon = lon
    wpt.name = cache.name
    wpt.cmt = cache.name
    wpt.desc = cache.name
    gpx.wpts.append(wpt)
    return gpx

def CacheDayToGPX(cacheday):
    gpx = gpsbabel.GPXData()
    route = gpsbabel.GPXRoute()
    route.name = cacheday.dayname
    for cdata in cacheday.caches:
        if cdata.cache_type == 1:
            wptdata = cdata.cache
        else:
            wptdata = cdata.loc
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
