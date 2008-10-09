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
import cache901.dbobjects as dbo
import cache901.sqlobjects as sqo

class CacheTest(unittest.TestCase):
    def setUp(self):
        cur = cache901.db().cursor()
        cur.execute("delete from locations")
        cur.execute("delete from caches")
        cur.execute("delete from travelbugs")
        cur.execute("delete from logs")
        cur.execute("delete from hints")
        cache901.db().commit()

        self.saver = sqo.xmlWaypointSaver()
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

    def testInitInvalidID(self):
        # Test init with invalid id. Should provide exception
        try:
            c=dbo.Cache(101)
            self.fail("Cache was made with invalid ID")
        except cache901.InvalidID, e:
            pass

    def testInitValidId(self):
        self.saver.Save()

        c = dbo.Cache(101)

        self.failUnless(c.cache_id == 101)
        self.failUnless(c.url == "http//www.cache901.org/")
        self.failUnless(c.url_name == "Test Cache #1")
        self.failUnless(c.url_desc == "The Tester's Choice!")
        self.failUnless(c.name == "Test Cache #1")
        self.failUnless(c.sym == "Ammo Can")
        self.failUnless(c.type == "Traditional")
        self.failUnless(c.available == True)
        self.failUnless(c.archived == True)
        self.failUnless(c.placed_by == "m.pedersen")
        self.failUnless(c.owner_id == 201)
        self.failUnless(c.owner_name == "mtngeeks")
        self.failUnless(c.container == "Ammunition Box")
        self.failUnless(c.difficulty == 3.5)
        self.failUnless(c.terrain == 4.5)
        self.failUnless(c.country == "USA")
        self.failUnless(c.state == "NJ")
        self.failUnless(c.short_desc == "<pre>Quick Desc</pre>")
        self.failUnless(c.long_desc == "<pre>Long Desc</pre>")
        self.failUnless(c.lat == 40.8130)
        self.failUnless(c.lon == -75.0047)
        self.failUnless(c.short_desc_html == True)
        self.failUnless(c.long_desc_html == True)

    def testMakeNewId(self):
        c=dbo.Cache(-999)
        self.failUnless(c.cache_id == -1)
        self.failUnless(c.url == "")
        self.failUnless(c.url_name == "")
        self.failUnless(c.url_desc == "")
        self.failUnless(c.name == "")
        self.failUnless(c.sym == "")
        self.failUnless(c.type == "")
        self.failUnless(c.available == True)
        self.failUnless(c.archived == False)
        self.failUnless(c.placed_by == "")
        self.failUnless(c.owner_id == 0)
        self.failUnless(c.owner_name == "")
        self.failUnless(c.container == "")
        self.failUnless(c.difficulty == 1.0)
        self.failUnless(c.terrain == 1.0)
        self.failUnless(c.country == "")
        self.failUnless(c.state == "")
        self.failUnless(c.short_desc == "")
        self.failUnless(c.long_desc == "")
        self.failUnless(c.lat == 0.0)
        self.failUnless(c.lon == 0.0)
        self.failUnless(c.short_desc_html == False)
        self.failUnless(c.long_desc_html == False)

    def testSave(self):
        self.saver.Save()
        c = dbo.Cache(101)
        c.owner_id=404
        c.archived=False
        c.Save()
        del c
        c=dbo.Cache(101)
        self.failUnless(c.owner_id == 404)
        self.failUnless(c.archived == False)

class WaypointTest(unittest.TestCase):
    def setUp(self):
        cur = cache901.db().cursor()
        cur.execute("delete from locations")
        cur.execute("delete from caches")
        cur.execute("delete from travelbugs")
        cur.execute("delete from logs")
        cur.execute("delete from hints")
        cache901.db().commit()

        self.saver = sqo.xmlWaypointSaver()
        self.saver.loc_type  = 1
        self.saver.refers_to = -1
        self.saver.name      = "Test Waypoint #1"
        self.saver.desc      = "The Tester's Choice!"
        self.saver.comment   = "The premier waypoint of tester's everywhere"
        self.saver.lat       = 42.8130
        self.saver.lon       = -77.0047

    def testInitInvalidID(self):
        try:
            c=dbo.Waypoint(101)
            self.fail("Waypoint created with invalid id")
        except cache901.InvalidID, e:
            pass

    def testInitValidID(self):
        cid = self.saver.Save()

        c = dbo.Waypoint(cid)
        self.failUnless(c.wpt_id    == cid)
        self.failUnless(c.loc_type  == 1)
        self.failUnless(c.refers_to == -1)
        self.failUnless(c.name      == "Test Waypoint #1")
        self.failUnless(c.desc      == "The Tester's Choice!")
        self.failUnless(c.comment   == "The premier waypoint of tester's everywhere")
        self.failUnless(c.lat       == 42.8130)
        self.failUnless(c.lon       == -77.0047)

    def testMakeNewId(self):
        c = dbo.Waypoint(-999)
        self.failUnless(c.wpt_id    == -1)
        self.failUnless(c.loc_type  == 0)
        self.failUnless(c.refers_to == -1)
        self.failUnless(c.name      == "")
        self.failUnless(c.desc      == "")
        self.failUnless(c.comment   == "")
        self.failUnless(c.lat       == 0.0)
        self.failUnless(c.lon       == 0.0)

    def testSave(self):
        cid = self.saver.Save()

        c = dbo.Waypoint(cid)
        c.loc_type = 1
        c.refers_to = 123
        c.name = "Test Point Alpha"
        c.Save()

        del c
        c=dbo.Waypoint(cid)
        self.failUnless(c.loc_type == 1)
        self.failUnless(c.refers_to == 123)
        self.failUnless(c.name == "Test Point Alpha")

class LogTest(unittest.TestCase):
    def setUp(self):
        cur = cache901.db().cursor()
        cur.execute("delete from locations")
        cur.execute("delete from caches")
        cur.execute("delete from travelbugs")
        cur.execute("delete from logs")
        cur.execute("delete from hints")
        cache901.db().commit()

        self.log = cache901.sqlobjects.xmlLogSaver()
        self.log.id = 1
        self.log.cache_id = 1
        self.log.date = 1
        self.log.type = "test"
        self.log.finder = "test"
        self.log.finder_id = 2
        self.log.log_entry = "test"
        self.log.log_entry_encoded = False
        self.log.my_log = False
        self.log.my_log_found = False

    def testInitInvalidID(self):
        try:
            l = dbo.Log(101)
            self.fail("Log created with invalid id")
        except cache901.InvalidID, e:
            pass

    def testInitValidID(self):
        self.log.Save()
        l = dbo.Log(1)
        self.failUnless(l.id == 1)
        self.failUnless(l.cache_id == 1)
        self.failUnless(l.date == 1)
        self.failUnless(l.type == "test")
        self.failUnless(l.finder == "test")
        self.failUnless(l.finder_id == 2)
        self.failUnless(l.log_entry == "test")
        self.failUnless(l.log_entry_encoded == False)
        self.failUnless(l.my_log == False)
        self.failUnless(l.my_log_found == False)

    def testMakeNewId(self):
        l = dbo.Log(-999)
        self.failUnless(l.id == -1)
        self.failUnless(l.cache_id == -1)
        self.failUnless(l.date == 0)
        self.failUnless(l.type == "")
        self.failUnless(l.finder == "")
        self.failUnless(l.finder_id == 0)
        self.failUnless(l.log_entry == "")
        self.failUnless(l.log_entry_encoded == False)
        self.failUnless(l.my_log == False)
        self.failUnless(l.my_log_found == False)

    def testSave(self):
        self.log.Save()
        l = dbo.Log(1)
        l.cache_id = 101
        l.log_entry = "testing"
        l.Save()
        del l
        l = dbo.Log(1)
        self.failUnless(l.cache_id == 101)
        self.failUnless(l.log_entry == "testing")

class TravelBugTest(unittest.TestCase):
    def setUp(self):
        cur = cache901.db().cursor()
        cur.execute("delete from locations")
        cur.execute("delete from caches")
        cur.execute("delete from travelbugs")
        cur.execute("delete from logs")
        cur.execute("delete from hints")
        cache901.db().commit()

        self.bug = sqo.xmlBugSaver()
        self.bug.id = 101
        self.bug.cache_id = 202
        self.bug.name = "The Best Bug"
        self.bug.ref = "bugref"

    def testInitInvalidID(self):
        try:
            c = dbo.TravelBug(101)
            self.fail("Travel Bug made with invalid ID")
        except cache901.InvalidID, e:
            pass

    def testInitValidID(self):
        self.bug.Save()
        
        b = dbo.TravelBug(101)
        self.failUnless(b.id == 101)
        self.failUnless(b.cache_id == 202)
        self.failUnless(b.name == "The Best Bug")
        self.failUnless(b.ref == "bugref")

    def testMakeNewId(self):
        b = dbo.TravelBug(-999)
        self.failUnless(b.id == -1)
        self.failUnless(b.cache_id == -1)
        self.failUnless(b.name == "")
        self.failUnless(b.ref == "")

    def testSave(self):
        self.bug.Save()
        b = dbo.TravelBug(101)
        b.cache_id = 303
        b.name = "The Worst Bug"
        b.ref = "refbug"
        b.Save()
        del b
        b = dbo.TravelBug(101)
        self.failUnless(b.id == 101)
        self.failUnless(b.cache_id == 303)
        self.failUnless(b.name == "The Worst Bug")
        self.failUnless(b.ref == "refbug")

class HintTest(unittest.TestCase):
    def setUp(self):
        cur = cache901.db().cursor()
        cur.execute("delete from locations")
        cur.execute("delete from caches")
        cur.execute("delete from travelbugs")
        cur.execute("delete from logs")
        cur.execute("delete from hints")
        cache901.db().commit()

        self.hint = "Best Hint Ever!"
        self.hintid = 101

    def testInitInvalidID(self):
        try:
            c = dbo.Hint(101)
            self.fail("int made with invalid ID")
        except cache901.InvalidID, e:
            pass

    def testInitValidID(self):
        cur = cache901.db().cursor()
        cur.execute("insert into hints(cache_id, hint) values(?,?)", (self.hintid, self.hint))
        
        h = dbo.Hint(101)
        self.failUnless(h.id == 101)
        self.failUnless(h.hint == "Best Hint Ever!")

    def testMakeNewId(self):
        h = dbo.Hint(-999)
        self.failUnless(h.id == -1)
        self.failUnless(h.hint == "")

    def testSave(self):
        cur = cache901.db().cursor()
        cur.execute("insert into hints(cache_id, hint) values(?,?)", (self.hintid, self.hint))

        h = dbo.Hint(101)
        h.hint = "The Worst Hint"
        h.Save()
        del h
        h = dbo.Hint(101)
        self.failUnless(h.id == 101)
        self.failUnless(h.hint == "The Worst Hint")

class AttributeTest(unittest.TestCase):
    """
    @todo: write this test case
    """
    def setUp(self):
        cur = cache901.db().cursor()
        cur.execute("delete from locations")
        cur.execute("delete from caches")
        cur.execute("delete from travelbugs")
        cur.execute("delete from logs")
        cur.execute("delete from hints")
        cache901.db().commit()

    def testInitInvalidID(self):
        pass

    def testInitValidID(self):
        pass

    def testMakeNewId(self):
        pass

    def testSave(self):
        pass

class CategoryTest(unittest.TestCase):
    """
    @todo: write this test case
    """
    def setUp(self):
        cur = cache901.db().cursor()
        cur.execute("delete from locations")
        cur.execute("delete from caches")
        cur.execute("delete from travelbugs")
        cur.execute("delete from logs")
        cur.execute("delete from hints")
        cache901.db().commit()

    def testInitInvalidID(self):
        pass

    def testInitValidID(self):
        pass

    def testMakeNewId(self):
        pass

    def testSave(self):
        pass

class AccountTest(unittest.TestCase):
    """
    @todo: write this test case
    """
    def setUp(self):
        cur = cache901.db().cursor()
        cur.execute("delete from locations")
        cur.execute("delete from caches")
        cur.execute("delete from travelbugs")
        cur.execute("delete from logs")
        cur.execute("delete from hints")
        cache901.db().commit()

    def testInitInvalidID(self):
        pass

    def testInitValidID(self):
        pass

    def testMakeNewId(self):
        pass

    def testSave(self):
        pass

