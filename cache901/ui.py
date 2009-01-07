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
import shutil
import sys
import time
import zipfile

from urlparse import urlparse

import gpsbabel
import wx
import wx.xrc as xrc
import wx.html

import cache901
import cache901.dbobjects
import cache901.dbm
import cache901.gpxsource
import cache901.mapping
import cache901.options
import cache901.search
import cache901.sql
import cache901.ui_xrc
import cache901.util as util
import cache901.xml901

class Cache901UI(cache901.ui_xrc.xrcCache901UI, wx.FileDropTarget):
    def __init__(self, parent=None):
        cache901.ui_xrc.xrcCache901UI.__init__(self, parent)
        wx.FileDropTarget.__init__(self)
        self.SetDropTarget(self)

        self.geoicons = geoicons()
        self.logtrans = logTrans()
        self.SetIcon(self.geoicons["appicon"])
        self.dropfile = wx.FileDataObject()
        self.SetDataObject(self.dropfile)

        # do all the GUI config stuff - creating extra controls and binding objects to events
        self.createStatusBarSearchField()
        self.miscBinds()        
        self.bindButtonEvents()
        self.bindListItemSelectedEvents()
        self.setSashPositionsFromConfig()

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
        self.caches.Bind(wx.EVT_CONTEXT_MENU, self.OnPopupMenuCaches)
        self.points.Bind(wx.EVT_CONTEXT_MENU, self.OnPopupMenuWpts)
    

    def createStatusBarSearchField(self):
        # add the search field to the program's status bar
        rect = self.statusBar.GetFieldRect(1)
        self.searchlabel = wx.StaticText(self.statusBar, label="Search:", pos=(rect.x+8, rect.y+2))
        w,h = self.searchlabel.GetSizeTuple()
        self.search = wx.TextCtrl(self.statusBar, pos=(rect.x+5+w, rect.y+2), style=wx.WANTS_CHARS, size=(rect.width-15-w, rect.height-2))
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


    def bindMenuOptions(self):
        # bind the menu options to their event handlers
        menuOptions = [
                        (self.OnClose,       self.mnuFileExit),
                        (self.OnDbMaint,     self.mnuFileDbMaint),
                        (self.OnImportFile,  self.mnuFileImport),
                        (self.OnAbout,       self.mnuHelpAbout),
                        (self.OnSearchLocs,  self.mnuFileLocs),
                        (self.OnPrefs,       self.mnuFilePrefs),
                        (self.OnShowMap,     self.showMap),
                        (self.OnAddPhoto,    self.mnuAddPhoto),
                        (self.OnRemovePhoto, self.mnuRemovePhoto),
                        (self.OnSaveNotes,   self.mnuSaveNote),
                        (self.OnClearNotes,  self.mnuClearNote),
                        (self.OnLogCache,    self.mnuLogThisCache),
                        (self.OnSendToGPS,   self.mnuSendToGPS),
                        (self.OnCacheDay,    self.mnuPrefsCacheDay),
                        (self.OnGeoAccounts, self.mnuPrefsAccounts),
                        (self.OnGpxSync,     self.mnuGpxSync),
                        (self.OnGpxSources,  self.mnuGpxSources)
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
                           (self.OnSaveLog,         self.logSaveButton)
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


    def setSashPositionsFromConfig(self):
        #-----------------------------------------------------------------------------------------
        # The following code block is a prime candidate for refactoring out into a separate object
        #-----------------------------------------------------------------------------------------
        # read the config file and set all the splitter window sash positions to their previous values
        cfg = wx.Config.Get()
        isinstance(cfg, wx.Config)
        cfg.SetPath("/MainWin")
        if cfg.HasEntry("Width") and cfg.HasEntry("Height"):
            self.SetSize((cfg.ReadInt("Width"), cfg.ReadInt("Height")))
        if cfg.HasEntry("DetailSplitPos"):
            self.splitListsAndDetails.SetSashPosition(cfg.ReadInt("DetailSplitPos"))
            
        self.splitLists.SetSashPosition(cfg.ReadInt("ListSplitPos"), 370)
        self.descriptionSplitter.SetSashPosition(cfg.ReadInt("DescriptionSplitPos"),150)
        self.logsSplitter.SetSashPosition(cfg.ReadInt("LogSplitPos"), 150)
        self.picSplitter.SetSashPosition(cfg.ReadInt("PicSplitPos"), 300)


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
        self.trackableListCtrl.InsertColumn(0, "Travel Bug Name", width=w)
        
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
                img = wx.BitmapFromImage(wx.Image(os.sep.join([cache901.dbpath, fname])).Scale(64, 64))
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


    def loadData(self, params={}, wpt_params={}):
        self.caches.DeleteAllItems()
        self.caches.DeleteAllColumns()
        for i in ((0, "D", "5.00"), (1, "T", "5.00"), (2, "Cache Name", "QQQQQQQQQQQQQQQQQQQQ"), (3, "Dist", "QQQQQQ")):
            w, h = self.GetTextExtent(i[2])
            self.caches.InsertColumn(i[0], i[1], width=w)
        self.points.DeleteAllItems()

        if len(self.search.GetValue()) > 2:
            params["urlname"] = self.search.GetValue()
        for row in cache901.search.execSearch(params):
            cache_id = self.caches.Append((row[1], row[2], row[3], row[4]))
            self.caches.SetItemData(cache_id, row[0])
        if self.caches.GetItemCount() > 0:
            self.caches.Select(0)

        wpt_params['searchpat'] = self.search.GetValue()
        for row in cache901.util.getWaypoints(wpt_params):
            wpt_id = self.points.Append((row[1], row[2]))
            self.points.SetItemData(wpt_id, row[0])


    def updStatus(self):
        cache901.notify('%d Caches Displayed, %d Waypoints Displayed' % (self.caches.GetItemCount(), self.points.GetItemCount()))


    def OnDbMaint(self, evt):
        cache901.sql.maintdb()
        self.updStatus()
        
        
    def OnClose(self, evt):
        if wx.MessageBox("Are you sure you wish to exit?", "Really Exit?", wx.YES_NO | wx.CENTER, self) == wx.YES:
            #-----------------------------------------------------------------------------------------
            # The following code block is a prime candidate for refactoring out into a separate object
            #-----------------------------------------------------------------------------------------
            cfg=wx.Config.Get()
            isinstance(cfg, wx.Config)
            cfg.SetPath("/MainWin")
            cfg.WriteInt("ListSplitPos", self.splitLists.GetSashPosition())
            cfg.WriteInt("DetailSplitPos", self.splitListsAndDetails.GetSashPosition())
            cfg.WriteInt("DescriptionSplitPos", self.descriptionSplitter.GetSashPosition())
            cfg.WriteInt("LogSplitPos", self.logsSplitter.GetSashPosition())
            cfg.WriteInt("PicSplitPos", self.picSplitter.GetSashPosition())
            (w, h) = self.GetSize()
            cfg.WriteInt("Width", w)
            cfg.WriteInt("Height", h)
            try:
                self.geoicons.Destroy()
            except:
                pass
            self.Destroy()
        else:
            if isinstance(evt, wx.CloseEvent): evt.Veto()


    def OnLogToggle(self, evt):
        try:
            self.logText.SetValue(self.logText.GetValue().encode('rot13'))
        except:
            pass


    def OnHintsToggle(self, evt):
        try:
            self.hintText.SetValue(self.hintText.GetValue().encode('rot13'))
        except:
            self.hintText.SetValue(util.forceAscii(self.ld_cache.hint.hint).encode('rot13'))


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
        self.placedByText.SetLabel(self.ld_cache.placed_by[:25])
        self.ownerText.SetLabel(self.ld_cache.owner_name[:25])
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
        self.Enable()
        self.updStatus()
        self.caches.Enable()
        self.points.Enable()

    def OnLoadLog(self, evt):
        log = cache901.dbobjects.Log(evt.GetData())
        self.logText.SetEditable(log.finder in self.listGCAccounts())
        self.logType.Enable(self.logText.IsEditable())
        self.logDate.Enable(self.logText.IsEditable())
        self.logSaveButton.Enable(self.logText.IsEditable())
        self.logText.SetValue(log.log_entry)
        self.logDate.SetValue(wx.DateTimeFromTimeT(log.date))
        self.logType.Select(self.logtrans.getIdx(log.type))
        self.logCacherNameText.SetLabel(log.finder)
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
            cache901.sql.maintdb()
    
    
    def OnImportFile(self, evt):
        fdg = wx.FileDialog(self, "Select GPX File", style=wx.FD_DEFAULT_STYLE | wx.FD_MULTIPLE | wx.FD_FILE_MUST_EXIST | wx.FD_OPEN, wildcard="GPX Files (*.gpx)|*.gpx|Zip Files(*.zip)|*.zip|All Files (*.*)|*.*")
        cfg = wx.Config.Get()
        isinstance(cfg, wx.Config)
        cfg.SetPath("/Files")
        if cfg.HasEntry("LastImportDir"):
            fdg.SetDirectory(cfg.Read("LastImportDir"))
        if fdg.ShowModal() == wx.ID_OK:
            cfg.Write("LastImportDir", fdg.GetDirectory())
            for path in fdg.GetPaths():
                self.importSpecificFile(path, False)
            cache901.sql.maintdb()
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
                self.loadData(params)
        elif mtext == "Clear Search":
            self.search.SetValue("")
            self.loadData({})
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
            self.loadData(cache_params, wpt_params)
        else:
            params = cache901.search.loadSavedSearch(mtext)
            self.loadData(params)
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
        fdg = wx.FileDialog(self, "Select Image File", style=wx.FD_DEFAULT_STYLE | wx.FD_MULTIPLE | wx.FD_FILE_MUST_EXIST | wx.FD_OPEN, wildcard="Photo Files (*.jpg;*.jpeg;*.png)|*.jpg;*.jpeg;*.png|All Files (*.*)|*.*")
        cfg = wx.Config.Get()
        isinstance(cfg, wx.Config)
        cfg.SetPath("/Files")
        if cfg.HasEntry("LastPhotoDir"):
            fdg.SetDirectory(cfg.Read("LastPhotoDir"))
        if fdg.ShowModal() == wx.ID_OK:
            cfg.Write("LastPhotoDir", fdg.GetDirectory())
            for fname in fdg.GetPaths():
                dest = os.path.split(fname)[1]
                idx = 0
                while os.path.exists(os.sep.join([cache901.dbpath, dest])):
                    dest = "%06d-%s" % (idx, dest)
                fulldest = os.sep.join([cache901.dbpath, dest])
                cache901.notify('Copying file %s to %s' % (fname, fulldest))
                shutil.copyfile(fname, fulldest)
                self.ld_cache.photolist.names.append(dest)
            self.ld_cache.photolist.Save()
            cache901.db().commit()
        self.updPhotoList()
        self.updStatus()


    def OnSwitchPhoto(self, evt):
        idx = evt.GetImage()
        fname = os.sep.join([cache901.dbpath, self.ld_cache.photolist.names[idx]])
        sz = self.currPhoto.GetSize()
        self.currPhoto.SetBitmap(wx.BitmapFromImage(wx.Image(fname).Scale(sz.width, sz.height, wx.IMAGE_QUALITY_HIGH)))
        self.updStatus()


    def OnRemovePhoto(self, evt):
        if wx.MessageBox("This operation cannot be undone!\nContinue?", "Warning: About To Remove Data", wx.YES_NO) == wx.YES:
            idx = self.photoList.GetFirstSelected()
            fname = os.sep.join([cache901.dbpath, self.ld_cache.photolist.names[idx]])
            os.unlink(fname)
            del self.ld_cache.photolist.names[idx]
            self.ld_cache.photolist.Save()
            cache901.db().commit()
            self.updPhotoList()


    def OnLogCache(self, evt):
        log = cache901.dbobjects.Log(cache901.dbobjects.minint)
        log.cache_id = self.ld_cache.cache_id
        log.my_log = True
        log.date = time.mktime(datetime.datetime.now().timetuple())
        cur = cache901.db().cursor()
        cur.execute('select username from accounts where sitename="GeoCaching.com" and ispremium=1 and isteam=0')
        row = cur.fetchone()
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
        cfg = wx.Config.Get()
        cfg.SetPath('/PerMachine')
        if self.caches.GetFirstSelected() != -1:
            cache = cache901.dbobjects.Cache(self.caches.GetItemData(self.caches.GetFirstSelected()))
            ctp = 'cache'
        else:
            cache = cache901.dbobjects.Waypoint(self.points.GetItemData(self.points.GetFirstSelected()))
            ctp = 'waypoint'
        gpx = cache901.util.CacheToGPX(cache)
        cache901.notify('Sending %s "%s" to GPS' % (ctp, cache.name))
        gpsbabel.gps.setInGpx(gpx)
        gpsbabel.gps.write(cfg.Read('GPSPort', 'usb:'), cfg.Read('GPSType', 'nmea'), wpt=True, parseOutput=False)
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
            if mtext != '':
                day = cache901.dbobjects.CacheDay(mtext)
                day.Save()
            else:
                day = None
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
        cfg = wx.Config.Get()
        cfg.SetPath('/PerMachine')
        cache901.notify('Sending Cache Day "%s" to GPS' % (mtext, ))
        gpsbabel.gps.setInGpx(gpx)
        gpsbabel.gps.write(cfg.Read('GPSPort', 'usb:'), cfg.Read('GPSType', 'nmea'), wpt=True, route=True, parseOutput=False)
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
            mitems.append(menu.Append(-1, row[0]))
        return mitems


    def OnDropFiles(self, x, y, filenames):
        for filename in filenames:
            self.importSpecificFile(filename, False)
        cache901.sql.maintdb()
        self.updStatus()
            
            
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
