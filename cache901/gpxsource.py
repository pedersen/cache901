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

import email
import email.message
import email.parser
import imaplib
import os
import os.path
import poplib
import zipfile

from cStringIO import StringIO

import cache901

class GPXSource(object):
    # Objects of this interface must be iterable. Furthermore, they must
    # return the next gpx file in their data set. Callers will only care
    # about the gpx files, so only those get returned.
    # gpx objects are required to be either files or file like objects
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
                self.count = self.count + 1
                cache901.notify('Processing Message %s' % self.msgnums[self.count])
                typ, pmsg = self.imap4.fetch(self.msgnums[self.count], '(RFC822)')
                msg = self.parser.parsestr(pmsg[0][1])
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
                print 'Processing Message %s, Zip Attachment, File %s' % (self.msgnums[self.count], self.gpxlist[-1])
                return self.zfile.read(self.gpxlist.pop())
        raise StopIteration