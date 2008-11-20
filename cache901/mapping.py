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

import cache901.ui
import cache901.ui_xrc
import cache901.validators

class MapUI(cache901.ui_xrc.xrcMapUI):
    def __init__(self, parent=None, caches=[]):
        cache901.ui_xrc.xrcMapUI.__init__(self, parent)
        self.parent = parent
        self.cacheids = caches
        
        self.mapSplit.SetValidator(cache901.validators.splitValidator("mapSplit"))
        
        self.Bind(wx.EVT_PAINT, self.OnPaint)
        
        self.mapArea.Bind(wx.EVT_LEFT_DCLICK, self.OnMapDoubleClick)
        
    def updMap(self, cltdc):
        sz = self.mapArea.GetVirtualSizeTuple()
        bmp = wx.EmptyBitmap(sz[0], sz[1], -1)
        dc = wx.MemoryDC(bmp)
        dc.SetBackground(wx.Brush(wx.Colour(0, 0, 0)))
        dc.SetBrush(wx.Brush(wx.Colour(0, 0, 0)))
        dc.Clear()
        cltdc.Blit(0, 0, sz[0], sz[1], dc, 0, 0)
        dc.SelectObject(wx.NullBitmap)
    
    def OnPaint(self, evt):
        paintdc = wx.PaintDC(self.mapArea)
        paintdc.SetBackground(wx.Brush(wx.SystemSettings_GetColour(wx.SYS_COLOUR_BACKGROUND)))
        paintdc.Clear()
        self.updMap(paintdc)
        evt.Skip()
    
    def OnMapDoubleClick(self, evt):
        wx.MessageBox("Map doubleclicked!", "Debug")
        
    def forWingIde(self):
        isinstance(self.mapArea,    wx.ScrolledWindow)
        isinstance(self.mapSplit,   wx.SplitterWindow)
        isinstance(self.cacheList,  wx.ListCtrl)
        isinstance(self.originList, wx.ListCtrl)
        