# -*- coding: utf8 -*-
## File autogenerated by SQLAutoCode
## see http://code.google.com/p/sqlautocode/

__all__ = ['Version', 'Accounts', 'CacheDayNames', 'Categories', \
           'EmailSources', 'GpxFolders', 'Searches', 'WatchedWayPoints', \
           'Caches', 'Locations', 'AltCoords', 'Attributes', 'CacheDay', \
           'Hints', 'Logs', 'Notes', 'Photos', 'TravelBugs', 'DBSession', \
           'maintdb', 'scrub', 'delAllCaches', 'backup']

import datetime
import os
import zipfile

from sqlalchemy import *
from sqlalchemy.types import *
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import scoped_session, sessionmaker

import migrate.changeset

import cache901
import cache901.util

engine = None
DBSession = None
maker = None
DeclarativeBase = declarative_base()
metadata = None

def getDbVersion():
    try:
        version = DBSession.query(Version).order_by(Version.version.desc()).first().version
    except Exception, e:
        print str(e)
        version = 0
    return version

def init_db(debugging=False):
    global engine, DBSession, maker, DeclarativeBase, metadata
    
    if DBSession is not None:
        DBSession.close()
    
    if debugging:
        url = 'sqlite:///:memory:'
    else:
        url = cache901.cfg().dbfile
    
    engine = create_engine(url, echo=True)
    engine.connect().connection.create_function("distance", 4, cache901.util.distance_exact)
    
    maker = sessionmaker(autoflush=True, autocommit=False)
    
    DBSession = scoped_session(maker)
    DeclarativeBase.metadata.bind = engine
    DBSession.configure(bind=engine)
    metadata = DeclarativeBase.metadata
    
    dbups = sorted(filter(lambda x: x.startswith("db_v"), globals().keys()))
    dbver = getDbVersion()
    while dbver < len(dbups):
        globals()['db_v%03d' % (dbver+1)]()
        dbver = getDbVersion()

def maintdb():
    scrub()
    cache901.notify('Recovering unused disk space')
    engine.execute("vacuum")
    cache901.notify('Rebuilding database indices')
    engine.execute("analyze")


def scrub():
    maxlogs = cache901.cfg().dbMaxLogs
    cache901.notify('Scrubbing database of old/invalid data')
    if DBSession is not None:
        validids = DBSession.query(Caches.cache_id).all()
        for objtype in [TravelBugs, Hints, Logs, Notes, Photos, CacheDay, AltCoords]:
            for obj in DBSession.query(objtype).filter(not_(objtype.cache_id.in_(DBSession.query(Caches.cache_id)))):
                DBSession.delete(obj)
        ## update logs to show my_log for any logs where finder is in gpx accounts
        cache901.notify('Ensuring my logs are noted properly')
        for log in DBSession.query(Logs).filter(Logs.finder.in_(DBSession.query(Accounts.username))):
            log.my_log = 1
        cache_id = -1
        cache901.notify('Removing old logs')
        for log in DBSession.query(Logs).filter(Logs.my_log != 1):
            if log.cache_id != cache_id:
                cache_id = log.cache_id
                logcount = 0
            logcount += 1
            if logcount > maxlogs:
                DBSession.delete(log)
        DBSession.commit()
    

def delAllCaches():
    cache901.notify("Emptying all caches and waypoints from the database")
    for i in DBSession.query(Caches):
        DBSession.delete(i)
    for i in DBSession.query(Locations).filter(Locations.loc_type == 1):
        DBSession.delete(i)
    DBSession.commit()


def backup():
    dbpath = cache901.cfg().dbpath
    today = datetime.date.today().isoformat()
    ext = "-%s.zip" % (today)
    zfilename = os.sep.join([dbpath, 'Cache901_Backup%s' % ext])
    z=zipfile.ZipFile(zfilename, "w", allowZip64=True)
    for dbfile in filter(lambda x:x.lower().endswith('.sqlite'), os.listdir(cache901.cfg().dbpath)):
        dbfile = os.sep.join([dbpath, dbfile.encode('ascii')])
        arcname = "%s-%s.sqlite" % (os.path.splitext(os.path.split(dbfile)[1])[0], today)
        arcname = arcname.encode('ascii')
        cache901.notify('Backing up %s into %s' % (arcname, zfilename))
        z.write(dbfile, arcname, compress_type=zipfile.ZIP_DEFLATED)
    z.close()

def db_v001():
    metadata.create_all(engine)
    v = Version()
    v.version=6
    DBSession.add(v)
    DBSession.flush()
    DBSession.commit()

def db_v002():
    Searches.__table__.drop()
    Searches.__table__.create()
    Index(u'searches_name', Searches.name)
    Notes.__table__.drop()
    Notes.__table__.create()
    Index(u'notes_id', Notes.cache_id)
    Photos.__table__.drop()
    Photos.__table__.create()
    Index(u'photos_id', Photos.cache_id)
    v = Version()
    v.version=2
    DBSession.add(v)
    DBSession.flush()
    DBSession.commit()

def db_v003():
    CacheDay.__table__.drop()
    CacheDay.__table__.create()
    Index(u'cacheday_name', CacheDay.dayname)
    CacheDayNames.__table__.drop()
    CacheDayNames.__table__.create()
    v = Version()
    v.version=3
    DBSession.add(v)
    DBSession.flush()
    DBSession.commit()

def db_v004():
    Accounts.__table__.drop()
    Accounts.__table__.create()
    EmailSources.__table__.drop()
    EmailSources.__table__.create()
    GpxFolders.__table__.drop()
    GpxFolders.__table__.create()
    WatchedWayPoints.__table__.drop()
    WatchedWayPoints.__table__.create()
    v = Version()
    v.version=4
    DBSession.add(v)
    DBSession.flush()
    DBSession.commit()

def db_v005():
    chidden = Column('hidden', Integer, primary_key=False)
    lhidden = Column('hidden', Integer, primary_key=False)
    chidden.create(Caches.__table__)
    lhidden.create(Locations.__table__)
    AltCoords.__table__.create()
    v = Version()
    v.version=5
    DBSession.add(v)
    DBSession.flush()
    DBSession.commit()


def db_v006():
    AltCoords.__table__.drop()
    AltCoords.__table__.create()
    Index(u'alt_coords_cid_seq', AltCoords.cache_id, AltCoords.sequence_num, unique=False)
    v = Version()
    v.version=6
    DBSession.add(v)
    DBSession.flush()
    DBSession.commit()



class Version(DeclarativeBase):
    __tablename__ = 'version'
    version = Column(Integer, primary_key=True)


class Accounts(DeclarativeBase):
    __tablename__ = 'accounts'
    
    accountid = Column(Integer, primary_key=True)
    sitename = Column(UnicodeText(), primary_key=False)
    username = Column(UnicodeText(), primary_key=False)
    password = Column(UnicodeText(), primary_key=False)
    isteam = Column(Integer, primary_key=False)
    ispremium = Column(Integer, primary_key=False)


class CacheDayNames(DeclarativeBase):
    __tablename__ =  'cacheday_names'
    dayname = Column(UnicodeText(), primary_key=True)


class Categories(DeclarativeBase):
    __tablename__ = 'categories'
    catid = Column(Integer, primary_key=True)
    catname = Column(Unicode(), primary_key=False)


class EmailSources(DeclarativeBase):
    __tablename__ = 'emailsources'
    emailid = Column(Integer, primary_key=True)
    svrtype = Column(Unicode(), primary_key=False)
    svrname = Column(Unicode(), primary_key=False)
    svruser = Column(Unicode(), primary_key=False)
    svrpass = Column(Unicode(), primary_key=False)
    usessl = Column(Integer, primary_key=False)
    deffolder = Column(Unicode(), primary_key=False)


class GpxFolders(DeclarativeBase):
    __tablename__ = 'gpxfolders'
    foldername = Column(Unicode(), primary_key=True)


class Searches(DeclarativeBase):
    __tablename__ = 'searches'
    name = Column(Unicode(), primary_key=True)
    param = Column(Unicode(), primary_key=True)
    value = Column(Unicode(), primary_key=False)


class WatchedWayPoints(DeclarativeBase):
    __tablename__ = 'watched_waypoints'
    waypoint_name = Column(Unicode(), primary_key=True)


class Caches(DeclarativeBase):
    __tablename__ =  'caches'
    cache_id = Column(Integer, primary_key=True)
    catid = Column(Integer, primary_key=False)
    name = Column(Unicode(), primary_key=False)
    lat= Column(Numeric(precision=None, scale=None, asdecimal=True), primary_key=False)
    lon= Column(Numeric(precision=None, scale=None, asdecimal=True), primary_key=False)
    url = Column(Unicode(), primary_key=False)
    url_name = Column(Unicode(), primary_key=False)
    url_desc = Column(Unicode(), primary_key=False)
    sym = Column(Unicode(), primary_key=False)
    type = Column(Unicode(), primary_key=False)
    available = Column(Integer, primary_key=False)
    archived = Column(Integer, primary_key=False)
    placed_by = Column(Unicode(), primary_key=False)
    owner_id = Column(Integer, primary_key=False)
    owner_name = Column(Unicode(), primary_key=False)
    container = Column(Unicode(), primary_key=False)
    difficulty= Column(Numeric(precision=None, scale=None, asdecimal=True), primary_key=False)
    terrain= Column(Numeric(precision=None, scale=None, asdecimal=True), primary_key=False)
    country = Column(Unicode(), primary_key=False)
    state = Column(Unicode(), primary_key=False)
    short_desc = Column(Unicode(), primary_key=False)
    short_desc_html = Column(Integer, primary_key=False)
    long_desc = Column(Unicode(), primary_key=False)
    long_desc_html = Column(Integer, primary_key=False)
    hidden = Column(Integer, primary_key=False)


class Locations(DeclarativeBase):
    __tablename__ = 'locations'
    wpt_id = Column(Integer, primary_key=True)
    loc_type = Column(Integer, primary_key=False)
    refers_to = Column(Integer, primary_key=False)
    name = Column(Unicode(), primary_key=False)
    desc = Column(Unicode(), primary_key=False)
    comment = Column(Unicode(), primary_key=False)
    lat= Column(Numeric(precision=None, scale=None, asdecimal=True), primary_key=False)
    lon= Column(Numeric(precision=None, scale=None, asdecimal=True), primary_key=False)
    hidden = Column(Integer, primary_key=False)


class AltCoords(DeclarativeBase):
    __tablename__ =  'alt_coords'
    cache_id = Column(Integer, primary_key=True)
    sequence_num = Column(Integer, primary_key=True)
    name = Column(UnicodeText(), primary_key=False)
    Column(u'lat', UnicodeText(), primary_key=False)
    Column(u'lon', UnicodeText(), primary_key=False)
    Column(u'setdefault', Integer(), primary_key=False)


class Attributes(DeclarativeBase):
    __tablename__ =  'attributes'
    cache_id = Column(Integer, primary_key=True)
    attribute = Column(UnicodeText(), primary_key=False)


class CacheDay(DeclarativeBase):
    __tablename__ =  'cacheday'
    dayname = Column(UnicodeText(), primary_key=True)
    cache_id = Column(Integer, primary_key=True)
    cache_type = Column(Integer, primary_key=False)
    cache_order = Column(Integer, primary_key=False)


class Hints(DeclarativeBase):
    __tablename__ = 'hints'
    cache_id = Column(Integer, primary_key=True)
    hint = Column(Unicode(), primary_key=False)


class Logs(DeclarativeBase):
    __tablename__ = 'logs'
    id = Column(Integer, primary_key=True)
    cache_id = Column(Integer, primary_key=False)
    date = Column(Integer, primary_key=False)
    type = Column(Unicode(), primary_key=False)
    finder = Column(Unicode(), primary_key=False)
    finder_id = Column(Integer, primary_key=False)
    log_entry = Column(Unicode(), primary_key=False)
    log_entry_encoded = Column(Integer, primary_key=False)
    my_log = Column(Integer, primary_key=False)
    my_log_found = Column(Integer, primary_key=False)
    my_log_uploaded = Column(Integer, primary_key=False)


class Notes(DeclarativeBase):
    __tablename__ = 'notes'
    cache_id = Column(Integer, primary_key=True)
    note = Column(Unicode(), primary_key=False)


class Photos(DeclarativeBase):
    __tablename__ = 'photos'
    cache_id = Column(Integer, primary_key=True)
    photofile = Column(Unicode(), primary_key=True)


class TravelBugs(DeclarativeBase):
    __tablename__ = 'travelbugs'
    id = Column(Integer, primary_key=True)
    cache_id = Column(Integer, primary_key=False)
    name = Column(Unicode(), primary_key=False)
    ref = Column(Unicode(), primary_key=False)


Index(u'alt_coords_cid_seq', AltCoords.cache_id, AltCoords.sequence_num, unique=False)
Index(u'cacheday_name', CacheDay.dayname, unique=False)
Index(u'caches_url_name', Caches.url_name, unique=0)
Index(u'caches_name', Caches.name, unique=0)
Index(u'locations_name', Locations.name, unique=0)
Index(u'locations_refers_to', Locations.refers_to, unique=0)
Index(u'logs_cache_id', Logs.cache_id, unique=0)
Index(u'notes_id', Notes.cache_id, unique=0)
Index(u'photos_id', Photos.cache_id, unique=0)
Index(u'searches_name', Searches.name, unique=0)
Index(u'travelbugs_cache_id', TravelBugs.cache_id, unique=0)
