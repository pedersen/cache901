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

class spinCtlValidator(wx.PyValidator):
    def __init__(self, varname):
        wx.PyValidator.__init__(self)
        self.varname = varname
        
    def Clone(self):
        return spinCtlValidator(self.varname)
    
    def Validate(self, win):
        return True
    
    def TransferToWindow(self):
        fp = self.GetWindow()
        isinstance(fp, wx.SpinCtrl)
        cfg = cache901.cfg()
        spinnum = getattr(cfg, self.varname)
        fp.SetValue(spinnum)
        fp.Refresh()
        
    def TransferFromWindow(self):
        fp = self.GetWindow()
        isinstance(fp, wx.SpinCtrl)
        cfg = cache901.cfg()
        spinnum = fp.GetValue()
        setattr(cfg, self.varname, spinnum)
        
class cmdValidator(wx.PyValidator):
    def Clone(self):
        return cmdValidator()
    
    def Validate(self, win):
        fp = self.GetWindow()
        isinstance(fp, wx.FilePickerCtrl)
        top = fp.GetTopLevelParent()
        isinstance(top, cache901.options.OptionsUI)
        fname = fp.GetPath()
        retval = (os.path.exists(fname) and os.access(fname, os.X_OK)) and (fname != 'Select Executable')
        if not retval:
            wx.MessageBox('Invalid location for GPSBabel.', 'GPSBabel Location Problem', parent=win)
            top.gpsbabelPath.SetLabel('Path: Invalid')
        else:
            top.gpsbabelPath.SetLabel('Path: %s' % fname)
        return retval
        
    def TransferToWindow(self):
        fp = self.GetWindow()
        top = fp.GetTopLevelParent()
        isinstance(top, cache901.options.OptionsUI)
        isinstance(fp, wx.FilePickerCtrl)
        cfg = cache901.cfg()
        loc = cfg.gpsbabel
        fp.SetPath(loc)
        top.gpsbabelPath.SetLabel('Path: %s' % loc)
        fp.Refresh()
    
    def TransferFromWindow(self):
        fp = self.GetWindow()
        isinstance(fp, wx.FilePickerCtrl)
        cfg = cache901.cfg()
        cfg.gpsbabel = fp.GetPath()
    
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
        if items[selnum] == 'USB:': return True
        try:
            s = serial.Serial(items[selnum])
            return True
        except:
            wx.MessageBox('Choose a different serial port', 'Invalid Serial Port')
            return False
    
    def TransferToWindow(self):
        choice = self.GetWindow()
        isinstance(choice, wx.Choice)
        cfg = cache901.cfg()
        choice.Clear()
        choice.Append('USB:')
        choice.AppendItems(cache901.util.scanForSerial())
        try:
            choice.SetSelection(choice.GetItems().index(cfg.gpsport))
        except:
            choice.SetSelection(0)
            
    def TransferFromWindow(self):
        choice = self.GetWindow()
        isinstance(choice, wx.Choice)
        cfg = cache901.cfg()
        cfg.gpsport = choice.GetItems()[choice.GetSelection()]
        
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
        isinstance(choice, wx.Choice)
        cfg = cache901.cfg()
        items = map(lambda x: x.lower(), choice.GetItems())
        try:
            choice.SetSelection(['garmin', 'nmea'].index(cfg.gpstype))
        except:
            choice.SetSelection(0)

    def TransferFromWindow(self):
        choice = self.GetWindow()
        isinstance(choice, wx.Choice)
        cfg = cache901.cfg()
        cfg.gpstype = choice.GetItems()[choice.GetSelection()].lower()
        
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
        isinstance(choice, wx.Choice)
        cfg = cache901.cfg()
        items = map(lambda x: x.lower(), choice.GetItems())
        try:
            choice.SetSelection(['deg min sec', 'deg min', 'deg'].index(cfg.degdisplay))
        except:
            choice.SetSelection(0)

    def TransferFromWindow(self):
        choice = self.GetWindow()
        isinstance(choice, wx.Choice)
        cfg = cache901.cfg()
        cfg.degdisplay = choice.GetItems()[choice.GetSelection()].lower()
        

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
        cfg = cache901.cfg()
        choice.SetSashPosition(getattr(cfg, self.varname))
    
    def TransferFromWindow(self):
        choice = self.GetWindow()
        isinstance(choice, wx.SplitterWindow)
        cfg = cache901.cfg()
        setattr(cfg, self.varname, choice.GetSashPosition())
