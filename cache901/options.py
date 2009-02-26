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
    def __init__(self, listOfCaches, parent=None):
        cache901.ui_xrc.xrcOptionsUI.__init__(self, parent)
        self.colsRearranged = False
        self.gpsbabelLoc.SetValidator(cache901.validators.cmdValidator())
        self.gpsPort.SetValidator(cache901.validators.portValidator())
        self.gpsType.SetValidator(cache901.validators.gpsTypeValidator())
        self.coordDisplay.SetValidator(cache901.validators.degDisplayValidator())
        self.locSplit.SetValidator(cache901.validators.splitValidator("optsplitloc"))
        self.acctTabSplit.SetValidator(cache901.validators.splitValidator("optsplitacct"))
        self.maxLogs.SetValidator(cache901.validators.spinCtlValidator("dbMaxLogs"))
        
        w,h = self.GetTextExtent("QQQQQQQQQQQQQQQQQQ")
        self.cacheDays.InsertColumn(0, 'Cache Day', width=w)
        self.cachesForDay.InsertColumn(0, 'Caches For Day', width=w)
        self.availCaches.InsertColumn(0, 'Available Caches', width=w)
        self.accountNames.InsertColumn(0, 'GeoCaching Accounts', width=w)

        isinstance(listOfCaches, wx.ListCtrl)
        idx = 0
        while idx < listOfCaches.GetItemCount():
            cache_item = listOfCaches.GetItem(idx, 2)
            ctext = cache_item.GetText()
            iid = self.availCaches.Append((ctext, ))
            self.availCaches.SetItemData(iid, listOfCaches.GetItemData(idx))
            idx = idx + 1
        
        self.loadOrigins()
        self.listCacheDays()
        self.loadAccounts()
        self.loadGUIPreferences()
        
        self.Bind(wx.EVT_BUTTON, self.OnRemoveOrigin,   self.remLoc)
        self.Bind(wx.EVT_BUTTON, self.OnAddOrigin,      self.addLoc)
        self.Bind(wx.EVT_BUTTON, self.OnClearSelection, self.clearSel)
        self.Bind(wx.EVT_BUTTON, self.OnGetFromGPS,     self.getFromGPS)
        self.Bind(wx.EVT_BUTTON, self.OnAddCacheDay,    self.addCacheDay)
        self.Bind(wx.EVT_BUTTON, self.OnRemCacheDay,    self.remCacheDay)
        self.Bind(wx.EVT_BUTTON, self.OnCacheUp,        self.upCache)
        self.Bind(wx.EVT_BUTTON, self.OnCacheDown,      self.downCache)
        self.Bind(wx.EVT_BUTTON, self.OnAddCache,       self.addCache)
        self.Bind(wx.EVT_BUTTON, self.OnRemCache,       self.remCache)
        self.Bind(wx.EVT_BUTTON, self.OnRenameCacheDay, self.btnRenameCacheDay)
        self.Bind(wx.EVT_BUTTON, self.OnAddAccount,     self.btnAddAcount)
        self.Bind(wx.EVT_BUTTON, self.OnRemAccount,     self.btnRemAccount)
        self.Bind(wx.EVT_BUTTON, self.OnSaveAccount,    self.btnSaveAccount)
        self.Bind(wx.EVT_BUTTON, self.OnColMoveUp,      self.colMoveUpButton)
        self.Bind(wx.EVT_BUTTON, self.OnColMoveDown,    self.colMoveDownButton)
        
        self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.OnLoadOrigin,   self.locations)
        self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.OnLoadCacheDay, self.cacheDays)
        self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.OnLoadAccount,  self.accountNames)
        self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.OnColumnSelect, self.colOrderList)

        self.Bind(wx.EVT_LIST_ITEM_DESELECTED, self.OnColumnDeselect, self.colOrderList)
        
        self.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.OnAddCache, self.availCaches)
        
    def loadAccounts(self):
        self.accountNames.DeleteAllItems()
        cur = cache901.db().cursor()
        cur.execute('select username || "@" || sitename as acctname, accountid from accounts order by acctname')
        for row in cur:
            aid = self.accountNames.Append((row['acctname'], ))
            self.accountNames.SetItemData(aid, row['accountid'])
        self.btnRemAccount.Disable()
        self.acctType.Disable()
        self.acctType.SetSelection(0)
        self.acctUsername.Disable()
        self.acctUsername.SetValue('')
        self.acctPassword.Disable()
        self.acctPassword.SetValue('')
        self.acctIsPremium.Disable()
        self.acctIsPremium.SetValue(False)
        self.acctIsTeam.Disable()
        self.acctIsTeam.SetValue(False)
        self.btnSaveAccount.Disable()
    
    def loadOrigins(self):
        self.locations.DeleteAllItems()
        self.locations.DeleteAllColumns()
        w,h = self.GetTextExtent("QQQQQQQQQQQQQQQQQQ")
        self.locations.InsertColumn(0, 'Location Name', width=w)
        for row in cache901.util.getSearchLocs():
            sid = self.locations.Append((row[1],))
            self.locations.SetItemData(sid, row[0])
            
    def loadGUIPreferences(self):
        # get the current column order list from the config
        cfg = cache901.cfg()
        orderList = cfg.cachecolumnorder
        for column in orderList:
            self.colOrderList.InsertStringItem(orderList.index(column), column)

    def OnAddAccount(self, evt):
        acct = cache901.dbobjects.Account(cache901.dbobjects.minint)
        acct.username = 'unknown'
        acct.sitename = self.acctType.GetItems()[0]
        acct.Save()
        self.loadAccounts()
        self.accountNames.Select(self.accountNames.FindItemData(0, acct.acctid))
    
    def OnRemAccount(self, evt):
        acctid = self.accountNames.GetFirstSelected()
        if acctid > -1:
            acct = cache901.dbobjects.Account(self.accountNames.GetItemData(acctid))
            acct.Delete()
            self.loadAccounts()
    
    def OnLoadAccount(self, evt):
        acctid = self.accountNames.GetFirstSelected()
        if acctid > -1:
            acct = cache901.dbobjects.Account(self.accountNames.GetItemData(acctid))
            self.btnRemAccount.Enable()
            self.acctType.Enable()
            self.acctType.SetValue(acct.sitename)
            self.acctUsername.Enable()
            self.acctUsername.SetValue(acct.username)
            self.acctPassword.Enable()
            self.acctPassword.SetValue(acct.password)
            self.acctIsPremium.Enable()
            self.acctIsPremium.SetValue(acct.ispremium)
            self.acctIsTeam.Enable()
            self.acctIsTeam.SetValue(acct.isteam)
            self.btnSaveAccount.Enable()
        
    def OnSaveAccount(self, evt):
        acctid = self.accountNames.GetFirstSelected()
        if acctid > -1:
            acct = cache901.dbobjects.Account(self.accountNames.GetItemData(acctid))
            acct.sitename = self.acctType.GetValue()
            acct.username = self.acctUsername.GetValue()
            acct.password = self.acctPassword.GetValue()
            acct.ispremium = self.acctIsPremium.GetValue()
            acct.isteam = self.acctIsTeam.GetValue()
            acct.Save()
            self.loadAccounts()
    
    def showGeneral(self):
        self.tabs.ChangeSelection(0)
        self.ShowModal()
        
    def showSearch(self):
        self.tabs.ChangeSelection(1)
        self.ShowModal()
    
    def showCacheDay(self):
        self.tabs.ChangeSelection(2)
        self.ShowModal()
        
    def showGeoAccounts(self):
        self.tabs.ChangeSelection(3)
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
    
    def listCacheDays(self):
        cur = cache901.db().cursor()
        cur.execute('select dayname from cacheday_names order by dayname')
        self.cacheDays.DeleteAllItems()
        for row in cur:
            self.cacheDays.Append((row['dayname'], ))
        if self.cacheDays.GetItemCount() > 0:
            self.cacheDays.Select(0)
            self.OnLoadCacheDay(None)
    
    def OnAddCacheDay(self, evt):
        newname = wx.GetTextFromUser('New Cache Day:', 'Enter The Name', parent=self)
        if newname != '':
            day = cache901.dbobjects.CacheDay(newname)
            day.Save()
            self.listCacheDays()
    
    def OnRemCacheDay(self, evt):
        iid = self.cacheDays.GetFirstSelected()
        while iid != -1:
            dname = self.cacheDays.GetItemText(iid)
            day = cache901.dbobjects.CacheDay(dname)
            if wx.MessageBox('Really delete cache day %s?' % dname, 'Remove Cache Day', style=wx.YES_NO, parent=self) == wx.YES:
                day.Delete()
            iid = self.cacheDays.GetNextSelected(iid)
        self.listCacheDays()
    
    def OnRenameCacheDay(self, evt):
        iid=self.cacheDays.GetFirstSelected()
        if iid != -1:
            dname = self.cacheDays.GetItemText(iid)
            newdname = wx.GetTextFromUser('Rename %s to what?' % dname, 'Rename Cache Day').strip()
            if newdname != '':
                day = cache901.dbobjects.CacheDay(dname)
                day.Rename(newdname)
                self.listCacheDays()
            else:
                wx.MessageBox('Cowardly refusing to rename a day to an empty name', 'Bad Cache Day Name', wx.ICON_EXCLAMATION)
                
    def OnCacheUp(self, evt):
        iid = self.cacheDays.GetFirstSelected()
        dname = self.cacheDays.GetItemText(iid)
        day = cache901.dbobjects.CacheDay(dname)
        
        iid = self.cachesForDay.GetFirstSelected()
        if iid > 0:
            cache = day.caches[iid]
            del day.caches[iid]
            day.caches.insert(iid-1, cache)
            day.Save()
            self.OnLoadCacheDay(evt)
            self.cachesForDay.Select(iid-1)
    
    def OnCacheDown(self, evt):
        iid = self.cacheDays.GetFirstSelected()
        dname = self.cacheDays.GetItemText(iid)
        day = cache901.dbobjects.CacheDay(dname)
        
        iid = self.cachesForDay.GetFirstSelected()
        if iid < len(day.caches)-1:
            cache = day.caches[iid]
            del day.caches[iid]
            day.caches.insert(iid+1, cache)
            day.Save()
            self.OnLoadCacheDay(evt)
            self.cachesForDay.Select(iid+1)
    
    def OnAddCache(self, evt):
        iid = self.cacheDays.GetFirstSelected()
        dname = self.cacheDays.GetItemText(iid)
        day = cache901.dbobjects.CacheDay(dname)
        
        iid = self.availCaches.GetFirstSelected()
        while iid != -1:
            day.caches.append(cache901.dbobjects.Cache(self.availCaches.GetItemData(iid)))
            iid = self.availCaches.GetNextSelected(iid)
        day.Save()
        self.OnLoadCacheDay(evt)
    
    def OnRemCache(self, evt):
        iid = self.cacheDays.GetFirstSelected()
        dname = self.cacheDays.GetItemText(iid)
        day = cache901.dbobjects.CacheDay(dname)
        
        iid = self.cachesForDay.GetFirstSelected()
        delme = []
        while iid != -1:
            delme.append(iid)
            iid = self.cachesForDay.GetNextSelected(iid)
        delme.reverse()
        for idx in delme:
            del day.caches[idx]
        day.Save()
        self.OnLoadCacheDay(evt)
    
    def OnLoadCacheDay(self, evt):
        iid = self.cacheDays.GetFirstSelected()
        dname = self.cacheDays.GetItemText(iid)
        day = cache901.dbobjects.CacheDay(dname)
        self.cachesForDay.DeleteAllItems()
        for cache in day.caches:
            if isinstance(cache, cache901.dbobjects.Cache):
                iid = self.cachesForDay.Append((cache.url_name, ))
                self.cachesForDay.SetItemData(iid, cache.cache_id)
            elif isinstance(cache, cache901.dbobjects.Waypoint):
                iid = self.cachesForDay.Append((cache.name, ))
                self.cachesForDay.SetItemData(iid, cache.wpt_id)

    def OnColMoveUp(self, evt):
        index = self.colOrderList.GetFirstSelected()
        newIndex = index - 1
        itemText = self.colOrderList.GetItemText(index)
        self.colOrderList.DeleteItem(index)
        self.colOrderList.InsertStringItem(newIndex, itemText)
        self.colOrderList.Select(newIndex)
        self.saveColumnOrder()
        
    def OnColMoveDown(self, evt):
        index = self.colOrderList.GetFirstSelected()
        newIndex = index + 1
        itemText = self.colOrderList.GetItemText(index)
        self.colOrderList.DeleteItem(index)
        self.colOrderList.InsertStringItem(newIndex, itemText)
        self.colOrderList.Select(newIndex)
        self.saveColumnOrder()

    def OnColumnSelect(self, evt):
        maxIndex = self.colOrderList.GetItemCount()
        index = self.colOrderList.GetFirstSelected()
        if index == 0:
            self.colMoveUpButton.Disable()
            self.colMoveDownButton.Enable()
        elif index == maxIndex - 1:
            self.colMoveUpButton.Enable()
            self.colMoveDownButton.Disable()
        else:
            self.colMoveUpButton.Enable()
            self.colMoveDownButton.Enable()
            
    def OnColumnDeselect(self, evt):
        index = self.colOrderList.GetFirstSelected()
        if index == -1:
            self.colMoveUpButton.Disable()
            self.colMoveDownButton.Disable()
            
    def saveColumnOrder(self):
        # get the column titles in the order they appear now
        newOrderList = map(lambda idx: self.colOrderList.GetItemText(idx), range(self.colOrderList.GetItemCount()))
        # save the new order list to the config
        cfg = cache901.cfg()
        cfg.cachecolumnorder = newOrderList
        self.colsRearranged = True
    
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
        isinstance(self.gpsbabelPath, wx.StaticText)
        isinstance(self.getFromGPS,   wx.Button)
        isinstance(self.maxLogs,      wx.SpinCtrl)
        
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
        isinstance(self.cacheday,          wx.Panel)
        isinstance(self.addCacheDay,       wx.Button)
        isinstance(self.remCacheDay,       wx.Button)
        isinstance(self.btnRenameCacheDay, wx.Button)
        isinstance(self.upCache,           wx.BitmapButton)
        isinstance(self.downCache,         wx.BitmapButton)
        isinstance(self.addCache,          wx.BitmapButton)
        isinstance(self.remCache,          wx.BitmapButton)
        isinstance(self.cacheDays,         wx.ListCtrl)
        isinstance(self.cachesForDay,      wx.ListCtrl)
        isinstance(self.availCaches,       wx.ListCtrl)

        
        # Accounts Tab
        isinstance(self.acctTabSplit,   wx.SplitterWindow)
        isinstance(self.accountNames,   wx.ListCtrl)
        isinstance(self.btnAddAcount,   wx.Button)
        isinstance(self.btnRemAccount,  wx.Button)
        isinstance(self.acctType,       wx.ComboBox)
        isinstance(self.acctUsername,   wx.TextCtrl)
        isinstance(self.acctPassword,   wx.TextCtrl)
        isinstance(self.acctIsTeam,     wx.CheckBox)
        isinstance(self.acctIsPremium,  wx.CheckBox)
        isinstance(self.btnSaveAccount, wx.Button)
        
        # GUI Preferences Tab
        isinstance(self.guiPreferences,    wx.Panel)
        isinstance(self.colOrderList,      wx.ListCtrl)
        isinstance(self.colMoveUpButton,   wx.Button)
        isinstance(self.colMoveDownButton, wx.Button)
        
