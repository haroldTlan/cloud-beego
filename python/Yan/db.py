from peewee import *
import peewee
import sys
import datetime
from env import config
from caused import caused
import threading
import log
import error
import md5

#db = SqliteDatabase(config.database.path, autocommit=False, threadlocals=True)
db = MySQLDatabase(config.database.name, autocommit=True, user=config.database.usr, passwd=config.database.passwd, threadlocals=True)

_local = threading.local()

def local():
    if not hasattr(_local, 'connect_nr'):
        _local.connect_nr = 0
        _local.transaction_nr = 0
        _local.transaction_end = ''
    return _local

inited = False

def begin():
    if local().transaction_nr == 0:
        local().transaction_end = ''
        db.set_autocommit(False)
        db.begin()
    local().transaction_nr += 1

def commit():
    local().transaction_nr -= 1
    if local().transaction_nr == 0:
        db.set_autocommit(True)
        if local().transaction_end == 'rollback':
            log.info('transaction end, nested rollback, so give up commit.')
            db.rollback()
        else:
            db.commit()
    elif local().transaction_nr < 0:
        db.set_autocommit(True)
        raise error.DB.TransactionUnmatch()

def rollback():
    local().transaction_end = 'rollback'
    local().transaction_nr -= 1
    if local().transaction_nr == 0:
        db.set_autocommit(True)
        db.rollback()
    elif local().transaction_nr < 0:
        db.set_autocommit(True)
        raise error.DB.TransactionUnmatch()

def connect():
    if local().connect_nr == 0:
        db.connect()
    local().connect_nr += 1

def close():
    local().connect_nr -= 1
    if local().connect_nr == 0:
        db.close()
    elif local().connect_nr < 0:
        raise error.DB.ConnectionUnmatch()

class transaction(object):
    def __enter__(self):
        connect()
        begin()

    def __exit__(self, type, value, traceback):
        if not traceback:
            commit()
        else:
            rollback()
        close()


def with_transaction(func):
    def _with_transaction(*vargs, **kv):
        try:
            connect()
            begin()
            ret = func(*vargs, **kv)
        except Exception as e:
            rollback()
            raise caused(e)
        else:
            commit()
        finally:
            close()
        return ret
    return _with_transaction

def with_db(func):
    def _with_db(*vargs, **kv):
        connect()
        try:
            s = func(*vargs, **kv)
        except Exception as e:
            raise caused(e)
        finally:
            close()
        return s
    return _with_db

def utime():
    return datetime.datetime.now()

class BaseModel(Model):
    created_at = DateTimeField()
    updated_at = DateTimeField()

    @classmethod
    def all(cls):
        return list(cls.select())

    @classmethod
    def create(cls, **kv):
        return Model.create.im_func(cls, created_at=utime(), updated_at=utime(), **kv)

    @classmethod
    def exists(cls, expr):
        return cls.select().where(expr).exists()

    def save(self, **kv):
        self.updated_at = utime()
        return Model.save(self, **kv)

    class Meta:
        database = db

class Bcache(BaseModel):
    uuid = CharField(primary_key=True)
    class Meta:
        db_table = 'bcaches'

class Raid(BaseModel):
    uuid     = CharField(primary_key=True)
    name     = CharField()
    level    = IntegerField()
    chunk_kb = IntegerField()
    rebuild_priority  = CharField()
    health   = CharField()
    raid_disks_nr = IntegerField()
    spare_disks_nr = IntegerField()
    cap = IntegerField()
    used_cap = IntegerField(default=0)
    dev_name = CharField()
    odev_name = CharField()
    unplug_seq = IntegerField()
    rqr_count = IntegerField()
    deleted = BooleanField(default=False)
    class Meta:
        db_table = 'raids'

class Disk(BaseModel):
    uuid = CharField(primary_key=True)
    location = CharField(index=True)
    prev_location = CharField(default='')

    health = CharField()
    role = CharField()
    raid = ForeignKeyField(Raid, related_name='disks', null=True, db_column='raid')
    raid_hint = CharField()
    #slot = IntegerField()
    #data_part_nr = IntegerField(default=0)

    disktype = CharField()
    vendor = CharField()
    model = CharField()
    host = CharField()
    sn = CharField()
    rpm = IntegerField()
    cap_sector = BigIntegerField(default=0)
    devno = IntegerField()
    dev_name = CharField()
    link = BooleanField()
    unplug_seq = IntegerField()
    rqr_count = IntegerField()
    class Meta:
        db_table = 'disks'

class Part(BaseModel):
    partno = IntegerField()
    dev_name = CharField()
    stub_dev = CharField()
    devno = IntegerField()
    disk = ForeignKeyField(Disk, related_name='parts', null=False, db_column='disk', on_delete='CASCADE')
    off_sector = BigIntegerField()
    data_sector = BigIntegerField()
    cap_sector = BigIntegerField()
    health = CharField()
    role = CharField()
    link = BooleanField()
    unplug_seq = IntegerField()
    rqr_count = IntegerField()

    class Meta:
        db_table = 'parts'

class RQR(BaseModel):
    part = ForeignKeyField(Part, related_name='rqrs', null=False, db_column='part', on_delete='CASCADE')
    meta_off1_sector = BigIntegerField()
    meta_off2_sector = BigIntegerField()
    meta_sector = IntegerField()
    repl_off_sector = BigIntegerField()
    repl_sector = BigIntegerField()

    class Meta:
        db_table = 'rqrs'

class Volume(BaseModel):
    uuid = CharField(primary_key=True)
    name = CharField()
    health = CharField()
    cap = IntegerField()
    used = BooleanField()
    deleted = IntegerField(default=0)
    #raid = ForeignKeyField(Raid, related_name='volumes', db_column='raid')
    owner_type = CharField()

    @property
    def initiators(self):
        return [vi.initiator for vi in InitiatorVolume.select().where(InitiatorVolume.volume==self.uuid)]

    class Meta:
        db_table = 'volumes'

class RaidVolume(BaseModel):
    raid = ForeignKeyField(Raid, db_column='raid', null=True)
    volume = ForeignKeyField(Volume, db_column='volume', null=True)
    type = CharField()

    class Meta:
        db_table = 'raid_volumes'

class Initiator(BaseModel):
    wwn = CharField(primary_key=True)
    target_wwn = CharField()

    @property
    def volumes(self):
        return [vi.volume for vi in InitiatorVolume.select().where(InitiatorVolume.initiator==self.wwn)]

    class Meta:
        db_table = 'initiators'

class InitiatorVolume(BaseModel):
    initiator = ForeignKeyField(Initiator, db_column='initiator')
    volume = ForeignKeyField(Volume, db_column='volume')
    class Meta:
        db_table = 'initiator_volumes'

class XFS(BaseModel):
    uuid   = CharField(primary_key=True)
    volume = ForeignKeyField(Volume, db_column='volume')
    name   = CharField()
    chunk_kb = IntegerField()
    mountpoint = CharField()
    type = CharField(default='xfs')
    class Meta:
        db_table = 'xfs'

class MonFS(BaseModel):
    uuid   = CharField(primary_key=True)
    volume = ForeignKeyField(Volume, db_column='volume')
    meta_off_sector = BigIntegerField()
    meta_sector = BigIntegerField()
    chunk_kb = IntegerField()
    nr = IntegerField()
    name = CharField()
    mdev_name = CharField()
    mountpoint = CharField()
    type = CharField(default='monfs')
    class Meta:
        db_table = 'monfs'

class NetworkInitiator(BaseModel):
    initiator = ForeignKeyField(Initiator, related_name='portals', db_column='initiator')
    eth = CharField()
    port = IntegerField()
    class Meta:
        db_table = 'network_initiators'

class SlaveOrigin(BaseModel):
    eth = CharField()
    ipaddr = CharField()
    netmask = CharField()
    class Meta:
        db_table = 'slave_origins'

class Journal(BaseModel):
    level = CharField()
    message = CharField()
    class Meta:
        db_table = 'journals'

class User(BaseModel):
    name = CharField()
    crypted_passwd = CharField()
    perishable_token = CharField()
    class Meta:
        db_table = 'users'

class RaidRecovery(BaseModel):
    uuid     = CharField(index=True)
    name     = CharField()
    level    = IntegerField()
    chunk_kb = IntegerField()
    raid_disks_nr  = IntegerField()
    raid_disks     = TextField()
    spare_disks_nr = IntegerField()
    spare_disks    = TextField()
    class Meta:
        db_table = 'raid_recoveries'

tables = [Raid, Disk, Part, RQR, Volume, XFS, MonFS, Initiator, InitiatorVolume, RaidVolume, NetworkInitiator, SlaveOrigin, Journal, User, RaidRecovery]

@with_transaction
def create_tables():
    for tbl in tables:
        if not tbl.table_exists():
            tbl.create_table()

    try:
        User.get(name='admin')
    except:
        crypted = md5.new('admin').hexdigest()
        User.create(name='admin', crypted_passwd=crypted, perishable_token='')


@with_transaction
def drop_data():
    tbls = tables[:]
    tbls.reverse()
    for tbl in tbls:
        if tbl.table_exists():
            tbl.delete().execute()

@with_transaction
def drop_tables():
    tbls = tables[:]
    tbls.reverse()
    for tbl in tbls:
        print tbl
        if tbl.table_exists():
            tbl.drop_table()
