# -*- coding: latin-1 -*-
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

import unittest
import cache901.util
from decimal import Decimal

import wx

# Oxford, NJ
lat1 =  40.8130
lon1 = -75.0047

# Somerset, NJ
lat2 =  40.5013
lon2 = -74.5325

class utilTest(unittest.TestCase):
    def testDistanceExact(self):
        self.failUnless("%3.4f" % cache901.util.distance_exact(lat1, lon1, lat2, lon2) == "32.8086")

    def testDMSToDec(self):
        try:
            cache901.util.dmsToDec('X 45%s 33\' 19.980"' % cache901.util.degsym)
            self.fail('Direction X is invalid, but was accepted')
        except cache901.util.InvalidDegFormat:
            pass
        try:
            cache901.util.dmsToDec('N X5%s 33\' 19.980"' % cache901.util.degsym)
            self.fail('X5 is invalid, but was accepted')
        except cache901.util.InvalidDegFormat:
            pass
        try:
            cache901.util.dmsToDec('N 4533\' 19.980"')
            self.fail('4533\' is invalid, but was accepted')
        except cache901.util.InvalidDegFormat:
            pass
        try:
            cache901.util.dmsToDec('N4533\'19.980"')
            self.fail('N4533\'19.980" is invalid, but was accepted')
        except cache901.util.InvalidDegFormat:
            pass
        self.failUnless(cache901.util.dmsToDec("45.555555") == Decimal("45.555555"))
        ret = cache901.util.dmsToDec('N 45%s 33\' 19.980"' % cache901.util.degsym)
        self.failUnless(ret == Decimal("45.55555"), "Expected 45.55555, got %s" % ret)
        ret = cache901.util.dmsToDec('N45 33\' 19.980"')
        self.failUnless(ret == Decimal("45.55555"), "Expected 45.55555, got %s" % ret)
        ret = cache901.util.dmsToDec('N45 33 19.980"')
        self.failUnless(ret == Decimal("45.55555"), "Expected 45.55555, got %s" % ret)
        ret = cache901.util.dmsToDec('N45 33 19.980')
        self.failUnless(ret == Decimal("45.55555"), "Expected 45.55555, got %s" % ret)
        ret = cache901.util.dmsToDec('N45 30')
        self.failUnless(ret == Decimal("45.5"), "Expected 45.5, got %s" % ret)
        ret = cache901.util.dmsToDec('N45 30.75')
        self.failUnless(ret == Decimal("45.5125"), "Expected 45.5125, got %s" % ret)
        
    def testDecToDMS(self):
        (plus, ret) = cache901.util.decToDMS(Decimal("45.555555"))
        self.failUnless(plus == True, "Expected positive, got negative")
        self.failUnless(ret == ' 45%s 33\' 19.9980"' %cache901.util.degsym, "Expected %s, and got %s" % (" 45%s 33' 19.9980", (cache901.util.degsym, ret)))

    def testLatToDMS(self):
        ret = cache901.util.latToDMS(Decimal("45.555555"))
        self.failUnless(ret == 'N 45%s 33\' 19.9980"' % cache901.util.degsym, "Expected %s, and got %s" % ('N 45%s 33\' 19.9980"' % cache901.util.degsym, ret))
        ret = cache901.util.latToDMS(Decimal("-45.555555"))
        self.failUnless(ret == 'S 45%s 33\' 19.9980"' % cache901.util.degsym, "Expected %s, and got %s" % ('S 45%s 33\' 19.9980"' % cache901.util.degsym, ret))
    
    def testLonToDMS(self):
        ret = cache901.util.lonToDMS(Decimal("45.555555"))
        self.failUnless(ret == 'E 45%s 33\' 19.9980"' % cache901.util.degsym, "Expected %s, and got %s" % ('E 45%s 33\' 19.9980"' % cache901.util.degsym, ret))
        ret = cache901.util.lonToDMS(Decimal("-45.555555"))
        self.failUnless(ret == 'W 45%s 33\' 19.9980"' % cache901.util.degsym, "Expected %s, and got %s" % ('W 45%s 33\' 19.9980"' % cache901.util.degsym, ret))
        ret = cache901.util.lonToDMS(Decimal("-100.555555"))
        self.failUnless(ret == 'W100%s 33\' 19.9980"' % cache901.util.degsym, "Expected %s, and got %s" % ('W100%s 33\' 19.9980"' % cache901.util.degsym, ret))

    def testForceAscii(self):
        self.failUnless(cache901.util.forceAscii('abc' + u'\u1234' + '123') == 'abc123')

app = wx.PySimpleApp()