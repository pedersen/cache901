from sqlalchemy import Column, Index
from sqlalchemy.types import Integer
import migrate.changeset

from cache901.sadbobjects import DeclarativeBase, Caches, Version, GpxFolders, Accounts, EmailSources, WatchedWayPoints, metadata, engine, DBSession, Locations, AltCoords, Searches, Notes, Photos, CacheDay, CacheDayNames
try:
    version = DBSession.query(Version).order_by(Version.version.desc()).first().version
except Exception as e:
    print str(e)
    version = 0

if version == 0:
    metadata.create_all(engine)
    v = Version()
    v.version=6
    DBSession.add(v)
    DBSession.flush()
    DBSession.commit()
elif version == 1:
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
elif version == 2:
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
elif version == 3:
    DBSession.configure(bind=engine)
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
elif version == 4:
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
elif version == 5:
    AltCoords.__table__.drop()
    AltCoords.__table__.create()
    Index(u'alt_coords_cid_seq', AltCoords.cache_id, AltCoords.sequence_num, unique=False)
    v = Version()
    v.version=6
    DBSession.add(v)
    DBSession.flush()
    DBSession.commit()
print version
