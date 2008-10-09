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
The main test program will be here. For now, this placeholder is put into
place to help keep track of where things go.
"""

import unittest
import sys
import os
import os.path
import psyco

from optparse import OptionParser

import test
import wx

import cache901
class TestApp(wx.App):
    def findTestModules(self):
        suite = unittest.TestSuite()
        for i in os.listdir(test.__path__[0]):
            if i.endswith('Test.py'):
                modname = 'test.' + os.path.splitext(os.path.split(i)[1])[0]
                exec 'import ' + modname
                suite.addTests(unittest.TestLoader().loadTestsFromModule(sys.modules[modname]))
        return suite

    def findSpeedModules(self):
        suite = unittest.TestSuite()
        for i in os.listdir(test.__path__[0]):
            if i.endswith('Speed.py'):
                modname = 'test.' + os.path.splitext(os.path.split(i)[1])[0]
                exec 'import ' + modname
                suite.addTests(unittest.TestLoader().loadTestsFromModule(sys.modules[modname]))
        return suite

    def OnInit(self):
        parser = OptionParser()
        parser.add_option("-d", "--debug", action="store_true", dest="debug", default=False, help="Backup existing database")
        parser.add_option("-r", "--restore", action="store_true", dest="restore", default=False, help="Restore existing database")
        parser.add_option("-c", "--correct", action="store_false", dest="correctness", default=True, help="Disable running correctness tests")
        parser.add_option("-s", "--speed", action="store_false", dest="speed", default=True, help="Disable running speed tests")
        (options, args) = parser.parse_args()
        dbbackname = cache901.dbfname + ".safe"
        if options.debug:
            if not os.path.exists(dbbackname):
                if os.path.exists(cache901.dbfname):
                    print "Saving database to %s" % dbbackname
                    os.rename(cache901.dbfname, dbbackname)
            else:
                print "%s exists, aborting." % dbbackname
                sys.exit(1)
        if options.restore:
            if not os.path.exists(dbbackname):
                print "No file to restore (%s), exiting." % dbbackname
                sys.exit(2)
            if os.path.exists(cache901.dbfname):
                print "Removing debugging database copy (%s)" % cache901.dbfname
                os.unlink(cache901.dbfname)
                print "Restoring backup database"
                os.rename(dbbackname, cache901.dbfname)
        cache901.db(not options.debug)
        if options.correctness:
            print "-------------------------------"
            print "  Running Correctness Tests    "
            print "-------------------------------"
            suite = self.findTestModules()
            unittest.TextTestRunner().run(suite)
        if options.speed:
            print "-------------------------------"
            print "     Running Speed Tests       "
            print "-------------------------------"
            suite = self.findSpeedModules()
            unittest.TextTestRunner().run(suite)
        cache901.db().commit()
        return True

def main():
    psyco.full()
    app=TestApp(redirect=False)
    app.MainLoop()

if __name__ == '__main__':
    main()
