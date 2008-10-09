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

"""
Up to revision 6, there was a file called 'distcalc.py'. This version had
some less precise distance measuring equations, and they can be used in
case of dire need. They ran up to four times faster.

It's noted here for future reference, but we should probably never use
them.

It was originally in trunk/test/distcalc.py
"""

import unittest
import timeit
try:
    import sqlite3 as sqlite
except ImportError, e:
    from pysqlite2 import dbapi2 as sqlite

import cache901.util
# Oxford, NJ
lat1 =  40.8130
lon1 = -75.0047

# Somerset, NJ
lat2 =  40.5013
lon2 = -74.5325

def sqlite_dist(lat1, lon1, lat2, lon2):
    con = sqlite.connect(":memory:")
    con.create_function("distance", 4, cache901.util.distance_exact)
    cur = con.cursor()
    i=0
    while i < 1000:
        cur.execute("select distance(?, ?, ?, ?)", (lat1, lon1, lat2, lon2))
        i += 1

class utilTest(unittest.TestCase):
    def testDistanceExact(self):
        t = timeit.Timer('cache901.util.distance_exact(%f, %f, %f, %f)' % (lat1, lon1, lat2, lon2), 'import cache901.util')
        print "Calculating exact distance 1,000 times",
        ttime = t.timeit(1000)
        print "Done!"

        print '\tTime to calculate exact distance 1,000 times: %3.3fs' % ttime
        print '\tCalculations per second: %3.3f' % (1000.0/ttime)

    def testSqliteDistanceExact(self):
        t = timeit.Timer('test.utilSpeed.sqlite_dist(%f, %f, %f, %f)' % (lat1, lon1, lat2, lon2), 'import test.utilSpeed')
        print "Calculating sqlite estimated distance 1,000 times",
        ttime = t.timeit(1)
        print "Done!"

        print '\tTime to calculate sqlite estimated distance 1,000 times: %3.3fs' % ttime
        print '\tCalculations per second: %3.3f' % (1000.0/ttime)
