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

import gpsbabel

class cmdValidator(wx.PyValidator):
    def Clone(self):
        return cmdValidator()
    
    def Validate(self, win):
        fp = self.GetWindow()
        isinstance(fp, wx.FilePickerCtrl)
        fname = fp.GetPath()
        retval = os.path.exists(fname) and os.access(fname, os.X_OK)
        if not retval:
            wx.MessageBox('Invalid location for GPSBabel.', 'GPSBabel Location Problem', parent=win)
        return retval
        
    def TransferToWindow(self):
        fp = self.GetWindow()
        cfg = wx.Config.Get()
        isinstance(fp, wx.FilePickerCtrl)
        isinstance(cfg, wx.Config)
        cfg.SetPath('/PerMachine')
        loc = cfg.Read('GPSBabelLoc', cache901.util.which('gpsbabel'))
        fp.SetPath(loc)
        fp.Refresh()
    
    def TransferFromWindow(self):
        fp = self.GetWindow()
        cfg = wx.Config.Get()
        isinstance(fp, wx.FilePickerCtrl)
        isinstance(cfg, wx.Config)
        cfg.SetPath('/PerMachine')
        cfg.Write('GPSBabelLoc', fp.GetPath())
    
class portValidator(wx.PyValidator):
    def Clone(self):
        return portValidator()
    
    def Validate(self, win):
        choice = self.GetWindow()
        isinstance(choice, wx.Choice)
        selnum = choice.GetSelection()
        if selnum == wx.NOT_FOUND: return False
        items = choice.GetItems()
        if selnum < 0 or selnum >= len(items): return False
        if items[selnum] == 'USB': return True
        try:
            s = serial.Serial(items[selnum])
            return True
        except:
            wx.MessageBox('Choose a different serial port', 'Invalid Serial Port')
            return False
    
    def TransferToWindow(self):
        choice = self.GetWindow()
        cfg = wx.Config.Get()
        isinstance(choice, wx.Choice)
        isinstance(cfg, wx.Config)
        cfg.SetPath('/PerMachine')
        choice.Clear()
        choice.Append('USB')
        choice.AppendItems(cache901.util.scanForSerial())
        try:
            choice.SetSelection(choice.GetItems().index(cfg.Read('GPSPort', 'USB')))
        except:
            choice.SetSelection(0)
            
    def TransferFromWindow(self):
        choice = self.GetWindow()
        cfg = wx.Config.Get()
        isinstance(choice, wx.Choice)
        isinstance(cfg, wx.Config)
        cfg.SetPath('/PerMachine')
        cfg.Write('GPSPort', choice.GetItems()[choice.GetSelection()])
        
class gpsTypeValidator(wx.PyValidator):
    def Clone(self):
        return gpsTypeValidator()
    
    def Validate(self, win):
        choice = self.GetWindow()
        isinstance(choice, wx.Choice)
        items = map(lambda x: x.lower(), choice.GetItems())
        return items[choice.GetSelection()] in ['garmin', 'nmea']
    
    def TransferToWindow(self):
        choice = self.GetWindow()
        cfg = wx.Config.Get()
        isinstance(cfg, wx.Config)
        isinstance(choice, wx.Choice)
        cfg.SetPath('/PerMachine')
        items = map(lambda x: x.lower(), choice.GetItems())
        try:
            choice.SetSelection(['garmin', 'nmea'].index(cfg.Read('GPSType', 'nmea')))
        except:
            choice.SetSelection(0)

    def TransferFromWindow(self):
        choice = self.GetWindow()
        cfg = wx.Config.Get()
        isinstance(cfg, wx.Config)
        isinstance(choice, wx.Choice)
        cfg.SetPath('/PerMachine')
        cfg.Write('GPSType', choice.GetItems()[choice.GetSelection()].lower())
        
class degDisplayValidator(wx.PyValidator):
    def Clone(self):
        return degDisplayValidator()
    
    def Validate(self, win):
        choice = self.GetWindow()
        isinstance(self, wx.Choice)
        items = map(lambda x: x.lower(), choice.GetItems())
        return items[choice.GetSelection()] in ['deg min sec', 'deg min', 'deg']
    
    def TransferToWindow(self):
        choice = self.GetWindow()
        cfg = wx.Config.Get()
        isinstance(cfg, wx.Config)
        isinstance(choice, wx.Choice)
        cfg.SetPath('/PerMachine')
        items = map(lambda x: x.lower(), choice.GetItems())
        try:
            choice.SetSelection(['deg min sec', 'deg min', 'deg'].index(cfg.Read('degDisplay', 'deg min sec')))
        except:
            choice.SetSelection(0)

    def TransferFromWindow(self):
        choice = self.GetWindow()
        cfg = wx.Config.Get()
        isinstance(cfg, wx.Config)
        isinstance(choice, wx.Choice)
        cfg.SetPath('/PerMachine')
        cfg.Write('degDisplay', choice.GetItems()[choice.GetSelection()].lower())
        

class splitValidator(wx.PyValidator):
    def __init__(self, varname):
        wx.PyValidator.__init__(self)
        self.varname = varname
        
    def Clone(self):
        return splitValidator(self.varname)
    
    def Validate(self, win):
        return True
    
    def TransferToWindow(self):
        choice = self.GetWindow()
        isinstance(choice, wx.SplitterWindow)
        win = choice.GetTopLevelParent().__class__.__name__
        cfg = wx.Config.Get()
        isinstance(cfg, wx.Config)
        cfg.SetPath('/%s' % win)
        choice.SetSashPosition(cfg.ReadInt(self.varname, 175))
    
    def TransferFromWindow(self):
        choice = self.GetWindow()
        isinstance(choice, wx.SplitterWindow)
        win = choice.GetTopLevelParent().__class__.__name__
        cfg = wx.Config.Get()
        isinstance(cfg, wx.Config)
        cfg.SetPath('/%s' % win)
        cfg.WriteInt(self.varname, choice.GetSashPosition())