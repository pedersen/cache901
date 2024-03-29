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
import cache901.util
import cache901.validators

from cache901 import sadbobjects

class MapUI(cache901.ui_xrc.xrcMapUI):
    def __init__(self, parent=None, caches=[]):
        cache901.ui_xrc.xrcMapUI.__init__(self, parent)
        self.parent = parent
        self.cacheids = caches
        self.found = None
        self.parms = '(%s)' % (','.join(map(lambda x: '%d' % x, self.cacheids)), )

        self.minlat = 92.0
        self.minlon = 182.0
        self.maxlat = -92.0
        self.maxlon = -182.0
        self.caches = []
        for c in cache901.db().query(sadbobjects.Caches).order_by(sadbobjects.Caches.url_name):
            if c.cache_id in self.cacheids:
                self.minlat = min(self.minlat, float(c.lat))
                self.maxlat = max(self.maxlat, float(c.lat))
                self.minlon = min(self.minlon, float(c.lon))
                self.maxlon = max(self.maxlon, float(c.lon))
                self.caches.append(c)
                
        self.searches = []
        for w in cache901.db().query(sadbobjects.Locations).filter(sadbobjects.Locations.loc_type == 2).order_by(sadbobjects.Locations.name):
            self.minlat = min(self.minlat, float(w.lat))
            self.maxlat = max(self.maxlat, float(w.lat))
            self.minlon = min(self.minlon, float(w.lon))
            self.maxlon = max(self.maxlon, float(w.lon))
            self.searches.append(w)
            
        if self.minlat == self.maxlat: self.minlat = self.minlat - 1
        if self.minlon == self.maxlon: self.minlon = self.minlon - 1

        self.minlat = float(self.minlat)
        self.minlon = float(self.minlon)
        self.maxlat = float(self.maxlat)
        self.maxlon = float(self.maxlon)
        
        cache901.notify('Loading caches')
        w,h = self.GetTextExtent("QQQQQQQQQQQQQQQQQQQQQQQQQ")
        self.cacheList.DeleteAllItems()
        self.cacheList.DeleteAllColumns()
        self.cacheList.InsertColumn(0, "Cache Name", width=w)
        #cur.execute('select cache_id, url_name, name, lat, lon, type, 0.0 as x, 0.0 as y, 0.0 as lx, 0.0 as ly from caches where cache_id in %s order by url_name' % self.parms)
        for cache in self.caches:
            cache.x = 0.0
            cache.y = 0.0
            cache.lx = 0.0
            cache.ly = 0.0
            iid = self.cacheList.Append((cache.url_name, ))
            self.cacheList.SetItemData(iid, cache.cache_id)
            if len(self.caches) % 250 == 0:
                cache901.notify('Loaded cache %s' % str(cache901.util.forceAscii(cache.url_name)))

        cache901.notify('Loading search origin locations')
        self.originList.DeleteAllItems()
        self.originList.DeleteAllColumns()
        self.originList.InsertColumn(0, "Search Origin Name", width=w)
        #cur.execute('select name, lat, lon, wpt_id, 0.0 as x, 0.0 as y, 0.0 as lx, 0.0 as ly from locations where loc_type=2 order by name')
        for w in self.searches:
            w.x = 0.0
            w.y = 0.0
            w.lx = 0.0
            w.ly = 0.0
            iid = self.originList.Append((w.name, ))
            self.originList.SetItemData(iid, w.wpt_id)
            if len(self.searches) % 10 == 0:
                cache901.notify('Loaded search origin %s' % str(cache901.util.forceAscii(w.name)))

        self.mapArea.SetScrollRate(20, 20)
        self.mapSplit.SetValidator(cache901.validators.splitValidator("mapsplit"))

        self.mapPanel.Bind(wx.EVT_PAINT,       self.OnPaint)
        self.mapPanel.Bind(wx.EVT_LEFT_DCLICK, self.OnMapDoubleClick)
        self.mapPanel.Bind(wx.EVT_MOTION,      self.OnMoveMouse)
        
        self.mapArea.Bind(wx.EVT_SCROLLWIN, self.OnScrollMapArea)

        self.zoomLevel.Bind(wx.EVT_SCROLL, self.OnChangeZoom)

        self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.OnSelectCache,  self.cacheList)
        self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.OnSelectSearch, self.originList)

        self.oldZoom = None

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
            wrange = 3.0
            hrange = 3.0
        else:
            wrange = wrange - ((((wrange - 3.0) / 9.0) * (zoom-1)) + 3.0)
            hrange = hrange - ((((hrange - 3.0) / 9.0) * (zoom-1)) + 3.0)
        self.mapPanel.SetSize(self.mapArea.GetClientSize())
        sz = self.mapArea.GetSize()
        sz.width  = int(sz.width /wrange*wdist+1)
        sz.height = int(sz.height/hrange*hdist+1)
        #self.mapPanel.SetSize(sz)
        self.mapArea.SetVirtualSize(sz)
        #sz = self.mapPanel.GetSizeTuple()
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
        sz = self.mapArea.GetClientSizeTuple()
        (lrx, lry) = self.mapArea.CalcUnscrolledPosition(0, 0)
        (ulx, uly) = self.mapArea.CalcUnscrolledPosition(sz)
        winminlon = (float(lrx) / wprop) + self.minlon
        winmaxlon = (float(ulx) / wprop) + self.minlon
        # For some reason, lat needs CalcScrolledPosition, but lon needs CalcUnscrolledPosition. Weird.
        (lrx, lry) = self.mapArea.CalcScrolledPosition(0, 0)
        (ulx, uly) = self.mapArea.CalcScrolledPosition(sz)
        winminlat = self.maxlat - ((sz[1]-lry) / hprop)
        winmaxlat = self.maxlat - ((sz[1]-uly) / hprop)
        geo = wx.GetApp().GetTopWindow().geoicons
        for i, cache in enumerate(self.caches):
            x = int(wprop * (float(cache.lon) - winminlon))
            y = sz[1] - int(hprop * (float(cache.lat) - winminlat))
            tbmpsz = geo[cache.type].GetSize()
            if x + tbmpsz.width > sz[0]: x = x - tbmpsz.width
            if y + tbmpsz.height > sz[1]: y = y - tbmpsz.height
            self.caches[i].x = x
            self.caches[i].y = y
            self.caches[i].lx = x+tbmpsz.width
            self.caches[i].ly = y+tbmpsz.height
            dc.DrawBitmap(geo[cache.type], x, y)
        locbmp = wx.BitmapFromImage(wx.ImageFromBitmap(geo["searchloc"]).Scale(16,16))
        tbmpsz = locbmp.GetSize()
        for i, loc in enumerate(self.searches):
            x = int(wprop * (float(loc.lon) - winminlon))
            y = sz[1] - int(hprop * (float(loc.lat) - winminlat))
            if x + tbmpsz.width > sz[0]: x = x - tbmpsz.width
            if y + tbmpsz.height > sz[1]: y = y - tbmpsz.height
            self.searches[i].x = x
            self.searches[i].y = y
            self.searches[i].lx = x+tbmpsz.width
            self.searches[i].ly = y+tbmpsz.height
            dc.DrawBitmap(locbmp, x, y)

        hprop = float(sz[1]) / float(hrange) # pixels per mile
        wprop = float(sz[0]) / float(wrange) # pixels per mile
        #hscale = int(hrange / 16.0 * hprop) # Screen size divided by 4, and then by 4 again for each bar
        #wscale = int(wrange / 16.0 * wprop) # Then multiplied by proportion to give accurate size
        dc.SetFont(wx.SystemSettings_GetFont(wx.SYS_SYSTEM_FONT))
        dc.DrawText('%1.2fmi' % ((wrange / 4)), 20 + 4*wbar, 10)
        dc.DrawText('%1.2fkm' % ((wrange / 4)*1.61), 20 + 4*wbar, 24)
        dc.DrawText('%1.2fmi' % ((hrange / 4)), 10, 25+ 4*hbar)
        dc.DrawText('%1.2fkm' % ((hrange / 4)*1.61), 10, 39+ 4*hbar)
        dc.SelectObject(wx.NullBitmap)
        self.bmp = bmp
        self.oldZoom = self.zoomLevel.GetValue()

    def OnPaint(self, evt):
        if self.oldZoom is None or self.oldZoom != self.zoomLevel.GetValue():
            self.updMap()
        
        paintdc = wx.PaintDC(self.mapPanel)
        paintdc.DrawBitmap(self.bmp, 0, 0)
        self.mapPanel.SetPosition((0,0))

    def OnScrollMapArea(self, evt):
        self.updMap()
        self.mapArea.Refresh()
        evt.Skip()
        
    def OnChangeZoom(self, evt):
        self.updMap()
        self.mapArea.SetScrollRate(20, 20)
        self.Refresh()

    def OnSelectCache(self, evt):
        cid = evt.GetData()
        self.found = cid
        idx = 0
        while self.caches[idx].cache_id != cid: idx = idx+1
        sz = self.mapArea.GetSize()
        sz.width = sz.width/2
        sz.height = sz.height/2
        xpix = self.caches[idx].x-sz.width
        ypix = self.caches[idx].y-sz.height
        if xpix < 0: xpix = 0
        if ypix < 0: ypix = 0
        xscr, yscr = self.mapArea.GetScrollPixelsPerUnit()
        self.mapArea.Scroll(xpix/xscr, ypix/yscr)

    def OnSelectSearch(self, evt):
        cid = evt.GetData()
        idx = 0
        while self.searches[idx].wpt_id != cid: idx = idx+1
        sz = self.mapArea.GetSize()
        sz.width = sz.width/2
        sz.height = sz.height/2
        xpix = self.searches[idx].x-sz.width
        ypix = self.searches[idx].y-sz.height
        if xpix < 0: xpix = 0
        if ypix < 0: ypix = 0
        xscr, yscr = self.mapArea.GetScrollPixelsPerUnit()
        self.mapArea.Scroll(xpix/xscr, ypix/yscr)

    def OnMapDoubleClick(self, evt):
        isinstance(evt, wx.MouseEvent)
        pos = evt.GetPosition()
        x=pos.x
        y=pos.y
        self.found = None
        for cache in self.caches:
            if x >= cache.x and x <= cache.lx and y >= cache.y and y <= cache.ly:
                self.mapPanel.SetToolTipString(cache.url_name)
                self.found = cache.cache_id
        if self.found is not None:
            self.EndModal(wx.ID_OK)

    def OnMoveMouse(self, evt):
        isinstance(evt, wx.MouseEvent)
        pos = evt.GetPosition()
        x=pos.x
        y=pos.y
        found = False
        for cache in self.caches:
            if x >= cache.x and x <= cache.lx and y >= cache.y and y <= cache.ly:
                self.mapPanel.SetToolTipString(cache.url_name)
                found = True
        for search in self.searches:
            if x >= search.x and x <= search.lx and y >= search.y and y <= search.ly:
                self.mapPanel.SetToolTipString(search.name)
                found = True
        if not found: self.mapPanel.SetToolTipString('')

    def forWingIde(self):
        isinstance(self.mapArea,    wx.ScrolledWindow)
        isinstance(self.mapPanel,   wx.Panel)
        isinstance(self.mapSplit,   wx.SplitterWindow)
        isinstance(self.cacheList,  wx.ListCtrl)
        isinstance(self.originList, wx.ListCtrl)
        isinstance(self.zoomLevel,  wx.Slider)

