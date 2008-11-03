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

import unittest
import timeit
import os

import cache901
import cache901.xml901

parser = cache901.xml901.XMLParser()

def testXmlParse(xmlstr):
    global parser
    parser.parse(xmlstr)

class XmlTest(unittest.TestCase):
    def setUp(self):
        self.parser = cache901.xml901.XMLParser()
        cur = cache901.db().cursor()
        cur.execute("delete from caches")
        cur.execute("delete from logs")
        cur.execute("delete from locations")
        cur.execute("delete from hints")
        cur.execute("delete from travelbugs")
        cache901.db().commit()

    def TestXmlFragments(self):
        """
        This test is left for historical purposes. Change the first T in
        the method name to a lower case to make it run. Once the initial
        tests were completed, and a full file could be read, this test was
        no longer needed.
        """
        t = timeit.Timer('test.Xml901Speed.testXmlParse("""%s""")' % waypoint, 'import test.Xml901Speed')
        print "Parsing waypoint 100 times ... ",
        ttime = t.timeit(100)
        print "Done!"

        print '\tTime to parse waypoint 100 times: %3.3fs' % ttime
        print '\tParses per second: %3.3f' % (100.0/ttime)

        t = timeit.Timer('test.Xml901Speed.testXmlParse("""%s""")' % cache_simple, 'import test.Xml901Speed')
        print "Parsing simple cache 100 times ... ",
        ttime = t.timeit(100)
        print "Done!"

        print '\tTime to parse simple cache 100 times: %3.3fs' % ttime
        print '\tParses per second: %3.3f' % (100.0/ttime)

        t = timeit.Timer('test.Xml901Speed.testXmlParse("""%s""")' % hint, 'import test.Xml901Speed')
        print "Parsing hint 100 times ... ",
        ttime = t.timeit(100)
        print "Done!"

        print '\tTime to parse hint 100 times: %3.3fs' % ttime
        print '\tParses per second: %3.3f' % (100.0/ttime)

        t = timeit.Timer('test.Xml901Speed.testXmlParse("""%s""")' % log, 'import test.Xml901Speed')
        print "Parsing log 100 times ... ",
        ttime = t.timeit(100)
        print "Done!"

        print '\tTime to parse log 100 times: %3.3fs' % ttime
        print '\tParses per second: %3.3f' % (100.0/ttime)

        t = timeit.Timer('test.Xml901Speed.testXmlParse("""%s""")' % travelbug, 'import test.Xml901Speed')
        print "Parsing travelbug 100 times ... ",
        ttime = t.timeit(100)
        print "Done!"

        print '\tTime to parse travelbug 100 times: %3.3fs' % ttime
        print '\tParses per second: %3.3f' % (100.0/ttime)

        t = timeit.Timer('test.Xml901Speed.testXmlParse("""%s""")' % cache_full, 'import test.Xml901Speed')
        print "Parsing full cache 100 times ... ",
        ttime = t.timeit(100)
        print "Done!"

        print '\tTime to parse full cache 100 times: %3.3fs' % ttime
        print '\tParses per second: %3.3f' % (100.0/ttime)

    def testParseFullFile(self):
        path = cache901.__path__[0].split(os.sep)[:-3]
        path.extend(['trunk', 'docs', 'gpx', 'samples', '746247.gpx'])
        path = os.sep.join(path)
        fullfile = open(path).read()

        t = timeit.Timer('test.Xml901Speed.testXmlParse("""%s""")' % fullfile, 'import test.Xml901Speed')
        print "Parsing full file 1 time ... ",
        ttime = t.timeit(1)
        print "Done!"

        print '\tTime to parse full file 1 time: %3.3fs' % ttime



#####################
###  XML Samples  ###
#####################
waypoint = """
  <wpt lat="40.620333" lon="-75.383567">
    <time>2007-04-12T07:07:46.8730000-07:00</time>
    <name>S1EAFC</name>
    <cmt>1. What is this location called?
2. Name three buildings and what they are used for.</cmt>
    <desc>GCEAFC Stage 1</desc>
    <url>http://www.geocaching.com/seek/wpt.aspx?WID=619abe07-c3ed-420c-bbd0-8bdf00dfd01b</url>
    <urlname>GCEAFC Stage 1</urlname>
    <sym>Question to Answer</sym>
    <type>Waypoint|Question to Answer</type>
  </wpt>
"""

cache_simple = """
  <wpt lat="40.71365" lon="-75.280633">
    <time>2005-02-20T00:00:00.0000000-08:00</time>
    <name>GCMW2V</name>
    <desc>Wally's So Easy #4 by Shuecrew, Traditional Cache (2/1.5)</desc>
    <url>http://www.geocaching.com/seek/cache_details.aspx?guid=d314f32c-5b48-4c80-a4b1-f3c4ae01980c</url>
    <urlname>Wally's So Easy #4</urlname>
    <sym>Geocache</sym>
    <type>Geocache|Traditional Cache</type>
    <groundspeak:cache id="210735" available="True" archived="False" xmlns:groundspeak="http://www.groundspeak.com/cache/1/0">
      <groundspeak:name>Wally's So Easy #4</groundspeak:name>
      <groundspeak:placed_by>Shuecrew</groundspeak:placed_by>
      <groundspeak:owner id="286400">Shuecrew</groundspeak:owner>
      <groundspeak:type>Traditional Cache</groundspeak:type>
      <groundspeak:container>Micro</groundspeak:container>
      <groundspeak:difficulty>2</groundspeak:difficulty>
      <groundspeak:terrain>1.5</groundspeak:terrain>
      <groundspeak:country>United States</groundspeak:country>
      <groundspeak:state>Pennsylvania</groundspeak:state>
      <groundspeak:short_description html="False">Easily accessible. Located off of 248 - in between Easton and Nazareth, although I think it's got an Easton address. This one gets a 1.5 terrain rating because I don't think it's wheelchair accessible. ** Added a star for difficulty due to high Muggle activity **</groundspeak:short_description>
      <groundspeak:long_description html="False">This is the 4th in a Series of easy micro hides that are designed to provide a quick geocache fix. These micros can be found at lunchtime, a quick stop on the way home from work, running out on a weekend errand - just about any reason to get out of the house. This is a quick, easy way to squeeze in a find. The cache contains a log and a pencil, but you may want to bring your own writing instrument just in case. ENJOY!</groundspeak:long_description>
    </groundspeak:cache>
  </wpt>
"""

hint = """
  <wpt lat="40.71365" lon="-75.280633">
    <groundspeak:cache id="210735" available="True" archived="False" xmlns:groundspeak="http://www.groundspeak.com/cache/1/0">
      <groundspeak:encoded_hints>35 mm film canister. You won't need to get wet.</groundspeak:encoded_hints>
    </groundspeak:cache>
  </wpt>
"""

log = """
  <wpt lat="40.71365" lon="-75.280633">
    <groundspeak:cache id="210735" available="True" archived="False" xmlns:groundspeak="http://www.groundspeak.com/cache/1/0">
        <groundspeak:log id="47487076">
          <groundspeak:date>2008-06-29T19:00:00</groundspeak:date>
          <groundspeak:type>Found it</groundspeak:type>
          <groundspeak:finder id="1072011">merenner</groundspeak:finder>
          <groundspeak:text encoded="False">Found on the way to Tri States Treasure 2.  Found with The Soloist.</groundspeak:text>
        </groundspeak:log>
    </groundspeak:cache>
  </wpt>
"""

travelbug = """
  <wpt lat="40.71365" lon="-75.280633">
    <groundspeak:cache id="210735" available="True" archived="False" xmlns:groundspeak="http://www.groundspeak.com/cache/1/0">
        <groundspeak:travelbug id="567295" ref="TB11V3R">
          <groundspeak:name>Got Art?</groundspeak:name>
        </groundspeak:travelbug>
    </groundspeak:cache>
  </wpt>
"""

cache_full = """
  <wpt lat="40.71365" lon="-75.280633">
    <time>2005-02-20T00:00:00.0000000-08:00</time>
    <name>GCMW2V</name>
    <desc>Wally's So Easy #4 by Shuecrew, Traditional Cache (2/1.5)</desc>
    <url>http://www.geocaching.com/seek/cache_details.aspx?guid=d314f32c-5b48-4c80-a4b1-f3c4ae01980c</url>
    <urlname>Wally's So Easy #4</urlname>
    <sym>Geocache</sym>
    <type>Geocache|Traditional Cache</type>
    <groundspeak:cache id="210735" available="True" archived="False" xmlns:groundspeak="http://www.groundspeak.com/cache/1/0">
      <groundspeak:name>Wally's So Easy #4</groundspeak:name>
      <groundspeak:placed_by>Shuecrew</groundspeak:placed_by>
      <groundspeak:owner id="286400">Shuecrew</groundspeak:owner>
      <groundspeak:type>Traditional Cache</groundspeak:type>
      <groundspeak:container>Micro</groundspeak:container>
      <groundspeak:difficulty>2</groundspeak:difficulty>
      <groundspeak:terrain>1.5</groundspeak:terrain>
      <groundspeak:country>United States</groundspeak:country>
      <groundspeak:state>Pennsylvania</groundspeak:state>
      <groundspeak:short_description html="False">Easily accessible. Located off of 248 - in between Easton and Nazareth, although I think it's got an Easton address. This one gets a 1.5 terrain rating because I don't think it's wheelchair accessible. ** Added a star for difficulty due to high Muggle activity **</groundspeak:short_description>
      <groundspeak:long_description html="False">This is the 4th in a Series of easy micro hides that are designed to provide a quick geocache fix. These micros can be found at lunchtime, a quick stop on the way home from work, running out on a weekend errand - just about any reason to get out of the house. This is a quick, easy way to squeeze in a find. The cache contains a log and a pencil, but you may want to bring your own writing instrument just in case. ENJOY!</groundspeak:long_description>
      <groundspeak:encoded_hints>
      </groundspeak:encoded_hints>
      <groundspeak:logs>
        <groundspeak:log id="47487076">
          <groundspeak:date>2008-06-29T19:00:00</groundspeak:date>
          <groundspeak:type>Found it</groundspeak:type>
          <groundspeak:finder id="1072011">merenner</groundspeak:finder>
          <groundspeak:text encoded="False">Found on the way to Tri States Treasure 2.  Found with The Soloist.</groundspeak:text>
        </groundspeak:log>
        <groundspeak:log id="47462029">
          <groundspeak:date>2008-06-29T19:00:00</groundspeak:date>
          <groundspeak:type>Found it</groundspeak:type>
          <groundspeak:finder id="1699569">110204</groundspeak:finder>
          <groundspeak:text encoded="False">Cool little container!  TFTC!</groundspeak:text>
        </groundspeak:log>
        <groundspeak:log id="47018885">
          <groundspeak:date>2008-06-22T19:00:00</groundspeak:date>
          <groundspeak:type>Found it</groundspeak:type>
          <groundspeak:finder id="713800">padlinfool</groundspeak:finder>
          <groundspeak:text encoded="False">The log is still toast, wet toast.  Found after a brief search in a muggly spot.  Thanks!</groundspeak:text>
        </groundspeak:log>
        <groundspeak:log id="46483069">
          <groundspeak:date>2008-06-14T19:00:00</groundspeak:date>
          <groundspeak:type>Found it</groundspeak:type>
          <groundspeak:finder id="1563210">OESgeo4Fun</groundspeak:finder>
          <groundspeak:text encoded="False">I had to do some errands here and decided to take another shot at this one. Darn thing probably hit me in the face the last visits. Container was much too wet to even try removing.  I am going to email the owner and give the description  I hope this is acceptable.  Oesgeo4fun</groundspeak:text>
        </groundspeak:log>
        <groundspeak:log id="46320319">
          <groundspeak:date>2008-06-11T19:00:00</groundspeak:date>
          <groundspeak:type>Found it</groundspeak:type>
          <groundspeak:finder id="775450">rapprapp</groundspeak:finder>
          <groundspeak:text encoded="False">It is indeed still where it should be.  The log is completely saturated and I was unable to sign the log.  Looks like the little rubber gasket is worn out.  Thanks for the hide.</groundspeak:text>
        </groundspeak:log>
      </groundspeak:logs>
      <groundspeak:travelbugs />
    </groundspeak:cache>
  </wpt>
"""
