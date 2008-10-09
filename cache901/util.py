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

def distance_exact(lat1, lon1, lat2, lon2):
    return 3958.75 * math.acos(math.sin(lat1/57.2958) *
          math.sin(lat2/57.2958) + 
          math.cos(lat1/57.2958) * 
          math.cos(lat2/57.2958) * 
          math.cos(lon2/57.2958 - lon1/57.2958))

def decToDMS(decDegree):
    plus = (decDegree >= 0)
    decDegree = abs(decDegree)
    d = int(decDegree)
    r = (decDegree - d) * 60
    m = int(r)
    r = r - m
    s = "%3.04f" % (r*60)
    return (plus, "%3d° %2d' %s%s" % (d, m, s, '"'))

def latToDMS(decDegree):
    plus, val = decToDMS(decDegree)
    if plus: lat="N"
    else: lat = "S"
    return "%s%s" % (lat, val)

def lonToDMS(decDegree):
    plus, val = decToDMS(decDegree)
    if plus: lat="E"
    else: lat = "W"
    return "%s%s" % (lat, val)

def forceAscii(s):
    return filter(lambda x: ord(x) < 128 and ord(x) > 26, s)