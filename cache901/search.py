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

# Saved searches, too
# Fields to put in:
# Simple Fields
#   Max num of caches: 10, 25, 50, 100, 250, 500, no limit
#   Terrain is >=/=/<= rating
#   Difficulty is >=/=/<= rating
#   Set Radius from origin (requires origin)
# Complex Fields:
#   Cache Type (multi-select): any, traditional, virtual, event,
#      project ape, cito, mega-event, wherigo, multi-cache, letterbox,
#      webcam, earthcache, gps adventures
#   Container (multi-select): any, small, large, micro, other,
#      regular, unknown, virtual
#   Conditions (multi-select): I haven't found, I don't own,
#      are available to all users, are not on my ignore list,
#      found in the last 7 days, have travel bugs, is not active,
#      i have found, i own, are for members only, are on my watch list,
#      have not been found, updated in the last 7 days, is active
#   Within Countries *or* states/provinces
#   Set origin from origin locs, new loc, or gps
#   Placed During last week/month/year/date range