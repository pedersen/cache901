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

class NoteTest(unittest.TestCase):
    def setUp(self):
        cur = cache901.db().cursor()
        cur.execute("delete from locations")
        cur.execute("delete from caches")
        cur.execute("delete from travelbugs")
        cur.execute("delete from logs")
        cur.execute("delete from hints")
        cur.execute("delete from notes")
        cache901.db().commit()

        self.note = "Best Note Ever!"
        self.noteid = 101

    def testInitInvalidID(self):
        try:
            c = dbo.Note(101)
            self.fail("Note made with invalid ID")
        except cache901.InvalidID, e:
            pass

    def testInitValidID(self):
        cur = cache901.db().cursor()
        cur.execute("insert into notes(cache_id, note) values(?,?)", (self.noteid, self.note))
        
        h = dbo.Note(101)
        self.failUnless(h.id == 101)
        self.failUnless(h.note == "Best Note Ever!")

    def testMakeNewId(self):
        h = dbo.Note(-999)
        self.failUnless(h.id == -1)
        self.failUnless(h.note == "")

    def testSave(self):
        cur = cache901.db().cursor()
        cur.execute("insert into notes(cache_id, note) values(?,?)", (self.noteid, self.note))

        h = dbo.Note(101)
        h.note = "The Worst Note"
        h.Save()
        del h
        h = dbo.Note(101)
        self.failUnless(h.id == 101)
        self.failUnless(h.note == "The Worst Note")

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
            self.fail("Hint made with invalid ID")
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

class PhotoListTest(unittest.TestCase):
    def setUp(self):
        cur = cache901.db().cursor()
        cur.execute("delete from locations")
        cur.execute("delete from caches")
        cur.execute("delete from travelbugs")
        cur.execute("delete from logs")
        cur.execute("delete from hints")
        cur.execute("delete from photos")
        cache901.db().commit()
        
        self.plist = ['a', 'b', 'c']
        self.cache_id = 101
        
    def testInitInvalidID(self):
        try:
            pl = dbo.PhotoList(101)
            self.fail("PhotoList made with Invalid ID!")
        except cache901.InvalidID, e:
            pass
    
    def testInitValidID(self):
        cur = cache901.db().cursor()
        for i in self.plist:
            cur.execute('insert into photos(cache_id, photofile) values(?, ?)', (self.cache_id, i))
        
        pl = dbo.PhotoList(self.cache_id)
        self.failUnless(pl.id == self.cache_id)
        self.failUnless(pl.names == sorted(self.plist))
    
    def testMakeNewId(self):
        pl = dbo.PhotoList(-1)
        self.failUnless(pl.id == -1)
        self.failUnless(pl.names == [])
    
    def testSave(self):
        cur = cache901.db().cursor()
        for i in self.plist:
            cur.execute('insert into photos(cache_id, photofile) values(?, ?)', (self.cache_id, i))
        
        pl = dbo.PhotoList(self.cache_id)
        pl.names.append('d')
        pl.names.append('efg')
        pl.Save()
        del pl
        
        pl = dbo.PhotoList(self.cache_id)
        self.failUnless(pl.id == self.cache_id)
        self.failUnless(pl.names == ['a', 'b', 'c', 'd', 'efg'])
        
class CacheDayTest(unittest.TestCase):
    def setUp(self):
        cur = cache901.db().cursor()
        cur.execute("delete from cacheday")
        cur.execute("delete from cacheday_names")
        cur.execute("delete from caches")
        cur.execute("delete from locations")
        cache901.db().commit()
    
    def testEmptyDay(self):
        day = cache901.dbobjects.CacheDay('emptyday')
        self.failUnless(day.dayname == 'emptyday')
        self.failUnless(len(day.caches) == 0)
    
    def testFullDay(self):
        cur = cache901.db().cursor()
        cur.execute('insert into caches(cache_id) values(1)')
        cur.execute('insert into caches(cache_id) values(2)')
        cur.execute('insert into caches(cache_id) values(4)')
        cur.execute('insert into locations(wpt_id) values(3)')
        for idx_tuple in (('fullday', 1, 1, 1), ('fullday', 2, 1, 2), ('fullday', 3, 2, 3), ('fullday', 4, 1, 4)):
            cur.execute('insert into cacheday(dayname, cache_id, cache_type, cache_order) values (?,?,?,?)', idx_tuple)
        cache901.db().commit()
        day = cache901.dbobjects.CacheDay('fullday')
        self.failUnless(day.dayname == 'fullday')
        self.failUnless(len(day.caches) == 4)
        self.failUnless(isinstance(day.caches[0], cache901.dbobjects.Cache))
        self.failUnless(day.caches[0].cache_id == 1)
        self.failUnless(isinstance(day.caches[1], cache901.dbobjects.Cache))
        self.failUnless(day.caches[1].cache_id == 2)
        self.failUnless(isinstance(day.caches[2], cache901.dbobjects.Waypoint))
        self.failUnless(day.caches[2].wpt_id == 3)
        self.failUnless(isinstance(day.caches[3], cache901.dbobjects.Cache))
        self.failUnless(day.caches[3].cache_id == 4)
        
    def testSave(self):
        cur = cache901.db().cursor()
        cur.execute('insert into caches(cache_id) values(1)')
        cur.execute('insert into caches(cache_id) values(2)')
        cur.execute('insert into caches(cache_id) values(4)')
        cur.execute('insert into locations(wpt_id) values(3)')
        c1 = cache901.dbobjects.Cache(1)
        c2 = cache901.dbobjects.Cache(2)
        c3 = cache901.dbobjects.Waypoint(3)
        c4 = cache901.dbobjects.Cache(4)
        day = cache901.dbobjects.CacheDay('saveday')
        day.caches.append(c1)
        day.caches.append(c2)
        day.caches.append(c3)
        day.caches.append(c4)
        day.Save()
        
        del day
        day = cache901.dbobjects.CacheDay('saveday')
        self.failUnless(day.dayname == 'saveday')
        self.failUnless(len(day.caches) == 4)
        self.failUnless(isinstance(day.caches[0], cache901.dbobjects.Cache))
        self.failUnless(day.caches[0].cache_id == 1)
        self.failUnless(isinstance(day.caches[1], cache901.dbobjects.Cache))
        self.failUnless(day.caches[1].cache_id == 2)
        self.failUnless(isinstance(day.caches[2], cache901.dbobjects.Waypoint))
        self.failUnless(day.caches[2].wpt_id == 3)
        self.failUnless(isinstance(day.caches[3], cache901.dbobjects.Cache))
        self.failUnless(day.caches[3].cache_id == 4)
    
    def testSaveEmpty(self):
        day = cache901.dbobjects.CacheDay('emptyday')
        day.Save()
        cur = cache901.db().cursor()
        cur.execute('select dayname from cacheday_names')
        row = cur.fetchone()
        self.failUnless(row[0] == 'emptyday')
    
    def testDelete(self):
        cur = cache901.db().cursor()
        cur.execute('insert into caches(cache_id) values(1)')
        cur.execute('insert into caches(cache_id) values(2)')
        cur.execute('insert into caches(cache_id) values(4)')
        cur.execute('insert into locations(wpt_id) values(3)')
        c1 = cache901.dbobjects.Cache(1)
        c2 = cache901.dbobjects.Cache(2)
        c3 = cache901.dbobjects.Waypoint(3)
        c4 = cache901.dbobjects.Cache(4)
        day = cache901.dbobjects.CacheDay('saveday')
        day.caches.append(c1)
        day.caches.append(c2)
        day.caches.append(c3)
        day.caches.append(c4)
        day.Save()
        
        day.Delete()
        cur.execute('select dayname from cacheday_names where dayname="saveday"')
        daydelete = True
        for row in cur:
            daydelete = False
        self.failUnless(daydelete == True, "Entry still exists in cacheday_names")
        
        cur.execute('select dayname from cacheday where dayname="saveday"')
        daydelete = True
        for row in cur:
            daydelete = False
        self.failUnless(daydelete == True, "Entry still exists in cacheday")
        
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
    def setUp(self):
        cur = cache901.db().cursor()
        cur.execute("delete from accounts")
        cache901.db().commit()

    def testInitInvalidID(self):
        try:
            acct = cache901.dbobjects.Account(101)
            self.fail('Account with invalid ID created')
        except cache901.InvalidID, e:
            pass


    def testMakeNewId(self):
        acct = cache901.dbobjects.Account(-999999)
        self.failUnless(acct.acctid    == -1)
        self.failUnless(acct.sitename  == '')
        self.failUnless(acct.username  == '')
        self.failUnless(acct.password  == '')
        self.failUnless(acct.isteam    == False)
        self.failUnless(acct.ispremium == False)

    def testSave(self):
        acct = cache901.dbobjects.Account(-999999)
        acctid = acct.acctid
        acct.sitename  = 'http://www.geocaching.com/'
        acct.username  = 'username'
        acct.password  = 'password'
        acct.isteam    = True
        acct.ispremium = True
        acct.Save()
        
        del acct
        acct = cache901.dbobjects.Account(acctid)
        self.failUnless(acct.sitename  == 'http://www.geocaching.com/')
        self.failUnless(acct.username  == 'username')
        self.failUnless(acct.password  == 'password')
        self.failUnless(acct.isteam    == True)
        self.failUnless(acct.ispremium == True)
    
    def testDelete(self):
        acct = cache901.dbobjects.Account(-999999)
        acctid = acct.acctid
        acct.sitename  = 'http://www.geocaching.com/'
        acct.username  = 'username'
        acct.password  = 'password'
        acct.isteam    = True
        acct.ispremium = True
        acct.Save()
        
        del acct
        acct = cache901.dbobjects.Account(acctid)
        acct.Delete()
        
        del acct
        acct = cache901.dbobjects.Account(acctid)
        self.failUnless(acct.acctid    == -1)
        self.failUnless(acct.sitename  == '')
        self.failUnless(acct.username  == '')
        self.failUnless(acct.password  == '')
        self.failUnless(acct.isteam    == False)
        self.failUnless(acct.ispremium == False)

class EmailAccountTest(unittest.TestCase):
    def setUp(self):
        cur = cache901.db().cursor()
        cur.execute("delete from emailsources")
        cache901.db().commit()

    def testInitInvalidID(self):
        try:
            acct = cache901.dbobjects.Email(101)
            self.fail('Email with invalid ID created')
        except cache901.InvalidID, e:
            pass


    def testMakeNewId(self):
        acct = cache901.dbobjects.Email(-999999)
        self.failUnless(acct.emailid   == -1)
        self.failUnless(acct.svrtype   == 'pop')
        self.failUnless(acct.svrname   == '')
        self.failUnless(acct.username  == '')
        self.failUnless(acct.password  == '')
        self.failUnless(acct.usessl    == False)
        self.failUnless(acct.deffolder == 'INBOX')

    def testSave(self):
        acct = cache901.dbobjects.Email(-999999)
        acctid = acct.emailid
        acct.svrtype   = 'imap'
        acct.svrname   = 'localhost'
        acct.username  = 'username'
        acct.password  = 'password'
        acct.usessl    = True
        acct.deffolder = 'INBOX'
        acct.Save()
        
        del acct
        acct = cache901.dbobjects.Email(acctid)
        self.failUnless(acct.svrtype   == 'imap')
        self.failUnless(acct.svrname   == 'localhost')
        self.failUnless(acct.username  == 'username')
        self.failUnless(acct.password  == 'password')
        self.failUnless(acct.usessl    == True)
        self.failUnless(acct.deffolder == 'INBOX')
    
    def testDelete(self):
        acct = cache901.dbobjects.Email(-999999)
        acctid = acct.emailid
        acct.svrtype   = 'http://www.geocaching.com/'
        acct.svrname   = 'http://www.geocaching.com/'
        acct.username  = 'username'
        acct.password  = 'password'
        acct.usessl    = True
        acct.deffolder = 'INBOX'
        acct.Save()
        
        del acct
        acct = cache901.dbobjects.Email(acctid)
        acct.Delete()
        
        del acct
        acct = cache901.dbobjects.Email(acctid)
        self.failUnless(acct.emailid   == -1)
        self.failUnless(acct.svrtype   == 'pop')
        self.failUnless(acct.svrname   == '')
        self.failUnless(acct.username  == '')
        self.failUnless(acct.password  == '')
        self.failUnless(acct.usessl    == False)
        self.failUnless(acct.deffolder == 'INBOX')
    
    def testPopImapProperty(self):
        acct=cache901.dbobjects.Email(-999999)
        self.failUnless(acct.pop == True)
        
        acct.pop = False
        self.failUnless(acct.pop == False)
        self.failUnless(acct.imap == True)
        
        acct.imap = False
        self.failUnless(acct.pop == True)
        self.failUnless(acct.imap == False)
        
        acct.imap = True
        self.failUnless(acct.pop == False)
        self.failUnless(acct.imap == True)

        acct.pop = True
        self.failUnless(acct.pop == True)
        self.failUnless(acct.imap == False)
        
