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
import os
import os.path

import cache901

class initTest(unittest.TestCase):
    def testAppName(self):
        self.failUnless(cache901.appname == 'Cache901')

    def testDbPaths(self):
        self.failUnless(cache901.dbfile == 'Cache901.sqlite')
        self.failUnless(cache901.dbpath == os.sep.join([os.environ['HOME'], cache901.appname]))
        self.failUnless(cache901.dbfname == os.sep.join([os.environ['HOME'], cache901.appname, cache901.dbfile]))

    def testSingleton(self):
        db = cache901.database
        cache901.database = None
        self.failUnless(cache901.database == None)
        self.failUnless(cache901.db() != None)
        self.failUnless(os.path.exists(cache901.dbfname))
        cache901.database = db

