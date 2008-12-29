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

import cookielib
import email
import email.message
import email.parser
import imaplib
import os
import os.path
import poplib
import random
import re
import time
import urllib
import urllib2
import zipfile

from cStringIO import StringIO

import wx

import cache901
import cache901.ui_xrc
import cache901.validators

class GPXSource(object):
    # Objects of this interface must be iterable. Furthermore, they must
    # return the next gpx file in their data set. Callers will only care
    # about the gpx files, so only those get returned.
    # gpx objects are required to be file contents as a single string
    def __iter__(self):
        return self
    
    def next(self):
        raise StopIteration

class FolderSource(GPXSource):
    def __init__(self, folder):
        self.folder = folder
        self.gpxfiles = filter(lambda x: x.lower().endswith('.gpx'), os.listdir(folder))
        self.zipfiles = filter(lambda x: x.lower().endswith('.zip'), os.listdir(folder))
        self.gpxzip = []
        self.z = None
        
    def next(self):
        ext = ""
        if len(self.gpxfiles) > 0:
            fname = self.gpxfiles.pop()
            cache901.notify('Processing %s' % fname)
            f = open(os.sep.join([self.folder, fname]))
            return "\n".join(f.readlines())
        if len(self.zipfiles) > 0:
            if self.z is None:
                fname = self.zipfiles[-1]
                self.z = zipfile.ZipFile(os.sep.join([self.folder, fname]))
                self.gpxzip = filter(lambda x: x.lower().endswith('.gpx'), self.z.namelist())
            if len(self.gpxzip) > 0:
                cache901.notify('Processing %s' % os.sep.join([fname, self.gpxzip[-1]]))
                return self.z.read(self.gpxzip.pop())
            else:
                self.z = None
                self.zipfiles.pop()
        raise StopIteration

class PopSource(GPXSource):
    def __init__(self, host, user, password, ssl=False):
        if ssl:
            self.pop3 = poplib.POP3_SSL(host)
        else:
            self.pop3 = poplib.POP3(host)
        self.pop3.user(user)
        self.pop3.pass_(password)
        self.nummsgs = len(self.pop3.list()[1])
        self.count = 0
        self.parser = email.parser.Parser()
        self.zfile = None
        self.gpxlist = []
        
    def __del__(self):
        self.pop3.quit()
        
    def next(self):
        while (self.count < self.nummsgs) or (self.zfile is not None):
            if self.zfile is None:
                self.count = self.count + 1
                cache901.notify('Processing Message %d' % self.count)
                pmsg = "\n".join(self.pop3.retr(self.count)[1])
                msg = self.parser.parsestr(pmsg)
                isinstance(msg, email.message.Message)
                if msg.is_multipart():
                    for part in msg.get_payload():
                        isinstance(part, email.message.Message)
                        fname = part.get_filename('').lower()
                        if fname.endswith('.gpx'):
                            return part.get_payload(decode=True)
                        if fname.endswith('.zip'):
                            self.zfile = zipfile.ZipFile(StringIO(part.get_payload(decode=True)))
                            self.gpxlist = filter(lambda x: x.lower().endswith('.gpx'), self.zfile.namelist())
                            if len(self.gpxlist) == 0:
                                self.zfile = None
            else:
                if len(self.gpxlist) == 0:
                    self.zfile = None
                    return '<gpx></gpx>'
                fname = self.gpxlist.pop()
                cache901.notify('Processing Message %d, Zip Attachment, File %s' % (self.count, fname))
                return self.zfile.read(fname)
        raise StopIteration

class IMAPSource(GPXSource):
    def __init__(self, host, user, password, ssl=False, folder='INBOX'):
        if ssl:
            self.imap4 = imaplib.IMAP4(host)
        else:
            self.imap4 = imaplib.IMAP4_SSL(host)
        self.imap4.login(user, password)
        self.imap4.select(folder)
        typ, data = self.imap4.search(None, 'UNSEEN')
        self.msgnums = data[0].split()
        self.count = 0
        self.parser = email.parser.Parser()
        self.zfile = None
        self.gpxlist = []
        
    def __del__(self):
        self.imap4.close()
        
    def next(self):
        while self.count < len(self.msgnums)-1:
            if self.zfile is None:
                cache901.notify('Processing Message %s' % self.msgnums[self.count])
                typ, pmsg = self.imap4.fetch(self.msgnums[self.count], '(RFC822)')
                self.count = self.count + 1
                msg = self.parser.parsestr(pmsg[0][1])
                isinstance(msg, email.message.Message)
                if msg.is_multipart():
                    foundgpx = False
                    for part in msg.get_payload():
                        isinstance(part, email.message.Message)
                        fname = part.get_filename('').lower()
                        if fname.endswith('.gpx'):
                            cache901.notify('Found gpx file, processing')
                            return part.get_payload(decode=True)
                        if fname.endswith('.zip'):
                            cache901.notify('Found zip file, trying to load')
                            self.zfile = zipfile.ZipFile(StringIO(part.get_payload(decode=True)))
                            self.gpxlist = filter(lambda x: x.lower().endswith('.gpx'), self.zfile.namelist())
                            if len(self.gpxlist) == 0:
                                self.zfile = None
                            else:
                                self.count = self.count - 1
                                foundgpx = True
                    if not foundgpx:
                        self.imap4.store(self.msgnums[self.count], '-FLAGS', '(\\SEEN)')
                else:
                    self.imap4.store(self.msgnums[self.count], '-FLAGS', '(\\SEEN)')
            else:
                if len(self.gpxlist) == 0:
                    self.zfile = None
                    self.count = self.count + 1
                    return '<gpx></gpx>'
                cache901.notify('Processing Message %s, Zip Attachment, File %s' % (self.msgnums[self.count], self.gpxlist[-1]))
                return self.zfile.read(self.gpxlist.pop())
        raise StopIteration

class GeoCachingComSource(GPXSource):
    def __init__(self, username, password, wptnames=[]):
        self.username = username
        self.password = password
        self.wptnames = wptnames
        self.useragent = 'Mozilla/4.0 (compatible; MSIE 5.5; Cache 901)'
        self.cfilename = os.sep.join([cache901.dbpath, 'gccom_cookie.jar'])
        self.login()
        
    def __del__(self):
        self.wwwSetup()
        urllib2.urlopen('http://www.geocaching.com/login/default.aspx?RESET=Y')
        self.wwwClose()
        
    def wwwSetup(self):
            self.jar = cookielib.LWPCookieJar()
            try:
                self.jar.load(self.cfilename)
            except:
                pass
            self.opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(self.jar))
            urllib2.install_opener(self.opener)
            
    def wwwClose(self):
        if self.jar is not None:
            self.jar.save(self.cfilename)
        self.opener = None
        self.jar = None
        
    def setWpts(self, wptnames=[]):
        self.wptnames = wptnames
        
    def login(self):
        try:
            cache901.notify('Logging into geocaching.com site')
            self.wwwSetup()
            
            gcmain = 'http://www.geocaching.com/default.aspx'
            
            page = urllib2.urlopen(gcmain)
            time.sleep((random.random()*2)+0.5)
            m = re.match(r'.+?id="__VIEWSTATE"\s+value="(.+?)"', page.read(), re.S)
            fromvalues = urllib.urlencode({
                '__VIEWSTATE': m.group(1),
                'ctl00$MiniProfile$loginUsername' : self.username,
                'ctl00$MiniProfile$loginPassword' : self.password,
                'ctl00$MiniProfile$LoginBtn' : 'Go',
                'ctl00$MiniProfile$loginRemember' : 'on'
            })
            headers = {'User-agent' : self.useragent }

            request = urllib2.Request(gcmain, fromvalues, headers)
            page = urllib2.urlopen(request)
            time.sleep((random.random()*2)+0.5)

            m = re.match('.+%s.+' % self.username, page.read(), re.S)
    
            if m is None:
                raise Exception('GeoCaching.com Login Failed, invalid username/password')
            cache901.notify('Login successful')
            self.wwwClose()
        except IOError, e:
            if hasattr(e, 'code'):
                raise Exception('GeoCaching.com Login Failed, error code: %s' % e.code)
            elif hasattr(e, 'reason'):
                raise Exception('GeoCaching.com Login Failed, error reason: %s' % e.reason)
            else:
                raise Exception('GeoCaching.com Login Failed, error %s' % str(e))
        
    def next(self):
        cfind = 'http://www.geocaching.com/seek/cache_details.aspx?wp='
        headers = {'User-agent' : self.useragent }
        if len(self.wptnames) > 0:
            self.wwwSetup()
            cname = self.wptnames.pop()
            curl = '%s%s' % (cfind, cname)
            
            # Get __VIEWSTATE
            cache901.notify('Retrieving cache page for %s' % cname)
            page = urllib2.urlopen(curl)
            time.sleep((random.random()*2)+0.5)
            m = re.match(r'.+?id="__VIEWSTATE"\s+value="(.+?)"', page.read(), re.S)
            fromvalues = urllib.urlencode({
                '__VIEWSTATE': m.group(1),
                'btnGPXDL' : 'GPX eXchange File'
            })
            
            # Get GPX file
            cache901.notify('Retrieving GPX file for %s' % cname)
            request = urllib2.Request(curl, fromvalues, headers)
            page = urllib2.urlopen(request)
            time.sleep((random.random()*2)+0.5)
            ptext = page.read()
            cache901.notify('Retrieved GPX file for %s' % cname)
            self.wwwClose()
            return ptext
        raise StopIteration
    
def gpxSyncAll():
    # @todo: Implement this routine
    cache901.notify('todo: implement this routine')

class GPXSourceUI(cache901.ui_xrc.xrcGPXSourcesUI):
    def __init__(self, parent=None):
        cache901.ui_xrc.xrcGPXSourcesUI.__init__(self, parent)
        self.foldersWaypointSplitter.SetValidator(cache901.validators.splitValidator('foldersWptsSplit'))
        self.pop3Splitter.SetValidator(cache901.validators.splitValidator('pop3Split'))
        self.imap4Splitter.SetValidator(cache901.validators.splitValidator('imap4Split'))
        
        w,h = self.GetTextExtent("QQQQQQQQQQQQQQQQQQ")
        self.folderNames.InsertColumn(0, 'Folder Name', width=w)
        self.geoWpts.InsertColumn(0, 'Watched Waypoints', width=w)
        self.pop3Servers.InsertColumn(0, 'POP3 Server', width=w)
        self.imap4SvrList.InsertColumn(0, 'IMAP Server', width=w)
        
        self.loadFolders()
        self.loadWpts()
        self.loadPopAccounts()
        self.loadImapAccounts()
        
        self.Bind(wx.EVT_BUTTON, self.OnAddFolder, self.btnAddFolder)
        self.Bind(wx.EVT_BUTTON, self.OnRemFolder, self.btnRemFolder)
        self.Bind(wx.EVT_BUTTON, self.OnAddWpt,    self.btnAddWpt)
        self.Bind(wx.EVT_BUTTON, self.OnRemWpt,    self.btnRemWpt)
        self.Bind(wx.EVT_BUTTON, self.OnAddPop,    self.btnAddPop3Svr)
        self.Bind(wx.EVT_BUTTON, self.OnRemPop,    self.btnRemPop3Svr)
        self.Bind(wx.EVT_BUTTON, self.OnSavePop,   self.pop3Save)
        self.Bind(wx.EVT_BUTTON, self.OnAddImap,   self.btnAddImap4Svr)
        self.Bind(wx.EVT_BUTTON, self.OnRemImap,   self.btnRemImap4Svr)
        self.Bind(wx.EVT_BUTTON, self.OnSaveImap,  self.imap4Save)
        
        self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.OnLoadPop,  self.pop3Servers)
        self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.OnLoadImap, self.imap4SvrList)
        
    def OnAddImap(self, evt):
        pass
    
    def OnRemImap(self, evt):
        pass
    
    def OnLoadImap(self, evt):
        pass
    
    def OnSaveImap(self, evt):
        pass
    
    def loadImapAccounts(self):
        pass
    
    def OnAddPop(self, evt):
        pass
    
    def OnRemPop(self, evt):
        pass
    
    def OnLoadPop(self, evt):
        pass
    
    def OnSavePop(self, evt):
        pass
    
    def loadPopAccounts(self):
        pass
    
    def OnAddWpt(self, evt):
        pass
    
    def OnRemWpt(self, evt):
        pass
    
    def loadWpts(self):
        pass
    
    def OnAddFolder(self, evt):
        dirpath = wx.DirSelector('Add Watched Folder')
        if dirpath != "":
            cur = cache901.db().cursor()
            cur.execute('insert into gpxfolders(foldername) values(?)', (dirpath, ))
            cache901.db().commit()
            self.loadFolders()
    
    def OnRemFolder(self, evt):
        fid = self.folderNames.GetFirstSelected()
        if fid > -1:
            fname = self.folderNames.GetItemText(fid)
            cur = cache901.db().cursor()
            cur.execute('delete from gpxfolders where foldername=?', (fname, ))
            cache901.db().commit()
            self.loadFolders()
    
    def loadFolders(self):
        self.folderNames.DeleteAllItems()
        cur = cache901.db().cursor()
        cur.execute('select foldername from gpxfolders order by foldername')
        for row in cur:
            self.folderNames.Append((row['foldername'], ))
    
    def forWingIde(self):
        isinstance(self.tabs, wx.Notebook)
        
        # Folders and Waypoints Tab
        isinstance(self.foldersAndWpts,          wx.Panel)
        isinstance(self.foldersWaypointSplitter, wx.SplitterWindow)
        
        isinstance(self.folderNames,  wx.ListCtrl)
        isinstance(self.btnAddFolder, wx.Button)
        isinstance(self.btnRemFolder, wx.Button)
        
        isinstance(self.geoWpts,   wx.ListCtrl)
        isinstance(self.btnAddWpt, wx.Button)
        isinstance(self.btnRemWpt, wx.Button)
        
        # POP3 Servers Tab
        isinstance(self.popServers,   wx.Panel)
        isinstance(self.pop3Splitter, wx.SplitterWindow)
        
        isinstance(self.pop3Servers,   wx.ListCtrl)
        isinstance(self.btnAddPop3Svr, wx.Button)
        isinstance(self.btnRemPop3Svr, wx.Button)
        
        isinstance(self.pop3ServerName, wx.TextCtrl)
        isinstance(self.pop3Username,   wx.TextCtrl)
        isinstance(self.pop3Password,   wx.TextCtrl)
        isinstance(self.pop3UseSSL,     wx.CheckBox)
        isinstance(self.pop3Save,       wx.Button)
        
        # IMAP4 Servers Tab
        isinstance(self.imapServers, wx.Panel)
        isinstance(self.imap4Splitter, wx.SplitterWindow)
        
        isinstance(self.imap4SvrList, wx.ListCtrl)
        isinstance(self.btnAddImap4Svr, wx.Button)
        isinstance(self.btnRemImap4Svr, wx.Button)
        
        isinstance(self.imap4ServerName, wx.TextCtrl)
        isinstance(self.imap4Username,   wx.TextCtrl)
        isinstance(self.imap4Password,   wx.TextCtrl)
        isinstance(self.imap4Folder,     wx.Choice)
        isinstance(self.imap4UseSSL,     wx.CheckBox)
        isinstance(self.imap4Save,       wx.Button)

