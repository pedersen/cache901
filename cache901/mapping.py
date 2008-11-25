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
        
        cache901.notify('Loading caches')
        self.caches = []
        cur.execute('select cache_id, url_name, name, lat, lon, type from caches where cache_id in %s' % self.parms)
        for row in cur:
            r = []
            r.extend(row)
            r[3] = float(r[3])
            r[4] = float(r[4])
            self.caches.append(r)
            if len(self.caches) % 250 == 0:
                cache901.notify('Loaded cache %s' % str(cache901.util.forceAscii(self.caches[-1][1])))
        
        self.mapSplit.SetValidator(cache901.validators.splitValidator("mapSplit"))
        
        self.mapPanel.Bind(wx.EVT_PAINT,       self.OnPaint)
        self.mapPanel.Bind(wx.EVT_LEFT_DCLICK, self.OnMapDoubleClick)
        
    def updMap(self, cltdc):
        sz = self.mapPanel.GetSize()
        bmp = wx.EmptyBitmap(sz[0], sz[1], -1)
        dc = wx.MemoryDC(bmp)
        dc.SetBackground(wx.Brush(wx.SystemSettings_GetColour(wx.SYS_COLOUR_BACKGROUND)))
        dc.Clear()
        
        wprop = float(sz[0]) / float(self.maxlat - self.minlat)
        hprop = float(sz[0]) / float(self.maxlon - self.minlon)
        geo = wx.GetApp().GetTopWindow().geoicons
        for i, cache in enumerate(self.caches):
            x = int(wprop * (cache[3] - self.minlat))
            y = int(hprop * (cache[4] - self.minlon))
            dc.DrawBitmap(geo[cache[5]], x, y)
            if i % 300 == 0:
                cltdc.Blit(0, 0, sz[0], sz[1], dc, 0, 0)
        cltdc.Blit(0, 0, sz[0], sz[1], dc, 0, 0)
        dc.SelectObject(wx.NullBitmap)
    
    def OnPaint(self, evt):
        paintdc = wx.PaintDC(self.mapPanel)
        self.updMap(paintdc)
        self.mapArea.SetVirtualSize(self.mapPanel.GetSize())
        self.mapArea.SetScrollRate(20, 20)
        evt.Skip()
    
    def OnMapDoubleClick(self, evt):
        wx.MessageBox("Map doubleclicked!", "Debug")
        
    def forWingIde(self):
        isinstance(self.mapArea,    wx.ScrolledWindow)
        isinstance(self.mapPanel,   wx.Panel)
        isinstance(self.mapSplit,   wx.SplitterWindow)
        isinstance(self.cacheList,  wx.ListCtrl)
        isinstance(self.originList, wx.ListCtrl)
        