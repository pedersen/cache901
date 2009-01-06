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

import unittest

import cache901
import cache901.dbm

class DbmTest(unittest.TestCase):
    def setUp(self):
        cur = cache901.db().cursor()
        cur.execute("delete from locations")
        cur.execute("delete from caches")
        cur.execute("delete from travelbugs")
        cur.execute("delete from logs")
        cur.execute("delete from hints")
        cache901.db().commit()

    def testScrub(self):
        counter = 0
        cur = cache901.db().cursor()
        for i in range(25):
            cur.execute("insert into caches(cache_id) values(?)", (i,))
            cur.execute("insert into travelbugs(id, cache_id) values(?,?)", (counter,i))
            counter += 1
            cur.execute("insert into travelbugs(id, cache_id) values(?,?)", (counter,i+100))
            counter += 1
            cur.execute("insert into hints(hint, cache_id) values(?,?)", (str(counter),i))
            counter += 1
            cur.execute("insert into hints(hint, cache_id) values(?,?)", (str(counter),i+100))
            counter += 1
            for j in range(25):
                cur.execute("insert into logs(id, cache_id, my_log) values(?,?,0)", (counter, i))
                counter += 1
                cur.execute("insert into logs(id, cache_id, my_log) values(?,?,0)", (counter, i+100))
                counter += 1
        cur.execute('select count(*) from caches')
        row = cur.fetchone()
        self.failUnless(row[0] == 25, 'Expected 25 caches, got %d' % row[0])
        cur.execute('select count(*) from hints')
        row = cur.fetchone()
        self.failUnless(row[0] == 50, 'Expected 50 hints, got %d' % row[0])
        cur.execute('select count(*) from travelbugs')
        row = cur.fetchone()
        self.failUnless(row[0] == 50, 'Expected 50 travelbugs, got %d' % row[0])
        cur.execute('select count(*) from logs')
        row = cur.fetchone()
        self.failUnless(row[0] == 1250, 'Expected 1250 logs, got %d' % row[0])
        cache901.dbm.scrub()
        cur.execute('select count(*) from caches')
        row = cur.fetchone()
        self.failUnless(row[0] == 25, 'Expected 25 caches, got %d' % row[0])
        cur.execute('select count(*) from hints')
        row = cur.fetchone()
        self.failUnless(row[0] == 25, 'Expected 25 hints, got %d' % row[0])
        cur.execute('select count(*) from travelbugs')
        row = cur.fetchone()
        self.failUnless(row[0] == 25, 'Expected 25 travelbugs, got %d' % row[0])