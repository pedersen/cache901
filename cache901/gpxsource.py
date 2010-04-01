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
import datetime
import email
import email.iterators
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
import wx.grid

import cache901
import cache901.options
import cache901.ui
import cache901.ui_xrc
import cache901.validators

from cache901.xml901 import parse
from cache901.sadbobjects import *
from cache901 import sadbobjects
from sqlalchemy import func, and_

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
        while self.count <= len(self.msgnums)-1:
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
        self.cfilename = os.sep.join([cache901.cfg().dbpath, 'gccom_cookie.jar'])
        self.ltrans = cache901.ui.logTrans()
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
        time.sleep((random.random()*2)+0.5)
        
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
        raise StopIteration
    
    def postCacheLog(self, logEntry):
        isinstance(logEntry, cache901.sadbobjects.Logs)
        
        # prep timestamps for loading
        now = datetime.datetime.now()
        isinstance(now, datetime.datetime)
        month = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'][now.month-1]
        nowstr='%s/%02d/%d' % (month, now.day, now.year)
        if time.daylight:
            logEntry.date += time.altzone
        else:
            logEntry.date += time.timezone
        logdate = datetime.datetime.fromtimestamp(logEntry.date)
        isinstance(logdate, datetime.datetime)
        
        # prep web access
        dbocache = cache901.db().query(sadbobjects.Cache).get(logEntry.cache_id)
        cachename = '%s - %s' % (dbocache.name, dbocache.url_name)
        headers = {'User-agent' : self.useragent }
        self.wwwSetup()
        cfind = 'http://www.geocaching.com/seek/log.aspx?ID='
        curl = '%s%d' % (cfind, logEntry.cache_id)
        
        # download log posting page to retrieve __VIEWSTATE
        cache901.notify('Retrieving log page for cache id %s' % cachename)
        page = urllib2.urlopen(curl)
        time.sleep((random.random()*2)+0.5)
        
        # post log entry, filling in all necessary fields
        cache901.notify('Posting log entry for cache id %s' % cachename)
        m = re.match(r'.+?id="__VIEWSTATE"\s+value="(.+?)"', page.read(), re.S)
        postdata = {
            '__VIEWSTATE': m.group(1),
            'LogBookPanel1$DateTimeLogged' : nowstr,
            'LogBookPanel1$DateTimeLogged$Day' : logdate.day,
            'LogBookPanel1$DateTimeLogged$Month' : logdate.month,
            'LogBookPanel1$DateTimeLogged$Year' : logdate.year,
            'LogBookPanel1$LogButton' : 'Submit log entry',
            'LogBookPanel1$ddLogType' : self.ltrans.getWeb(logEntry.type),
            'LogBookPanel1$tbLogInfo' : logEntry.log_entry
            }
        fromvalues = urllib.urlencode(postdata)
        request = urllib2.Request(curl, fromvalues, headers)
        page = urllib2.urlopen(request)
        self.wwwClose()
        cache901.notify('Posted log entry for cache id %s' % cachename)
    
def gpxSyncAll(callingwin):
    dbsession = cache901.db()
    
    # Next, validate that we have some sources to synchronize
    srccount = dbsession.query(func.count(EmailSources.emailid).label('cnt')).first().cnt + \
             dbsession.query(func.count(GpxFolders.foldername).label('cnt')).first().cnt + \
             dbsession.query(func.count(WatchedWayPoints.waypoint_name).label('cnt')).first().cnt

    if srccount == 0:
        wx.MessageBox('Warning: No GPX Sources have been defined yet.\nPlease define some now.', 'No GPX Sources', wx.ICON_EXCLAMATION | wx.OK)
        gpxsrc = GPXSourceUI()
        gpxsrc.ShowModal()
    
    # Next, check if we have logs to upload, show the log upload window if we do, and upload any results
    loguploadtable = LogUploadTable()
    if len(loguploadtable.logs) > 0:
        uploadergui = LogUploadGUI(loguploadtable, callingwin)
        if uploadergui.ShowModal() == wx.ID_OK:
            for acctidx in range(len(loguploadtable.accounts)):
                acct = None
                dbacct = loguploadtable.accounts[acctidx]
                for logidx in range(len(loguploadtable.logs)):
                    uplog = loguploadtable.logs[logidx]
                    savedentry = uplog.log_entry
                    if loguploadtable.marks[logidx]:
                        uplog.my_log_uploaded = True
                        uplog.Save()
                    elif loguploadtable.uploads[logidx][acctidx]:
                        if acct is None:
                            acct = GeoCachingComSource(dbacct.username, dbacct.password)
                        if dbacct.isteam:
                            uplog.log_entry = 'Team %s logging the cache' % dbacct.username
                        acct.postCacheLog(uplog)
                        uplog.log_entry = savedentry
                        uplog.my_log_uploaded = True
                        uplog.Save()
                del acct
    
    # Next, gather gpx sources lists
    folders = []
    wpts = []
    popaccts = []
    imapaccts = []
    for folder in dbsession.query(sadbobjects.GpxFolders).order_by(sadbobjects.GpxFolders.foldername):
        folders.append(folder.foldername)
    for wpt in dbsession.query(sadbobjects.WatchedWayPoints).order_by(sadbobjects.WatchedWayPoints.waypoint_name):
        wpts.append(wpt.waypoint_name)
    for pop in dbsession.query(sadbobjects.EmailSources).filter(sadbobjects.EmailSources.svrtype == 'pop'):
        popaccts.append(pop.emailid)
    for imap in dbsession.query(sadbobjects.EmailSources).filter(sadbobjects.EmailSources.svrtype == 'imap'):
        imapaccts.append(imap.emailid)
        
    # Synchronize folders
    for folder in folders:
        fld = FolderSource(folder)
        for gpxfile in fld:
            parse(gpxfile, False)
    
    # Synchronize POP3 sources
    for popid in popaccts:
        email = cache901.db().query(sadbobjects.EmailSources).get(popid)
        popsrc = PopSource(email.svrname, email.username, email.password, email.usessl)
        for gpxfile in popsrc:
            parse(gpxfile, False)
            
    # Synchronize IMAP4 sources
    for imapid in imapaccts:
        email = cache901.db().query(sadbobjects.EmailSources).get(imapid)
        imapsrc = IMAPSource(email.svrname, email.username, email.password, email.usessl, email.deffolder)
        for gpxfile in imapsrc:
            parse(gpxfile, False)
            
    # Finally, perform all database maintenance
    cache901.db().maintdb()

class GPXSourceUI(cache901.ui_xrc.xrcGPXSourcesUI):
    def __init__(self, parent=None):
        cache901.ui_xrc.xrcGPXSourcesUI.__init__(self, parent)
        self.foldersWaypointSplitter.SetValidator(cache901.validators.splitValidator('gpxfoldersplit'))
        self.pop3Splitter.SetValidator(cache901.validators.splitValidator('gpxpop3split'))
        self.imap4Splitter.SetValidator(cache901.validators.splitValidator('gpximap4split'))
        
        w,h = self.GetTextExtent("QQQQQQQQQQQQQQQQQQ")
        self.folderNames.InsertColumn(0, 'Folder Name', width=w)
        self.geoWpts.InsertColumn(0, 'Watched Waypoints', width=w)
        self.pop3Servers.InsertColumn(0, 'POP3 Server', width=w)
        self.imap4SvrList.InsertColumn(0, 'IMAP Server', width=w)
        
        self.loadFolders()
        self.loadWpts()
        self.loadPopAccounts()
        self.loadImapAccounts()
        
        self.Bind(wx.EVT_BUTTON, self.OnAddFolder,          self.btnAddFolder)
        self.Bind(wx.EVT_BUTTON, self.OnRemFolder,          self.btnRemFolder)
        self.Bind(wx.EVT_BUTTON, self.OnAddWpt,             self.btnAddWpt)
        self.Bind(wx.EVT_BUTTON, self.OnRemWpt,             self.btnRemWpt)
        self.Bind(wx.EVT_BUTTON, self.OnAddPop,             self.btnAddPop3Svr)
        self.Bind(wx.EVT_BUTTON, self.OnRemPop,             self.btnRemPop3Svr)
        self.Bind(wx.EVT_BUTTON, self.OnSavePop,            self.pop3Save)
        self.Bind(wx.EVT_BUTTON, self.OnAddImap,            self.btnAddImap4Svr)
        self.Bind(wx.EVT_BUTTON, self.OnRemImap,            self.btnRemImap4Svr)
        self.Bind(wx.EVT_BUTTON, self.OnSaveImap,           self.imap4Save)
        self.Bind(wx.EVT_BUTTON, self.OnRefreshImapFolders, self.btnRefreshFolders)
        
        self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.OnLoadPop,  self.pop3Servers)
        self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.OnLoadImap, self.imap4SvrList)
        
    def OnAddImap(self, evt):
        email = sadbobjects.EmailSources()
        email.svrname = 'unknownhost.com'
        email.username = 'unknown'
        email.imap = True
        cache901.db().add(email)
        cache901.db().commit()
        self.loadImapAccounts()
        self.imap4SvrList.Select(self.imap4SvrList.FindItemData(0, email.emailid))
    
    def OnRemImap(self, evt):
        if wx.MessageBox('Warning! This operation cannot be undone!', 'Really Delete?', wx.YES_NO) == wx.NO:
            return
        eid = self.imap4SvrList.GetFirstSelected()
        if eid > -1:
            email = cache901.db().query(sadbobjects.EmailSources).get(self.imap4SvrList.GetItemData(eid))
            cache901.db().delete(email)
            cache901.db().commit()
            self.loadImapAccounts()
    
    def OnLoadImap(self, evt):
        eid = self.imap4SvrList.GetFirstSelected()
        if eid > -1:
            email = cache901.db().query(sadbobjects.EmailSources).get(self.imap4SvrList.GetItemData(eid))
            self.btnRemImap4Svr.Enable()
            self.btnRefreshFolders.Enable()
            self.imap4Save.Enable()
            self.imap4ServerName.Enable()
            self.imap4Username.Enable()
            self.imap4Password.Enable()
            self.imap4Folder.Enable()
            self.imap4UseSSL.Enable()
            self.imap4ServerName.SetValue(email.svrname)
            self.imap4Username.SetValue(email.username)
            self.imap4Password.SetValue(email.password)
            self.imap4Folder.SetItems([email.deffolder])
            self.imap4Folder.SetSelection(0)
            self.imap4UseSSL.SetValue(email.usessl)
    
    def OnSaveImap(self, evt):
        eid = self.imap4SvrList.GetFirstSelected()
        if eid > -1:
            email = cache901.db().query(sadbobjects.EmailSources).get(self.imap4SvrList.GetItemData(eid))
            email.svrname   = self.imap4ServerName.GetValue()
            email.username  = self.imap4Username.GetValue()
            email.password  = self.imap4Password.GetValue()
            email.deffolder = self.imap4Folder.GetItems()[self.imap4Folder.GetSelection()]
            email.usessl    = self.imap4UseSSL.GetValue()
            cache901.db().commit()
            self.loadImapAccounts()
    
    def OnRefreshImapFolders(self, evt):
        eid = self.imap4SvrList.GetFirstSelected()
        if eid > -1:
            email = cache901.db().query(sadbobjects.EmailSources).get(self.imap4SvrList.GetItemData(eid))
            email.svrname   = self.imap4ServerName.GetValue()
            email.username  = self.imap4Username.GetValue()
            email.password  = self.imap4Password.GetValue()
            email.usessl    = self.imap4UseSSL.GetValue()
            cache901.db().commit()
            cdef = self.imap4Folder.GetItems()[self.imap4Folder.GetSelection()]
            imapc = None
            try:
                if email.usessl: imapc = imaplib.IMAP4_SSL(email.svrname)
                else: imapc = imaplib.IMAP4(email.svrname)
            except Exception, e:
                wx.MessageBox(str(e), 'Invalid Hostname')
                return
            try:
                imapc.login(email.username, email.password)
            except Exception, e:
                wx.MessageBox(str(e), 'Invalid User/Password')
                return
            self.imap4Folder.SetItems(sorted(map(lambda x: x[x.rfind(' ')+1:].strip('"'), imapc.list()[1])))
            idx = self.imap4Folder.FindString(cdef)
            if idx == wx.NOT_FOUND: idx=0
            self.imap4Folder.Select(idx)
    
    def loadImapAccounts(self):
        self.imap4SvrList.DeleteAllItems()
        for email in cache901.db().query(sadbobjects.EmailSources).filter(sadbobjects.EmailSources.svrtype=='imap').order_by(sadbobjects.EmailSources.svruser, sadbobjects.EmailSources.svrname):
            eid = self.imap4SvrList.Append(('%s@%s' % (email.svruser, email.svrname), ))
            self.imap4SvrList.SetItemData(eid, email.emailid)
        self.btnRemImap4Svr.Disable()
        self.imap4ServerName.Disable()
        self.imap4Username.Disable()
        self.imap4Password.Disable()
        self.imap4Folder.Disable()
        self.btnRefreshFolders.Disable()
        self.imap4UseSSL.Disable()
        self.imap4Save.Disable()
    
    def OnAddPop(self, evt):
        email = sadbobjects.EmailSources()
        email.svrname = 'unknownhost.com'
        email.username = 'unknown'
        cache901.db().add(email)
        cache901.db().commit()
        self.loadPopAccounts()
        self.pop3Servers.Select(self.pop3Servers.FindItemData(0, email.emailid))
    
    def OnRemPop(self, evt):
        if wx.MessageBox('Warning! This operation cannot be undone!', 'Really Delete?', wx.YES_NO) == wx.NO:
            return
        eid = self.pop3Servers.GetFirstSelected()
        if eid > -1:
            email = cache901.db().query(sadbobjects.EmailSources).get(self.pop3Servers.GetItemData(eid))
            cache901.db().delete(email)
            cache901.db().commit()
            self.loadPopAccounts()
    
    def OnLoadPop(self, evt):
        eid = self.pop3Servers.GetFirstSelected()
        if eid > -1:
            email = cache901.db().query(sadbobjects.EmailSources).get(self.pop3Servers.GetItemData(eid))
            self.pop3ServerName.SetValue(email.svrname)
            self.pop3ServerName.Enable()
            self.pop3Username.SetValue(email.username)
            self.pop3Username.Enable()
            self.pop3Password.SetValue(email.password)
            self.pop3Password.Enable()
            self.pop3UseSSL.SetValue(email.usessl)
            self.pop3UseSSL.Enable()
            self.btnRemPop3Svr.Enable()
            self.pop3Save.Enable()
    
    def OnSavePop(self, evt):
        eid = self.pop3Servers.GetFirstSelected()
        if eid > -1:
            email = cache901.db().query(sadbobjects.EmailSources).get(self.pop3Servers.GetItemData(eid))
            email.svrname  = self.pop3ServerName.GetValue()
            email.username = self.pop3Username.GetValue()
            email.password = self.pop3Password.GetValue()
            email.usessl   = self.pop3UseSSL.GetValue()
            cache901.db().commit()
            self.loadPopAccounts()
    
    def loadPopAccounts(self):
        self.pop3Servers.DeleteAllItems()
        for email in cache901.db().query(sadbobjects.EmailSources).filter(sadbobjects.EmailSources.svrtype=='pop').order_by(sadbobjects.EmailSources.svruser, sadbobjects.EmailSources.svrname):
            eid = self.pop3Servers.Append(('%s@%s' % (email.svruser, email.svrname), ))
            self.pop3Servers.SetItemData(eid, emailemailid)
        self.btnRemPop3Svr.Disable()
        self.pop3ServerName.Disable()
        self.pop3Username.Disable()
        self.pop3Password.Disable()
        self.pop3UseSSL.Disable()
        self.pop3Save.Disable()
    
    def OnAddWpt(self, evt):
        wpt = wx.GetTextFromUser('Enter the waypoint name:', 'Enter Waypoint Name').upper()
        if wpt != '':
            w = cache901.db().query(sadbobjects.WatchedWayPoints).get(wpt)
            if not w:
                w = sadbobjects.WatchedWayPoints()
                w.waypoint_name = wpt
                cache901.db().add(w)
                cache901.db().commit(w)
            self.loadWpts()
    
    def OnRemWpt(self, evt):
        if wx.MessageBox('Warning! This operation cannot be undone!', 'Really Delete?', wx.YES_NO) == wx.NO:
            return
        wptid = self.geoWpts.GetFirstSelected()
        if wptid > -1:
            fname = self.geoWpts.GetItemText(wptid)
            w = cache901.db().query(sadbobjects.WatchedWayPoints).get(fname)
            if w:
                cache901.db().delete(w)
                cache901.db().commit()
            self.loadWpts()
    
    def loadWpts(self):
        self.geoWpts.DeleteAllItems()
        for wpt in cache901.db().query(sadbobjects.WatchedWayPoints).order_by(sadbobjects.WatchedWayPoints.waypoint_name):
            self.geoWpts.Append((wpt.waypoint_name, ))
    
    def OnAddFolder(self, evt):
        dirpath = wx.DirSelector('Add Watched Folder')
        if dirpath != "":
            f = cache901.db().query(sadbobjects.GpxFolders).get(dirpath)
            if not f:
                f = sadbobjects.GpxFolders()
                f.foldername = dirpath
                cache901.db().add(f)
                cache901.db().commit()
            self.loadFolders()
    
    def OnRemFolder(self, evt):
        if wx.MessageBox('Warning! This operation cannot be undone!', 'Really Delete?', wx.YES_NO) == wx.NO:
            return
        fid = self.folderNames.GetFirstSelected()
        if fid > -1:
            fname = self.folderNames.GetItemText(fid)
            f = cache901.db().query(sadbobjects.GpxFolders).get(fname)
            if f:
                cache901.db().delete(f)
                cache901.db().commit()
            self.loadFolders()
    
    def loadFolders(self):
        self.folderNames.DeleteAllItems()
        for folder in cache901.db().query(sadbobjects.GpxFolders).order_by(sadbobjects.GpxFolders.foldername):
            self.folderNames.Append((folder.foldername, ))
    
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
        
        isinstance(self.imap4ServerName,   wx.TextCtrl)
        isinstance(self.imap4Username,     wx.TextCtrl)
        isinstance(self.imap4Password,     wx.TextCtrl)
        isinstance(self.imap4Folder,       wx.Choice)
        isinstance(self.btnRefreshFolders, wx.Button)
        isinstance(self.imap4UseSSL,       wx.CheckBox)
        isinstance(self.imap4Save,         wx.Button)

class LogUploadTable(wx.grid.PyGridTableBase):
    def __init__(self):
        wx.grid.PyGridTableBase.__init__(self)
        self.accounts = []
        self.logs = []
        self.caches = {}
        self.accounts = cache901.db().query(sadbobjects.Accounts). \
            order_by(sadbobjects.Accounts.ispremium.desc(), sadbobjects.Accounts.isteam.desc()).all()
        for log in cache901.db().query(sadbobjects.Logs).filter(and_(
            sadbobjects.Logs.my_log_uploaded == 0,
            sadbobjects.Logs.finder.in_(cache901.db().query(sadbobjects.Accounts.username)))):
            self.logs.append(logs)
            cid = log.cache.cache_id
            self.caches[cid] = log.cache
        self.uploads = map(lambda x: map(lambda y: False, self.accounts), self.logs)
        self.marks = map(lambda x: False, self.logs)
        self.centercell = wx.grid.GridCellAttr()
        self.centercell.SetAlignment(wx.ALIGN_CENTER, wx.ALIGN_CENTER)
        self.nullattr = wx.grid.GridCellAttr()
    
    def GetNumberRows(self):
        return len(self.logs)
    
    def GetNumberCols(self):
        return 3+len(self.accounts)
    
    def IsEmptyCell(self, row, col):
        return False
    
    def GetValue(self, row, col):
        if col == 0:
            return self.caches[self.logs[row].cache_id].url_name
        if col == 1:
            logdate = datetime.datetime.fromtimestamp(self.logs[row].date).date()
            isinstance(logdate, datetime.date)
            return logdate.isoformat()
        if col == 2:
            return self.marks[row]
        return self.uploads[row][col-3]
    
    def SetValue(self, row, col, value):
        if col == 2:
            self.marks[row] = value
            self.uploads[row] = map(lambda x: False, self.accounts)
        if col >= 3:
            self.uploads[row][col-3] = value
    
    def GetColLabelValue(self, col):
        if col == 0:
            return 'Cache Name'
        elif col == 1:
            return 'Log Date'
        elif col == 2:
            return 'Mark As\nUploaded'
        else:
            acct = self.accounts[col-3]
            if acct.isteam:
                team = 'Team '
            else:
                team = ''
            return '%s%s @\n%s' % (team, acct.username, acct.sitename)
    
    def GetRowLabelValue(self, row):
        return self.caches[self.logs[row].cache_id].name
    
    def GetTypeName(self, row, col):
        if col == 0 or col == 1:
            return wx.grid.GRID_VALUE_STRING
        else:
            return wx.grid.GRID_VALUE_BOOL
    
    def GetAttr(self, row, col, kind):
        if col >= 2:
            self.centercell.IncRef()
            return self.centercell
        else:
            self.nullattr.IncRef()
            return self.nullattr
        
class LogUploadGUI(cache901.ui_xrc.xrcLogUploadUI):
    def __init__(self, table, parent=None):
        cache901.ui_xrc.xrcLogUploadUI.__init__(self, parent)
        self.logGrid.SetTable(table)
        self.logGrid.AutoSize()
        self.logGrid.EnableDragGridSize()
    
    def forWingIde(self):
        isinstance(self.logGrid, wx.grid.Grid)
        
        
