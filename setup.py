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

# py2exe: http://www.py2exe.org/
# py2app: http://pypi.python.org/pypi/py2app/
# easy dmg: http://www.versiontracker.com/dyn/moreinfo/macosx/26358

# OSX Issue:
# GPSBabel could not run correctly from the app bundle, but had already been
# release. As a result, the app bundle requires the svn version of
# Python-GPSBabel. That version will be released when the next version of
# Cache901 comes out.

# OSX Serial issue:
# When installing pyserial on OSX, an egg is created. py2app doesn't
# support eggs correctly. As a result, the serial module was not being
# included, and I could not make it happen. The fix I employed (which is
# far from ideal) was to execute the following commands:
#  mv /Library/Frameworks/Python.framework/Versions/2.5/lib/python2.5/site-packages/pyserial-2.4-py2.5.egg/serial /Library/Frameworks/Python.framework/Versions/2.5/lib/python2.5/site-packages
# rm -rf /Library/Frameworks/Python.framework/Versions/2.5/lib/python2.5/site-packages/pyserial-2.4-py2.5.egg
# After that, the serial module was correctly included

# OSX Issue:
# Seems that macholib has problems with the way these options are for OSX.
# Had to correct by installing an updated version. Used this command:
# sudo easy_install "macholib==dev"

from distutils.core import setup
import os, os.path, sys


try:
    import py2exe
except ImportError, e:
    pass

try:
    import py2app
except ImportError, e:
    pass

if sys.platform == "win32":
    try:
        import win32file
    except:
        print "Without win32file, pyserial will fail on Windows. Aborting."
        sys.exit(1)
    datafiles = [('cache901', [os.sep.join(['cache901', 'shield.ico']), os.sep.join(['osfiles', 'gpsbabel.exe']), os.sep.join(['osfiles', 'libexpat.dll'])],) ]
elif sys.platform == "darwin":
    datafiles = []
else:
    datafiles = []

try:
    import wxversion
    wxversion.ensureMinimal("2.8")
    import wx
except:
    print "Without wx, this program will fail. Aborting."
    sys.exit(1)

try:
    import serial
except:
    print "Without serial, this program will fail. Aborting."
    sys.exit(1)

try:
    import sqlite3
except:
    print "Without sqlite3, this program will fail. Aborting."
    sys.exit(1)

try:
    import gpsbabel
except:
    print "Without gpsbabel, this program will fail. Aborting."
    sys.exit(1)

setup(name='Cache901',
        version="0.6",
        description='Paperless Geocaching Tool',
        author='Michael Pedersen',
        author_email='m.pedersen@icelus.org ',
        url='http://www.cache901.org/',
        scripts=['geocache901',],
        packages=['cache901', ],
        package_data={'cache901' : ['shield.ico', ]},
        # Combined options for py2app and py2exe
        options = {
            "py2exe": {
                "dll_excludes": ["user32.dll", "ole32.dll", "kernel32.dll", "rpcrt4.dll", "oleaut32.dll", "shell32.dll", "shlwapi.dll", "ntdll.dll", "comdlg32.dll", "wsock32.dll", "comctl32.dll", "advapi32.dll", "ws2_32.dll", "gdi32.dll", "winmm.dll", "ws2help.dll", "mswsock.dll"]
            },
            "py2app" : {
                "resources": [os.sep.join(['cache901', 'shield.ico']), os.sep.join(['osfiles', 'gpsbabel'])],
                "iconfile": "shield.icns"
            }
        },
        # py2exe options below here
        data_files = datafiles,
        console=[{
            'script' : 'geocache901',
            'icon_resources' : [(1, os.sep.join(['cache901', 'shield.ico']))]
        }],
        windows=[{
            'script' : 'geocache901',
            'icon_resources' : [(1, os.sep.join(['cache901', 'shield.ico']))]
        }],
        # py2app options below here
        app = ['geocache901.py', ]
    )

if sys.platform=="win32":
    os.rename(os.sep.join(['dist', 'cache901', 'gpsbabel.exe']), os.sep.join(['dist', 'gpsbabel.exe']))
    os.rename(os.sep.join(['dist', 'cache901', 'libexpat.dll']), os.sep.join(['dist', 'libexpat.dll']))
