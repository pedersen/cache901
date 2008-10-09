# py2exe: http://www.py2exe.org/
# py2app: http://pypi.python.org/pypi/py2app/
# easy dmg: http://www.versiontracker.com/dyn/moreinfo/macosx/26358

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
    datafiles = [('cache901', [os.sep.join(['cache901', 'shield.ico'])],) ]
else:
    datafiles = []

setup(name='Cache901',
        version="0.2",
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
                "dll_excludes": ["user32.dll", "ole32.dll", "kernel32.dll", "rpcrt4.dll", "oleaut32.dll", "shell32.dll", "shlwapi.dll", "ntdll.dll", "comdlg32.dll", "wsock32.dll", "comctl32.dll", "advapi32.dll", "ws2_32.dll", "gdi32.dll", "winmm.dll", "ws2help.dll"]
            },
            "py2app" : {
                "resources": [os.sep.join(['cache901', 'shield.ico'])],
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

