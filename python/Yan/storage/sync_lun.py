#!/usr/bin/env python
import sys
import getopt
import re
import adm
import lm
from env import config
from peewee import Model, CharField, IntegerField, DateTimeField, MySQLDatabase
import multiprocessing as mp
import os
import log
from util import execute
from unit import GB, MB, KB, Sector, Unit
import time
from datetime import datetime
import error
from peewee import *
import threading
from caused import *

db = MySQLDatabase('sync_lundb', autocommit=True, user='root',\
        passwd=config.database.passwd, threadlocals=True, connect_timeout=30)

BS = KB(128)
DEFAULT_TOTAL_PER_WRITE = GB(16)
DEFAULT_SLEEP_SEC = 1
ERR = -1

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

class Volume(Model):
    name   = CharField(primary_key=True)
    status = CharField()
    nr     = IntegerField()
    count  = IntegerField()
    begin  = DateTimeField()
    end    = DateTimeField()

    @classmethod
    def exists(cls, expr):
        return cls.select().where(expr).exists()

    class Meta:
        db_table = 'volumes'
        database = db

if not Volume.table_exists():
    Volume.create_table()

def save_dbo(dbo):
    try:
        dbo.save()
    except Exception as e:
        log.error("pid: %s save dbo error, try reconnect" % os.getpid())
        log.error(e)
        for i in range(0, 5):
            try:
                db.connect()
                break
            except:
                log.error("pid: %s reconnect:%s error" % os.getpid(), i)
                pass
        try:
            dbo.save()
        except:
            log.error("pid: %s save dbo error" % os.getpid())
            return ERR

    return 0

def del_dbo(dbo):
    try:
        dbo.delete_instance(recursive=True)
    except Exception as e:
        log.error("pid: %s delete dbo error" % os.getpid())
        log.error(e)
        return ERR
    return 0

@with_db
def _zero_volume_using_dd(volume, tpw, sleep_sec):
    dbo = None
    if Volume.exists(Volume.name == volume.name):
        dbo = Volume.get(name = volume.name)
    else:
        dbo = Volume.create(name=volume.name, status='prepare', nr=0, count=0, begin=datetime.now(), end=datetime.now())
        
        cmd = 'blockdev --getsz %s' % volume.dev_path
        e,o = execute(cmd, False)
        if e <> 0:
            dbo.status = 'error'
            dbo.save()
            return ERR
        dbo.nr = int(Sector(o) / tpw + 1) #number of total blocks

    dbo.status = 'inprogress'
    dbo.save()

    log.info('Volume:%s pid: %s ready' % (volume.name, os.getpid()))

    count = int(tpw / BS)
    log.info('Volume:%s total_per_write: %s, sleep_sec: %ss' % (volume.name, tpw, sleep_sec))
    for i in range(dbo.count, dbo.nr):
        cmd = 'dd if=/dev/zero of=%s bs=%sK seek=%s count=%s oflag=direct' % (volume.dev_path, int(BS.KB), count*i, count)
        e,o = execute(cmd, False, logging=False)
        if e == 0 or 'No space left on device' in o:
            dbo.count += 1
            save_dbo(dbo)
        else:
            log.info('Volume:%s seek:%s count:%s bs:%s dd error' % (volume.name, count*i, count, BS))
            dbo.status = 'error'
            dbo.end = datetime.now()
            save_dbo(dbo)
            return ERR

        time.sleep(sleep_sec)

    dbo.status = 'completed'
    dbo.end = datetime.now()
    save_dbo(dbo)
    return 0

@with_db
def zero_volume(lun_name, tpw, sleep_sec):
    try:
        volume = adm.Volume.lookup(name=lun_name)
        return _zero_volume_using_dd(volume, tpw, sleep_sec)
    except Exception as e:
        log.error(e)
        return ERR

@with_db
def query_zero_progress():
    progress = []
    for volume in Volume.select():
        if volume.status == 'inprogress' or volume.status == 'prepare':
            cost = datetime.now() - volume.begin
        else:
            cost = volume.end - volume.begin
        progress.append({'name':volume.name, 'status':volume.status, 'nr':volume.nr, 'count':volume.count, \
                         'begin':volume.begin.strftime("%Y-%m-%d-%H"), 'cost':cost.seconds})
    return progress

@with_db
def del_zero_volume(lun_name):
    if Volume.exists(Volume.name == lun_name):
        dbo = Volume.get(name = lun_name)
        return del_dbo(dbo)
    else:
        return ERR

@with_db
def change_status_to_stop(lun_name):
    if Volume.exists(Volume.name == lun_name):
        dbo = Volume.get(name = lun_name)
        dbo.status = 'stop'
        return save_dbo(dbo)
    else:
        return ERR
