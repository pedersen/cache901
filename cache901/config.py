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

import os
import sys

import wx

import cache901
import cache901.util

class Config(object):
    __shared_state = {}
    def __init__(self):
        self.__dict__ = self.__shared_state
        if not hasattr(self, "config"):
            self.config = wx.Config(cache901.appname)
            wx.Config.Set(self.config)
    
    def getDbMaxLogs(self):
        self.config.SetPath('/PerMachine')
        return self.config.ReadInt("maxLogs", 10)
    
    def setDbMaxLogs(self, maxLogs):
        self.config.SetPath('/PerMachine')
        self.config.WriteInt("maxLogs", maxLogs)
        return maxLogs
    
    def getGpsType(self):
        self.config.SetPath('/PerMachine')
        return self.config.Read('GPSType', 'nmea')
    
    def setGpsType(self, gpstype):
        self.config.SetPath('/PerMachine')
        self.config.Write('GPSType', gpstype)
        return gpstype
    
    def getGpsPort(self):
        self.config.SetPath('/PerMachine')
        return self.config.Read('GPSPort', 'USB')
    
    def setGpsPort(self, gpsport):
        self.config.SetPath('/PerMachine')
        self.config.Write('GPSPort', gpsport)
        return gpsport
    
    def getDegDisplay(self):
        self.config.SetPath('/PerMachine')
        return self.config.Read('degDisplay', 'deg min')
    
    def setDegDisplay(self, degdisplay):
        self.config.SetPath('/PerMachine')
        self.config.Write('degDisplay', 'deg min')
        return degdisplay
    
    def getMainWinSize(self):
        self.config.SetPath('/MainWin')
        if not self.config.HasEntry('Width') or not self.config.HasEntry('Height'): return wx.Size(800, 420)
        size = wx.Size()
        size.width = self.config.ReadInt('Width')
        size.height = self.config.ReadInt('Height')
        return size
    
    def setMainWinSize(self, size):
        self.config.SetPath('/MainWin')
        self.config.WriteInt('Width', size.width)
        self.config.WriteInt('Height', size.height)
        return size
    
    def getDetailSplitPos(self):
        self.config.SetPath('/MainWin')
        return self.config.ReadInt('DetailSplitPos', 200)
    
    def setDetailSplitPos(self, pos):
        self.config.SetPath('/MainWin')
        self.config.WriteInt('DetailSplitPos', pos)
        return pos
    
    def getListSplitPos(self):
        self.config.SetPath('/MainWin')
        return self.config.ReadInt('ListSplitPos', 370)
    
    def setListSplitPos(self, pos):
        self.config.SetPath('/MainWin')
        self.config.WriteInt('ListSplitPos', pos)
        return pos
    
    def getDescSplitPos(self):
        self.config.SetPath('/MainWin')
        return self.config.ReadInt('DescriptionSplitPos', 150)
    
    def setDescSplitPos(self, pos):
        self.config.SetPath('/MainWin')
        self.config.WriteInt('DescriptionSplitPos', pos)
        return pos
    
    def getLogSplitPos(self):
        self.config.SetPath('/MainWin')
        return self.config.ReadInt('LogSplitPos', 150)
    
    def setLogSplitPos(self, pos):
        self.config.SetPath('/MainWin')
        self.config.WriteInt('LogSplitPos', pos)
        return pos
    
    def getPicSplitPos(self):
        self.config.SetPath('/MainWin')
        return self.config.ReadInt('PicSplitPos', 300)
    
    def setPicSplitPos(self, pos):
        self.config.SetPath('/MainWin')
        self.config.WriteInt('PicSplitPos', pos)
        return pos
    
    def getLastPhotoDir(self):
        self.config.SetPath("/Files")
        if not self.config.HasEntry("LastPhotoDir"): return None
        return self.config.Read("LastPhotoDir")
    
    def setLastPhotoDir(self, lastdir):
        self.config.SetPath("/Files")
        self.config.Write("LastPhotoDir", lastdir)
        return lastdir
    
    def getLastImportDir(self):
        self.config.SetPath("/Files")
        if not self.config.HasEntry("LastImportDir"): return None
        return self.config.Read("LastImportDir")
    
    def setLastImportDir(self, lastdir):
        self.config.SetPath("/Files")
        self.config.Write("LastImportDir", lastdir)
        return lastdir
    
    def getGpsbabelLoc(self):
        self.config.SetPath('/PerMachine')
        cmd = cache901.util.which('gpsbabel')
        if cmd is None: cmd = 'Select Executable'
        return self.config.Read('GPSBabelLoc', cmd)
    
    def setGpsbabelLoc(self, gpsbabel):
        self.config.SetPath('/PerMachine')
        self.config.Write('GPSBabelLoc', gpsbabel)
        return gpsbabel
    
    def getSearchSplitSave(self):
        self.config.SetPath('/SearchBox')
        return self.config.ReadInt('splitterSave', 175)
    
    def setSearchSplitSave(self, pos):
        self.config.SetPath('/SearchBox')
        self.config.WriteInt('splitterSave', 175)
        return pos
    
    def getSearchSplitType(self):
        self.config.SetPath('/SearchBox')
        return self.config.ReadInt('splitterType', 175)
    
    def setSearchSplitType(self, pos):
        self.config.SetPath('/SearchBox')
        self.config.WriteInt('splitterType', 175)
        return pos
    
    def getSearchSplitRegions(self):
        self.config.SetPath('/SearchBox')
        return self.config.ReadInt('splitRegions', 175)
    
    def setSearchSplitRegions(self, pos):
        self.config.SetPath('/SearchBox')
        self.config.WriteInt('splitRegions', 175)
        return pos
    
    def getOptSplitLoc(self):
        self.config.SetPath('/OptionsUI')
        return self.config.ReadInt('locSplit', 175)
    
    def setOptSplitLoc(self, pos):
        self.config.SetPath('/OptionsUI')
        self.config.WriteInt('locSplit', pos)
        return pos
    
    def getOptSplitAcct(self):
        self.config.SetPath('/OptionsUI')
        return self.config.ReadInt('acctTabSplit', 175)
    
    def setOptSplitAcct(self, pos):
        self.config.SetPath('/OptionsUI')
        self.config.WriteInt('acctTabSplit', 175)
        return pos
    
    def getGpxFolderSplit(self):
        self.config.SetPath('/GPXSourceUI')
        return self.config.ReadInt('foldersWptsSplit', 175)
    
    def setGpxFolderSplit(self, pos):
        self.config.SetPath('/GPXSourceUI')
        self.config.WriteInt('foldersWptsSplit', pos)
        return pos
        
    def getGpxPop3Split(self):
        self.config.SetPath('/GPXSourceUI')
        return self.config.ReadInt('pop3Split', 175)
    
    def setGpxPop3Split(self, pos):
        self.config.SetPath('/GPXSourceUI')
        self.config.WriteInt('pop3Split', pos)
        return pos
        
    def getGpxImap4Split(self):
        self.config.SetPath('/GPXSourceUI')
        return self.config.ReadInt('imap4Split', 175)
    
    def setGpxImap4Split(self, pos):
        self.config.SetPath('/GPXSourceUI')
        self.config.WriteInt('imap4Split', pos)
        return pos
    
    def getMapSplit(self):
        self.config.SetPath('/MapUI')
        return self.config.ReadInt('mapSplit', 175)
    
    def setMapSplit(self, pos):
        self.config.SetPath('/MapUI')
        self.config.WriteInt('mapSplit', pos)
        return pos
    
    def getDbPath(self):
        if sys.platform == 'win32':
            envvar = 'HOMEPATH'
        else:
            envvar = 'HOME'
        return(os.sep.join([os.environ[envvar], cache901.appname]))
        
    def getDbFile(self):
        self.config.SetPath('/PerMachine')
        if not self.config.HasEntry('LastOpenedDb'):
            return os.sep.join([self.dbpath, '%s.sqlite' % (cache901.appname)])
        else:
            return os.sep.join([self.dbpath, self.config.Read('LastOpenedDb')])
        
    def setDbFile(self, lastdb):
        self.config.SetPath('/PerMachine')
        isinstance(lastdb, str)
        dbfile = lastdb.replace('%s%s' % (self.dbpath, os.sep), '')
        if dbfile == lastdb:
            raise Exception('Invalid Database Location. Database must be under %s' % (self.dbpath))
        self.config.Write('LastOpenedDb', dbfile)
        return lastdb
        
    dbMaxLogs          = property(getDbMaxLogs,          setDbMaxLogs)
    gpstype            = property(getGpsType,            setGpsType)
    gpsport            = property(getGpsPort,            setGpsPort)
    degdisplay         = property(getDegDisplay,         setDegDisplay)
    mainwinsize        = property(getMainWinSize,        setMainWinSize)
    detailsplitpos     = property(getDetailSplitPos,     setDetailSplitPos)
    listsplitpos       = property(getListSplitPos,       setListSplitPos)
    descsplitpos       = property(getDescSplitPos,       setDescSplitPos)
    logsplitpos        = property(getLogSplitPos,        setLogSplitPos)
    picsplitpos        = property(getPicSplitPos,        setPicSplitPos)
    lastimportdir      = property(getLastImportDir,      setLastImportDir)
    lastphotodir       = property(getLastPhotoDir,       setLastPhotoDir)
    gpsbabel           = property(getGpsbabelLoc,        setGpsbabelLoc)
    searchsplitsave    = property(getSearchSplitSave,    setSearchSplitSave)
    searchsplittype    = property(getSearchSplitType,    setSearchSplitType)
    searchsplitregions = property(getSearchSplitRegions, setSearchSplitRegions)
    optsplitloc        = property(getOptSplitLoc,        setOptSplitLoc)
    optsplitacct       = property(getOptSplitAcct,       setOptSplitAcct)
    gpxfoldersplit     = property(getGpxFolderSplit,     setGpxFolderSplit)
    gpxpop3split       = property(getGpxPop3Split,       setGpxPop3Split)
    gpximap4split      = property(getGpxImap4Split,      setGpxImap4Split)
    mapsplit           = property(getMapSplit,           setMapSplit)
    dbpath             = property(getDbPath)
    dbfile             = property(getDbFile,             setDbFile)
    
    def forWingIde(self):
        isinstance(self.config, wx.Config)

