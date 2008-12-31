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

import wx

import cache901

def scrub():
    cfg = wx.Config.Get()
    isinstance(cfg, wx.Config)
    cfg.SetPath('/PerMachine')
    maxlogs = cfg.ReadInt("maxLogs", 10)
    cache901.notify('Scrubbing database of old/invalid data')
    con = cache901.db()
    cur = con.cursor()
    cur.execute("delete from travelbugs where cache_id not in (select cache_id from caches)")
    cur.execute("delete from hints where cache_id not in (select cache_id from caches)")
    cur.execute("delete from logs where cache_id not in (select cache_id from caches)")
    # update logs to show my_log for any logs where finder is in gpx accounts
    cache901.notify('Ensuring my logs are noted properly')
    cur.execute('update logs set my_log=1 where finder in (select username from accounts)')
    # delete logs after maxlogs entries for a given cache, keeping only the newest (and the my_log)
    cur.execute('select distinct id, cache_id, my_log from logs order by cache_id, id desc')
    cache_id = -1
    logcount = 0
    delthese = []
    for row in cur:
        if row['cache_id'] != cache_id:
            cache_id = row['cache_id']
            logcount = 0
        logcount += 1
        if logcount > maxlogs and row['my_log'] == 0:
            delthese.append(str(row['id']))
    cur.execute('delete from logs where id in (%s)' % ",".join(delthese))
    con.commit()
    cache901.notify('Recovering free space')
    cur.execute("vacuum")
    cache901.notify('Analyzing database to improve speed')
    cur.execute("analyze")
