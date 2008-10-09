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
import cache901.sqlobjects

class XmlWaypointSaverTest(unittest.TestCase):
    def setUp(self):
        self.saver = cache901.sqlobjects.xmlWaypointSaver()
        cur = cache901.db().cursor()
        cur.execute("delete from locations")
        cur.execute("delete from caches")
        cur.execute("delete from travelbugs")
        cur.execute("delete from logs")
        cur.execute("delete from hints")
        cache901.db().commit()

    def testInit(self):
        for strs in ['name', 'desc', 'comment', 'url', 'url_name', 'url_desc', 'sym', 'type', 'placed_by', 'owner_name', 'container', 'country', 'state', 'short_desc', 'long_desc']:
            self.failUnless(getattr(self.saver, strs) == "")
        for ints in ['loc_type', 'refers_to', 'id', 'catid', 'owner_id' ]:
            self.failUnless(getattr(self.saver, ints) == 0)
        for floats in ['lat', 'lon', 'difficulty', 'terrain' ]:
            self.failUnless(getattr(self.saver, floats) == 0.00)
        for bools in ['available', 'archived', 'short_desc_html', 'long_desc_html', 'cache']:
            self.failUnless(getattr(self.saver, bools) == False)

    def testCacheStatus(self):
        self.failUnless(self.saver.isCache() == False)

    def testClear(self):
        for strs in ['name', 'desc', 'comment', 'url', 'url_name', 'url_desc', 'sym', 'type', 'placed_by', 'owner_name', 'container', 'country', 'state', 'short_desc', 'long_desc']:
            setattr(self.saver, strs, "text")
        for ints in ['loc_type', 'refers_to', 'id', 'catid', 'owner_id' ]:
            setattr(self.saver, ints, 1)
        for floats in ['lat', 'lon', 'difficulty', 'terrain' ]:
            setattr(self.saver, floats, 2.22)
        for bools in ['available', 'archived', 'short_desc_html', 'long_desc_html', 'cache']:
            setattr(self.saver, bools, True)
        self.saver.Clear()
        for strs in ['name', 'desc', 'comment', 'url', 'url_name', 'url_desc', 'sym', 'type', 'placed_by', 'owner_name', 'container', 'country', 'state', 'short_desc', 'long_desc']:
            self.failUnless(getattr(self.saver, strs) == "")
        for ints in ['loc_type', 'refers_to', 'id', 'catid', 'owner_id' ]:
            self.failUnless(getattr(self.saver, ints) == 0)
        for floats in ['lat', 'lon', 'difficulty', 'terrain' ]:
            self.failUnless(getattr(self.saver, floats) == 0.00)
        for bools in ['available', 'archived', 'short_desc_html', 'long_desc_html', 'cache']:
            self.failUnless(getattr(self.saver, bools) == False)

    def testSaveWaypoint(self):
        self.saver.loc_type  = 1
        self.saver.refers_to = -1
        self.saver.name      = "Test Waypoint #1"
        self.saver.desc      = "The Tester's Choice!"
        self.saver.comment   = "The premier waypoint of tester's everywhere"
        self.saver.lat       = 40.8130
        self.saver.lon       = -75.0047
        wpt_id = self.saver.Save()
        for strs in ['name', 'desc', 'comment', 'url', 'url_name', 'url_desc', 'sym', 'type', 'placed_by', 'owner_name', 'container', 'country', 'state', 'short_desc', 'long_desc']:
            self.failUnless(getattr(self.saver, strs) == "")
        for ints in ['loc_type', 'refers_to', 'id', 'catid', 'owner_id' ]:
            self.failUnless(getattr(self.saver, ints) == 0)
        for floats in ['lat', 'lon', 'difficulty', 'terrain' ]:
            self.failUnless(getattr(self.saver, floats) == 0.00)
        for bools in ['available', 'archived', 'short_desc_html', 'long_desc_html', 'cache']:
            self.failUnless(getattr(self.saver, bools) == False)
        cur = cache901.db().cursor()
        cur.execute("select wpt_id, loc_type, refers_to, name, desc, comment, lat, lon from locations where wpt_id=?", (wpt_id, ))
        rowfound = 0
        for row in cur:
            rowfound += 1
            self.failUnless(row[0] == wpt_id)
            self.failUnless(row[1] == 1)
            self.failUnless(row[2] == -1)
            self.failUnless(row[3] == "Test Waypoint #1")
            self.failUnless(row[4] == "The Tester's Choice!")
            self.failUnless(row[5] == "The premier waypoint of tester's everywhere")
            self.failUnless(row[6] == 40.8130)
            self.failUnless(row[7] == -75.0047)
        self.failUnless(rowfound == 1, "Waypoint was not found in the database!")
        # Check to make sure the update works
        self.saver.loc_type  = 1
        self.saver.refers_to = -1
        self.saver.name      = "Test Waypoint #1"
        self.saver.desc      = "The Tester's Choice!"
        self.saver.comment   = "The premier waypoint of tester's everywhere"
        self.saver.lat       = 42.8130
        self.saver.lon       = -77.0047
        wpt_id = self.saver.Save()
        cur = cache901.db().cursor()
        cur.execute("select wpt_id, loc_type, refers_to, name, desc, comment, lat, lon from locations where name=?", ("Test Waypoint #1", ))
        rowfound = 0
        for row in cur:
            rowfound += 1
            self.failUnless(row[0] == wpt_id)
            self.failUnless(row[1] == 1)
            self.failUnless(row[2] == -1)
            self.failUnless(row[3] == "Test Waypoint #1")
            self.failUnless(row[4] == "The Tester's Choice!")
            self.failUnless(row[5] == "The premier waypoint of tester's everywhere")
            self.failUnless(row[6] == 42.8130)
            self.failUnless(row[7] == -77.0047)
        self.failUnless(rowfound == 1, "Too many copies of waypoint found in the database!")
        # Check to make sure that adding another waypoint works
        self.saver.loc_type  = 1
        self.saver.refers_to = -1
        self.saver.name      = "Test Waypoint #2"
        self.saver.desc      = "The Tester's Choice!"
        self.saver.comment   = "The premier waypoint of tester's everywhere"
        self.saver.lat       = 42.8130
        self.saver.lon       = -77.0047
        wpt_id = self.saver.Save()
        cur = cache901.db().cursor()
        cur.execute("select wpt_id, loc_type, refers_to, name, desc, comment, lat, lon from locations where wpt_id=?", (wpt_id, ))
        rowfound = 0
        for row in cur:
            rowfound += 1
            self.failUnless(row[0] == wpt_id)
            self.failUnless(row[1] == 1)
            self.failUnless(row[2] == -1)
            self.failUnless(row[3] == "Test Waypoint #2")
            self.failUnless(row[4] == "The Tester's Choice!")
            self.failUnless(row[5] == "The premier waypoint of tester's everywhere")
            self.failUnless(row[6] == 42.8130)
            self.failUnless(row[7] == -77.0047)
        self.failUnless(rowfound == 1, "Too many copies of waypoint found in the database!")

        cur.execute("select count(*) from locations")
        count = cur.fetchone()[0]
        self.failUnless(count == 2, "Incorrect number of rows found: %d (2 expected)" % rowfound)

    def testSaveCache(self):
        self.saver.cache      = True
        self.saver.cache_id   = 101
        self.saver.url        = "http//www.cache901.org/"
        self.saver.url_name   = "Test Cache #1"
        self.saver.url_desc   = "The Tester's Choice!"
        self.saver.name       = "Test Cache #1"
        self.saver.sym        = "Ammo Can"
        self.saver.type       = "Traditional"
        self.saver.available  = True
        self.saver.archived   = True
        self.saver.placed_by  = "m.pedersen"
        self.saver.owner_id   = 201
        self.saver.owner_name = "mtngeeks"
        self.saver.container  = "Ammunition Box"
        self.saver.difficulty = 3.5
        self.saver.terrain    = 4.5
        self.saver.country    = "USA"
        self.saver.state      = "NJ"
        self.saver.short_desc = "<pre>Quick Desc</pre>"
        self.saver.long_desc  = "<pre>Long Desc</pre>"
        self.saver.lat        = 40.8130
        self.saver.lon        = -75.0047
        self.saver.short_desc_html = True
        self.saver.long_desc_html  = True
        cache_id = self.saver.Save()
        for strs in ['name', 'desc', 'comment', 'url', 'url_name', 'url_desc', 'sym', 'type', 'placed_by', 'owner_name', 'container', 'country', 'state', 'short_desc', 'long_desc']:
            self.failUnless(getattr(self.saver, strs) == "")
        for ints in ['loc_type', 'refers_to', 'id', 'catid', 'owner_id' ]:
            self.failUnless(getattr(self.saver, ints) == 0)
        for floats in ['lat', 'lon', 'difficulty', 'terrain' ]:
            self.failUnless(getattr(self.saver, floats) == 0.00)
        for bools in ['available', 'archived', 'short_desc_html', 'long_desc_html', 'cache']:
            self.failUnless(getattr(self.saver, bools) == False)
        cur = cache901.db().cursor()
        cur.execute("select cache_id, url, url_name, url_desc, name, sym, type, available, archived, placed_by, owner_id, owner_name, container, difficulty, terrain, country, state, short_desc, long_desc, lat, lon, short_desc_html, long_desc_html from caches where cache_id=?", (cache_id, ))
        rowfound = 0
        for row in cur:
            rowfound += 1
            self.failUnless(row[ 0] == 101)
            self.failUnless(row[ 1] == "http//www.cache901.org/")
            self.failUnless(row[ 2] == "Test Cache #1")
            self.failUnless(row[ 3] == "The Tester's Choice!")
            self.failUnless(row[ 4] == "Test Cache #1")
            self.failUnless(row[ 5] == "Ammo Can")
            self.failUnless(row[ 6] == "Traditional")
            self.failUnless(row[ 7] == True)
            self.failUnless(row[ 8] == True)
            self.failUnless(row[ 9] == "m.pedersen")
            self.failUnless(row[10] == 201)
            self.failUnless(row[11] == "mtngeeks")
            self.failUnless(row[12] == "Ammunition Box")
            self.failUnless(row[13] == 3.5)
            self.failUnless(row[14] == 4.5)
            self.failUnless(row[15] == "USA")
            self.failUnless(row[16] == "NJ")
            self.failUnless(row[17] == "<pre>Quick Desc</pre>")
            self.failUnless(row[18] == "<pre>Long Desc</pre>")
            self.failUnless(row[19] == 40.8130)
            self.failUnless(row[20] == -75.0047)
            self.failUnless(row[21] == True)
            self.failUnless(row[22] == True)
        self.failUnless(rowfound == 1, "Cache was not found in the database!")
        # Check to make sure the update works
        self.saver.cache      = True
        self.saver.cache_id   = 101
        self.saver.url        = "http//www.cache901.org/"
        self.saver.url_name   = "Test Cache #1"
        self.saver.url_desc   = "The Tester's Choice!"
        self.saver.name       = "Test Cache #1"
        self.saver.sym        = "Ammo Can"
        self.saver.type       = "Traditional"
        self.saver.available  = True
        self.saver.archived   = True
        self.saver.placed_by  = "m.pedersen"
        self.saver.owner_id   = 201
        self.saver.owner_name = "mtngeeks"
        self.saver.container  = "Ammunition Box"
        self.saver.difficulty = 3.5
        self.saver.terrain    = 4.5
        self.saver.country    = "USA"
        self.saver.state      = "NJ"
        self.saver.short_desc = "<pre>Quick Desc</pre>"
        self.saver.long_desc  = "<pre>Long Desc</pre>"
        self.saver.lat        = 42.8130
        self.saver.lon        = -73.0047
        self.saver.short_desc_html = True
        self.saver.long_desc_html  = True
        cache_id = self.saver.Save()
        cur = cache901.db().cursor()
        cur.execute("select cache_id, url, url_name, url_desc, name, sym, type, available, archived, placed_by, owner_id, owner_name, container, difficulty, terrain, country, state, short_desc, long_desc, lat, lon, short_desc_html, long_desc_html from caches where cache_id=?", (cache_id, ))
        rowfound = 0
        for row in cur:
            rowfound += 1
            self.failUnless(row[ 0] == 101)
            self.failUnless(row[ 1] == "http//www.cache901.org/")
            self.failUnless(row[ 2] == "Test Cache #1")
            self.failUnless(row[ 3] == "The Tester's Choice!")
            self.failUnless(row[ 4] == "Test Cache #1")
            self.failUnless(row[ 5] == "Ammo Can")
            self.failUnless(row[ 6] == "Traditional")
            self.failUnless(row[ 7] == True)
            self.failUnless(row[ 8] == True)
            self.failUnless(row[ 9] == "m.pedersen")
            self.failUnless(row[10] == 201)
            self.failUnless(row[11] == "mtngeeks")
            self.failUnless(row[12] == "Ammunition Box")
            self.failUnless(row[13] == 3.5)
            self.failUnless(row[14] == 4.5)
            self.failUnless(row[15] == "USA")
            self.failUnless(row[16] == "NJ")
            self.failUnless(row[17] == "<pre>Quick Desc</pre>")
            self.failUnless(row[18] == "<pre>Long Desc</pre>")
            self.failUnless(row[19] == 42.8130)
            self.failUnless(row[20] == -73.0047)
            self.failUnless(row[21] == True)
            self.failUnless(row[22] == True)
        self.failUnless(rowfound == 1, "Too many copies of cache found in the database!")
        # Check to make sure that adding another cache works
        self.saver.cache      = True
        self.saver.cache_id   = 102
        self.saver.url        = "http//www.cache901.org/"
        self.saver.url_name   = "Test Cache #2"
        self.saver.url_desc   = "The Tester's Choice!"
        self.saver.name       = "Test Cache #2"
        self.saver.sym        = "Ammo Can"
        self.saver.type       = "Traditional"
        self.saver.available  = True
        self.saver.archived   = True
        self.saver.placed_by  = "m.pedersen"
        self.saver.owner_id   = 202
        self.saver.owner_name = "mtngeeks"
        self.saver.container  = "Ammunition Box"
        self.saver.difficulty = 3.5
        self.saver.terrain    = 4.5
        self.saver.country    = "USA"
        self.saver.state      = "NJ"
        self.saver.short_desc = "<pre>Quick Desc</pre>"
        self.saver.long_desc  = "<pre>Long Desc</pre>"
        self.saver.lat        = 42.8130
        self.saver.lon        = -73.0047
        self.saver.short_desc_html = True
        self.saver.long_desc_html  = True
        cache_id = self.saver.Save()
        cur = cache901.db().cursor()
        cur.execute("select cache_id, url, url_name, url_desc, name, sym, type, available, archived, placed_by, owner_id, owner_name, container, difficulty, terrain, country, state, short_desc, long_desc, lat, lon, short_desc_html, long_desc_html from caches where cache_id=?", (cache_id, ))
        rowfound = 0
        for row in cur:
            rowfound += 1
            self.failUnless(row[ 0] == 102)
            self.failUnless(row[ 1] == "http//www.cache901.org/")
            self.failUnless(row[ 2] == "Test Cache #2")
            self.failUnless(row[ 3] == "The Tester's Choice!")
            self.failUnless(row[ 4] == "Test Cache #2")
            self.failUnless(row[ 5] == "Ammo Can")
            self.failUnless(row[ 6] == "Traditional")
            self.failUnless(row[ 7] == True)
            self.failUnless(row[ 8] == True)
            self.failUnless(row[ 9] == "m.pedersen")
            self.failUnless(row[10] == 202)
            self.failUnless(row[11] == "mtngeeks")
            self.failUnless(row[12] == "Ammunition Box")
            self.failUnless(row[13] == 3.5)
            self.failUnless(row[14] == 4.5)
            self.failUnless(row[15] == "USA")
            self.failUnless(row[16] == "NJ")
            self.failUnless(row[17] == "<pre>Quick Desc</pre>")
            self.failUnless(row[18] == "<pre>Long Desc</pre>")
            self.failUnless(row[19] == 42.8130)
            self.failUnless(row[20] == -73.0047)
            self.failUnless(row[21] == True)
            self.failUnless(row[22] == True)
        self.failUnless(rowfound == 1, "Too many copies of cache found in the database!")

        cur.execute("select count(*) from caches")
        count = cur.fetchone()[0]
        self.failUnless(count == 2, "Incorrect number of rows found: %d (2 expected)" % rowfound)

class XmlLogSaverTest(unittest.TestCase):
    def setUp(self):
        self.log = cache901.sqlobjects.xmlLogSaver()

    def testInit(self):
        self.failUnless(self.log.id == -1)
        self.failUnless(self.log.cache_id == -1)
        self.failUnless(self.log.date == 0)
        self.failUnless(self.log.type == "")
        self.failUnless(self.log.finder == "")
        self.failUnless(self.log.finder_id == "")
        self.failUnless(self.log.log_entry == "")
        self.failUnless(self.log.log_entry_encoded == "")
        self.failUnless(self.log.my_log == False)
        self.failUnless(self.log.my_log_found == False)

    def testClear(self):
        self.log.id = 1
        self.log.cache_id = 1
        self.log.date = 1
        self.log.type = "test"
        self.log.finder = "test"
        self.log.finder_id = "test"
        self.log.log_entry = "test"
        self.log.log_entry_encoded = "test"
        self.log.my_log = True
        self.log.my_log_found = True
        self.log.Clear()
        self.failUnless(self.log.id == -1)
        self.failUnless(self.log.cache_id == -1)
        self.failUnless(self.log.date == 0)
        self.failUnless(self.log.type == "")
        self.failUnless(self.log.finder == "")
        self.failUnless(self.log.finder_id == "")
        self.failUnless(self.log.log_entry == "")
        self.failUnless(self.log.log_entry_encoded == "")
        self.failUnless(self.log.my_log == False)
        self.failUnless(self.log.my_log_found == False)

    def testSave(self):
        cur=cache901.db().cursor()
        cur.execute("delete from logs")

        self.log.id = 1
        self.log.cache_id = 1
        self.log.date = 1
        self.log.type = "test"
        self.log.finder = "test"
        self.log.finder_id = 2
        self.log.log_entry = "test"
        self.log.log_entry_encoded = "test"
        self.log.my_log = True
        self.log.my_log_found = True
        self.log.Save()

        self.failUnless(self.log.id == -1)
        self.failUnless(self.log.cache_id == -1)
        self.failUnless(self.log.date == 0)
        self.failUnless(self.log.type == "")
        self.failUnless(self.log.finder == "")
        self.failUnless(self.log.finder_id == "")
        self.failUnless(self.log.log_entry == "")
        self.failUnless(self.log.log_entry_encoded == "")
        self.failUnless(self.log.my_log == False)
        self.failUnless(self.log.my_log_found == False)

        cur=cache901.db().cursor()
        cur.execute("select count(*) from logs")
        count = cur.fetchone()[0]
        self.failUnless(count == 1, "Incorrect number of logs found: %d (1 expected)!" % count)

        self.log.id = 1
        self.log.cache_id = 1
        self.log.date = 1
        self.log.type = "test"
        self.log.finder = "test"
        self.log.finder_id = 2
        self.log.log_entry = "test"
        self.log.log_entry_encoded = "test"
        self.log.my_log = True
        self.log.my_log_found = True
        self.log.Save()

        cur=cache901.db().cursor()
        cur.execute("select count(*) from logs")
        count = cur.fetchone()[0]
        self.failUnless(count == 1, "Incorrect number of logs found: %d (1 expected)!" % count)

        self.log.id = 2
        self.log.cache_id = 2
        self.log.date = 1
        self.log.type = "test"
        self.log.finder = "test"
        self.log.finder_id = 3
        self.log.log_entry = "test"
        self.log.log_entry_encoded = "test"
        self.log.my_log = True
        self.log.my_log_found = True
        self.log.Save()

        cur=cache901.db().cursor()
        cur.execute("select count(*) from logs")
        count = cur.fetchone()[0]
        self.failUnless(count == 2, "Incorrect number of logs found: %d! (2 expected)" % count)

class XmlBugSaverTest(unittest.TestCase):
    def setUp(self):
        self.bug = cache901.sqlobjects.xmlBugSaver()

    def testInit(self):
        self.failUnless(self.bug.id == -1)
        self.failUnless(self.bug.cache_id == -1)
        self.failUnless(self.bug.name == "")
        self.failUnless(self.bug.ref == "")

    def testClear(self):
        self.bug.id = 101
        self.bug.cache_id = 202
        self.bug.name = "The Best Bug"
        self.bug.ref = "bugref"
        self.bug.Clear()

        self.failUnless(self.bug.id == -1)
        self.failUnless(self.bug.cache_id == -1)
        self.failUnless(self.bug.name == "")
        self.failUnless(self.bug.ref == "")

    def testSave(self):
        cur=cache901.db().cursor()
        cur.execute("delete from travelbugs")

        self.bug.id = 101
        self.bug.cache_id = 202
        self.bug.name = "The Best Bug"
        self.bug.ref = "bugref"
        bug_id = self.bug.Save()

        self.failUnless(self.bug.id == -1)
        self.failUnless(self.bug.cache_id == -1)
        self.failUnless(self.bug.name == "")
        self.failUnless(self.bug.ref == "")

        cur.execute("select id, cache_id, name, ref from travelbugs where id=?", (bug_id, ))
        rowfound = 0
        for row in cur:
            rowfound += 1
            self.failUnless(row[0] == bug_id)
            self.failUnless(row[1] == 202)
            self.failUnless(row[2] == "The Best Bug")
            self.failUnless(row[3] == "bugref")
        self.failUnless(rowfound == 1, "Incorrect number of rows found: %d (1 expected)" % rowfound)

        self.bug.id = 101
        self.bug.cache_id = 202
        self.bug.name = "The Best Bug"
        self.bug.ref = "bugref"
        bug_id = self.bug.Save()
        cur.execute("select id, cache_id, name, ref from travelbugs where id=?", (bug_id, ))
        rowfound = 0
        for row in cur:
            rowfound += 1
            self.failUnless(row[0] == bug_id)
            self.failUnless(row[1] == 202)
            self.failUnless(row[2] == "The Best Bug")
            self.failUnless(row[3] == "bugref")
        self.failUnless(rowfound == 1, "Incorrect number of rows found: %d (1 expected)" % rowfound)

        self.bug.id = 102
        self.bug.cache_id = 204
        self.bug.name = "The Middle Bug"
        self.bug.ref = "bugref-baz"
        bug_id = self.bug.Save()

        cur.execute("select id, cache_id, name, ref from travelbugs where id=?", (bug_id, ))
        rowfound = 0
        for row in cur:
            rowfound += 1
            self.failUnless(row[0] == bug_id)
            self.failUnless(row[1] == 204)
            self.failUnless(row[2] == "The Middle Bug")
            self.failUnless(row[3] == "bugref-baz")
        self.failUnless(rowfound == 1, "Incorrect number of rows found: %d (1 expected)" % rowfound)

        cur.execute("select count(*) from travelbugs")
        count = cur.fetchone()[0]
        self.failUnless(count == 2, "Incorrect number of rows found: %d (2 expected)" % rowfound)
