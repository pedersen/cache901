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

import os
import os.path

import serial
import wx

import cache901
import cache901.dbobjects
import cache901.ui_xrc
import cache901.util
import cache901.validators

import gpsbabel

class OptionsUI(cache901.ui_xrc.xrcOptionsUI):
    def __init__(self, parent=None):
        cache901.ui_xrc.xrcOptionsUI.__init__(self, parent)
        self.gpsbabelLoc.SetValidator(cache901.validators.cmdValidator())
        self.gpsPort.SetValidator(cache901.validators.portValidator())
        self.gpsType.SetValidator(cache901.validators.gpsTypeValidator())
        self.coordDisplay.SetValidator(cache901.validators.degDisplayValidator())
        self.locSplit.SetValidator(cache901.validators.splitValidator("locSplit"))
        
        self.loadOrigins()
        
        self.Bind(wx.EVT_BUTTON, self.OnRemoveOrigin,   self.remLoc)
        self.Bind(wx.EVT_BUTTON, self.OnAddOrigin,      self.addLoc)
        self.Bind(wx.EVT_BUTTON, self.OnClearSelection, self.clearSel)
        self.Bind(wx.EVT_BUTTON, self.OnGetFromGPS,     self.getFromGPS)
        
        self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.OnLoadOrigin, self.locations)
        
    def loadOrigins(self):
        self.locations.DeleteAllItems()
        self.locations.DeleteAllColumns()
        w,h = self.GetTextExtent("QQQQQQQQQQQQQQQQQQ")
        self.locations.InsertColumn(0, 'Location Name', width=w)
        for row in cache901.util.getSearchLocs():
            sid = self.locations.Append((row[1],))
            self.locations.SetItemData(sid, row[0])
        
    def showGeneral(self):
        self.tabs.ChangeSelection(0)
        self.ShowModal()
        
    def showSearch(self):
        self.tabs.ChangeSelection(1)
        self.ShowModal()
        
    def OnRemoveOrigin(self, evt):
        sel = self.locations.GetFirstSelected()
        wptid = self.locations.GetItemData(sel)
        cur = cache901.db().cursor()
        cur.execute('delete from locations where loc_type=2 and wpt_id=?', (wptid, ))
        self.loadOrigins()
        cache901.db().commit()
    
    def OnAddOrigin(self, evt):
        lid = self.locations.GetFirstSelected()
        if lid != -1:
            lid = self.locations.GetItemData(lid)
        else:
            lid = -999999
        wpt = cache901.dbobjects.Waypoint(lid)
        wpt.name = self.locName.GetValue()
        wpt.loc_type = 2
        if len(wpt.name) != 0:
            failed = False
            try:
                wpt.lat = str(cache901.util.dmsToDec(self.latitude.GetValue()))
                self.latitude.SetValue(wpt.lat)
            except cache901.util.InvalidDegFormat, msg:
                wx.MessageBox(str(msg), "Invalid Latitude", parent=self)
                failed = True
            try:
                wpt.lon = str(cache901.util.dmsToDec(self.longitude.GetValue()))
                self.longitude.SetValue(wpt.lon)
            except cache901.util.InvalidDegFormat, msg:
                wx.MessageBox(str(msg), "Invalid Longitude", parent=self)
                failed = True
            if not failed:
                wpt.Save()
                cache901.db().commit()
                self.loadOrigins()
                wpt_id = self.locations.FindItemData(0, wpt.wpt_id)
                if wpt_id >= 0:
                    self.locations.Select(wpt_id)
                else:
                    self.locName.SetValue("")
                    self.latitude.SetValue("")
                    self.longitude.SetValue("")
        else:
            wx.MessageBox("Empty names cannot be saved", "Empty Name Error")
    
    def OnLoadOrigin(self, evt):
        wptid = evt.GetData()
        wpt = cache901.dbobjects.Waypoint(wptid)
        self.locName.SetValue(wpt.name)
        self.latitude.SetValue(cache901.util.latToDMS(wpt.lat))
        self.longitude.SetValue(cache901.util.lonToDMS(wpt.lon))
    
    def OnClearSelection(self, evt):
        lid = self.locations.GetFirstSelected()
        while lid != -1:
            self.locations.Select(lid, False)
            lid = self.locations.GetFirstSelected()
    
    def OnGetFromGPS(self, evt):
        # Get the path for GPSBabel, and make sure it's in use.
        fp = self.gpsbabelLoc.GetPath()
        gpsbabel.gps = gpsbabel.GPSBabel(fp)
        # Get the port the GPS is attached to
        selnum = self.gpsPort.GetSelection()
        if selnum == wx.NOT_FOUND:
            wx.MessageBox('Please select the GPS Port on the "General" page', 'Invalid GPS Port')
        items = self.gpsPort.GetItems()
        if selnum < 0 or selnum >= len(items):
            wx.MessageBox('Please select the GPS Port on the "General" page', 'Invalid GPS Port')
        else:
            port = items[selnum]
        if port == 'USB': port = 'usb:'
        # Get the type of GPS
        selnum = self.gpsType.GetSelection()
        if selnum == wx.NOT_FOUND:
            wx.MessageBox('Please select the GPS Type on the "General" page', 'Invalid GPS Type')
        items = self.gpsType.GetItems()
        if selnum < 0 or selnum >= len(items):
            wx.MessageBox('Please select the GPS Type on the "General" page', 'Invalid GPS Type')
        else:
            gpstype = items[selnum].lower()
        try:
            wpt = gpsbabel.gps.getCurrentGpsLocation(port, gpstype)
            self.latitude.SetValue(cache901.util.latToDMS(wpt.lat))
            self.longitude.SetValue(cache901.util.lonToDMS(wpt.lon))
        except Exception, e:
            wx.MessageBox(str(e), "An Error Occured")
    
    def forWingIde(self):
        """
        This method shouldn't ever be called, since it's a do nothing
        method. However, by having it in here, Wing IDE can provide
        autocompletion, and it won't interfere with anything else, so here
        it is.
        """
        # Overall Dialog
        isinstance(self.tabs, wx.Notebook)
        
        # General Tab
        isinstance(self.general,      wx.Panel)
        isinstance(self.coordDisplay, wx.Choice)
        isinstance(self.gpsType,      wx.Choice)
        isinstance(self.gpsPort,      wx.Choice)
        isinstance(self.gpsbabelLoc,  wx.FilePickerCtrl)
        isinstance(self.getFromGPS,   wx.Button)
        
        # Search Tab
        isinstance(self.search,    wx.Panel)
        isinstance(self.locations, wx.ListCtrl)
        isinstance(self.locName,   wx.TextCtrl)
        isinstance(self.latitude,  wx.TextCtrl)
        isinstance(self.longitude, wx.TextCtrl)
        isinstance(self.addLoc,    wx.Button)
        isinstance(self.remLoc,    wx.Button)
        isinstance(self.clearSel,  wx.Button)
        isinstance(self.locSplit,  wx.SplitterWindow)
        
        # Cache Day Tab
        isinstance(self.cacheday,     wx.Panel)
        isinstance(self.addCacheDay,  wx.Button)
        isinstance(self.remCacheDay,  wx.Button)
        isinstance(self.upCache,      wx.BitmapButton)
        isinstance(self.downCache,    wx.BitmapButton)
        isinstance(self.addCache,     wx.BitmapButton)
        isinstance(self.remCache,     wx.BitmapButton)
        isinstance(self.cacheDays,    wx.ListCtrl)
        isinstance(self.cachesForDay, wx.ListCtrl)
        isinstance(self.availCaches,  wx.ListCtrl)