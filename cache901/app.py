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

import wx

import cache901
import cache901.ui
import cache901.ui_xrc

class Cache901App(wx.App):
    def OnInit(self):
        cache901.updating = True
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
