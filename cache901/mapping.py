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

# @todo: bug: with my 1490 caches, at zoom level 10, turbo exit
# @todo: recenter map on clicking cache or search origin
# @todo: add tooltip for currently selected cache
# @todo: Add double-clicking to load a cache

import wx

import cache901
import cache901.dbobjects
import cache901.ui
import cache901.ui_xrc
import cache901.util
import cache901.validators

class MapUI(cache901.ui_xrc.xrcMapUI):
    def __init__(self, parent=None, caches=[]):
        cache901.ui_xrc.xrcMapUI.__init__(self, parent)
        self.parent = parent
        self.cacheids = caches
        self.parms = '(%s)' % (','.join(map(lambda x: '%d' % x, self.cacheids)), )
        
        cur = cache901.db().cursor()
        qry = 'select min(lat), min(lon), max(lat), max(lon) from caches where cache_id in %s' % self.parms
        cur.execute(qry)
        row = cur.fetchone()
        self.minlat = float(row[0])
        self.minlon = float(row[1])
        self.maxlat = float(row[2])
        self.maxlon = float(row[3])
        
        qry = 'select min(lat), min(lon), max(lat), max(lon) from locations where loc_type=2'
        cur.execute(qry)
        for row in cur:
            self.minlat = min(self.minlat, row[0])
            self.minlon = min(self.minlon, row[1])
            self.maxlat = max(self.maxlat, row[2])
            self.maxlon = max(self.maxlon, row[3])
        
        cache901.notify('Loading caches')
        w,h = self.GetTextExtent("QQQQQQQQQQQQQQQQQQQQQQQQQ")
        self.cacheList.DeleteAllItems()
        self.cacheList.DeleteAllColumns()
        self.cacheList.InsertColumn(0, "Cache Name", width=w)
        self.caches = []
        cur.execute('select cache_id, url_name, name, lat, lon, type from caches where cache_id in %s' % self.parms)
        for row in cur:
            r = []
            r.extend(row)
            r[3] = float(r[3])
            r[4] = float(r[4])
            self.caches.append(r)
            iid = self.cacheList.Append((r[1], ))
            self.cacheList.SetItemData(iid, r[0])
            if len(self.caches) % 250 == 0:
                cache901.notify('Loaded cache %s' % str(cache901.util.forceAscii(self.caches[-1][1])))
                
        cache901.notify('Loading search origin locations')
        self.originList.DeleteAllItems()
        self.originList.DeleteAllColumns()
        self.originList.InsertColumn(0, "Search Origin Name", width=w)
        self.searches = []
        cur.execute('select name, lat, lon, wpt_id from locations where loc_type=2')
        for row in cur:
            r=[]
            r.extend(row)
            r[1] = float(r[1])
            r[2] = float(r[2])
            self.searches.append(r)
            iid = self.originList.Append((r[0], ))
            self.originList.SetItemData(iid, r[3])
            if len(self.searches) % 10 == 0:
                cache901.notify('Loaded search origin %s' % str(cache901.util.forceAscii(self.searches[-1][0])))
        
        self.mapSplit.SetValidator(cache901.validators.splitValidator("mapSplit"))
        
        self.mapPanel.Bind(wx.EVT_PAINT,       self.OnPaint)
        self.mapPanel.Bind(wx.EVT_LEFT_DCLICK, self.OnMapDoubleClick)
        
        self.zoomLevel.Bind(wx.EVT_SCROLL, self.OnChangeZoom)
        self.oldZoom = None
        self.mapArea.SetScrollRate(20,20)
        
    def updMap(self):
        # zoom 1 is all caches on-screen, minimum of 5 miles across horizontal
        # zoom 10 is 1mi across horizontal
        # all other zooms are proportional differences between 1 and 10, using the minimum of 5 miles
        zoom = self.zoomLevel.GetValue()
        wrange = cache901.util.distance_exact(0, self.minlon, 0, self.maxlon)
        wdist = wrange
        hrange = cache901.util.distance_exact(self.minlat, 0, self.maxlat, 0)
        hdist = hrange
        if zoom == 1:
            wrange = 5.0 if wrange < 5.0 else wrange
            hrange = 5.0 if hrange < 5.0 else hrange
        elif zoom == 10:
            wrange = 1.0
            hrange = 1.0
        else:
            wrange = wrange - ((((wrange - 1.0) / 9.0) * (zoom-1)) + 1.0)
            hrange = hrange - ((((hrange - 1.0) / 9.0) * (zoom-1)) + 1.0)
        sz = self.mapArea.GetSize()
        sz.width  = int(sz.width /wrange*wdist+1)
        sz.height = int(sz.height/hrange*hdist+1)
        self.mapPanel.SetSize(sz)
        self.mapPanel.SetPosition((0, 0))
        self.mapArea.SetVirtualSize(sz)
        sz = self.mapPanel.GetSizeTuple()
        bmp = wx.EmptyBitmap(sz[0], sz[1], -1)
        dc = wx.MemoryDC(bmp)
        dc.SetBackground(wx.Brush(wx.SystemSettings_GetColour(wx.SYS_COLOUR_BACKGROUND)))
        dc.Clear()
        
        asz = self.mapArea.GetSizeTuple()
        wbar = asz[0] / 16
        hbar = asz[1] / 16
        blk = wx.Brush(wx.Colour(0, 0, 0))
        wht = wx.Brush(wx.Colour(255, 255, 255))
        brushes = [blk, wht]
        for i in range(4):
            dc.SetBackground(brushes[0])
            dc.SetBrush(brushes[1])
            dc.DrawRectangle(10 + i*wbar, 10, wbar, 10)
            brushes.reverse()
            dc.SetBackground(brushes[0])
            dc.SetBrush(brushes[1])
            dc.DrawRectangle(0, 20+i*hbar, 10, hbar)
            
        hprop = float(sz[1]) / float(self.maxlat - self.minlat)
        wprop = float(sz[0]) / float(self.maxlon - self.minlon)
        geo = wx.GetApp().GetTopWindow().geoicons
        for i, cache in enumerate(self.caches):
            x = int(wprop * (cache[4] - self.minlon))
            y = int(hprop * (cache[3] - self.minlat))
            tbmpsz = geo[cache[5]].GetSize()
            if x + tbmpsz.width > sz[0]: x = x - tbmpsz.width
            if y + tbmpsz.height > sz[1]: y = y - tbmpsz.height
            dc.DrawBitmap(geo[cache[5]], x, y)
        locbmp = wx.BitmapFromImage(wx.ImageFromBitmap(geo["searchloc"]).Scale(16,16))
        tbmpsz = locbmp.GetSize()
        for i, loc in enumerate(self.searches):
            x = int(wprop * (loc[2] - self.minlon))
            y = int(hprop * (loc[1] - self.minlat))
            if x + tbmpsz.width > sz[0]: x = x - tbmpsz.width
            if y + tbmpsz.height > sz[1]: y = y - tbmpsz.height
            dc.DrawBitmap(locbmp, x, y)
        
        hprop = float(sz[1]) / float(hrange) # pixels per mile
        wprop = float(sz[0]) / float(wrange) # pixels per mile
        #hscale = int(hrange / 16.0 * hprop) # Screen size divided by 4, and then by 4 again for each bar
        #wscale = int(wrange / 16.0 * wprop) # Then multiplied by proportion to give accurate size
        dc.SetFont(wx.SystemSettings_GetFont(wx.SYS_SYSTEM_FONT))
        dc.DrawText('%1.2fmi' % (wrange / 4), 20 + 4*wbar, 10)
        dc.DrawText('%1.2fmi' % (hrange / 4), 10, 25+ 4*hbar)
        dc.SelectObject(wx.NullBitmap)
        self.bmp = bmp
        self.oldZoom = self.zoomLevel.GetValue()
    
    def OnPaint(self, evt):
        if self.oldZoom is None or self.oldZoom != self.zoomLevel.GetValue():
            self.updMap()
        paintdc = wx.PaintDC(self.mapPanel)
        paintdc.DrawBitmap(self.bmp, 0, 0)
    
    def OnChangeZoom(self, evt):
        self.updMap()
        self.Refresh()
        
    def OnMapDoubleClick(self, evt):
        wx.MessageBox("Map doubleclicked!", "Debug")
        
    def forWingIde(self):
        isinstance(self.mapArea,    wx.ScrolledWindow)
        isinstance(self.mapPanel,   wx.Panel)
        isinstance(self.mapSplit,   wx.SplitterWindow)
        isinstance(self.cacheList,  wx.ListCtrl)
        isinstance(self.originList, wx.ListCtrl)
        isinstance(self.zoomLevel,  wx.Slider)
        