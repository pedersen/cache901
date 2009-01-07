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

import datetime
import time

import wx

import gpsbabel

import cache901
import cache901.dbobjects
import cache901.ui_xrc
import cache901.util
import cache901.validators

class SearchBox(cache901.ui_xrc.xrcSearchUI):
    def __init__(self, parent=None):
        cache901.ui_xrc.xrcSearchUI.__init__(self, parent=parent)
        self.splitterSave.SetValidator(cache901.validators.splitValidator("splitterSave"))
        self.splitterType.SetValidator(cache901.validators.splitValidator("splitterType"))
        self.splitRegions.SetValidator(cache901.validators.splitValidator("splitRegions"))
        
        self.w,h = self.GetTextExtent("QQQQQQQQQQQQQQQQQQQQ")
        self.cur = cache901.db().cursor()
    
        self.loadCacheContainers()
        self.loadCacheTypes()
        self.loadCountries()
        self.loadStates()
        self.loadSearchLocs()
        self.loadSavedSearches()
        
        self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.OnLoadSavedSearch, self.savedSearches)
        
        self.Bind(wx.EVT_CHECKBOX, self.OnCheckCountry, self.countriesCheck)
        self.Bind(wx.EVT_CHECKBOX, self.OnCheckState,   self.statesCheck)
        
        self.Bind(wx.EVT_CHOICE, self.OnCheckOrigin,       self.searchOrigin)
        
        self.Bind(wx.EVT_BUTTON, self.OnClearCacheContainers, self.btnClearContainers)
        self.Bind(wx.EVT_BUTTON, self.OnClearCacheTypes,      self.clearTypes)
        self.Bind(wx.EVT_BUTTON, self.OnClearCountries,       self.clearCountries)
        self.Bind(wx.EVT_BUTTON, self.OnClearStates,          self.clearStates)
        self.Bind(wx.EVT_BUTTON, self.OnSaveSearch,           self.saveSearch)
        
        self.searchName.Bind(wx.EVT_KEY_UP, self.OnChangeSearchName)
        
        self.distance.SetValidator(FloatValidator())
        
    def clearSearch(self, sname=""):
        self.searchName.SetValue(sname)
        self.saveSearch.Enable()
        self.maxResults.SetSelection(0)
        self.distance.Disable()
        self.distanceScale.Disable()
        self.distance.SetValue("")
        self.distanceScale.SetSelection(0)
        self.deselectList(self.countriesList)
        self.deselectList(self.statesList)
        self.statesCheck.SetValue(False)
        self.countriesCheck.SetValue(False)
        self.deselectList(self.cacheContainers)
        self.deselectList(self.cacheTypes)
        for i in ['notFoundByMe', 'found', 'notOwned', 'owned', 'foundLast7',
                  'notFound', 'hasBugs', 'updatedLast7', 'notActive',
                  'active', 'hasMyLogs', 'hasMyNotes', 'hasMyPhotos']:
            getattr(self, i).SetValue(False)
    
    def loadSearchLocs(self):
        self.searchOrigin.Clear()
        self.searchOrigin.Append("None")
        self.searchOrigin.Append("From GPS")
        for row in cache901.util.getSearchLocs():
            self.searchOrigin.Append(row['name'], row['wpt_id'])
        self.searchOrigin.SetSelection(0)
        
    def loadCacheTypes(self):
        self.cacheTypes.DeleteAllItems()
        self.cur.execute("select distinct type from caches order by type")
        for row in self.cur:
            self.cacheTypes.Append((row['type'], ))
        
    def loadCacheContainers(self):
        self.cacheContainers.DeleteAllItems()
        self.cur.execute("select distinct container from caches order by container")
        for row in self.cur:
            self.cacheContainers.Append((row['container'], ))
        
    def loadCountries(self):
        self.countriesList.DeleteAllItems()
        self.countriesList.DeleteAllColumns()
        self.countriesList.InsertColumn(0, "Country", width=self.w)
        self.cur.execute("select distinct country from caches order by country")
        for row in self.cur:
            self.countriesList.Append((row['country'], ))
            
    def loadStates(self):
        self.statesList.DeleteAllItems()
        self.statesList.DeleteAllColumns()
        self.statesList.InsertColumn(0, "State / Province", width=self.w)
        self.cur.execute("select distinct state from caches order by state")
        for row in self.cur:
            self.statesList.Append((row['state'], ))
        
    def loadSavedSearches(self):
        self.savedSearches.DeleteAllItems()
        self.savedSearches.DeleteAllColumns()
        self.savedSearches.InsertColumn(0, "Search Name", width = self.w)
        self.cur.execute("SELECT DISTINCT name FROM searches ORDER BY name")
        for row in self.cur:
            self.savedSearches.Append((row['name'], ))
    
    def OnLoadSavedSearch(self, evt):
        item = self.savedSearches.GetNextSelected(-1)
        if item != -1:
            sname = self.savedSearches.GetItemText(item)
            self.clearSearch(sname)
            params = loadSavedSearch(sname)
            for param in params.keys():
                if param == 'maxresults':
                    self.maxResults.SetSelection(self.maxResults.GetItems().index(params[param]))
                elif param == 'terrain':
                    cond, rating = params[param].split(" ")
                    self.terrainCond.SetSelection(self.terrainCond.GetItems().index(cond))
                    self.terrainRating.SetSelection(self.terrainRating.GetItems().index(rating))
                elif param == 'difficulty':
                    cond, rating = params[param].split(" ")
                    self.difficultyCond.SetSelection(self.difficultyCond.GetItems().index(cond))
                    self.difficultyRating.SetSelection(self.difficultyRating.GetItems().index(rating))
                elif param == 'searchOrigin':
                    self.searchOrigin.SetSelection(self.searchOrigin.GetItems().index(params[param]))
                    self.distance.Enable()
                    self.distanceScale.Enable()
                elif param == 'searchDist':
                    self.distance.SetValue(params[param])
                elif param == 'searchScale':
                    self.distanceScale.SetSelection(self.distanceScale.GetItems().index(params[param]))
                elif param == 'countries':
                    self.deselectList(self.countriesList)
                    self.deselectList(self.statesList)
                    self.countriesCheck.SetValue(True)
                    self.statesCheck.SetValue(False)
                    for country in params[param].split(","):
                        idx = self.countriesList.FindItem(-1, country)
                        if idx != -1: self.countriesList.Select(idx)
                elif param == 'states':
                    self.deselectList(self.countriesList)
                    self.deselectList(self.statesList)
                    self.countriesCheck.SetValue(False)
                    self.statesCheck.SetValue(True)
                    for state in params[param].split(","):
                        idx = self.statesList.FindItem(-1, state)
                        if idx != -1: self.statesList.Select(idx)
                elif param == 'types':
                    self.deselectList(self.cacheTypes)
                    for ctype in params[param].split(","):
                        idx = self.cacheTypes.FindItem(-1, ctype)
                        if idx != -1: self.cacheTypes.Select(idx)
                elif param == 'containers':
                    self.deselectList(self.cacheContainers)
                    for ctype in params[param].split(","):
                        idx = self.cacheContainers.FindItem(-1, ctype)
                        if idx != -1: self.cacheContainers.Select(idx)
                else:
                    for i in ['notFoundByMe', 'found', 'notOwned', 'owned', 'foundLast7',
                              'notFound', 'hasBugs', 'updatedLast7', 'notActive',
                              'active', 'hasMyLogs', 'hasMyNotes', 'hasMyPhotos']:
                        if param == i.lower():
                            getattr(self, i).SetValue(1 == int(params[param]))
    
    def OnSaveSearch(self, evt):
        sname = self.searchName.GetValue()
        self.cur.execute("DELETE FROM searches WHERE name=?", (sname, ))
        sparams = self.getSearchParams()
        for sparam in sparams.keys():
            self.cur.execute("INSERT INTO searches(name, param, value) VALUES(?, ?, ?)", (sname, sparam, sparams[sparam]))
        cache901.db().commit()
        self.loadSavedSearches()
    
    def getSearchParams(self):
        params = {}
        mridx = self.maxResults.GetSelection()
        if mridx != 0:
            params['maxresults'] = int(self.maxResults.GetItems()[mridx])
        params['terrain'] = '%s %s' % (self.terrainCond.GetItems()[self.terrainCond.GetSelection()],
                                       self.terrainRating.GetItems()[self.terrainRating.GetSelection()])
        params['difficulty'] = '%s %s' % (self.difficultyCond.GetItems()[self.difficultyCond.GetSelection()],
                                       self.difficultyRating.GetItems()[self.difficultyRating.GetSelection()])
        params['searchOrigin'] = self.searchOrigin.GetItems()[self.searchOrigin.GetSelection()]
        if params['searchOrigin'] == 'None':
            del params['searchOrigin']
        else:
            params['searchDist'] = self.distance.GetValue()
            if len(params['searchDist']) > 0:
                params['searchScale'] = self.distanceScale.GetItems()[self.distanceScale.GetSelection()]
            else:
                del params['searchDist']
        for i in ['notFoundByMe', 'found', 'notOwned', 'owned', 'foundLast7',
                  'notFound', 'hasBugs', 'updatedLast7', 'notActive',
                  'active', 'hasMyLogs', 'hasMyNotes', 'hasMyPhotos']:
            if getattr(self, i).GetValue(): params[i.lower()] = 1
        countries = []
        item = self.countriesList.GetNextSelected(-1)
        while item != -1:
            countries.append(self.countriesList.GetItemText(item))
            item = self.countriesList.GetNextSelected(item)
        if len(countries) > 0:
            params['countries'] = ",".join(countries)
        states = []
        item = self.statesList.GetNextSelected(-1)
        while item != -1:
            states.append(self.statesList.GetItemText(item))
            item = self.statesList.GetNextSelected(item)
        if len(states) > 0:
            params['states'] = ",".join(states)
        types = []
        item = self.cacheTypes.GetNextSelected(-1)
        while item != -1:
            types.append(self.cacheTypes.GetItemText(item))
            item = self.cacheTypes.GetNextSelected(item)
        if len(types) > 0:
            params['types'] = ",".join(types)
        containers = []
        item = self.cacheContainers.GetNextSelected(-1)
        while item != -1:
            containers.append(self.cacheContainers.GetItemText(item))
            item = self.cacheContainers.GetNextSelected(item)
        if len(containers) > 0:
            params['containers'] = ",".join(containers)
            
        return params
    
    def OnCheckOrigin(self, evt):
        if self.searchOrigin.GetSelection() != 0:
            self.distance.Enable()
            self.distanceScale.Enable()
        else:
            self.distance.Disable()
            self.distanceScale.Disable()
            self.distance.SetValue("")
    
    def OnCheckCountry(self, evt):
        pass
        co = self.countriesCheck.GetValue()
        if co:
            self.statesCheck.SetValue(False)
            self.statesList.Disable()
            self.countriesList.Enable()
            self.deselectList(self.statesList)
        else:
            self.countriesList.Disable()
            self.deselectList(self.countriesList)
    
    def OnCheckState(self, evt):
        st = self.statesCheck.GetValue()
        if st:
            self.statesList.Enable()
            self.countriesList.Disable()
            self.countriesCheck.SetValue(False)
            self.deselectList(self.countriesList)
        else:
            self.statesList.Disable()
            self.deselectList(self.statesList)
    
    def OnClearCacheTypes(self, evt):
        self.deselectList(self.cacheTypes)
    
    def OnClearCacheContainers(self, evt):
        self.deselectList(self.cacheContainers)
    
    def OnClearCountries(self, evt):
        self.deselectList(self.countriesList)
    
    def OnClearStates(self, evt):
        self.deselectList(self.statesList)
    
    def OnChangeSearchName(self, evt):
        val = self.searchName.GetValue()
        if val != None and len(val) > 0:
            self.saveSearch.Enable()
        else:
            self.saveSearch.Disable()
    
    def deselectList(self, wxlist):
        lid = wxlist.GetFirstSelected()
        while lid != -1:
            wxlist.Select(lid, False)
            lid = wxlist.GetFirstSelected()
            
    def forWingIde(self):
        isinstance(self.splitterSave, wx.SplitterWindow)
        isinstance(self.savedSearches, wx.ListCtrl)
        isinstance(self.searchName, wx.TextCtrl)
        isinstance(self.maxResults, wx.Choice)
        isinstance(self.terrainCond, wx.Choice)
        isinstance(self.terrainRating, wx.Choice)
        isinstance(self.difficultyCond, wx.Choice)
        isinstance(self.difficultyRating, wx.Choice)
        isinstance(self.searchOrigin, wx.Choice)
        isinstance(self.distance, wx.TextCtrl)
        isinstance(self.distanceScale, wx.Choice)
        isinstance(self.splitterType, wx.SplitterWindow)
        isinstance(self.cacheTypes, wx.ListCtrl)
        isinstance(self.clearTypes, wx.Button)
        isinstance(self.cacheContainers, wx.ListCtrl)
        isinstance(self.btnClearContainers, wx.Button)
        isinstance(self.notFoundByMe, wx.CheckBox)
        isinstance(self.notFound, wx.CheckBox)
        isinstance(self.found, wx.CheckBox)
        isinstance(self.notOwned, wx.CheckBox)
        isinstance(self.owned, wx.CheckBox)
        isinstance(self.foundLast7, wx.CheckBox)
        isinstance(self.notFound, wx.CheckBox)
        isinstance(self.hasBugs, wx.CheckBox)
        isinstance(self.updatedLast7, wx.CheckBox)
        isinstance(self.notActive, wx.CheckBox)
        isinstance(self.active, wx.CheckBox)
        isinstance(self.hasMyLogs, wx.CheckBox)
        isinstance(self.hasMyNotes, wx.CheckBox)
        isinstance(self.hasMyPhotos, wx.CheckBox)
        isinstance(self.splitRegions, wx.SplitterWindow)
        isinstance(self.countriesCheck, wx.CheckBox)
        isinstance(self.countriesList, wx.ListCtrl)
        isinstance(self.clearCountries, wx.Button)
        isinstance(self.statesCheck, wx.CheckBox)
        isinstance(self.statesList, wx.ListCtrl)
        isinstance(self.clearStates, wx.Button)
        isinstance(self.saveSearch, wx.Button)

class FloatValidator(wx.PyValidator):
    def __init__(self):
        wx.PyValidator.__init__(self)
        self.Bind(wx.EVT_CHAR, self.OnChar)
    
    def Clone(self):
        return FloatValidator()
    
    def TransferToWindow(self):
        return True
    
    def TransferFromWindow(self):
        return True
    
    def Validate(self, win):
        return True
    
    def OnChar(self, evt):
        textctrl = self.GetWindow()
        try:
            key = chr(evt.GetKeyCode())
            v = "%s%s" % (textctrl.GetValue(), key)
            f = float(v)
            if f >= 0:
                textctrl.SetBackgroundColour(wx.SystemSettings_GetColour(wx.SYS_COLOUR_WINDOW))
                textctrl.Refresh()
                evt.Skip()
            else:
                textctrl.SetBackgroundColour("red")
                textctrl.Refresh()
        except ValueError:
                textctrl.SetBackgroundColour("red")
                textctrl.Refresh()

def loadSavedSearch(sname):
    params = {}
    cur = cache901.db().cursor()
    cur.execute("SELECT name, param, value FROM searches WHERE name = ?", (sname, ))
    for row in cur:
        params[row['param']] = row['value']
    return params

def execSearch(params):
    seconds = 86400*7 # Number of seconds in a week
    now = int(time.time())
    isinstance(params, dict)
    query = "select cache_id, difficulty, terrain, url_name, 0 as distance, name from caches "
    where = []
    sqlparams = []
    order_by = "order by url_name"
    if params.has_key('ids'):
        query = "select cache_id, difficulty, terrain, url_name, 0 as distance, name, (select cache_order from cacheday as cd where cd.cache_id=c.cache_id and cd.dayname='%s') as cache_order  from caches as c " % params['dayname']
        order_by = "order by cache_order"
        where.append('cache_id in (%s)' % ",".join(map(lambda x: '?', params['ids'])))
        sqlparams.extend(params['ids'])
    if params.has_key("urlname"):
        sname = '%%%s%%' % params['urlname'].replace('*', '%').lower()
        where.append('lower(url_name) like ? or lower(name) like ?')
        sqlparams.append(sname)
        sqlparams.append(sname)
    if params.has_key('terrain'):
        vals=params['terrain'].split(' ')
        where.append('terrain %s ?' % vals[0])
        sqlparams.append(vals[1])
    if params.has_key('difficulty'):
        vals=params['difficulty'].split(' ')
        where.append('difficulty %s ?' % vals[0])
        sqlparams.append(vals[1])
    if params.has_key("searchDist"):
        dist = float(params["searchDist"])
    else:
        dist = 12000 # 12,000 miles, roughly one half the circumference of the earth at the equator. *better* be enough
    if params.has_key("searchScale"):
        if params["searchScale"] != "mi":
            dist = dist * 1.61
    else: params["searchScale"] = "mi"
    if params.has_key("searchOrigin"):
        org = params["searchOrigin"]
        if org == "From GPS":
            cfg = wx.Config.Get()
            cfg.SetPath('/PerMachine')
            gpstype = cfg.Read('GPSType', 'nmea')
            gpsport = cfg.Read('GPSPort', 'USB')
            cache901.notify('Retrieving current GPS position')
            loc = gpsbabel.gps.getCurrentGpsLocation(gpsport, gpstype)
        else:
            wpt_id = cache901.util.getSearchLocs(org).next()[0]
            loc = cache901.dbobjects.Waypoint(wpt_id)
        where.append('distance(lat, lon, ?, ?) <= ?')
        sqlparams.append(float(loc.lat))
        sqlparams.append(float(loc.lon))
        sqlparams.append(dist)
        query = "select cache_id, difficulty, terrain, url_name, cast(distance(lat, lon, ?, ?) * ? as text) || %s as distance from caches " % (params["searchScale"])
        if params.has_key("searchScale") and params["searchScale"] != "mi":
            scale = 1.61
        else:
            scale = 1.0
        sqlparams.insert(0, scale)
        sqlparams.insert(0, float(loc.lon))
        sqlparams.insert(0, float(loc.lat))
        order_by = "order by distance"
        cache901.notify("Found location")
    if params.has_key('countries'):
        countries = params['countries'].split(',')
        where.append('country in (%s)' % ','.join(map(lambda x: '?', countries)))
        sqlparams.extend(countries)
    if params.has_key('states'):
        states = params['states'].split(',')
        where.append('state in (%s)' % ','.join(map(lambda x: '?', states)))
        sqlparams.extend(states)
    if params.has_key('types'):
        types = params['types'].split(',')
        where.append('type in (%s)' % ','.join(map(lambda x: '?', types)))
        sqlparams.extend(types)
    if params.has_key('containers'):
        containers = params['containers'].split(',')
        where.append('container in (%s)' % ','.join(map(lambda x: '?', containers)))
        sqlparams.extend(containers)
    if params.has_key('notFoundByMe'):
        where.append("cache_id not in (select cache_id from logs where lower(type)='found it' and finder in (select username from accounts))")
    if params.has_key('found'):
        where.append("cache_id in (select cache_id from logs where lower(type)='found it' and finder in (select username from accounts))")
    if params.has_key('notOwned'):
        where.append('owner_name not in (select username from accounts)')
    if params.has_key('owned'):
        where.append('owner_name in (select username from accounts)')
    if params.has_key('foundLast7'):
        where.append("cache_id in (select distinct cache_id from logs where date >= ? and logs.cache_id in (select distinct cache_id from logs where type='Found it'))")
        sqlparams.append(now-seconds)
    if params.has_key('notFound'):
        where.append("cache_id not in (select distinct cache_id from logs where type='Found it')")
    if params.has_key('updatedLast7'):
        where.append('cache_id in (select distinct cache_id from logs where date >= ?')
        sqlparams.append(now-seconds)
    if params.has_key('hasBugs'):
        where.append("cache_id in (select distinct cache_id from travelbugs)")
    if params.has_key('notActive'):
        where.append("archived = 1")
    if params.has_key('active'):
        where.append("available = 1")
    if params.has_key('hasmylogs'):
        where.append("cache_id in (select cache_id from logs where finder in (select username from accounts))")
    if params.has_key('hasmynotes'):
        where.append('cache_id in (select cache_id from notes)')
    if params.has_key('hasmyphotos'):
        where.append('cache_id in (select cache_id from photos)')
    if len(where) > 0:
        where_clause = 'where %s' % " and ".join(where)
    else:
        where_clause = ""
    if params.has_key('maxresults'):
        limit = "limit ?"
        sqlparams.append(int(params['maxresults']))
    else:
        limit = ""
    fquery = "%s %s %s %s" % (query, where_clause, order_by, limit)
    cur = cache901.db().cursor()
    cur.execute(fquery, sqlparams)
    for row in cur:
        yield row