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
