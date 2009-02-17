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

import datetime
import os
import os.path
import re
import shutil
import sys
import time
import zipfile

from urlparse import urlparse

import gpsbabel
import wx
import wx.grid
import wx.lib.mixins.listctrl  as  listmix
import wx.xrc as xrc
import wx.html

import cache901
import cache901.dbobjects
import cache901.gpxsource
import cache901.mapping
import cache901.options
import cache901.search
import cache901.ui_xrc
import cache901.util as util
import cache901.xml901

class Cache901UI(cache901.ui_xrc.xrcCache901UI, wx.FileDropTarget, listmix.ColumnSorterMixin):
    def __init__(self, parent=None):
        cache901.ui_xrc.xrcCache901UI.__init__(self, parent)
        wx.FileDropTarget.__init__(self)
        self.SetDropTarget(self)
        listmix.ColumnSorterMixin.__init__(self, 5)

        self.geoicons = geoicons()
        self.logtrans = logTrans()
        self.SetIcon(self.geoicons["appicon"])
        self.dropfile = wx.FileDataObject()
        self.SetDataObject(self.dropfile)
        self.itemDataMap = {}
        self.wptlist = {}

        # do all the GUI config stuff - creating extra controls and binding objects to events
        self.miscBinds()        
        self.bindButtonEvents()
        self.bindListItemSelectedEvents()
        self.setSashPositionsFromConfig()
        self.createStatusBarSearchField()
        self.prepAltCoordsGrid()

        self.clearAllGui()
        self.configureListBoxes()

        self.pop = None
        self.ld_cache = None

        self.loadData()
        self.updSearchMenu()
        self.updPhotoList()
        # The following is done last, since some menu items are dynamically generated.
        self.bindMenuOptions()


    def miscBinds(self):
        # these three are in here because they don't fold nicely into another method
        self.Bind(wx.EVT_CLOSE,  self.OnClose)
        self.Bind(wx.EVT_SIZE, self.OnWindowResize)
        self.caches.Bind(wx.EVT_CONTEXT_MENU, self.OnPopupMenuCaches)
        self.points.Bind(wx.EVT_CONTEXT_MENU, self.OnPopupMenuWpts)
    

    def createStatusBarSearchField(self):
        # add the search field to the program's status bar
        rect = self.statusBar.GetFieldRect(1)
        self.searchlabel = wx.StaticText(self.statusBar, label="Search:", pos=(rect.x+8, rect.y+2))
        w,h = self.searchlabel.GetSizeTuple()
        self.search = wx.TextCtrl(self.statusBar, pos=(rect.x+5+w, rect.y+2), style=wx.WANTS_CHARS, size=(rect.width-15-w, rect.height))
        self.search.SetToolTipString("At least three characters to search")
        self.search.SetLabel('Search: ')
        self.search.SetValue("")
        font = self.search.GetFont()
        isinstance(font, wx.Font)
        w,h = self.search.GetTextExtent('lq')
        while (h > rect.height - 4) and (font.GetPointSize() >= 10):
            font.SetPointSize(font.GetPointSize() - 0.5)
            w,h = self.search.GetTextExtent('lq')
            self.search.SetFont(font)

        # bind the key up event to the event handler
        self.search.Bind(wx.EVT_KEY_UP, self.OnChangeSearch)
        self.moveStatusBarSearchField()

    def moveStatusBarSearchField(self):
        rect = self.statusBar.GetFieldRect(1)
        self.searchlabel.SetPosition(wx.Point(rect.x+8, rect.y+2))
        w,h = self.searchlabel.GetSizeTuple()
        self.search.SetPosition(wx.Point(rect.x+5+w, rect.y+2))

    def bindMenuOptions(self):
        # bind the menu options to their event handlers
        menuOptions = [
                        (self.OnClose,          self.mnuFileExit),
                        (self.OnDbMaint,        self.mnuFileDbMaint),
                        (self.OnImportFile,     self.mnuFileImport),
                        (self.OnAbout,          self.mnuHelpAbout),
                        (self.OnSearchLocs,     self.mnuFileLocs),
                        (self.OnPrefs,          self.mnuFilePrefs),
                        (self.OnShowMap,        self.showMap),
                        (self.OnAddPhoto,       self.mnuAddPhoto),
                        (self.OnRemovePhoto,    self.mnuRemovePhoto),
                        (self.OnSaveNotes,      self.mnuSaveNote),
                        (self.OnClearNotes,     self.mnuClearNote),
                        (self.OnLogCache,       self.mnuLogThisCache),
                        (self.OnSendToGPS,      self.mnuSendToGPS),
                        (self.OnCacheDay,       self.mnuPrefsCacheDay),
                        (self.OnGeoAccounts,    self.mnuPrefsAccounts),
                        (self.OnGpxSync,        self.mnuGpxSync),
                        (self.OnGpxSources,     self.mnuGpxSources),
                        (self.OnDeleteCacheLog, self.mnuDeleteThisLog),
                        (self.OnDeleteCacheOrWaypoint, self.mnuDeleteThisCache),
                        (self.OnDeleteAllCaches, self.mnuDeleteAll),
                        (self.OnDbBackup,       self.mnuFileBackup)
                      ] 

        for option in menuOptions:
            self.Bind(wx.EVT_MENU, option[0], option[1])
        
        for item in self.updCacheDayMenus(self.mnuAddCurrentToCacheDay):
            self.Bind(wx.EVT_MENU, self.OnAddToCacheDay, item)

        for item in self.updCacheDayMenus(self.mnuSendCacheDayToGPS, False):
            self.Bind(wx.EVT_MENU, self.OnSendCacheDayToGPS, item)
            
        self.mnuLogThisCache.Enable(len(self.listGCAccounts()) > 0)

            
    def bindButtonEvents(self):
        # bind the button events to their event handlers
        buttonEvents = [
                           (self.OnHintsToggle,     self.decodeButton),
                           (self.OnLogToggle,       self.logDecodeButton),
                           (self.OnSaveNotes,       self.saveNotes),
                           (self.OnUndoNoteChanges, self.undoNotes),
                           (self.OnSaveLog,         self.logSaveButton),
                           (self.OnAddAltCoords,    self.btnAddAltCoords),
                           (self.OnRemAltCoords,    self.btnRemAltCoords)
                       ] 
        for buttonEvent in buttonEvents:
            self.Bind(wx.EVT_BUTTON, buttonEvent[0], buttonEvent[1])

        
    def bindListItemSelectedEvents(self):
        # bind the list items to their item selected event handlers
        listItems = [
                        (self.OnLoadCache,   self.caches),
                        (self.OnLoadWpt,     self.points),
                        (self.OnLoadLog,     self.logDateList),
                        (self.OnSwitchPhoto, self.photoList)
                    ]
        for item in listItems:
            self.Bind(wx.EVT_LIST_ITEM_SELECTED, item[0], item[1])
            
            
    def prepAltCoordsGrid(self):
        self.altCoordsTable = AltCoordsTable()
        self.grdAltCoords.SetTable(self.altCoordsTable)
        self.grdAltCoords.AutoSize()
        self.grdAltCoords.EnableDragGridSize()

    def setSashPositionsFromConfig(self):
        #-----------------------------------------------------------------------------------------
        # The following code block is a prime candidate for refactoring out into a separate object
        #-----------------------------------------------------------------------------------------
        # read the config file and set all the splitter window sash positions to their previous values
        cfg = cache901.cfg()
        mainwinsize = cfg.mainwinsize
        self.SetSize(mainwinsize)
        self.splitListsAndDetails.SetSashPosition(cfg.detailsplitpos)
            
        self.splitLists.SetSashPosition(cfg.listsplitpos)
        self.descriptionSplitter.SetSashPosition(cfg.descsplitpos)
        self.logsSplitter.SetSashPosition(cfg.logsplitpos)
        self.picSplitter.SetSashPosition(cfg.picsplitpos)


    def clearAllGui(self):
        self.ld_cache = None
        
        # dummy strings to allow for decent layout with no text
        notSpecifiedLong = "Not Specified     "
        notSpecifiedShort = "None"
        
        # update the basics tab
        self.cacheTypeIcon.SetBitmap(self.geoicons["Unknown"])
        self.cacheName.SetLabel(notSpecifiedLong)
        self.waypointLink.SetLabel(notSpecifiedShort)
        self.waypointLink.SetURL(notSpecifiedShort)
        self.waypointLink.SetVisited(False)
        self.waypointLink.Refresh()
        self.coordinateText.SetLabel(notSpecifiedLong)
        self.sizeText.SetLabel(notSpecifiedShort)
        self.placedByText.SetLabel(notSpecifiedLong)
        self.ownerText.SetLabel(notSpecifiedLong)
        self.difficultyText.SetLabel(notSpecifiedShort)
        self.terrainText.SetLabel(notSpecifiedShort)
        self.stateText.SetLabel(notSpecifiedLong)
        self.countryText.SetLabel(notSpecifiedLong)
        self.available.SetValue(True)
        self.archived.SetValue(False)
        self.hintText.SetValue("")
        
        # Clear the descriptions tab
        self.cacheDescriptionShort.SetPage("")
        self.cacheDescriptionLong.SetPage("")
        
        # Clear the log listings
        self.logDateList.DeleteAllItems()
        self.logCacherNameText.SetLabel("")
        self.logType.Select(self.logtrans.getIdx("Didn't Find It"))
        self.logText.SetValue("")
        self.logText.SetEditable(False)
        self.logSaveButton.Enable(False)
        self.logType.Enable(self.logText.IsEditable())
        self.logDate.Enable(self.logText.IsEditable())
        
        # Clear the travel bug listings
        self.trackableListCtrl.DeleteAllColumns()
        self.trackableListCtrl.DeleteAllItems()
        w,h = self.GetTextExtent("QQQQQQQQQQQQQQ")
        #self.trackableListCtrl.InsertColumn(0, "Travel Bug Name", width=w)
        
        # Clear the notes
        self.currNotes.SetValue("")
        
        # Clear the photos
        self.updPhotoList()
        
        self.Layout()


    def configureListBoxes(self):
        # set up the columns on the appropriate list boxes
        self.logDateList.DeleteAllColumns()
        w,h = self.GetTextExtent("QQQQ/QQ/QQQQQ")
        self.logDateList.InsertColumn(0, "Log Date", width=w)
        w,h = self.GetTextExtent("QQQQQQQ")
        self.points.InsertColumn(0, "Wpt Name", width=w)
        w,h = self.GetTextExtent("QQQQQQQQQQQQQQQQQQ")
        self.points.InsertColumn(1, "Wpt Desc", width=w)

    
    def OnWindowResize(self, evt):
        self.moveStatusBarSearchField()
        evt.Skip()
        
        
    def OnGpxSync(self, evt):
        cache901.gpxsource.gpxSyncAll(self)
        self.updStatus()
    
    
    def OnGpxSources(self, evt):
        gpx = cache901.gpxsource.GPXSourceUI(self)
        gpx.ShowModal()
        self.updStatus()
        
        
    def updPhotoList(self):
        if not hasattr(self, "photoImageList"):
            self.photoImageList = wx.ImageList(64, 64, True)
            self.photoList.AssignImageList(self.photoImageList, wx.IMAGE_LIST_NORMAL)
        self.photoList.DeleteAllItems()
        self.photoImageList.RemoveAll()
        sz = self.currPhoto.GetSize()
        bmp = wx.EmptyBitmap(sz.width, sz.height)
        dc = wx.MemoryDC(bmp)
        dc.SetBackground(wx.Brush(wx.SystemSettings_GetColour(wx.SYS_COLOUR_BACKGROUND)))
        dc.Clear()
        dc.SelectObject(wx.NullBitmap)
        self.currPhoto.SetBitmap(bmp)

        if self.ld_cache is not None:
            for fname in self.ld_cache.photolist.names:
                cache901.notify('Retreiving photo %s' % fname)
                img = wx.BitmapFromImage(wx.Image(os.sep.join([cache901.cfg().dbpath, fname])).Scale(64, 64))
                pnum = self.photoImageList.Add(img)
                self.photoList.InsertImageItem(pnum, pnum)
            if self.photoList.GetItemCount() > 0:
                self.photoList.Select(0)


    def updSearchMenu(self):
        for item in self.CacheSearchMenu.GetMenuItems():
            self.CacheSearchMenu.RemoveItem(item)
        item = self.CacheSearchMenu.Append(-1, 'Advanced Search')
        self.Bind(wx.EVT_MENU, self.OnSearch, item)
        item = self.CacheSearchMenu.Append(-1, 'Clear Search')
        self.Bind(wx.EVT_MENU, self.OnSearch, item)
        self.CacheSearchMenu.AppendSeparator()
        cur = cache901.db().cursor()
        cur.execute('select distinct name from searches order by name')
        for i in cur:
            item = self.CacheSearchMenu.Append(-1, i[0])
            self.Bind(wx.EVT_MENU, self.OnSearch, item)
        self.CacheSearchMenu.AppendSeparator()
        cur.execute('select distinct dayname from cacheday_names order by dayname')
        for i in cur:
            item = self.CacheSearchMenu.Append(-1, 'Cache Day: %s' % i[0])
            self.Bind(wx.EVT_MENU, self.OnSearch, item)

            
    def loadWaypoints(self, wpt_params={}):
        self.points.DeleteAllItems()
        self.wptlist = {}
        if len(wpt_params.keys()) == 0:
            wpt_params['searchpat'] = self.search.GetValue()
        for row in cache901.util.getWaypoints(wpt_params):
            wpt_id = self.points.Append((row[1], row[2]))
            self.points.SetItemData(wpt_id, row[0])
            self.wptlist[row[0]] = (row[1], row[2])
            

    def loadData(self, params={}, wpt_params={}):
        self.caches.DeleteAllItems()
        self.caches.DeleteAllColumns()
        self.itemDataMap = {}
        for i in ((0, "D", "5.00"), (1, "T", "5.00"), (2, "Cache Name", "QQQQQQQQQQQQQQQQQQQQ"), (3, "Cache ID", "QQQQQQQQ"), (4, "Dist", "QQQQQQ")):
            w, h = self.GetTextExtent(i[2])
            self.caches.InsertColumn(i[0], i[1], width=w)

        if len(self.search.GetValue()) > 2:
            params["urlname"] = self.search.GetValue()
        else:
            if params.has_key("urlname"):
                del params["urlname"]
        cache901.notify('Refreshing cache list from database')
        for row in cache901.search.execSearch(params):
            cache_id = self.caches.Append((row[1], row[2], row[3], row[5], row[4]))
            self.caches.SetItemData(cache_id, row[0])
            self.itemDataMap[row[0]] = (row[1], row[2], row[3], row[5], row[4])
        if self.caches.GetItemCount() > 0:
            self.caches.Select(0)

        #self.loadWaypoints(wpt_params)


    def updStatus(self):
        cache901.notify('%d Caches Displayed, %d Waypoints Displayed' % (self.caches.GetItemCount(), self.points.GetItemCount()))


    def OnDbMaint(self, evt):
        cache901.db().maintdb()
        self.updStatus()
        
    def OnDbBackup(self, evt):
        cache901.db().backup()
        self.updStatus()
        
    def OnClose(self, evt):
        if  wx.MessageBox("Are you sure you wish to exit?", "Really Exit?", wx.YES_NO | wx.CENTER, self) == wx.YES:
            #-----------------------------------------------------------------------------------------
            # The following code block is a prime candidate for refactoring out into a separate object
            #-----------------------------------------------------------------------------------------
            cfg=cache901.cfg()
            cfg.listsplitpos = self.splitLists.GetSashPosition()
            cfg.detailsplitpos = self.splitListsAndDetails.GetSashPosition()
            cfg.descsplitpos = self.descriptionSplitter.GetSashPosition()
            cfg.logsplitpos = self.logsSplitter.GetSashPosition()
            cfg.picsplitpos = self.picSplitter.GetSashPosition()
            cfg.mainwinsize = self.GetSize()
            try:
                self.geoicons.Destroy()
            except:
                pass
            self.Destroy()
        else:
            if isinstance(evt, wx.CloseEvent): evt.Veto()


    def OnDeleteAllCaches(self, evt):
        if  wx.MessageBox("Are you sure you wish to delete *all* caches and waypoints?\nThis action *cannot* be undone!", "Really Delete?", wx.YES_NO | wx.CENTER, self) == wx.YES:
            cache901.db().delAllCaches()
            self.clearAllGui()
            self.loadData()
            self.loadWaypoints()
            self.altCoordsTable.changeCache()
            
    def OnLogToggle(self, evt):
        iid = self.logDateList.GetFirstSelected()
        if iid == -1: return
        log = cache901.dbobjects.Log(self.logDateList.GetItemData(iid))
        try:
            if log.log_entry_encoded:
                def decode(m):
                    try:
                        return m.group(0).encode('rot13')
                    except:
                        return cache901.util.forceAscii(m.group(1).encode('rot13'))
                self.logText.SetValue(re.sub('\[(.*?)\]', decode, self.logText.GetValue(), re.S | re.M))
            else:
                self.logText.SetValue(self.logText.GetValue().encode('rot13'))
        except:
            if log.log_entry_encoded:
                def decode(m):
                    try:
                        return m.group(0).encode('rot13')
                    except:
                        return cache901.util.forceAscii(m.group(1).encode('rot13'))
                self.logText.SetValue(re.sub('\[(.*?)\]', decode, self.logText.GetValue(), re.S | re.M))
            else:
                self.logText.SetValue(cache901.util.forceAscii(self.logText.GetValue()).encode('rot13'))
        dectext = self.logDecodeButton.GetLabel()
        dectext = "Encode Log" if dectext == "Decode Log" else "Decode Log"
        self.logDecodeButton.SetLabel(dectext)

    def OnHintsToggle(self, evt):
        try:
            self.hintText.SetValue(self.hintText.GetValue().encode('rot13'))
        except:
            self.hintText.SetValue(util.forceAscii(self.ld_cache.hint.hint).encode('rot13'))
        dectext = self.decodeButton.GetLabel()
        dectext = "Encode" if dectext == "Decode" else "Decode"
        self.decodeButton.SetLabel(dectext)


    def OnLoadWpt(self, evt):
        iid = self.caches.GetFirstSelected()
        while iid != -1:
            self.caches.Select(iid, 0)
            iid = self.caches.GetFirstSelected()
        self.clearAllGui()
        self.ld_cache = cache901.dbobjects.Waypoint(evt.GetData())
        self.cacheName.SetLabel(self.ld_cache.name)
        self.waypointLink.Label = self.ld_cache.name
        self.waypointLink.Refresh()
        self.coordinateText.SetLabel('%s %s' % (cache901.util.latToDMS(self.ld_cache.lat), cache901.util.lonToDMS(self.ld_cache.lon)))
        self.cacheDescriptionLong.SetPage('<p>' + self.ld_cache.comment.replace('\n', '</p><p>') + '</p>')
        self.altCoordsTable.changeCache()


    def OnLoadCache(self, evt):
        iid = self.points.GetFirstSelected()
        while iid != -1:
            self.points.Select(iid, 0)
            iid = self.points.GetFirstSelected()
        self.clearAllGui()
        self.ld_cache = cache901.dbobjects.Cache(evt.GetData())
        # Set up travel bug listings
        self.trackableListCtrl.DeleteAllItems()
        for bug in self.ld_cache.bugs:
            self.trackableListCtrl.Append((bug.name, ))
        # set up log listings
        self.logDateList.DeleteAllItems()
        for log in self.ld_cache.logs:
            s=datetime.date.fromtimestamp(log.date).isoformat()
            log_id = self.logDateList.Append((s, ))
            self.logDateList.SetItemData(log_id, log.id)
        self.logText.SetValue("")
        self.logDate.SetValue(wx.DateTime_Now())
        self.logType.Select(self.logtrans.getIdx("Didn't Find It"))
        self.currNotes.SetValue(self.ld_cache.note.note)
        self.updPhotoList()
        self.cacheName.SetLabel(self.ld_cache.url_name)
        self.waypointLink.URL = self.ld_cache.url
        self.waypointLink.Label = self.ld_cache.name
        self.waypointLink.Refresh()
        self.difficultyText.SetLabel(str(self.ld_cache.difficulty))
        self.terrainText.SetLabel(str(self.ld_cache.terrain))
        self.coordinateText.SetLabel('%s %s' % (cache901.util.latToDMS(self.ld_cache.lat), cache901.util.lonToDMS(self.ld_cache.lon)))
        self.sizeText.SetLabel(self.ld_cache.container)
        self.placedByText.SetLabel(self.ld_cache.placed_by.replace('&', '&&')[:25])
        self.ownerText.SetLabel(self.ld_cache.owner_name.replace('&', '&&')[:25])
        bmp = wx.ImageFromBitmap(self.geoicons[self.ld_cache.type]).Scale(32,32)
        self.cacheTypeIcon.SetBitmap(wx.BitmapFromImage(bmp))
        self.stateText.SetLabel(self.ld_cache.state)
        self.countryText.SetLabel(self.ld_cache.country)
        self.available.SetValue(self.ld_cache.available)
        self.archived.SetValue(self.ld_cache.archived)
        self.cacheType.SetLabel(self.ld_cache.type.split("|")[-1])
        self.cacheBasics.Fit()
        try:
            self.hintText.SetValue(self.ld_cache.hint.hint.encode('rot13'))
        except:
            self.hintText.SetValue(self.ld_cache.hint.hint)
        self.Disable()
        cache901.notify('Updating short cache description')
        if self.ld_cache.short_desc_html:
            self.cacheDescriptionShort.SetPage(self.ld_cache.short_desc)
        else:
            self.cacheDescriptionShort.SetPage('<p>' + self.ld_cache.short_desc.replace('\n', '</p><p>') + '</p>')
        cache901.notify('Updating long cache description')
        if self.ld_cache.long_desc_html:
            self.cacheDescriptionLong.SetPage(self.ld_cache.long_desc)
        else:
            self.cacheDescriptionLong.SetPage('<p>' + self.ld_cache.long_desc.replace('\n', '</p><p>') + '</p>')
        if self.logDateList.GetItemCount() > 0:
            self.logDateList.Select(0)
        wpt_params = {'addwpts': [] }
        m=re.match('.*Additional Waypoints(.*)$', self.ld_cache.long_desc, re.S)
        if m is not None:
            for row in re.findall('([A-Z0-9]{5,8})', m.group(1)):
                wpt_params['addwpts'].append(row)
        self.loadWaypoints(wpt_params)
        self.altCoordsTable.changeCache(self.ld_cache.cache_id)
            
        self.Enable()
        self.updStatus()
        self.caches.Enable()
        self.points.Enable()

    def OnLoadLog(self, evt):
        log = cache901.dbobjects.Log(evt.GetData())
        self.logDecodeButton.SetLabel("Decode Log" if log.log_entry_encoded else "Encode Log")
        self.logText.SetEditable(log.finder in self.listGCAccounts())
        self.logType.Enable(self.logText.IsEditable())
        self.logDate.Enable(self.logText.IsEditable())
        self.logSaveButton.Enable(self.logText.IsEditable())
        if log.log_entry_encoded:
            def decode(m):
                try:
                    return m.group(0).encode('rot13')
                except:
                    return cache901.util.forceAscii(m.group(1).encode('rot13'))
            self.logText.SetValue(re.sub('\[(.*?)\]', decode, log.log_entry, re.S | re.M))
        else:
            self.logText.SetValue(log.log_entry)
        self.logDate.SetValue(wx.DateTimeFromTimeT(log.date))
        self.logType.Select(self.logtrans.getIdx(log.type))
        self.logCacherNameText.SetLabel(log.finder.replace('&', '&&'))
        self.logSaveButton.Enable(log.my_log)

    def listGCAccounts(self):
        cur = cache901.db().cursor()
        usernames = []
        cur.execute('select username from accounts')
        for row in cur:
            if row is not None:
                usernames.append(row['username'])
        return usernames

    def importSpecificFile(self, path, maintdb=True):
        parser = cache901.xml901.XMLParser()
        if path.lower().endswith('.zip'):
            cache901.notify('Examining %s for gpx files' % path)
            zfile = zipfile.ZipFile(path)
            gpxziplist = filter(lambda x: x.lower().endswith('.gpx'), zfile.namelist())
            for gpxname in gpxziplist:
                cache901.notify('Processing %s%s%s' % (path, os.sep, gpxname))
                parser.parse(zfile.read(gpxname), False)
                cache901.notify('Completed processing %s%s%s' % (path, os.sep, gpxname))
        elif path.lower().endswith('.gpx'):
            cache901.notify('Processing %s' % path)
            infile = open(path)
            parser.parse(infile, False)
            cache901.notify('Completed processing %s' % path)
        else:
            cache901.notify('Unable to process file %s' % path)
        if maintdb:
            cache901.db().maintdb()
    
    
    def OnImportFile(self, evt):
        fdg = wx.FileDialog(self, "Select GPX File", style=wx.FD_DEFAULT_STYLE | wx.FD_MULTIPLE | wx.FD_FILE_MUST_EXIST | wx.FD_OPEN, wildcard="GPX and Zip Files (*.gpx)|*.gpx;*.GPX;*.Gpx;*.zip;*.ZIP;*.Zip|All Files (*.*)|*.*")
        cfg = cache901.cfg()
        if cfg.lastimportdir is not None:
            fdg.SetDirectory(cfg.lastimportdir)
        if fdg.ShowModal() == wx.ID_OK:
            cfg.lastimportdir = fdg.GetDirectory()
            for path in fdg.GetPaths():
                self.importSpecificFile(path, False)
            cache901.db().maintdb()
            self.loadData()
        self.updStatus()


    def OnChangeSearch(self, evt):
        if len(self.search.GetValue()) > 2 or len(self.search.GetValue()) == 0:
            self.loadData()
            self.search.SetFocus()
            self.search.SetSelection(0, 0)
            self.search.SetInsertionPointEnd()


    def OnAbout(self, evt):
        abt = cache901.ui_xrc.xrcAboutBox(self)
        abt.version.SetLabel("Version: %s" % cache901.version)
        abt.SetIcon(self.geoicons["appicon"])
        abt.ShowModal()


    def OnSearchLocs(self, evt):
        opts = cache901.options.OptionsUI(self.caches, self)
        opts.showSearch()
        self.mnuLogThisCache.Enable(len(self.listGCAccounts()) > 0)
        iid = self.caches.GetFirstSelected()
        if iid == -1:
            iid = self.points.GetFirstSelected()
            self.points.Select(iid, 0)
            self.points.Select(iid, 1)
        else:
            self.caches.Select(iid, 0)
            self.caches.Select(iid, 1)
        self.updSearchMenu()
        for item in self.updCacheDayMenus(self.mnuAddCurrentToCacheDay):
            self.Bind(wx.EVT_MENU, self.OnAddToCacheDay, item)
        for item in self.updCacheDayMenus(self.mnuSendCacheDayToGPS, False):
            self.Bind(wx.EVT_MENU, self.OnSendCacheDayToGPS, item)


    def OnGeoAccounts(self, evt):
        opts = cache901.options.OptionsUI(self.caches, self)
        opts.showGeoAccounts()
        self.mnuLogThisCache.Enable(len(self.listGCAccounts()) > 0)
        iid = self.caches.GetFirstSelected()
        if iid == -1:
            iid = self.points.GetFirstSelected()
            self.points.Select(iid, 0)
            self.points.Select(iid, 1)
        else:
            self.caches.Select(iid, 0)
            self.caches.Select(iid, 1)
        self.updSearchMenu()
        for item in self.updCacheDayMenus(self.mnuAddCurrentToCacheDay):
            self.Bind(wx.EVT_MENU, self.OnAddToCacheDay, item)
        for item in self.updCacheDayMenus(self.mnuSendCacheDayToGPS, False):
            self.Bind(wx.EVT_MENU, self.OnSendCacheDayToGPS, item)
        
        
    def OnPrefs(self, evt):
        opts = cache901.options.OptionsUI(self.caches, self)
        opts.showGeneral()
        self.mnuLogThisCache.Enable(len(self.listGCAccounts()) > 0)
        iid = self.caches.GetFirstSelected()
        if iid == -1:
            iid = self.points.GetFirstSelected()
            self.points.Select(iid, 0)
            self.points.Select(iid, 1)
        else:
            self.caches.Select(iid, 0)
            self.caches.Select(iid, 1)
        self.updSearchMenu()
        for item in self.updCacheDayMenus(self.mnuAddCurrentToCacheDay):
            self.Bind(wx.EVT_MENU, self.OnAddToCacheDay, item)
        for item in self.updCacheDayMenus(self.mnuSendCacheDayToGPS, False):
            self.Bind(wx.EVT_MENU, self.OnSendCacheDayToGPS, item)


    def OnCacheDay(self, evt):
        opts = cache901.options.OptionsUI(self.caches, self)
        opts.showCacheDay()
        self.mnuLogThisCache.Enable(len(self.listGCAccounts()) > 0)
        iid = self.caches.GetFirstSelected()
        if iid == -1:
            iid = self.points.GetFirstSelected()
            self.points.Select(iid, 0)
            self.points.Select(iid, 1)
        else:
            self.caches.Select(iid, 0)
            self.caches.Select(iid, 1)
        self.updSearchMenu()
        for item in self.updCacheDayMenus(self.mnuAddCurrentToCacheDay):
            self.Bind(wx.EVT_MENU, self.OnAddToCacheDay, item)
        for item in self.updCacheDayMenus(self.mnuSendCacheDayToGPS, False):
            self.Bind(wx.EVT_MENU, self.OnSendCacheDayToGPS, item)


    def OnSearch(self, evt):
        isinstance(evt, wx.CommandEvent)
        self.search.SetValue("")
        itemid = evt.GetId()
        item = self.GetMenuBar().FindItemById(itemid)
        mtext = item.GetLabel()
        isinstance(mtext, str)
        if mtext == "Advanced Search":
            dlg = cache901.search.SearchBox(self)
            if dlg.ShowModal() == wx.ID_OK:
                params = dlg.getSearchParams()
                try:
                    self.loadData(params)
                except Exception, e:
                    wx.MessageBox(str(e), 'An Error Occurred While Searching', wx.ICON_ERROR, self)
        elif mtext == "Clear Search":
            self.search.SetValue("")
            try:
                self.loadData({})
            except Exception, e:
                wx.MessageBox(str(e), 'An Error Occurred While Searching', wx.ICON_ERROR, self)
        elif mtext.startswith('Cache Day: '):
            mtext = mtext.replace('Cache Day: ', '')
            day = cache901.dbobjects.CacheDay(mtext)
            cache_params = {}
            cache_params['dayname'] = mtext
            cache_params['ids'] = []
            wpt_params = {}
            wpt_params['ids'] = []
            wpt_params['dayname'] = mtext
            for cw in day.caches:
                if isinstance(cw, cache901.dbobjects.Cache):
                    cache_params['ids'].append(cw.cache_id)
                else:
                    wpt_params['ids'].append(cw.wpt_id)
            if len(cache_params['ids']) == 0: del cache_params['ids']
            if len(wpt_params['ids']) == 0: del wpt_params['ids']
            try:
                self.loadData(cache_params, wpt_params)
            except Exception, e:
                wx.MessageBox(str(e), 'An Error Occurred While Searching', wx.ICON_ERROR, self)
        else:
            params = cache901.search.loadSavedSearch(mtext)
            try:
                self.loadData(params)
            except Exception, e:
                wx.MessageBox(str(e), 'An Error Occurred While Searching', wx.ICON_ERROR, self)
        self.updSearchMenu()
        for item in self.updCacheDayMenus(self.mnuAddCurrentToCacheDay):
            self.Bind(wx.EVT_MENU, self.OnAddToCacheDay, item)
        for item in self.updCacheDayMenus(self.mnuSendCacheDayToGPS, False):
            self.Bind(wx.EVT_MENU, self.OnSendCacheDayToGPS, item)


    def OnShowMap(self, evt):
        i = 0
        cacheids = []
        while i < self.caches.GetItemCount():
            cacheids.append(self.caches.GetItemData(i))
            i = i + 1
        mapui = cache901.mapping.MapUI(self, cacheids)
        if mapui.ShowModal() == wx.ID_OK:
            cid = mapui.found
            if cid is not None:
                item = self.caches.GetFirstSelected()
                while item != -1:
                    self.caches.Select(item, 0)
                    item = self.caches.GetNextSelected(item)
                item = self.caches.FindItemData(0, cid)
                self.caches.Select(item)
                self.caches.EnsureVisible(item)
        self.updStatus()


    def OnClearNotes(self, evt):
        if wx.MessageBox("This operation cannot be undone!\nContinue?", "Warning: About To Remove Data", wx.YES_NO) == wx.YES:
            self.currNotes.SetValue("")
            self.ld_cache.note.note = ""
            self.ld_cache.note.Save()
            cache901.db().commit()


    def OnSaveNotes(self, evt):
        self.ld_cache.note.note = self.currNotes.GetValue()
        self.ld_cache.note.Save()
        cache901.db().commit()


    def OnUndoNoteChanges(self, evt):
        if wx.MessageBox("This operation cannot be undone!\nContinue?", "Warning: About To Remove Data", wx.YES_NO) == wx.YES:
            self.currNotes.SetValue(self.ld_cache.note.note)


    def OnAddPhoto(self, evt):
        fdg = wx.FileDialog(self, "Select Image File", style=wx.FD_DEFAULT_STYLE | wx.FD_MULTIPLE | wx.FD_FILE_MUST_EXIST | wx.FD_OPEN, wildcard="Photo Files (*.jpg;*.jpeg;*.png)|*.jpg;*.JPG;*.Jpg;*.jpeg;*.JPEG;*.Jpeg;*.png;*.PNG;*.Png|All Files (*.*)|*.*")
        cfg = cache901.cfg()
        if cfg.lastphotodir is not None:
            fdg.SetDirectory(cfg.lastphotodir)
        if fdg.ShowModal() == wx.ID_OK:
            cfg.lastphotodir = fdg.GetDirectory()
            for fname in fdg.GetPaths():
                dest = os.path.split(fname)[1]
                idx = 0
                while os.path.exists(os.sep.join([cache901.cfg().dbpath, dest])):
                    dest = "%06d-%s" % (idx, dest)
                fulldest = os.sep.join([cache901.cfg().dbpath, dest])
                cache901.notify('Copying file %s to %s' % (fname, fulldest))
                shutil.copyfile(fname, fulldest)
                self.ld_cache.photolist.names.append(dest)
            self.ld_cache.photolist.Save()
            cache901.db().commit()
        self.updPhotoList()
        self.updStatus()


    def OnSwitchPhoto(self, evt):
        idx = evt.GetImage()
        fname = os.sep.join([cache901.cfg().dbpath, self.ld_cache.photolist.names[idx]])
        img = wx.Image(fname)
        
        # Get photo size and scale it
        sz = self.currPhoto.GetSize()
        aspect = float(img.GetWidth()) / float(img.GetHeight())
        if float(sz.width) / aspect > sz.height: sz.width = int(sz.height * aspect)
        else: sz.height = int(sz.width / aspect)
        img = wx.BitmapFromImage(img.Scale(sz.width, sz.height, wx.IMAGE_QUALITY_HIGH))
        
        # Calculate new position for photo
        possz = self.currPhoto.GetSize()
        x = (possz.width - sz.width) / 2
        y = (possz.height - sz.height) / 2
        
        bmp = wx.EmptyBitmap(possz.width, possz.height)
        dc = wx.MemoryDC(bmp)
        dc.SetBackground(wx.Brush(wx.SystemSettings_GetColour(wx.SYS_COLOUR_BACKGROUND)))
        dc.Clear()
        dc.DrawBitmap(img, x, y)
        dc.SelectObject(wx.NullBitmap)
        
        # Put the photo onscreen
        self.currPhoto.SetBitmap(bmp)
        self.updStatus()


    def OnRemovePhoto(self, evt):
        if wx.MessageBox("This operation cannot be undone!\nContinue?", "Warning: About To Remove Data", wx.YES_NO) == wx.YES:
            idx = self.photoList.GetFirstSelected()
            fname = os.sep.join([cache901.cfg().dbpath, self.ld_cache.photolist.names[idx]])
            os.unlink(fname)
            del self.ld_cache.photolist.names[idx]
            self.ld_cache.photolist.Save()
            cache901.db().commit()
            self.updPhotoList()


    def OnDeleteCacheLog(self, evt):
        if wx.MessageBox("This operation cannot be undone!\nContinue?", "Warning: About To Remove Data", wx.YES_NO) == wx.YES:
            iid = self.logDateList.GetFirstSelected()
            if iid > -1:
                log = cache901.dbobjects.Log(self.logDateList.GetItemData(iid))
                log.Delete()
                cid = self.caches.GetFirstSelected()
                self.caches.Select(cid, 0)
                self.caches.Select(cid, 1)
                
    def OnLogCache(self, evt):
        log = cache901.dbobjects.Log(cache901.dbobjects.minint)
        log.cache_id = self.ld_cache.cache_id
        log.my_log = True
        log.date = time.mktime(datetime.datetime.now().timetuple())
        cur = cache901.db().cursor()
        cur.execute('select username from accounts where lower(sitename)="geocaching.com" and isteam=0')
        row = cur.fetchone()
        if row is None:
            wx.MessageBox('Without a non-team account defined\nin Preferences->GeoCaching Accounts,\nI don\'t know what username to attach\nto this log.\nAborting.', 'Missing Username', wx.ICON_ERROR)
            return
        log.finder = row['username']
        log.Save()
        cache901.db().commit()
        iid = self.caches.GetFirstSelected()
        self.caches.Select(iid, 0)
        self.caches.Select(iid, 1)
        self.logText.SetEditable(True)
        self.logType.Enable(self.logText.IsEditable())
        self.logDate.Enable(self.logText.IsEditable())
        self.logSaveButton.Enable(self.logText.IsEditable())
        self.logDateList.Select(0)
        self.cacheInfo.ChangeSelection(2)


    def OnSaveLog(self, evt):
        self.logText.SetEditable(False)
        self.logType.Enable(self.logText.IsEditable())
        self.logDate.Enable(self.logText.IsEditable())
        self.logSaveButton.Enable(self.logText.IsEditable())
        log = cache901.dbobjects.Log(self.logDateList.GetItemData(self.logDateList.GetFirstSelected()))
        log.log_entry = self.logText.GetValue()
        log.type = self.logtrans.getType(self.logType.GetSelection())
        cur = cache901.db().cursor()
        cur.execute('select username from accounts where sitename="GeoCaching.com" and ispremium=1 and isteam=0')
        row = cur.fetchone()
        log.finder = row['username']

        dt = self.logDate.GetValue()
        d = datetime.datetime(dt.GetYear(), dt.GetMonth()+1, dt.GetDay(), 0, 0, 0)
        log.date = time.mktime(d.timetuple())
        if time.daylight:
            log.date += time.altzone
        else:
            log.date += time.timezone
        log.Save()
        cache901.db().commit()
        self.ld_cache = cache901.dbobjects.Cache(log.cache_id)
        self.reloadLogList()
        
        
    def reloadLogList(self):
        self.logDateList.DeleteAllItems()
        for log in self.ld_cache.logs:
            s=datetime.date.fromtimestamp(log.date).isoformat()
            log_id = self.logDateList.Append((s, ))
            self.logDateList.SetItemData(log_id, log.id)
        self.logText.SetValue("")
        self.logDate.SetValue(wx.DateTime_Now())
        self.logType.Select(self.logtrans.getIdx("Didn't Find It"))


    def OnPopupMenu(self, evt):
        self.mnu = cache901.ui_xrc.xrcCwMenu()
        self.mnu.Bind(wx.EVT_MENU, self.OnSendToGPS, self.mnu.popSendToGPS)
        self.updCacheDayMenus(self.mnu.popAddCurrentToCacheDay)
        for item in self.updCacheDayMenus(self.mnu.popAddCurrentToCacheDay):
            if sys.platform == 'win32':
                self.mnu.Bind(wx.EVT_MENU, self.OnAddToCacheDay, item)
            else:
                item.GetMenu().Bind(wx.EVT_MENU, self.OnAddToCacheDay, item)
        self.PopupMenu(self.mnu)
        self.mnu.Destroy()
        self.mnu = None


    def OnPopupMenuCaches(self, evt):
        self.pop = self.caches
        self.OnPopupMenu(evt)


    def OnPopupMenuWpts(self, evt):
        self.pop = self.points
        self.OnPopupMenu(evt)


    def OnSendToGPS(self, evt):
        isinstance(evt, wx.CommandEvent)
        win = evt.GetEventObject()
        isinstance(win, wx.Menu)
        cfg = cache901.cfg()
        if self.caches.GetFirstSelected() != -1:
            cache = cache901.dbobjects.Cache(self.caches.GetItemData(self.caches.GetFirstSelected()))
            ctp = 'cache'
        else:
            cache = cache901.dbobjects.Waypoint(self.points.GetItemData(self.points.GetFirstSelected()))
            ctp = 'waypoint'
        gpx = cache901.util.CacheToGPX(cache)
        cache901.notify('Sending %s "%s" to GPS' % (ctp, cache.name))
        try:
            gpsbabel.gps.setInGpx(gpx)
            gpsbabel.gps.write(cfg.gpsport, cfg.gpstype, wpt=True, parseOutput=False)
        except RuntimeError, e:
            wx.MessageBox(str(e), 'A GPS Babel Failure Occured', wx.ICON_ERROR | wx.CENTRE, self)
        self.pop = None
        self.updStatus()


    def OnAddToCacheDay(self, evt):
        isinstance(evt, wx.CommandEvent)
        self.search.SetValue("")
        itemid = evt.GetId()
        item = self.GetMenuBar().FindItemById(itemid)
        if item is None:
            if self.mnu is not None:
                item = self.mnu.FindItemById(itemid)
            else:
                cache901.notify('An error occurred in the popup menu handler')
        mtext = item.GetLabel()
        if mtext == "New Cache Day":
            mtext =  wx.GetTextFromUser('New Cache Day Name', 'New Cache Day Name', parent = self)
            if mtext.strip() != '':
                day = cache901.dbobjects.CacheDay(mtext)
                day.Save()
            else:
                day = None
                wx.MessageBox('Cowardly refusing to create a day name with just spaces in it', 'Bad Cache Day Name', wx.ICON_EXCLAMATION)
                return
        else:
            day = cache901.dbobjects.CacheDay(mtext)
        if day is not None:
            iid = self.caches.GetFirstSelected()
            if iid != -1:
                day.caches.append(cache901.dbobjects.Cache(self.caches.GetItemData(iid)))
            else:
                day.caches.append(cache901.dbobjects.Waypoint(self.points.GetItemData(self.points.GetFirstSelected())))
            day.Save()
        self.updSearchMenu()
        for item in self.updCacheDayMenus(self.mnuAddCurrentToCacheDay):
            self.Bind(wx.EVT_MENU, self.OnAddToCacheDay, item)
        for item in self.updCacheDayMenus(self.mnuSendCacheDayToGPS, False):
            self.Bind(wx.EVT_MENU, self.OnSendCacheDayToGPS, item)


    def OnSendCacheDayToGPS(self, evt):
        isinstance(evt, wx.CommandEvent)
        self.search.SetValue("")
        itemid = evt.GetId()
        item = self.GetMenuBar().FindItemById(itemid)
        mtext = item.GetLabel()
        day = cache901.dbobjects.CacheDay(mtext)
        gpx = cache901.util.CacheDayToGPX(day)
        cfg = cache901.cfg()
        cache901.notify('Sending Cache Day "%s" to GPS' % (mtext, ))
        try:
            gpsbabel.gps.setInGpx(gpx)
            gpsbabel.gps.write(cfg.gpsport, cfg.gpstype, wpt=True, route=True, parseOutput=False)
        except RuntimeError, e:
            wx.MessageBox(str(e), 'A GPS Babel Failure Occured', wx.ICON_ERROR | wx.CENTRE, self)
        self.updStatus()


    def updCacheDayMenus(self, menu, includenew=True):
        isinstance(menu, wx.Menu)
        for item in menu.GetMenuItems():
            menu.RemoveItem(item)
        mitems = []
        if includenew:
            mitems.append(menu.Append(-1, 'New Cache Day'))
            menu.AppendSeparator()
        cur = cache901.db().cursor()
        cur.execute('select dayname from cacheday_names order by dayname')
        for row in cur:
            if row[0].strip() != '':
                mitems.append(menu.Append(-1, row[0]))
        return mitems


    def OnDropFiles(self, x, y, filenames):
        for filename in filenames:
            self.importSpecificFile(filename, False)
        cache901.db().maintdb()
        self.updStatus()
            
    
    def GetListCtrl(self):
        return self.caches
    
    def OnDeleteCacheOrWaypoint(self, evt):
        iid = self.caches.GetFirstSelected()
        if iid > -1:
            cache = cache901.dbobjects.Cache(self.caches.GetItemData(iid))
            if wx.MessageBox('Warning! This cannot be undone!\nReally delete cache: "%s"?' % cache.url_name, 'Really Delete?', wx.ICON_WARNING | wx.YES_NO, self) == wx.YES:
                cache.Delete()
                if self.caches.GetItemCount() > 1:
                    if iid == 0:
                        self.caches.Select(iid+1)
                        self.caches.DeleteItem(iid)
                    else:
                        self.caches.Select(iid-1)
                        self.caches.DeleteItem(iid)
                else:
                    self.caches.DeleteItem(iid)
                    self.clearAllGui()
        else:
            iid = self.points.GetFirstSelected()
            if iid > -1:
                wpt = cache901.dbobjects.Waypoint(self.points.GetItemData(iid))
                if wx.MessageBox('Warning! This cannot be undone!\nReally delete waypoint: "%s"?' % wpt.name, 'Really Delete?', wx.ICON_WARNING | wx.YES_NO, self) == wx.YES:
                    wpt.Delete()
                    if self.points.GetItemCount() > 1:
                        if iid == 0:
                            self.points.Select(iid+1)
                            self.points.DeleteItem(iid)
                        else:
                            self.points.Select(iid-1)
                            self.points.DeleteItem(iid)
                    else:
                        self.points.DeleteItem(iid)
                        self.clearAllGui()
                
    def OnAddAltCoords(self, evt):
        self.grdAltCoords.AppendRows()
    
    def OnRemAltCoords(self, evt):
        #self.grdAltCoords.DeleteRows(self.grdAltCoords.GetS
        rows = self.grdAltCoords.GetSelectedRows()
        rows.append(self.grdAltCoords.GetGridCursorRow())
        for row in rows:
            if row > 0:
                rowname = self.grdAltCoords.GetTable().alts.alts[row-1]['name']
                if wx.MessageBox('Really remove coordinates for "%s"?' % (rowname), "Confirm Deletion", wx.ICON_QUESTION | wx.YES_NO, self) == wx.YES:
                    self.grdAltCoords.DeleteRows(row-1)
        
    def forWingIde(self):
        cwmenu = cache901.ui_xrc.xrcCwMenu()
        isinstance(cwmenu.popSendToGPS, wx.MenuItem)
        isinstance(cwmenu.popAddCurrentToCacheDay, wx.Menu)
        isinstance(self.cacheName, wx.StaticText)
        isinstance(self.waypointLink, wx.HyperlinkCtrl)
        isinstance(self.coordinateText, wx.StaticText)
        isinstance(self.mnuAddCurrentToCacheDay, wx.MenuItem)
        isinstance(self.mnuSendToGPS, wx.MenuItem)
        isinstance(self.mnuAddPhoto, wx.MenuItem)
        isinstance(self.mnuClearNote, wx.MenuItem)
        isinstance(self.mnuRemovePhoto, wx.MenuItem)
        isinstance(self.mnuSaveNote, wx.MenuItem)
        isinstance(self.containerIcon, wx.StaticBitmap)
        isinstance(self.containerType, wx.StaticText)
        isinstance(self.splitLists, wx.SplitterWindow)
        isinstance(self.splitListsAndDetails, wx.SplitterWindow)
        isinstance(self.splitLogsandLog, wx.SplitterWindow)
        isinstance(self.splitLogsAndBugs, wx.SplitterWindow)
        isinstance(self.caches, wx.ListCtrl)
        isinstance(self.points, wx.ListCtrl)
        isinstance(self.cacheInfo, wx.Notebook)
        isinstance(self.urlName, wx.TextCtrl)
        isinstance(self.urlDesc, wx.TextCtrl)
        isinstance(self.difficulty, wx.TextCtrl)
        isinstance(self.cacheType, wx.StaticText)
        isinstance(self.terrain, wx.TextCtrl)
        isinstance(self.available, wx.CheckBox)
        isinstance(self.archived, wx.CheckBox)
        isinstance(self.lat, wx.TextCtrl)
        isinstance(self.lon, wx.TextCtrl)
        isinstance(self.placedByText, wx.StaticText)
        isinstance(self.ownerText, wx.StaticText)
        isinstance(self.stateText, wx.StaticText)
        isinstance(self.countryText, wx.StaticText)
        isinstance(self.hintText, wx.TextCtrl)
        isinstance(self.hintsCoding, wx.Button)
        isinstance(self.trackableListCtrl, wx.ListCtrl)
        isinstance(self.cacheDescriptionShort, wx.html.HtmlWindow)
        isinstance(self.cacheDescriptionLong, wx.html.HtmlWindow)
        isinstance(self.logDate, wx.DatePickerCtrl)
        isinstance(self.logType, wx.Choice)
        isinstance(self.logCacherNameText, wx.StaticText)
        isinstance(self.logDateList, wx.ListCtrl)
        isinstance(self.logText, wx.TextCtrl)
        isinstance(self.encText, wx.Button)
        isinstance(self.cacheUrl, wx.HyperlinkCtrl)
        isinstance(self.waypointId, wx.StaticText)
        isinstance(self.statusBar, wx.StatusBar)
        isinstance(self.cacheNotes, wx.Panel)
        isinstance(self.cachePics, wx.Panel)
        isinstance(self.currNotes, wx.TextCtrl)
        isinstance(self.saveNotes, wx.Button)
        isinstance(self.undoNotes, wx.Button)
        isinstance(self.currPhoto, wx.StaticBitmap)
        isinstance(self.photoList, wx.ListCtrl)
        isinstance(self.CacheSearchMenu, wx.Menu)
        isinstance(self.logSaveButton, wx.Button)
        isinstance(self.mnuLogThisCache, wx.MenuItem)
        isinstance(self.mnuDeleteThisLog, wx.MenuItem)
        isinstance(self.logDecodeButton, wx.Button)
        isinstance(self.mnuDeleteThisCache, wx.MenuItem)
        isinstance(self.btnAddAltCoords, wx.Button)
        isinstance(self.btnRemAltCoords, wx.Button)
        isinstance(self.grdAltCoords, wx.grid.Grid)
        isinstance(self.mnuDeleteAll, wx.MenuItem)

        
class AltCoordsTable(wx.grid.PyGridTableBase):
    def __init__(self):
        wx.grid.PyGridTableBase.__init__(self)
        self.centercell = wx.grid.GridCellAttr()
        self.centercell.SetAlignment(wx.ALIGN_CENTER, wx.ALIGN_CENTER)
        self.nullattr = wx.grid.GridCellAttr()
        self.colnames = ["Name", "Latitude", "Longitude", "Is Default"]
        self.alts = None
        self.cache = None
        
    def GetNumberRows(self):
        if self.cache is None: return 0
        if self.alts is None: return 1
        return len(self.alts.alts) + 1
    
    def GetNumberCols(self):
        return 4
    
    def IsEmptyCell(self, row, col):
        return False
    
    def GetValue(self, row, col):
        if row == 0:
            if col == 0: return "Original"
            if col == 1: return cache901.util.latToDMS(self.cache.lat)
            if col == 2: return cache901.util.lonToDMS(self.cache.lon)
            if col == 3: return self.rowIsDefault(row)
        if row <= len(self.alts.alts):
            if col == 0: return self.alts.alts[row-1]['name']
            if col == 1: return self.alts.alts[row-1]['lat']
            if col == 2: return self.alts.alts[row-1]['lon']
            if col == 3: return self.rowIsDefault(row)
        if col != 3: return "Unknown"
        else: return 0
    
    def AppendRows(self, numRows=1):
        if numRows == 1:
            self.alts.alts.append({
                'name' : 'Stage %d' % (len(self.alts.alts) + 1),
                'lat' : '',
                'lon' : '',
                'setdefault' : 0
                })
            self.alts.Save()
            self.GetView().SetTable(self)
            self.GetView().AutoSize()
            return True
        return False
    
    def DeleteRows(self, pos=0, numRows=1):
        for i in range(numRows):
            del self.alts.alts[pos]
        self.alts.Save()
        self.GetView().SetTable(self)
        self.GetView().AutoSize()
        return True
    
    def SetValue(self, row, col, value):
        if len(self.alts.alts) > 0 and col == 3:
            try:
                lat = cache901.util.dmsToDec(self.alts.alts[row-1]['lat'])
                lon = cache901.util.dmsToDec(self.alts.alts[row-1]['lon'])
                for idx in range(len(self.alts.alts)):
                    self.alts.alts[idx]['setdefault'] = 0
                if row > 0:
                    self.alts.alts[row-1]['setdefault'] = int(value)
            except Exception, e:
                wx.MessageBox('Row %d has either latitude or longitude invalid, and cannot be the default\nError Text: %s' % (row, str(e)), 'An Error Occurred', wx.ICON_ERROR | wx.OK)
                return
        if row > 0:
            row = row - 1
            if col == 0:   self.alts.alts[row]['name'] = value
            elif col == 1: self.alts.alts[row]['lat'] = value
            elif col == 2: self.alts.alts[row]['lon'] = value
        self.GetView().ForceRefresh()
        self.alts.Save()
    
    def GetColLabelValue(self, col):
        return self.colnames[col]
    
    def GetRowLabelValue(self, row):
        return "%d" % (row+1)
    
    def GetTypeName(self, row, col):
        if col != 3:
            return wx.grid.GRID_VALUE_STRING
        else:
            return wx.grid.GRID_VALUE_BOOL
    
    def GetAttr(self, row, col, kind):
        if col == 3:
            self.centercell.IncRef()
            return self.centercell
        else:
            self.nullattr.IncRef()
            return self.nullattr
        
    # The following should be called whenever a new cache/waypoint is clicked
    def changeCache(self, newcacheid=None):
        if self.alts is not None:
            self.alts.Save()
        if newcacheid is not None:
            self.alts = cache901.dbobjects.AltCoordsList(newcacheid)
            self.cache = cache901.dbobjects.Cache(newcacheid)
        else:
            self.alts = None
            self.cache = None
        self.GetView().SetTable(self)
        self.GetView().AutoSize()
        
    def rowIsDefault(self, row):
        if len(self.alts.alts) == 0: return 1
        if row == 0:
            return 0 if len(filter(lambda x: x['setdefault'] == 1, self.alts.alts)) > 0 else 1
        return self.alts.alts[row-1]['setdefault']

class logTrans(object):
    def __init__(self):
        self.weblognums = {
            "Found It" : 2,
            "Didn't Find It" : 3,
            "Write Note" : 4,
            "Needs Archived" : 7,
            "Needs Maintenance" : 45
            }
        self.opts = [
            "Found It",
            "Didn't Find It",
            "Write Note",
            "Needs Archived",
            "Needs Maintenance"
            ]
        
    def getWeb(self, ltype):
        ltype = ltype.title()
        if self.weblognums.has_key(ltype): return self.weblognums[ltype]
        else: return self.weblognums["Didn't Find It"]
    
    def getIdx(self, ltype):
        idx = 1
        ltype = ltype.title()
        try:
            idx = self.opts.index(ltype)
        except:
            pass
        return idx
    
    def getType(self, idx):
        retval = self.opts[1]
        try:
            retval = self.opts[idx]
        except:
            pass
        return retval

class geoicons(cache901.ui_xrc.xrcgeoIcons):
    def __init__(self):
        cache901.ui_xrc.xrcgeoIcons.__init__(self, None)
        isinstance(self.cito, wx.StaticBitmap)
        isinstance(self.earthcache, wx.StaticBitmap)
        isinstance(self.event, wx.StaticBitmap) 
        isinstance(self.geocoin, wx.StaticBitmap) 
        isinstance(self.letterboxHybrid, wx.StaticBitmap) 
        isinstance(self.locationless, wx.StaticBitmap) 
        isinstance(self.maze, wx.StaticBitmap) 
        isinstance(self.mega, wx.StaticBitmap) 
        isinstance(self.multi, wx.StaticBitmap) 
        isinstance(self.mystery, wx.StaticBitmap) 
        isinstance(self.projectApe, wx.StaticBitmap) 
        isinstance(self.traditional, wx.StaticBitmap) 
        isinstance(self.travelbug, wx.StaticBitmap) 
        isinstance(self.virtual, wx.StaticBitmap) 
        isinstance(self.webcam, wx.StaticBitmap) 
        isinstance(self.wherigo, wx.StaticBitmap)
        self.www_geocaching_com = xrc.XRCCTRL(self, "www_geocaching_com")
        isinstance(self.www_geocaching_com, wx.StaticBitmap)

    def __getitem__(self, key):
        if key == "Geocache|Cache In Trash Out Event":
            return self.cito.GetBitmap()
        elif key == "Geocache|Earthcache":
            return self.earthcache.GetBitmap()
        elif key == "Geocache|Event Cache":
            return self.event.GetBitmap()
        elif key == "Geocache|Letterbox Hybrid":
            return self.letterboxHybrid.GetBitmap()
        elif key == "Geocache|Mega-Event Cache":
            return self.mega.GetBitmap()
        elif key == "Geocache|Multi-cache":
            return self.multi.GetBitmap()
        elif key == "Geocache|Traditional Cache":
            return self.traditional.GetBitmap()
        elif key == "Geocache|Unknown Cache":
            return self.mystery.GetBitmap()
        elif key == "Geocache|Virtual Cache":
            return self.virtual.GetBitmap()
        elif key == "Geocache|Webcam Cache":
            return self.webcam.GetBitmap()
        elif key == "Geocache|Wherigo Cache":
            return self.wherigo.GetBitmap()
        elif key == "www.geocaching.com":
            return self.www_geocaching_com.GetBitmap()
        elif key == "appicon":
            if sys.platform == "win32":
                return wx.Icon(os.path.join(cache901.__path__[0].replace('%slibrary.zip' % os.sep, ''), 'shield.ico'), wx.BITMAP_TYPE_ICO)
            elif sys.platform == "darwin":
                return wx.Icon(os.path.join(os.sep.join(sys.argv[0].split(os.sep)[:-1]), 'shield.ico'), wx.BITMAP_TYPE_ICO)
            else:
                return wx.Icon(os.path.join(cache901.__path__[0], 'shield.ico'), wx.BITMAP_TYPE_ICO)
        elif key == "searchloc":
            return self.appicon.GetBitmap()
        else:
            return self.mystery.GetBitmap()
