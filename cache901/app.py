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
# Three files have very similar code pieces. They are:
#   * geocache901
#   * geocache901.py
#   * cache901/app.py
# The reason for this is different environments with different needs.
# geocache901 is the main shell script to run for UNIX-type settings
# geocache901.py is required for py2app (OSX Bundle Maker) to work
# cache901/app.py is the main debug file in Wingware IDE, so that
#    breakpoints work properly (psyco stops the breakpoints from
#    working in Wingware IDE)
# As such, all three of these need to be kept in sync. Fortunately,
# there is extremely little logic in here. It's mostly a startup
# shell, so this bit of code can be mostly ignored. This note is
# just to explain why these pieces are here, and why all of them must
# be updated if one of them is.

import sys
import traceback

if not hasattr(sys, "frozen"):
    import wxversion
    wxversion.ensureMinimal("2.8")
import wx

import cache901
import cache901.ui
import cache901.ui_xrc

def Cache901ExceptionHandler(exctype, val, tb):
    excout =  "".join(traceback.format_exception(exctype, val, tb))
    wx.MessageBox(excout, "An Error Has Occurred", style=wx.ICON_ERROR)
    
class Cache901App(wx.App):
    def OnInit(self):
        cache901.updating = True
        sys.excepthook = Cache901ExceptionHandler
        wx.InitAllImageHandlers()
        geoicons = cache901.ui.geoicons()
        splash = cache901.ui_xrc.xrcsplash(None)
        splash.SetIcon(geoicons["appicon"])
        w,h = splash.GetSizeTuple()
        x = wx.SystemSettings.GetMetric(wx.SYS_SCREEN_X)/2 - w/2
        y = wx.SystemSettings.GetMetric(wx.SYS_SCREEN_Y)/2 - h/2
        splash.SetPosition((x,y))
        splash.Show()
        wx.SafeYield()
        cache901.config = wx.Config(cache901.appname)
        wx.Config.Set(cache901.config)

        self.mainwin = cache901.ui.Cache901UI(None)
        w,h = self.mainwin.GetSizeTuple()
        x = wx.SystemSettings.GetMetric(wx.SYS_SCREEN_X)/2 - w/2
        y = wx.SystemSettings.GetMetric(wx.SYS_SCREEN_Y)/2 - h/2
        self.mainwin.SetPosition((x,y))
        self.mainwin.Show(True)
        self.SetTopWindow(self.mainwin)
        self.mainwin.SetFocus()
        splash.Destroy()
        geoicons.Destroy()
        wx.SafeYield()
        cache901.updating = False
        self.mainwin.updStatus()
        return(True)

def main():
    app = Cache901App(redirect=False, useBestVisual=True)
    app.MainLoop()

if __name__ == '__main__':
    main()
