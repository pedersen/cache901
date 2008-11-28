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

# @todo: Add double-clicking to load a cache

import sys
import os
import datetime
from urlparse import urlparse

import wx
import wx.xrc as xrc
import wx.html

import cache901
import cache901.ui_xrc
import cache901.dbobjects
import cache901.util as util
import cache901.xml901
import cache901.dbm
import cache901.options
import cache901.search
import cache901.mapping

class Cache901UI(cache901.ui_xrc.xrcCache901UI):
    def __init__(self, parent=None):
        cache901.ui_xrc.xrcCache901UI.__init__(self, parent)
        self.geoicons = geoicons()
        self.SetIcon(self.geoicons["appicon"])
        self.clearAllGui()

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

        self.Bind(wx.EVT_CLOSE,  self.OnClose)

        self.Bind(wx.EVT_MENU,   self.OnClose,      self.mnuFileExit)
        self.Bind(wx.EVT_MENU,   self.OnImportFile, self.mnuFileImport)
        self.Bind(wx.EVT_MENU,   self.OnAbout,      self.mnuHelpAbout)
        self.Bind(wx.EVT_MENU,   self.OnSearchLocs, self.mnuFileLocs)
        self.Bind(wx.EVT_MENU,   self.OnPrefs,      self.mnuFilePrefs)
        self.Bind(wx.EVT_MENU,   self.OnShowMap,    self.showMap)

        self.Bind(wx.EVT_BUTTON, self.OnHintsToggle, self.hintsCoding)
        self.Bind(wx.EVT_BUTTON, self.OnLogToggle,   self.encText)

        self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.OnLoadCache, self.caches)
        self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.OnLoadWpt,   self.points)
        self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.OnLoadLog,   self.logList)

        self.search.Bind(wx.EVT_KEY_UP, self.OnChangeSearch)

        cfg=wx.Config.Get()
        isinstance(cfg, wx.Config)
        cfg.SetPath("/MainWin")
        if cfg.HasEntry("Width") and cfg.HasEntry("Height"):
            self.SetSize((cfg.ReadInt("Width"), cfg.ReadInt("Height")))
        if cfg.HasEntry("DetailSplitPos"):
            self.splitListsAndDetails.SetSashPosition(cfg.ReadInt("DetailSplitPos"))
        self.splitLists.SetSashPosition(cfg.ReadInt("ListSplitPos"), 370)
        self.splitLogsAndBugs.SetSashPosition(cfg.ReadInt("BugLogSplitPos"), 200)
        self.splitLogsandLog.SetSashPosition(cfg.ReadInt("LogDateLogSplitPos"), 200)
        
        self.logList.DeleteAllColumns()
        w,h = self.GetTextExtent("QQQQ/QQ/QQQQQ")
        self.logList.InsertColumn(0, "Log Date", width=w)
        w,h = self.GetTextExtent("QQQQQQQ")
        self.points.InsertColumn(0, "Wpt Name", width=w)
        w,h = self.GetTextExtent("QQQQQQQQQQQQQQQQQQ")
        self.points.InsertColumn(1, "Wpt Desc", width=w)
        self.loadData()
        self.updSearchMenu()

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

    def loadData(self, params={}):
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

        for row in cache901.util.getWaypoints(self.search.GetValue()):
            wpt_id = self.points.Append((row[1], row[2]))
            self.points.SetItemData(wpt_id, row[0])

        self.ld_cache = None
        self.updStatus()

    def updStatus(self):
        cache901.notify('%d Caches Displayed, %d Waypoints Displayed' % (self.caches.GetItemCount(), self.points.GetItemCount()))

    def OnClose(self, evt):
        if wx.MessageBox("Are you sure you wish to exit?", "Really Exit?", wx.YES_NO | wx.CENTER, self) == wx.YES:
            cfg=wx.Config.Get()
            isinstance(cfg, wx.Config)
            cfg.SetPath("/MainWin")
            cfg.WriteInt("ListSplitPos", self.splitLists.GetSashPosition())
            cfg.WriteInt("DetailSplitPos", self.splitListsAndDetails.GetSashPosition())
            cfg.WriteInt("BugLogSplitPos", self.splitLogsAndBugs.GetSashPosition())
            cfg.WriteInt("LogDateLogSplitPos", self.splitLogsandLog.GetSashPosition())
            (w, h) = self.GetSize()
            cfg.WriteInt("Width", w)
            cfg.WriteInt("Height", h)
            self.geoicons.Destroy()
            self.Destroy()
        else:
            if isinstance(evt, wx.CloseEvent): evt.Veto()

    def OnLogToggle(self, evt):
        try:
            self.logEntry.SetValue(self.logEntry.GetValue().encode('rot13'))
        except:
            self.logEntry.SetValue(cache901.util.forceAscii(self.ld_cache.hint.hint))

    def OnHintsToggle(self, evt):
        try:
            self.hints.SetValue(self.hints.GetValue().encode('rot13'))
        except:
            self.hints.SetValue(util.forceAscii(self.ld_cache.hint.hint))

    def clearAllGui(self):
        self.ld_cache = None
        # Set up travel bug listings
        self.travelbugs.DeleteAllColumns()
        self.travelbugs.DeleteAllItems()
        w,h = self.GetTextExtent("QQQQQQQQQQQQQQ")
        self.travelbugs.InsertColumn(0, "Travel Bug Name", width=w)
        # set up log listings
        self.logList.DeleteAllItems()
        self.logEntry.SetValue("")
        self.logDate.SetValue("")
        self.logType.SetValue("")
        self.logMine.SetValue(False)
        self.logMineFound.SetValue(False)
        self.cacheSiteIcon.SetBitmap(self.geoicons["Unknown"])
        self.cacheSiteName.SetLabel("")
        self.waypointId.SetLabel("")
        self.urlName.SetValue("")
        self.urlDesc.SetValue("")
        self.difficulty.SetValue("")
        self.cacheType.SetValue("")
        self.terrain.SetValue("")
        self.available.SetValue(False)
        self.archived.SetValue(False)
        self.lat.SetValue("")
        self.lon.SetValue("")
        self.cacheUrl.URL = ""
        self.cacheUrl.Label = ""
        self.cacheUrl.Refresh()
        self.placedBy.SetValue("")
        self.owner.SetValue("")
        self.state.SetValue("")
        self.country.SetValue("")
        self.hints.SetValue("")
        self.cacheDescShort.SetPage("")
        self.cacheDescLong.SetPage("")
        self.containerIcon.SetBitmap(self.geoicons["Unknown"])
        self.containerType.SetLabel("")
        self.Layout()

    def OnLoadWpt(self, evt):
        self.clearAllGui()
        self.ld_cache = cache901.dbobjects.Waypoint(evt.GetData())
        self.waypointId.SetLabel(self.ld_cache.name)
        self.waypointId.SetSize(self.GetTextExtent(self.ld_cache.name))
        self.waypointId.GetContainingSizer().Layout()
        self.urlName.SetValue(self.ld_cache.name)
        self.lat.SetValue(util.latToDMS(self.ld_cache.lat))
        self.lon.SetValue(util.lonToDMS(self.ld_cache.lon))
        self.cacheDescLong.SetPage('<p>' + self.ld_cache.comment.replace('\n', '</p><p>') + '</p>')

    def OnLoadCache(self, evt):
        self.ld_cache = cache901.dbobjects.Cache(evt.GetData())
        # Set up travel bug listings
        self.travelbugs.DeleteAllItems()
        for bug in self.ld_cache.bugs:
            self.travelbugs.Append((bug.name, ))
        # set up log listings
        self.logList.DeleteAllItems()
        for log in self.ld_cache.logs:
            s=datetime.date.fromtimestamp(log.date).isoformat()
            log_id = self.logList.Append((s, ))
            self.logList.SetItemData(log_id, log.id)
        self.logEntry.SetValue("")
        self.logDate.SetValue("")
        self.logType.SetValue("")
        self.logMine.SetValue(False)
        self.logMineFound.SetValue(False)
        cn = urlparse(self.ld_cache.url)[1]
        bmp = wx.ImageFromBitmap(self.geoicons[cn]).Scale(16,16)
        self.cacheSiteIcon.SetBitmap(wx.BitmapFromImage(bmp))
        self.cacheSiteName.SetLabel(cn)
        self.waypointId.SetLabel(self.ld_cache.name)
        self.waypointId.SetSize(self.GetTextExtent(self.ld_cache.name))
        self.waypointId.GetContainingSizer().Layout()
        self.urlName.SetValue(self.ld_cache.url_name)
        self.urlDesc.SetValue(self.ld_cache.url_desc)
        self.difficulty.SetValue(str(self.ld_cache.difficulty))
        self.cacheType.SetValue(self.ld_cache.type.split("|")[-1])
        self.terrain.SetValue(str(self.ld_cache.terrain))
        self.available.SetValue(self.ld_cache.available)
        self.archived.SetValue(self.ld_cache.archived)
        self.lat.SetValue(util.latToDMS(self.ld_cache.lat))
        self.lon.SetValue(util.lonToDMS(self.ld_cache.lon))
        self.cacheUrl.URL = self.ld_cache.url
        self.cacheUrl.Label = self.ld_cache.url
        self.cacheUrl.Refresh()
        self.placedBy.SetValue(self.ld_cache.placed_by)
        self.owner.SetValue(self.ld_cache.owner_name)
        self.state.SetValue(self.ld_cache.state)
        self.country.SetValue(self.ld_cache.country)
        try:
            self.hints.SetValue(self.ld_cache.hint.hint.encode('rot13'))
        except:
            self.hints.SetValue(self.ld_cache.hint.hint)
        if self.ld_cache.short_desc_html:
            self.cacheDescShort.SetPage(self.ld_cache.short_desc)
        else:
            self.cacheDescShort.SetPage('<p>' + self.ld_cache.short_desc.replace('\n', '</p><p>') + '</p>')
        if self.ld_cache.long_desc_html:
            self.cacheDescLong.SetPage(self.ld_cache.long_desc)
        else:
            self.cacheDescLong.SetPage('<p>' + self.ld_cache.long_desc.replace('\n', '</p><p>') + '</p>')
        bmp = wx.ImageFromBitmap(self.geoicons[self.ld_cache.type]).Scale(16,16)
        self.containerIcon.SetBitmap(wx.BitmapFromImage(bmp))
        self.containerType.SetLabel(self.ld_cache.type.split("|")[-1])
        self.Layout()

    def OnLoadLog(self, evt):
        log = cache901.dbobjects.Log(evt.GetData())
        self.logEntry.SetValue(log.log_entry)
        self.logDate.SetValue(datetime.date.fromtimestamp(log.date).isoformat())
        self.logType.SetValue(log.type)
        self.logMine.SetValue(log.my_log)
        self.logMineFound.SetValue(log.my_log_found)

    def OnImportFile(self, evt):
        fdg = wx.FileDialog(self, "Select GPX File", style=wx.FD_DEFAULT_STYLE | wx.FD_MULTIPLE | wx.FD_FILE_MUST_EXIST | wx.FD_OPEN, wildcard="GPX Files (*.gpx)|*.gpx|All Files (*.*)|*.*")
        cfg = wx.Config.Get()
        isinstance(cfg, wx.Config)
        cfg.SetPath("/Files")
        if cfg.HasEntry("LastImportDir"):
            fdg.SetDirectory(cfg.Read("LastImportDir"))
        if fdg.ShowModal() == wx.ID_OK:
            cfg.Write("LastImportDir", fdg.GetDirectory())
            for path in fdg.GetPaths():
                infile = open(path)
                parser = cache901.xml901.XMLParser()
                parser.parse(infile)
                cache901.notify('Completed processing %s' % path)
            cache901.dbm.scrub()
            self.loadData()

    def OnChangeSearch(self, evt):
        if len(self.search.GetValue()) > 2 or len(self.search.GetValue()) == 0:
            self.loadData()

    def OnAbout(self, evt):
        abt = cache901.ui_xrc.xrcAboutBox(self)
        abt.version.SetLabel("Version: %s" % cache901.version)
        abt.SetIcon(self.geoicons["appicon"])
        abt.ShowModal()
    
    def OnSearchLocs(self, evt):
        opts = cache901.options.OptionsUI(self)
        opts.showSearch()
    
    def OnPrefs(self, evt):
        opts = cache901.options.OptionsUI(self)
        opts.showGeneral()
    
    def OnSearch(self, evt):
        isinstance(evt, wx.CommandEvent)
        self.search.SetValue("")
        itemid = evt.GetId()
        item = self.GetMenuBar().FindItemById(itemid)
        mtext = item.GetLabel()
        if mtext == "Advanced Search":
            dlg = cache901.search.SearchBox(self)
            if dlg.ShowModal() == wx.ID_OK:
                params = dlg.getSearchParams()
                self.loadData(params)
        elif mtext == "Clear Search":
            self.search.SetValue("")
            self.loadData({})
        else:
            params = cache901.search.loadSavedSearch(mtext)
            self.loadData(params)
        self.updSearchMenu()
        
    def OnShowMap(self, evt):
        i = 0
        cacheids = []
        while i < self.caches.GetItemCount():
            cacheids.append(self.caches.GetItemData(i))
            i = i + 1
        mapui = cache901.mapping.MapUI(self, cacheids)
        mapui.ShowModal()
        
    def forWingIde(self):
        isinstance(self.cacheSiteIcon, wx.StaticBitmap)
        isinstance(self.cacheSiteName, wx.StaticText)
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
        isinstance(self.cacheType, wx.TextCtrl)
        isinstance(self.terrain, wx.TextCtrl)
        isinstance(self.available, wx.CheckBox)
        isinstance(self.archived, wx.CheckBox)
        isinstance(self.lat, wx.TextCtrl)
        isinstance(self.lon, wx.TextCtrl)
        isinstance(self.placedBy, wx.TextCtrl)
        isinstance(self.owner, wx.TextCtrl)
        isinstance(self.state, wx.TextCtrl)
        isinstance(self.country, wx.TextCtrl)
        isinstance(self.hints, wx.TextCtrl)
        isinstance(self.hintsCoding, wx.Button)
        isinstance(self.travelbugs, wx.ListCtrl)
        isinstance(self.cacheDescShort, wx.html.HtmlWindow)
        isinstance(self.cacheDescLong, wx.html.HtmlWindow)
        isinstance(self.logDate, wx.TextCtrl)
        isinstance(self.logType, wx.TextCtrl)
        isinstance(self.logMine, wx.CheckBox)
        isinstance(self.logMineFound, wx.CheckBox)
        isinstance(self.logList, wx.ListCtrl)
        isinstance(self.logEntry, wx.TextCtrl)
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
