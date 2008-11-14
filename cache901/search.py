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

import cache901
import cache901.ui_xrc
import cache901.util

class SearchBox(cache901.ui_xrc.xrcSearchUI):
    def __init__(self, parent=None):
        cache901.ui_xrc.xrcSearchUI.__init__(self, parent=parent)
        
        self.w,h = self.GetTextExtent("QQQQQQQQQQQQQQQQQQQQ")
        self.cur = cache901.db().cursor()
    
        self.loadCacheContainers()
        self.loadCacheTypes()
        self.loadCountries()
        self.loadStates()
        self.loadSearchLocs()
        self.loadSavedSearches()
        
        begin = wx.DateTime.Now()
        self.endDate.SetValue(begin)
        begin = begin - wx.DateSpan(30, 0, 0, 0)
        self.beginDate.SetValue(begin)
        
        self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.OnLoadSavedSearch, self.savedSearches)
        
        self.Bind(wx.EVT_CHECKBOX, self.OnCheckCountry, self.countriesCheck)
        self.Bind(wx.EVT_CHECKBOX, self.OnCheckState,   self.statesCheck)
        
        self.Bind(wx.EVT_CHOICE, self.OnCheckDates,        self.rangeChoice)
        self.Bind(wx.EVT_CHOICE, self.OnCheckOrigin,       self.searchOrigin)
        
        self.Bind(wx.EVT_BUTTON, self.OnClearCacheContainers, self.btnClearContainers)
        self.Bind(wx.EVT_BUTTON, self.OnClearCacheTypes,      self.clearTypes)
        self.Bind(wx.EVT_BUTTON, self.OnClearCountries,       self.clearCountries)
        self.Bind(wx.EVT_BUTTON, self.OnClearStates,          self.clearStates)
        self.Bind(wx.EVT_BUTTON, self.OnSaveSearch,           self.saveSearch)
        
        self.searchName.Bind(wx.EVT_KEY_UP, self.OnChangeSearchName)
        
        self.distance.SetValidator(FloatValidator())
        self.beginDate.SetValidator(DateValidator(self.beginDate, self.endDate))
        self.endDate.SetValidator(DateValidator(self.beginDate, self.endDate))
        
    def loadSearchLocs(self):
        self.searchOrigin.Clear()
        self.searchOrigin.Append("None")
        self.searchOrigin.Append("From GPS")
        for row in cache901.util.getSearchLocs():
            self.searchOrigin.Append(row[1], row[0])
        self.searchOrigin.SetSelection(0)
        
    def loadCacheTypes(self):
        self.cacheTypes.DeleteAllItems()
        self.cacheTypes.DeleteAllColumns()
        self.cacheTypes.InsertColumn(0, "Cache Types", width=self.w)
        self.cur.execute("select distinct type from caches order by type")
        for row in self.cur:
            self.cacheTypes.Append((row[0], ))
        
    def loadCacheContainers(self):
        self.cacheContainers.DeleteAllItems()
        self.cacheContainers.DeleteAllColumns()
        self.cacheContainers.InsertColumn(0, "Cache Containers", width=self.w)
        self.cur.execute("select distinct container from caches order by container")
        for row in self.cur:
            self.cacheContainers.Append((row[0], ))
        
    def loadCountries(self):
        self.countriesList.DeleteAllItems()
        self.countriesList.DeleteAllColumns()
        self.countriesList.InsertColumn(0, "Country", width=self.w)
        self.cur.execute("select distinct country from caches order by country")
        for row in self.cur:
            self.countriesList.Append((row[0], ))
            
    def loadStates(self):
        self.statesList.DeleteAllItems()
        self.statesList.DeleteAllColumns()
        self.statesList.InsertColumn(0, "State / Province", width=self.w)
        self.cur.execute("select distinct state from caches order by state")
        for row in self.cur:
            self.statesList.Append((row[0], ))
        
    def loadSavedSearches(self):
        self.savedSearches.DeleteAllItems()
        self.savedSearches.DeleteAllColumns()
        self.savedSearches.InsertColumn(0, "Search Name", width = self.w)
        self.cur.execute("SELECT DISTINCT name FROM searches ORDER BY name")
        for row in self.cur:
            self.savedSearches.Append((row[0], ))
    
    def OnLoadSavedSearch(self, evt):
        item = self.savedSearches.GetNextSelected(-1)
        if item != -1:
            sname = self.savedSearches.GetItemText(item)
            self.searchName.SetValue(sname)
            self.saveSearch.Enable()
            self.maxResults.SetSelection(0)
            self.distance.Disable()
            self.distanceScale.Disable()
            self.distance.SetValue("")
            self.distanceScale.SetSelection(0)
            self.rangeChoice.SetSelection(0)
            begin = wx.DateTime.Now()
            self.endDate.SetValue(begin)
            begin = begin - wx.DateSpan(30, 0, 0, 0)
            self.beginDate.SetValue(begin)
            self.deselectList(self.countriesList)
            self.deselectList(self.statesList)
            self.statesCheck.SetValue(False)
            self.countriesCheck.SetValue(False)
            self.deselectList(self.cacheContainers)
            self.deselectList(self.cacheTypes)
            for i in ['notFoundByMe', 'found', 'notOwned', 'owned', 'genAvail',
                      'memAvail', 'notIgnored', 'ignored', 'foundLast7',
                      'notFound', 'hasBugs', 'updatedLast7', 'notActive',
                      'active']:
                getattr(self, i).SetValue(False)
            self.cur.execute("SELECT name, param, value FROM searches WHERE name = ?", (sname, ))
            for row in self.cur:
                if row[1] == 'maxresults':
                    self.maxResults.SetSelection(self.maxResults.GetItems().index(row[2]))
                elif row[1] == 'terrain':
                    cond, rating = row[2].split(" ")
                    self.terrainCond.SetSelection(self.terrainCond.GetItems().index(cond))
                    self.terrainRating.SetSelection(self.terrainRating.GetItems().index(rating))
                elif row[1] == 'difficulty':
                    cond, rating = row[2].split(" ")
                    self.difficultyCond.SetSelection(self.difficultyCond.GetItems().index(cond))
                    self.difficultyRating.SetSelection(self.difficultyRating.GetItems().index(rating))
                elif row[1] == 'searchOrigin':
                    self.searchOrigin.SetSelection(self.searchOrigin.GetItems().index(row[2]))
                    self.distance.Enable()
                    self.distanceScale.Enable()
                elif row[1] == 'searchDist':
                    self.distance.SetValue(row[2])
                elif row[1] == 'searchScale':
                    self.distanceScale.SetSelection(self.distanceScale.GetItems().index(row[2]))
                elif row[1] == 'daterange':
                    self.rangeChoice.SetSelection(self.rangeChoice.GetItems().index(row[2]))
                    val = (self.rangeChoice.GetSelection() == 4)
                    self.beginDate.Enable(val)
                    self.endDate.Enable(val)
                elif row[1] == 'begindate':
                    dt = datetime.datetime.fromtimestamp(int(row[2]))
                    time_t = time.mktime(dt.timetuple())
                    self.beginDate.SetValue(wx.DateTimeFromTimeT(time_t))
                elif row[1] == 'enddate':
                    dt = datetime.datetime.fromtimestamp(int(row[2]))
                    time_t = time.mktime(dt.timetuple())
                    self.endDate.SetValue(wx.DateTimeFromTimeT(time_t))
                elif row[1] == 'countries':
                    self.deselectList(self.countriesList)
                    self.deselectList(self.statesList)
                    self.countriesCheck.SetValue(True)
                    self.statesCheck.SetValue(False)
                    for country in row[2].split(","):
                        idx = self.countriesList.FindItem(-1, country)
                        if idx != -1: self.countriesList.Select(idx)
                elif row[1] == 'states':
                    self.deselectList(self.countriesList)
                    self.deselectList(self.statesList)
                    self.countriesCheck.SetValue(False)
                    self.statesCheck.SetValue(True)
                    for state in row[2].split(","):
                        idx = self.statesList.FindItem(-1, state)
                        if idx != -1: self.statesList.Select(idx)
                elif row[1] == 'types':
                    self.deselectList(self.cacheTypes)
                    for ctype in row[2].split(","):
                        idx = self.cacheTypes.FindItem(-1, ctype)
                        if idx != -1: self.cacheTypes.Select(idx)
                elif row[1] == 'containers':
                    self.deselectList(self.cacheContainers)
                    for ctype in row[2].split(","):
                        idx = self.cacheContainers.FindItem(-1, ctype)
                        if idx != -1: self.cacheContainers.Select(idx)
                else:
                    for i in ['notFoundByMe', 'found', 'notOwned', 'owned', 'genAvail',
                              'memAvail', 'notIgnored', 'ignored', 'foundLast7',
                              'notFound', 'hasBugs', 'updatedLast7', 'notActive',
                              'active']:
                        if row[1] == i.lower():
                            getattr(self, i).SetValue(1 == int(row[2]))
    
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
            params['searchScale'] = self.distanceScale.GetItems()[self.distanceScale.GetSelection()]
        params['daterange'] = self.rangeChoice.GetItems()[self.rangeChoice.GetSelection()]
        params['begindate'] = self.beginDate.GetValue().GetTicks()
        params['enddate'] = self.endDate.GetValue().GetTicks()
        for i in ['notFoundByMe', 'found', 'notOwned', 'owned', 'genAvail',
                  'memAvail', 'notIgnored', 'ignored', 'foundLast7',
                  'notFound', 'hasBugs', 'updatedLast7', 'notActive',
                  'active']:
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
    
    def OnCheckDates(self, evt):
        idx = self.rangeChoice.GetSelection()
        val = (idx == 4)
        self.beginDate.Enable(val)
        self.endDate.Enable(val)
        begin = wx.DateTime.Now()
        end = wx.DateTime.Now()
        if idx == 0:
            begin = begin - wx.DateSpan(30, 0, 0, 0)
        elif idx == 1:
            begin = begin - wx.DateSpan(0, 0, 1, 0)
        elif idx == 2:
            begin = begin - wx.DateSpan(0, 1, 0, 0)
        elif idx == 3:
            begin = begin - wx.DateSpan(1, 0, 0, 0)
        self.beginDate.SetValue(begin)
        self.endDate.SetValue(end)
    
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
        isinstance(self.genAvail, wx.CheckBox)
        isinstance(self.memAvail, wx.CheckBox)
        isinstance(self.notIgnored, wx.CheckBox)
        isinstance(self.ignored, wx.CheckBox)
        isinstance(self.foundLast7, wx.CheckBox)
        isinstance(self.notFound, wx.CheckBox)
        isinstance(self.hasBugs, wx.CheckBox)
        isinstance(self.updatedLast7, wx.CheckBox)
        isinstance(self.notActive, wx.CheckBox)
        isinstance(self.active, wx.CheckBox)
        isinstance(self.splitRegions, wx.SplitterWindow)
        isinstance(self.countriesCheck, wx.CheckBox)
        isinstance(self.countriesList, wx.ListCtrl)
        isinstance(self.clearCountries, wx.Button)
        isinstance(self.statesCheck, wx.CheckBox)
        isinstance(self.statesList, wx.ListCtrl)
        isinstance(self.clearStates, wx.Button)
        isinstance(self.rangeChoice, wx.Choice)
        isinstance(self.beginDate, wx.DatePickerCtrl)
        isinstance(self.endDate, wx.DatePickerCtrl)
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

class DateValidator(wx.PyValidator):
    def __init__(self, begin, end):
        wx.PyValidator.__init__(self)
        self.begin = begin
        self.end = end
        
    def Clone(self):
        return DateValidator(self.begin, self.end)
    
    def TransferFromWindow(self):
        return True
    
    def TransferToWindow(self):
        return True
    
    def Validate(self, win):
        if not self.end.IsEnabled(): return True
        try:
            ret = (self.end.GetValue() > self.begin.GetValue())
            if not ret:
                self.begin.SetBackgroundColour("red")
                self.end.SetBackgroundColour("red")
                return False
            else:
                self.begin.SetBackgroundColour(wx.SystemSettings_GetColour(wx.SYS_COLOUR_WINDOW))
                self.end.SetBackgroundColour(wx.SystemSettings_GetColour(wx.SYS_COLOUR_WINDOW))
                self.begin.Refresh()
                self.end.Refresh()
                return True
        except:
            self.begin.SetBackgroundColour("red")
            self.end.SetBackgroundColour("red")
            return False
    
    def forWingIde(self):
        isinstance(self.begin, wx.DatePickerCtrl)
        isinstance(self.end, wx.DatePickerCtrl)
