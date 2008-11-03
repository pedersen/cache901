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

import cache901.app

def main():
    app = cache901.app.Cache901App()
    app.MainLoop()

if __name__ == '__main__':
    main()
