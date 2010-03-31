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
import tempfile
import urllib

import wx

import cache901
import cache901.ui
import cache901.util

from cache901 import sadbobjects

from xml.sax.saxutils import escape

class KML(object):
    def __init__(self):
        self.fh = None
        self.cacheids = None
        self.geo = wx.GetApp().GetTopWindow().geoicons
    
    def export(self, cacheids, outdir, nodesc=False):
        """
        cacheids is a list of cache id numbers that can be found in the
            database
        """
        self.cacheids = cacheids
        self.nodesc = nodesc
        cache901.notify('Validating output directory')
        self.validateOutdir(outdir)
        cache901.notify('Exporting icons')
        self.saveImages(outdir)
        cache901.notify('Writing KML header')
        self.writeHeader(outdir)
        cache901.notify('Writing KML styles')
        self.writeStyles()
        cache901.notify('Writing Search Locations')
        self.writeSearchLocations()
        cache901.notify('Writing CacheDays')
        self.writeCacheDays()
        cache901.notify('Writing Caches')
        self.writeCaches()
        cache901.notify('Writing KML footer')
        self.writeFooter()
    
    def safeName(self, name):
        return name.replace('|', '_').replace(' ', '_').replace('.','_').replace('-','_').lower()
    
    def validateOutdir(self, outdir):
        if not os.path.exists(outdir):
            try:
                os.makedirs(outdir)
            except OSError:
                raise Exception('Insufficient permissions to create directory %s. Aborting' % outdir)
        if not os.path.isdir(outdir):
            raise Exception('KML can only be exported to a directory, not a file, and %s is a file. Aborting' % outdir)
        try:
            fname = os.sep.join([outdir, "cache901.kml"])
            f=open(fname, "w")
            f.close()
            os.unlink(fname)
        except:
            raise Exception("Unable to write to directory %s. Aborting" % outdir)
        
    def saveImages(self, outdir):
        for name in self.geo.keys():
            outfile = os.sep.join([outdir, "%s.png" % self.safeName(name)])
            img = wx.ImageFromBitmap(self.geo[name])
            isinstance(img, wx.Image)
            if not img.SaveFile(outfile, wx.BITMAP_TYPE_PNG):
                raise Exception('Unable to save image file %s. Aborting' % outfile)

        
    def writeHeader(self, outdir):
        self.fh = open(os.sep.join([outdir, "cache901.kml"]), "w")
        self.fh.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        self.fh.write('<kml xmlns="http://earth.google.com/kml/2.1">\n')
        self.fh.write('<Document>\n')
        self.fh.write('  <name>Cache901 Export</name>\n')
        self.fh.write('\n')
        
    def writeStyles(self):
        for style in self.geo.keys():
            self.fh.write('  <Style id="%s">\n' % self.safeName(style))
            self.fh.write('    <IconStyle>\n')
            self.fh.write('      <Icon>\n')
            self.fh.write('        <href>%s.png</href>\n' % self.safeName(style))
            self.fh.write('      </Icon>\n')
            self.fh.write('    </IconStyle>\n')
            self.fh.write('  </Style>\n')
        self.fh.write('\n')

    def writeSearchLocations(self):
        self.fh.write('  <Folder>\n')
        self.fh.write('    <name>Search Origins</name>\n')
        for wpt in cache901.util.getSearchLocs():
            self.fh.write('    <Placemark>\n')
            self.fh.write('      <name>%s</name>\n' % escape(cache901.util.forceAscii(wpt.name)))
            self.fh.write('      <styleUrl>#searchloc</styleUrl>\n')
            self.fh.write('      <Point>\n')
            self.fh.write('        <extrude>1</extrude>\n')
            self.fh.write('        <coordinates>%f,%f</coordinates>\n' % (wpt.lon, wpt.lat))
            self.fh.write('      </Point>\n')
            self.fh.write('    </Placemark>\n')
        self.fh.write('  </Folder>\n')
    
    def writeCacheDays(self):
        self.fh.write('  <Folder>\n')
        self.fh.write('    <name>Cache Days</name>\n')
        for cd in cache901.db().query(sadbobjects.CacheDayNames):
            visible = True
            for cache in cd.caches:
                if cache.cache_type == 1:
                    visible = visible and (cache.cache_id in self.cacheids)
            if visible:
                self.fh.write('    <Placemark>\n')
                self.fh.write('      <name>%s</name>\n' % escape(cache901.util.forceAscii(cd.dayname)))
                self.fh.write('      <LineString>\n')
                self.fh.write('        <extrude>1</extrude>\n')
                self.fh.write('        <tesselate>1</tesselate>\n')
                self.fh.write('        <coordinates>')
                self.fh.write(' '.join(map(lambda x: "%f,%f" % (x.cache.lon, x.cache.lat), cd.caches)))
                self.fh.write('</coordinates>\n')
                self.fh.write('      </LineString>\n')
                self.fh.write('    </Placemark>\n')
        self.fh.write('  </Folder>\n')
    
    def writeCaches(self):
        curtype = ''
        first=True
        qry = cache901.db().query(sadbobjects.Caches).order_by(sadbobjects.Caches.type).order_by(sadbobjects.Caches.name)
        for cache in qry:
            if cache.cache_id not in self.cacheids:
                continue
            kmlname = escape("%s - %s (%1.1f / %1.1f)" % (cache901.util.forceAscii(cache.name), cache901.util.forceAscii(cache.url_name), cache.difficulty, cache.terrain))
            if cache.type != curtype:
                curtype = cache.type
                if not first: self.fh.write('  </Folder>\n\n')
                self.fh.write('  <Folder>\n')
                self.fh.write('    <name>%ss</name>\n' % escape(curtype.replace("Geocache|", "")))
                first=False
            self.fh.write('    <Placemark>\n')
            self.fh.write('      <name>%s</name>\n' % kmlname)
            self.fh.write('      <styleUrl>#%s</styleUrl>\n' % self.safeName(cache.type))
            if not self.nodesc and cache.url is not None and len(cache.url) > 0:
                self.fh.write('      <description><![CDATA[<a href="%s">Full Cache Listing</a>]]></description>\n' % cache.url)
            self.fh.write('      <Point>\n')
            self.fh.write('        <extrude>1</extrude>\n')
            self.fh.write('        <coordinates>%f,%f</coordinates>\n' % (cache.lon, cache.lat))
            self.fh.write('      </Point>\n')
            self.fh.write('    </Placemark>\n')
        if not first: self.fh.write('  </Folder>\n\n')
            
    def writeFooter(self):
        self.fh.write('</Document>\n')
        self.fh.write('</kml>\n')
        self.fh.close()
        self.fh = None
        self.cacheids = None
    
    def forWingIde(self):
        isinstance(self.geo, cache901.ui.geoicons)