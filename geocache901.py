#!/usr/bin/env python
# Three files have very similar code pieces. They are:
#   * geocache901
#   * geocache901.py
#   * cache901/app.py
# The reason for this is different environments with different needs.
# geocache901 is the main shell script to run for UNIX-type settings
# geocache901.py is required for py2app (OSX Bundle Maker) to work
# cache901/app.py is the main debug file in Wingware IDE, so that
#    breakpoints work properly (psyco stops the breakpoints from
#    working in Wingware IDE)
# As such, all three of these need to be kept in sync. Fortunately,
# there is extremely little logic in here. It's mostly a startup
# shell, so this bit of code can be mostly ignored. This note is
# just to explain why these pieces are here, and why all of them must
# be updated if one of them is.

try:
    import psyco
    psyco.full()
except ImportError:
    pass

if not hasattr(sys, "frozen") and 'wx' not in sys.modules and 'wxPython' not in sys.modules:
    import wxversion
    wxversion.ensureMinimal("2.8")
import cache901.app

def main():
    app = cache901.app.Cache901App(redirect=False, useBestVisual=True)
    app.MainLoop()

if __name__ == '__main__':
    main()
