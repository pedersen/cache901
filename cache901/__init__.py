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

import os
import os.path
import sys

if not hasattr(sys, "frozen") and 'wx' not in sys.modules and 'wxPython' not in sys.modules:
    import wxversion
    wxversion.ensureMinimal("2.8")
import wx

import cache901.config
import cache901.database

version = "0.6.1"
appname = 'Cache901'

def cfg():
    return cache901.config.Config()

def db(debugging=False):
    return cache901.database.Database(debugging)

updating = False
def notify(message):
    global updating
    try:
        wx.GetApp().GetTopWindow().GetStatusBar().SetStatusText(message, 0)
        if not updating:
            updating = True
            wx.SafeYield()
            updating = False
    except:
        print "cache901.notify: %s" % message

class InvalidID(Exception):
    pass
