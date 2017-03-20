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

db = MySQLDatabase('zero_diskdb', autocommit=True, user=config.database.usr,\
        passwd=config.database.passwd, threadlocals=True, connect_timeout=30)

BS = KB(128)
DEFAULT_TOTAL_PER_WRITE = GB(16)
DEFAULT_SLEEP_SEC = 1
ERR = -1

class Disk(Model):
    uuid   = CharField(primary_key=True)
    status = CharField()
    nr     = IntegerField()
    count  = IntegerField()
    begin  = DateTimeField()
    end    = DateTimeField()

    class Meta:
        db_table = 'disks'
        database = db

if not Disk.table_exists():
    Disk.create_table()

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

def zero_disk(disk, dev, tpw, sleep_sec):
    try:
        return _zero_disk_using_dd(disk, dev, tpw, sleep_sec)
    except Exception as e:
        log.error(e)
        return ERR

def _zero_disk_using_dd(disk, dev, tpw, sleep_sec):
    dbo = Disk.create(uuid=disk.uuid, status='prepare', nr=0, count=0, begin=datetime.now(), end=datetime.now())
    disk.remove_dev()

    log.info('Disk:%s(%s) pid: %s ready' % (disk.location, dev, os.getpid()))
    time.sleep(10)

    cmd = 'blockdev --getsz /dev/%s' % dev
    e,o = execute(cmd, False)
    if e <> 0:
        dbo.status = 'error'
        dbo.save()
        return ERR

    cap = Sector(o)
    nr = int(cap / tpw + 1)
    count = int(tpw / BS)
    dbo.nr = nr
    dbo.status = 'inprogress'
    dbo.save()
    buf = '\0' * int(BS.Byte)

    log.info('Disk:%s(%s) total_per_write: %s, sleep_sec: %ss' % \
            (disk.location, dev, tpw, sleep_sec))
    for i in range(0, nr):
        cmd = 'dd if=/dev/zero of=/dev/%s bs=%sK seek=%s count=%s oflag=direct' % (dev, int(BS.KB), count*i, count)
        e,o = execute(cmd, False)
        if e == 0 or 'No space left on device' in o:
            dbo.count += 1
            save_dbo(dbo)
        else:
            log.info('Disk:%s(%s) seek:%s count:%s bs:%s dd error' % (disk.location,\
                    dev, count*i, count, BS))
            dbo.status = 'error'
            dbo.end = datetime.now()
            save_dbo(dbo)
            return ERR

        time.sleep(sleep_sec)

    dbo.status = 'completed'
    dbo.end = datetime.now()
    save_dbo(dbo)
    return 0

def _zero_disk_using_write(disk, dev):
    dbo = Disk.create(uuid=disk.uuid, status='prepare', nr=0, count=0)
    disk.remove_dev()

    cmd = 'blockdev --getsz /dev/%s' % dev
    e,o = execute(cmd, False)
    if e <> 0:
        dbo.status = 'error'
        dbo.save()
        return ERR

    time.sleep(5)

    cap = Sector(o)
    nr = int(cap / TOTAL_PER_WRITE + 1)
    nr = 8
    count = int(TOTAL_PER_WRITE / BS)
    dbo.nr = nr
    dbo.status = 'inprogress'
    dbo.save()
    buf = '\0' * int(BS.Byte)

    log.info('Disk:%s(%s) total_per_write: %s, sleep_sec: %ss' % \
            (disk.location, dev, TOTAL_PER_WRITE, SLEEP_SEC))
    with open('/dev/%s' % dev, 'w') as fout:
        for i in range(0, nr):
            error = False
            try:
                log.info('Disk:%s(%s) pid: %s write count: %s' % (disk.location, dev, os.getpid(), i))
                for j in range(0, count):
                    fout.write(buf)
                    fout.flush()
                    time.sleep(0.002)
            except IOError as e:
                if e.errno == 28:
                    log.info('Disk:%s(%s) no left space when write count: %s' %\
                            (disk.location, dev, i))
                else:
                    error = True
            except:
                error = True

            if error:
                dbo.status = 'error'
                dbo.save()
                return ERR
            else:
                dbo.count += 1
                if dbo.count == dbo.nr:
                    dbo.status = 'completed'
                dbo.save()

            log.info('Disk:%s(%s) sleep %ss' % (disk.location, dev, SLEEP_SEC))
            time.sleep(SLEEP_SEC)

    return 0

def cmp_disk(a, b):
    a3 = re.findall('(\d+)\.(\d+)\.(\d+)', a['location'])
    b3 = re.findall('(\d+)\.(\d+)\.(\d+)', b['location'])
    for x, y in zip(a3[0], b3[0]):
        if int(x) > int(y): return 1
        elif int(x) < int(y): return -1
    return 0

def query_zero_progress():
    progress = []
    for ds in Disk.select():
        try:
            disk = adm.Disk.lookup(uuid=ds.uuid)
        except:
            continue

        if ds.status == 'inprogress' or ds.status == 'prepare':
            cost = datetime.now() - ds.begin
        else:
            cost = ds.end - ds.begin
        progress.append({'location':disk.location, 'status':ds.status, 'nr':ds.nr, 'count':ds.count, 'begin':ds.begin, 'cost':cost})
    progress = sorted(progress, cmp=cmp_disk)
    return progress

def usage():
    print 'usage:'
    print '%s -s second -t size' % sys.argv[0]
    sys.exit(ERR)

def zero(tpw, sleep_sec):
    try:
        sleep_sec = float(sleep_sec)
    except:
        raise error.InvalidParam('sleep-seconds', sleep_sec)
    try:
        tpw = Unit(tpw)
    except:
        raise error.InvalidParam('total-per-write', tpw)
    cmd = 'nohup python zero_disk.pyc -s %s -w %s > /dev/null 2>&1 &' % (sleep_sec, tpw)
    os.system(cmd)

def main():
    optmap = dict(getopt.getopt(sys.argv[1:], 's:w:')[0])
    try:
        sleep_sec = float(optmap['-s'])
    except:
        sleep_sec = DEFAULT_SLEEP_SEC
    try:
        tpw = Unit(optmap['-w'])
    except:
        tpw = DEFAULT_TOTAL_PER_WRITE

    log.info('zero disk, sleep second: %s, total_per_write: %s' % (sleep_sec, tpw))
    cmd = "ps aux | grep 'python zero_disk.py'"
    _,o = execute(cmd, False)
    pids = re.findall('\w+?\s+(\d+).+\n', o)
    for pid in pids:
        if int(pid) <> os.getpid():
            cmd = 'kill %s' % pid
            execute(cmd, False)

    cmd = "ps aux | grep 'dd if=/dev/zero of=/dev/sd'"
    _,o = execute(cmd, False)
    pids = re.findall('\w+?\s+(\d+).+\n', o)
    for pid in pids:
        cmd = 'kill %s' % pid
        execute(cmd, False)

    Disk.delete().execute()

    mapping = lm.LocationMapping().mapping
    pool = mp.Pool(processes=len(mapping.keys()))
    for _,dev_name in mapping.items():
        try:
            disk = adm.Disk.lookup(dev_name=dev_name)
        except:
            continue
        if disk.online:
            pool.apply_async(zero_disk, (disk, dev_name, tpw, sleep_sec))
    pool.close()
    pool.join()

if __name__ == '__main__':
    main()
