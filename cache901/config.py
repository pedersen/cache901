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
        if not self.config.HasEntry('Width') or not self.config.HasEntry('Height'): return None
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
        if not self.config.HasEntry('DetailSplitPos'): return None
        return self.config.ReadInt('DetailSplitPos')
    
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
        return self.config.ReadInt('DescriptionSplitPos"', 150)
    
    def setDescSplitPos(self, pos):
        self.config.SetPath('/MainWin')
        self.config.WriteInt('DescriptionSplitPos"', pos)
        return pos
    
    def getLogSplitPos(self):
        self.config.SetPath('/MainWin')
        return self.config.ReadInt('LogSplitPos"', 150)
    
    def setLogSplitPos(self, pos):
        self.config.SetPath('/MainWin')
        self.config.WriteInt('LogSplitPos"', pos)
        return pos
    
    def getPicSplitPos(self):
        self.config.SetPath('/MainWin')
        return self.config.ReadInt('PicSplitPos"', 300)
    
    def setPicSplitPos(self, pos):
        self.config.SetPath('/MainWin')
        self.config.WriteInt('PicSplitPos"', pos)
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
    
    dbMaxLogs      = property(getDbMaxLogs,      setDbMaxLogs)
    gpstype        = property(getGpsType,        setGpsType)
    gpsport        = property(getGpsPort,        setGpsPort)
    degdisplay     = property(getDegDisplay,     setDegDisplay)
    mainwinsize    = property(getMainWinSize,    setMainWinSize)
    detailsplitpos = property(getDetailSplitPos, setDetailSplitPos)
    listsplitpos   = property(getListSplitPos,   setListSplitPos)
    descsplitpos   = property(getDescSplitPos,   setDescSplitPos)
    logsplitpos    = property(getLogSplitPos,    setLogSplitPos)
    picsplitpos    = property(getPicSplitPos,    setPicSplitPos)
    lastimportdir  = property(getLastImportDir,  setLastImportDir)
    lastphotodir   = property(getLastPhotoDir,   setLastPhotoDir)
    gpsbabel       = property(getGpsbabelLoc,    setGpsbabelLoc)
    
    def forWingIde(self):
        isinstance(self.config, wx.Config)

