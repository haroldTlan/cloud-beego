#!/usr/bin/env python
# -*- coding: utf-8 -*-
from caused import *
from db import with_db, transaction, with_transaction
import db
import glob
import log
import ipaddr
from md import *
import netifaces
from os import path
import peewee
import re
import lm
from rtslib import RTSRoot
from rtslib import FabricModule
from rtslib import NodeACL, NetworkPortal, MappedLUN
from rtslib import Target, TPG, LUN
from rtslib import FileIOStorageObject
from rtslib import BlockStorageObject
from util import *
from unit import unit, Byte, KB, MB, GB, Sector
import time
from zerod import *
import sys
import errno
import json
import multiprocessing as mp
from env import config
import os
from perf import Timer, Timeout
import traceback as tb
import math
import error
from error import exc2status
import md5
from collections import Counter
from collections import OrderedDict as odict
from rtslib.utils import is_dev_in_use
import ethtool
from watch import monfs_superblock
import uevent
from network import ifaces
import lvm
import psutil
import xml.etree.cElementTree as ET

import syncd
from beepd import *
def ensure_exist(path):
    time.sleep(0.1)
    for i in range(0, 120):
        if os.path.exists(path):
            break
        time.sleep(0.1)

    if os.path.exists(path):
        with open(path, 'r') as f:
            f.read(512)
    else:
        log.warning("ensure %s exist error" % path)

def ensure_not_exist(path):
    time.sleep(0.1)
    for i in range(0, 120):
        if not os.path.exists(path):
            break
        time.sleep(0.1)

    if os.path.exists(path):
        log.warning("ensure %s not exist error" % path)

def dmcreate(name, *rules):
    tmpfile = '/tmp/%s.rule' % name
    with open(tmpfile, 'w') as f:
        f.write('\n'.join(rules))

    cmd = 'dmsetup create %s %s' % (name, tmpfile)
    _,o = execute(cmd)

    dm_path = '/dev/mapper/%s' % name
    ensure_exist(dm_path)

    os.remove(tmpfile)

def dmremove(path):
    cmd = 'dmsetup remove %s' % path
    _,o = execute(cmd)
    ensure_not_exist(path)

def addpart(path, i, off, size):
    cmd = 'addpart %s %s %s %s' % (path, i, off.Sector, size.Sector)
    _,o = execute(cmd)
    part_path = '%s%s' % (path, i)
    ensure_exist(part_path)

def delpart(part_path):
    cmd = 'partx -d %s' % part_path
    _,o = execute(cmd)
    ensure_not_exist(part_path)

def is_abnormal_poweroff():
    return os.path.exists(config.boot.startup_file)

class FieldAdapter(object):
    def __init__(self, name='', to_field=lambda x: x, to_attr=lambda x: x, default=None):
        self.name = name
        self.to_field = to_field
        self.to_attr = to_attr
        self.default = default

class TableNotFound(Exception):pass
class FieldNotFound(CausedException):
    def __init__(self, field, table):
        super(FieldNotFound, self).__init__('field %s is not found in the table %s' % (field, table))

class AdminMeta(type):
    def __new__(mcs, name, bases, attrs):
        if bases[0] == object:
            return super(AdminMeta, mcs).__new__(mcs, name, bases, attrs)

        adapters = {}
        new_attrs = {}
        table = None
        for n, attr in attrs.items():
            if isinstance(attr, FieldAdapter):
                if not attr.name:
                    attr.name = n
                adapters[n] = attr
            else:
                if n == 'table': table = attr
                elif n == 'primary_index' and not isinstance(attr, tuple):
                    attr = (attr,)
                new_attrs[n] = attr

        cls = super(AdminMeta, mcs).__new__(mcs, name, bases, new_attrs)
        if not table:
            if adapters: raise TableNotFound
            else: return cls

        cls._field_adapters = {}

        for n in table._meta.fields:
            cls._field_adapters[n] = FieldAdapter(n)

        for n, adapter in adapters.items():
            if not adapter.name in cls._field_adapters: raise FieldNotFound(adapter.name, table.__name__)
            del cls._field_adapters[adapter.name]
            cls._field_adapters[n] = adapter

        return cls

class Admin(object):
    __metaclass__ = AdminMeta
    def __init__(self, **kv):
        if 'db' in kv:
            self._db = kv['db']
        else:
            self._db = None
            for k, v in kv.items():
                if k in self._field_adapters:
                    setattr(self, k, v)

    def __getattr__(self, name):
        if not name in self._field_adapters:
            raise AttributeError(name)
        adapter = self._field_adapters[name]
        if not self.exists:
            if adapter.default == None:
                raise AttributeError(name)
            else:
                return adapter.default
        else:
            field = getattr(self.db, adapter.name)
            attr = adapter.to_attr(field)
            setattr(self, name, attr)
            return attr

    def _set_default(self):
        for name, adapter in self._field_adapters.items():
            try:
                if adapter.default <> None:
                    attr = getattr(self, name)
                    if attr == '': setattr(self, name, adapter.default)
            except: pass

    def save(self, force_create=False, **kv):
        params = {}
        for name, adapter in self._field_adapters.items():
            if hasattr(self, name):
                field = adapter.to_field(getattr(self, name))
                params[adapter.name] = field

        for k, v in kv.items():
            try:
                adapter = self._field_adapters[k]
                params[adapter.name] = adapter.to_field(v)
                setattr(self, k, v)
            except:
                pass

        if not self.exists or force_create:
            if force_create:
                del params['created_at']
                del params['updated_at']
            self._db = self.table.create(**params)
        else:
            for name, field in params.items():
                setattr(self._db, name, field)
            self._db.save()

    @classmethod
    def lookup(cls, **kv):
        db = None
        try:
            conditions = {}
            for name, attr in kv.items():
                adapter = cls._field_adapters[name]
                conditions[adapter.name] = adapter.to_field(attr)
            db = cls.table.get(**conditions)
        except:
            raise error.NotExistError(' '.join(['%s=%s' % (k,v) for k,v in kv.items()]))

        return cls(db=db)

    @property
    def db(self):
        return self._db

    @property
    def online(self):
        return not os.path.isdir(self.dev_path) and os.path.exists(self.dev_path)

    def exists_get_db(self, cond):
        return self.table.get(**cond)

    @property
    def exists(self):
        if self.db: return True
        try:
            fas = [self._field_adapters[name] for name in self.primary_index]
            cols = [fa.name for fa in fas]
            vals = [getattr(self, name) for name in self.primary_index]
            self._db = self.exists_get_db(dict(zip(cols, vals)))
            return self.db <> None
        except:
            return False

    @property
    def _primary_value(self):
        return ' '.join([getattr(self, name, '') for name in self.primary_index])

    @classmethod
    def all(cls):
        return [cls(db=db) for db in cls.table.all()]

    def _check_create_param(self):
        pass

    def create(self):
        if self.exists:
            raise error.ExistError(self._primary_value)
        self._check_create_param()

    def _check_delete_param(self):
        pass

    def delete(self):
        if not self.exists:
            raise error.NotExistError(self._primary_value)
        self._check_delete_param()
        self.db.delete_instance()

HEALTH_DEGRADED = 'degraded'
HEALTH_DOWN     = 'down'
HEALTH_FAILED   = 'failed'
HEALTH_NORMAL   = 'normal'
HEALTH_PARTIAL  = 'partial'

ROLE_DATA          = 'data'
ROLE_DATA_SPARE    = 'data&spare'
ROLE_GLOBAL_SPARE  = 'global_spare'
ROLE_RESERVED      = 'reserved'
ROLE_SPARE         = 'spare'
ROLE_UNUSED        = 'unused'
ROLE_KICKED        = 'kicked'

SYNC_RECOVER = 'recover'
SYNC_RESYNC  = 'resync'
SYNC_IDLE    = 'idle'
SYNC_FROZEN  = 'frozen'

RV_NORMAL = 'normal'
RV_EXPANSION = 'expansion'

class Bcache(object):
    UUID = '37cc9798-b654-4bf5-bc5e-e140c850acb8'
    @property
    def exists(self):
        return os.path.exists('/sys/fs/bcache/%s' % self.UUID)

    def create(self):
        ssd = config.raid.ssd
        if not self.exists and ssd.location:
            m = lm.LocationMapping()
            dev = m.mapping[ssd.location]
            bucket_opt = '-b %sk' % ssd.bucket_size.KB if ssd.bucket_size else ''
            cmd = 'make-bcache -C /dev/%s --cset %s --wipe-bcache %s --writeback --discard' % (dev, self.UUID, bucket_opt)
            execute(cmd)
            time.sleep(0.05)
            while not self.exists:
                time.sleep(0.01)


    def attach(self, raid):
        if self.exists:
            s1 = set(glob.glob1('/dev', 'bcache*'))
            cmd = 'make-bcache -B %s --cset %s' % (raid.dev_path, self.UUID)
            execute(cmd)
            s2 = set(glob.glob1('/dev', 'bcache*'))
            raid.odev_name = s2.difference(s1).pop()

    def deattach(self, raid):
        if self.exists:
            cmd = 'echo 1 > /sys/block/%s/bcache/stop' % raid.dev_path
            execute(cmd)
            cmd = 'dd if=/dev/zero of=%s bs=4M count=1 oflag=direct' % raid.dev_path
            execute(cmd)

    def delete(self):
        ssd = config.raid.ssd
        if self.exists and ssd.location:
            cmd = 'echo 1 > /sys/fs/bcache/%s/stop' % self.UUID
            execute(cmd)
            m = lm.LocationMapping()
            dev = m.mapping[ssd.location]
            cmd = 'dd if=/dev/zero of=/dev/%s bs=4M count=1 oflag=direct' % dev
            execute(cmd)

class Raid(Admin):
    REBUILD_PRIORITY = ['low', 'medium', 'high']
    CHUNK   = [KB(8), KB(16), KB(32), KB(64), KB(128), KB(256), KB(512)]
    LEVEL = [0, 1, 5, 6, 10]
    NAME_PATTERN = '^[_a-zA-Z][-_a-zA-Z0-9]*$'
    NAME_MAX_LEN = 64

    DISK_NUM_LIMIT = 27

    DEFAULT_LEVEL = 5
    DEFAULT_CHUNK = KB(128)
    DEFAULT_REBUILD = 'low'
    DEFAULT_HEALTH = 'normal'

    LEVEL_DISK_NUM = {5:3, 0:1, 1:2,6:4, 10:2}

    table = db.Raid

    primary_index = 'name'

    chunk = FieldAdapter('chunk_kb', lambda x: x.KB, lambda x: KB(x), default=DEFAULT_CHUNK)
    level = FieldAdapter(default=DEFAULT_LEVEL)
    rebuild_priority = FieldAdapter(default=DEFAULT_REBUILD)
    _health = FieldAdapter('health', default=DEFAULT_HEALTH)
    unplug_seq = FieldAdapter(default=0)
    rqr_count = FieldAdapter(default=0)
    def __init__(self, raid_disks=[], spare_disks=[], **kv):
        super(Raid, self).__init__(**kv)

        if not self.exists:
            self.sync = False
            self._raid_disks = raid_disks
            self._spare_disks = spare_disks

        self._vg_name = None

    def exists_get_db(self, cond):
        cond.update(deleted=False)
        return self.table.get(**cond)

    @classmethod
    def all(cls):
        return [cls(db=_db) for _db in cls.table.select().where(db.Raid.deleted == False)]

    @classmethod
    def lookup(cls, **kv):
        kv.update(deleted=False)
        return super(Raid, cls).lookup(**kv)

    def volumes(self, deleted=0):
        volumes = [Volume(db=_db.volume) for _db in db.RaidVolume.select().join(db.Volume)\
            .where((db.RaidVolume.raid == self.uuid)&(db.Volume.deleted == deleted))]
        return volumes
        #return [vol for vol in volumes if vol.deleted == deleted]

    def _assoc_disks(self):
        self._raid_disks, self._spare_disks = [], []
        for disk in self.disks:
            if disk.role in [ROLE_DATA, ROLE_DATA_SPARE]:
                self._raid_disks.append(disk)
            elif disk.role == ROLE_SPARE:
                self._spare_disks.append(disk)

    @property
    def disks(self):
        if hasattr(self, '_disks'): return self._disks
        if self.exists:
            self._disks = [Disk(db=db) for db in self.db.disks]
        else:
            self._disks = []
        return self._disks

    @property
    def degraded(self):
        cmd = 'cat /sys/block/%s/md/degraded' % self.dev_name
        _,o = execute(cmd, logging=False)
        return int(o)

    @property
    def no_raid_disks(self):
        return self.degraded == self.raid_disks_nr

    @property
    def dev_path(self):
        return str('/dev/%s' % self.dev_name)

    @property
    def health(self):
        try:
            cmd = 'mdadm --detail %s' % self.dev_path
            _,o = execute(cmd, logging=False)
            states = [s.strip() for s in re.findall('State :\s+([^\n]+)', o)[0].split(',')]
            if 'degraded' in states:
                return HEALTH_DEGRADED
            elif 'FAILED' in states:
                return HEALTH_FAILED
            else:
                return HEALTH_NORMAL
        except:
            return HEALTH_FAILED

    @health.setter
    def health(self, v):
        self._health = v

    def save(self, force_create=False, **kv):
        if 'health' in kv:
            kv['_health'] = kv['health']
            del kv['health']
        super(Raid, self).save(force_create, **kv)

    @property
    def runnable(self):
        return self.online and self.health in [HEALTH_NORMAL, HEALTH_DEGRADED]

    @property
    def unavailable_disks(self):
        disks = [disk for disk in self.raid_disks if disk.health == HEALTH_FAILED or not disk.online]
        return sorted(disks, key=lambda x: x.unplug_seq, reverse=True)

    @property
    def rebuilding_disk(self):
        disks = [disk for disk in self.raid_disks if disk.role == ROLE_DATA_SPARE and disk.link]
        return disks[0] if disks else None

    def mdadm_remove(self, disk):
        cmd = 'mdadm --fail %s %s' % (self.dev_path, disk.dev_path)
        execute(cmd, False)

        for i in range(0, 60):
            if not is_dev_in_use(disk.dev_path):
                return

            cmd = 'mdadm --remove %s %s' % (self.dev_path, disk.dev_path)
            execute(cmd, False)
            time.sleep(1)

    def unplug(self, disk):
        try:
            if self.online and disk.link:
                self.mdadm_remove(disk)

                self.unplug_seq += 1
                disk.save(unplug_seq = self.unplug_seq, link=False, role=ROLE_DATA_SPARE)
                health = HEALTH_FAILED if self.level == 0 else self.health
                self.save(health=health)
        except Exception as e:
            tb.print_exc()

    @property
    def odev_path(self):
        if config.raid.cache.enabled:
            path = os.path.join('/dev/mapper', self.odev_name)
            if os.path.exists(path):
                return path

        if config.raid.ssd.enabled:
            path = os.path.join('/dev', self.odev_name)
            if os.path.exists(path):
                return path

        return self.dev_path

    @property
    def rebuilding(self):
        if self.online:
            if self.level == 0: return False
            else: return self.sync_action == SYNC_RECOVER
        else:
            return False

    @property
    def rebuild_progress(self):
        if self.rebuilding:
            cmd = 'cat /sys/block/%s/md/sync_completed' % self.dev_name
            _,o = execute(cmd, logging=False)
            return float('%.3f' % eval('%s.0' % o.strip()))
        else:
            return 0

    @property
    def sync_action(self):
        if self.online:
            with open('/sys/block/%s/md/sync_action' % self.dev_name) as fin:
                return fin.read().strip()
        else:
            return ''

    @property
    def raid_disks(self):
        if hasattr(self, '_raid_disks'): return self._raid_disks
        if self.exists:
            self._assoc_disks()
        else:
            self._raid_disks = []
        return self._raid_disks

    @property
    def spare_disks(self):
        if hasattr(self, '_spare_disks'): return self._spare_disks
        if self.exists:
            self._assoc_disks()
        else:
            self._spare_disks = []
        return self._spare_disks

    def available_spare_disk(self):
        disks = [s for s in self.spare_disks if s.role == ROLE_SPARE and s.health == HEALTH_NORMAL]
        return disks[0] if disks else None

    def _check_create_param(self):
        self._set_default()
        if self.sync == '': self.sync = False

        if not re.search(self.NAME_PATTERN, self.name):
            raise error.InvalidParam('name', self.name)

        if len(self.name) > self.NAME_MAX_LEN:
            raise error.NameTooLong(self.name, self.NAME_MAX_LEN)

        try:
            level = int(self.level)
        except:
            raise error.InvalidParam('level', self.level)
        if level not in self.LEVEL:
            raise error.InvalidParam('level', self.level)
        self.level = level

        try:
            chunk = unit(self.chunk)
        except:
            raise error.InvalidParam('chunk', self.chunk)
        if chunk not in self.CHUNK:
            raise error.InvalidParam('chunk', self.chunk)
        self.chunk = chunk

        try:
            sync = eval_bool(self.sync)
        except:
            raise error.InvalidParam('sync', self.sync)
        self.sync = sync

        nr = self.LEVEL_DISK_NUM[self.level]
        self.raid_disks_nr = len(self.raid_disks)
        self.spare_disks_nr = len(self.spare_disks)
        if self.raid_disks_nr < nr:
            raise error.Raid.NeedMoreDisk(self.raid_disks_nr, self.level)
        elif self.raid_disks_nr > self.DISK_NUM_LIMIT:
            raise error.Raid.DiskBeyondLimit(self.DISK_NUM_LIMIT)

        if self.level == 1 and self.raid_disks_nr <> 2:
            raise error.Raid.Level1DiskNum
        if self.level == 0 and self.spare_disks_nr > 0:
            raise error.Raid.NotSupportSpareDisk(self.level)

        raid_disks = [disk.location for disk in self.raid_disks]
        spare_disks = [disk.location for disk in self.spare_disks]
        repeated = Counter(raid_disks+spare_disks).most_common(1)
        if repeated[0][1] > 1:
            raise error.Raid.DiskRepeated(repeated[0][0])

        if len([loc for loc in raid_disks if loc.startswith('1.1')]) == 0:
            raise error.Raid.AtLeastOneDiskOnDSU11

        samecap = set(disk.cap.Byte for disk in self.raid_disks+self.spare_disks)
        if len(samecap) <> 1:
            raise error.Raid.NotSameCapacityDisk

        for disk in self.raid_disks + self.spare_disks:
            if disk.role <> ROLE_UNUSED:
                raise error.Raid.DiskUsed(disk.location)
            if disk.health <> HEALTH_NORMAL:
                raise error.Raid.DiskUnnormal(disk.location)
            if disk.host <> Disk.HOST_NATIVE:
                raise error.Raid.DiskUnnormal(disk.location)

        try:
            rebuild_priority = self.rebuild_priority.lower()
        except:
            raise error.InvalidParam('rebuild-priority', self.rebuild_priority)
        if rebuild_priority not in self.REBUILD_PRIORITY:
            raise error.InvalidParam('rebuild', self.rebuild_priority)
        self.rebuild_priority = rebuild_priority

        vm = psutil.avail_phymem()
        if vm / (1024*2) < config.raid.cache.mem_size.KB:
            raise error.NotEnoughCacheMem()


    def _next_dev_name(self):
        nr = [int(md[2:]) for md in glob.glob1('/dev', 'md?*') if 'p' not in md]
        for i in range(0, pow(2,20)):
            if not i in nr: return 'md%s' % i

    @property
    def has_bitmap(self):
        with open('/sys/block/%s/md/bitmap/location' % self.dev_name) as fin:
            return fin.read().strip() == 'file'

    @property
    def support_bitmap(self):
        return self.level in [1, 5, 10]

    def create_bitmap(self):
        if self.support_bitmap:
            bitmap = os.path.join(config.raid.bitmap.dir, '%s.bitmap' % self.uuid)
            cmd = 'mdadm --grow --bitmap=%s --bitmap-chunk=%sM %s' % \
                (bitmap, config.raid.bitmap.chunk_size.MB, self.dev_path)
            execute(cmd)

    def delete_bitmap(self):
        bitmap1 = os.path.join(config.raid.bitmap.dir, '%s.bitmap' % self.uuid)
        bitmap2 = os.path.join('%s.disk' % config.raid.bitmap.dir, '%s.bitmap' % self.uuid)
        if os.path.exists(bitmap1):
            os.remove(bitmap1)
        if os.path.exists(bitmap2):
            os.remove(bitmap2)

    @property
    def stripe_size(self):
        if self.level == 0:
            return self.raid_disks_nr * self.chunk
        elif self.level == 5:
            return (self.raid_disks_nr - 1) * self.chunk

    def active_rebuild_priority(self, prior):
        if prior.lower() == 'min':
            cmd = 'echo %d > /sys/block/%s/md/sync_speed_min' % (self.stripe_size.KB, self.dev_name)
            execute(cmd)
            cmd = 'echo %d > /sys/block/%s/md/sync_speed_max' % (self.stripe_size.KB, self.dev_name)
            execute(cmd)

        if self.raid_disks_nr < 12:
            cmd = 'echo 20480 > /sys/block/%s/md/stripe_cache_size' % (self.dev_name)
            execute(cmd)

        cmd = 'echo 0 > /sys/block/%s/md/preread_bypass_threshold' % (self.dev_name)
        execute(cmd)

    @property
    def partitions(self):
        parts = []
        for dev in glob.glob1('/dev', '%sp*' % self.dev_name):
            s = os.stat('/dev/%s' % dev)
            parts.append((s.st_rdev, dev))
        return [dev for n, dev in sorted(parts)]

    def _mdadm_create(self):
        raid_disks = self.raid_disks[:]
        raid_disk_paths = [disk.dev_path for disk in raid_disks]
        mdadm_uuid = uuid.format(uuid.MDADM_FORMAT, self.uuid)
        sync = '' if self.sync else '--assume-clean'
        bitmap = os.path.join(config.raid.bitmap.dir, '%s.bitmap' % self.uuid)

        if self.level == 0:
            cmd = 'mdadm --create %s --homehost="%s" --uuid="%s" --level=%s --chunk=%s '\
                  '--raid-disks=%s %s --run --force -q --name="%s" '\
                % (self.dev_path, config.raid.homehost, mdadm_uuid, self.level, self.chunk.KB,
                   len(raid_disk_paths), ' '.join(raid_disk_paths), self.name)
        elif self.level == 1 or self.level == 10:
            cmd = 'mdadm --create %s --homehost="%s" --uuid="%s" --level=%s --chunk=%s '\
                  '--raid-disks=%s %s --run %s --force -q --name="%s" --bitmap=%s '\
                  '--bitmap-chunk=%sM'\
                % (self.dev_path, config.raid.homehost, mdadm_uuid, self.level, self.chunk.KB,
                   len(raid_disk_paths), ' '.join(raid_disk_paths), sync, self.name, bitmap,
                   config.raid.bitmap.chunk_size.MB)
        else:
            cmd = 'mdadm --create %s --homehost="%s" --uuid="%s" --level=%s --chunk=%s '\
                  '--raid-disks=%s %s --run %s --force -q --name="%s" --bitmap=%s '\
                  '--bitmap-chunk=%sM --layout=%s '\
                % (self.dev_path, config.raid.homehost, mdadm_uuid, self.level, self.chunk.KB,
                   len(raid_disk_paths), ' '.join(raid_disk_paths), sync, self.name, bitmap,
                   config.raid.bitmap.chunk_size.MB, config.raid.layout)
        execute(cmd)

        db.RaidRecovery.create(uuid=self.uuid, name=self.name, level=self.level,
                chunk_kb=self.chunk.KB, raid_disks_nr=len(raid_disk_paths),
                raid_disks=','.join(d.uuid for d in raid_disks),
                spare_disks_nr=len(self.spare_disks),
                spare_disks=','.join(d.uuid for d in self.spare_disks))

        self._clean_existed_partition()

        s = os.stat(self.dev_path)
        self.save(devno = s.st_rdev)

        if self.level in [5, 6]:
            self.active_rebuild_priority(self.rebuild_priority)

    def _clean_existed_partition(self):
        cmd = 'blockdev --rereadpt %s' % self.dev_path
        _, o = execute(cmd)
        if len(self.partitions) > 0:
            cmd = 'dd if=/dev/zero of=%s bs=512 count=8 oflag=direct' % self.dev_path
            _, o = execute(cmd)

            cmd = 'blockdev --rereadpt %s' % self.dev_path
            _, o = execute(cmd)

    def update_extents(self):
        if self.health not in [HEALTH_DEGRADED, HEALTH_NORMAL]:
            return

        try:
            cmd = 'pvs %s -o pv_pe_alloc_count,pv_pe_count' % self.odev_path
            _,o = execute(cmd)
            counts = o.split('\n')[1].strip().split()
            self.used_cap = int(counts[0])
            self.cap = int(counts[1])
            self.save()
        except Exception as e:
            log.error(caused(e).detail)

    @property
    def free_cap(self):
        return self.cap - self.used_cap

    @property
    def vg_name(self):
        if self._vg_name is None:
            self._vg_name = 'VG-%s' % self.name
        return self._vg_name

    @vg_name.setter
    def vg_name(self, v):
        self._vg_name = v

    def create_ssd(self):
        if not config.raid.ssd.enabled:
            return

        odev_name = '<ssd_name>'
        self.save(odev_name=odev_name)

    def delete_ssd(self):
        if config.raid.ssd.enabled:
            dmremove(self.odev_path)

    def delete_cache(self):
        if config.raid.cache.enabled:
            dmremove(self.odev_path)

    def create_cache(self):
        if not config.raid.cache.enabled:
            return

        cmd = 'blockdev --getsz %s' % self.odev_path
        _, size = execute(cmd)

        odev_name = 'c%s' % self.dev_name
        rule = '0 %s cache %s %s %s %s' % (size.strip('\n'), self.odev_path,
                config.raid.cache.mem_size.MB, self.chunk.Byte, self.raid_disks_nr-1)
        dmcreate(odev_name, rule)

        self.save(odev_name=odev_name)

    @with_transaction
    def _create(self):
        super(Raid, self).create()

        dev_name = self._next_dev_name()
        self.save(uuid=uuid.uuid4(), dev_name=dev_name, cap=0, used_cap=0, odev_name=dev_name)

        for nr, disk in enumerate(self.raid_disks):
            disk.save(role=ROLE_DATA, raid=self, link=True)
            Metadata.update(disk.md_path, raid_uuid=self.uuid)

        for nr, disk in enumerate(self.spare_disks):
            disk.save(role=ROLE_SPARE, raid=self)
            Metadata.update(disk.md_path, raid_uuid=self.uuid)

        self._mdadm_create()

        self.create_ssd()

        self.create_cache()
        #bc = Bcache()
        #bc.create()
        #bc.attach(self)

        cmd = 'dd if=/dev/zero of=%s bs=1M count=128 oflag=direct' % self.odev_path
        execute(cmd)

        cmd = 'pvcreate %s -ff -y --metadatacopies 1' % self.odev_path
        execute(cmd)

        self.join_vg()
        #vg.extend(self)

        self.update_extents()
        self.save()

        log.journal_info('Raid %s is created successfully.' % self.name)

    def join_vg(self):
        cmd = 'vgs -o vg_name'
        _,o = execute(cmd)

        if self.vg_name not in o.split()[1:]:
            vg = config.lvm.vg
            cmd = 'vgcreate -s %sm %s %s' % (vg.pe_size.MB, self.vg_name, self.odev_path)
            execute(cmd)
        else:
            cmd = 'vgextend %s %s' % (self.vg_name, self.odev_path)
            execute(cmd)

    def detach_vg(self):
        cmd = 'vgs -o pv_count'
        _,o = execute(cmd)
        nr = int(o.split()[1])

        if nr == 1:
            cmd = 'vgremove %s' % self.vg_name
        else:
            cmd = 'vgreduce %s %s' % (self.vg_name, self.odev_path)
        execute(cmd)

    def create(self):
        self._create()
        uevent.RaidCreated(uuid=self.uuid).notify()

    def deactive(self):
        if self.online:
            cmd = 'mdadm --stop %s' % self.dev_path
            execute(cmd, False, logging=False)


    @with_transaction
    def _delete(self):
        if self.volumes():
            raise error.Raid.InUse(self.name)

        self.save(deleted=True)
        disks = [disk for disk in self.raid_disks]
        for disk in self.raid_disks + self.spare_disks:
            disk.role = ROLE_UNUSED
            disk.save(raid=None, link=False, unplug_seq=0)
            if disk.online and disk.health <> HEALTH_FAILED:
                Metadata.update(disk.md_path, raid_uuid='')

        if self.online:
            if self.health <> HEALTH_FAILED:
                try:
                    #cmd = 'vgremove %s' % self.vg_name
                    #execute(cmd)
                    self.detach_vg()

                    cmd = 'pvremove %s' % self.odev_path
                    execute(cmd)
                except:
                    pass

            self.delete_cache()

            self.delete_ssd()

            cmd = 'mdadm --stop %s' % self.dev_path
            execute(cmd, False)

        for disk in disks:
            if disk.online:
                cmd = 'mdadm --zero-superblock %s' % disk.dev_path
                execute(cmd, False)

        self.delete_bitmap()
        dev_dir = '/dev/%s' % self.vg_name
        cmd = 'rm %s -rf' % dev_dir
        execute(cmd, False)

    def delete(self):
        raid_disks = [disk.uuid for disk in self.raid_disks]
        self._delete()
        log.journal_info('Raid %s is deleted successfully.' % self.name)
        uevent.RaidRemoved(uuid=self.uuid, raid_disks=raid_disks).notify()

    def _can_online(self, raid_disks):
        disk_devs = [disk.dev_path for disk in raid_disks]
        cmd = 'mdadm --assemble --force --run /dev/md128 %s' % ' '.join(disk_devs)
        try:
            execute(cmd, logging=False)
            return True
        except:
            return False
        finally:
            cmd = 'mdadm --stop /dev/md128'
            execute(cmd, False, logging=False)

    def _find_back_disks(self):
        disks = []
        unplug_seq = self.unplug_seq
        if unplug_seq > 0:
            ds = [disk for disk in self.raid_disks\
                    if disk.role == ROLE_DATA_SPARE and disk.online and disk.health <> HEALTH_FAILED and not disk.link]
            for disk in sorted(ds, key=lambda x: x.unplug_seq, reverse=True):
                if  disk.unplug_seq > 0\
                and unplug_seq == disk.unplug_seq:
                    disks.append(disk)
                    unplug_seq -= 1
                else:
                    break
        return disks, unplug_seq

    def next_back_disk(self):
        disks, _ = self._find_back_disks()
        return disks[0] if disks else None

    def can_add_back_disk(self):
        disk = self.next_back_disk()
        return False if not disk else disk.unplug_seq == self.unplug_seq

    def add_back_disk(self):
        if self.no_raid_disks: return
        disk = self.next_back_disk()
        if disk:
            self._add_one_disk(disk, ROLE_DATA)
            return True
        else:
            return False

    def import_raid(self):
        def filter_disks(raid_disks):
            most = Counter(str(bytearray(disk.sb.dev_roles)) for disk in raid_disks if disk.sb.valid).most_common(1)
            rdisks  = []
            sdisks = [disk for disk in raid_disks if not disk.sb.valid]
            for disk in raid_disks:
                if str(bytearray(disk.sb.dev_roles)) == most[0][0]:
                    rdisks.append(disk)
                else:
                    sdisks.append(disk)
            return rdisks, sdisks

        self._raid_disks, self._spare_disks = filter_disks(self.raid_disks)

        with transaction():
            sb = self.raid_disks[0].sb if self.raid_disks else None
            if sb:
                self.save(name=sb.name, dev_name='', cap=0, used_cap=0,
                        unplug_seq=0, level=sb.level, chunk=Sector(sb.chunksize),
                        raid_disks_nr=sb.raid_disks, spare_disks_nr=0, odev_name='')

            for disk in self.raid_disks:
                disk.save(role=ROLE_DATA, raid=self, link=False)

            for disk in self.spare_disks:
                disk.save(role=ROLE_SPARE, raid=self, link=False)

        if not self._can_online(self.raid_disks):
            return

        self.assemble()

    @classmethod
    def import_all(cls):
        raids = {}
        for disk in Disk.all():
            if disk.raid_hint:
                raids.setdefault(disk.raid_hint, []).append(disk)

        for u, disks in raids.items():
            rd = Raid(disks, uuid=u)
            rd.import_raid()
            if rd.online and rd.health == HEALTH_NORMAL and not rd.has_bitmap:
                rd.create_bitmap()

    def _recreate_when_reboot(self):
        #import db
        #[db.RaidRecovery.select().where(db.RaidRecovery.uuid==<raid_uuid>).\
        #    order_by(db.RaidRecovery.created_at.desc()).tuples()]
        recoveries = list(db.RaidRecovery.select().where(db.RaidRecovery.uuid==self.uuid).\
            order_by(db.RaidRecovery.created_at.desc()))

        if len(recoveries) == 0:
            return False

        self.dev_name = self._next_dev_name()
        mdadm_uuid = uuid.format(uuid.MDADM_FORMAT, self.uuid)
        bitmap = os.path.join(config.raid.bitmap.dir, '%s.bitmap' % self.uuid)
        if os.path.exists(bitmap):
            os.remove(bitmap)

        disk_devs = []
        for u in recoveries[0].raid_disks.split(','):
            try:
                disk = Disk.lookup(uuid=u)
                disk_devs.append(disk.dev_path)
            except:
                pass

        if len(disk_devs) <> self.raid_disks_nr:
            return False

        cmd = 'mdadm --create %s --homehost="%s" --uuid="%s" --level=%s --chunk=%s '\
              '--raid-disks=%s %s --run --assume-clean --force -q --name="%s" --bitmap=%s '\
              '--bitmap-chunk=%sM --layout=%s '\
            % (self.dev_path, config.raid.homehost, mdadm_uuid, self.level, self.chunk.KB,
               len(disk_devs), ' '.join(disk_devs), self.name, bitmap,
               config.raid.bitmap.chunk_size.MB, config.raid.layout)
        execute(cmd)

        s = os.stat(self.dev_path)
        self.save(devno = s.st_rdev, odev_name=self.dev_name)

        if self.level in [5, 6]:
            self.active_rebuild_priority(self.rebuild_priority)
        return True

    @with_transaction
    def _assemble(self):
        raid_disks = [disk for disk in self.raid_disks\
                    if disk.role == ROLE_DATA and disk.online and disk.health <> HEALTH_FAILED]
        last_rdisks = [disk for disk in self.raid_disks\
                if disk.role == ROLE_DATA_SPARE and disk.online and disk.health <> HEALTH_FAILED and not disk.link and disk.unplug_seq == 0]
        if len(last_rdisks) == 1:
            last_rdisks[0].save(unplug_seq=1)
            self.save(unplug_seq=1)
        disks, unplug_seq = self._find_back_disks()
        if unplug_seq == 0 and len(disks) > 0:
            disks = disks[:-1]
            unplug_seq = 1
        raid_disks += disks
        self.dev_name = self._next_dev_name()
        if self._can_online(raid_disks):
            for disk in raid_disks:
                disk.save(link=True, role=ROLE_DATA, unplug_seq=0)
            disk_devs = [disk.dev_path for disk in raid_disks]

            recreated = False
            if len(disk_devs) == self.raid_disks_nr and self.level in [5, 6] and self._health == HEALTH_NORMAL:
                recreated = self._recreate_when_reboot()

            if not recreated:
                cmd = ''
                if self.level == 5:
                    bitmap = os.path.join(config.raid.bitmap.dir, '%s.bitmap' % self.uuid)
                    if os.path.exists(bitmap):
                        log.info('assemble %s with bitmap.' % self.name)
                        cmd = 'mdadm --assemble --force --run --bitmap=%s %s %s' % \
                            (bitmap, self.dev_path, ' '.join(disk_devs))

                if not cmd:
                    log.info('assemble %s without bitmap.' % self.name)
                    cmd = 'mdadm --assemble --force --run %s %s' % (self.dev_path, ' '.join(disk_devs))
                execute(cmd)

                time.sleep(1)
                if self.online and self.health == HEALTH_NORMAL and not self.has_bitmap:
                    self.create_bitmap()

                s = os.stat(self.dev_path)
                self.save(devno=s.st_rdev, unplug_seq=unplug_seq, odev_name=self.dev_name)

                if self.level in [5, 6]:
                    self.active_rebuild_priority(self.rebuild_priority)

            cmd = 'pvscan'
            execute(cmd, False)

    def assemble(self):
        try:
            self._assemble()
            if self.online:
                self.create_cache()
                uevent.RaidOnline(uuid=self.uuid).notify()
        except Exception as e:
            log.error(caused(e).detail)


    def _add_one_disk(self, disk, role):
        try:
            assert disk.unplug_seq == self.unplug_seq
        except:
            log.error("sraid unplug_seq[%s], disk unplug_seq[%s]" % (self.unplug_seq, disk.unplug_seq))
            return
        disk.save(link=True, role=role, unplug_seq=0)
        unplug_seq = self.unplug_seq-1 if self.unplug_seq > 0 else 0
        cmd = 'mdadm --add %s %s' % (self.dev_path, disk.dev_path)
        execute(cmd)
        health = self.health
        if self.level == 0:
            health == HEALTH_FAILED if unplug_seq > 0 else HEALTH_NORMAL
        self.save(unplug_seq=unplug_seq, health=health)

    def adjust_disk_role(self, disk):
        if disk.health <> HEALTH_FAILED:
            disk.save(role=ROLE_SPARE, unplug_seq=0)
        else:
            disk.save(role=ROLE_UNUSED, raid=None, unplug_seq=0)

    def rebuild(self):
        if self.rebuilding:
            return

        log.info("try to select disk for raid %s rebuilding" % self.name)
        if self.online and self.health == HEALTH_DEGRADED:
            disk = self.next_back_disk()
            if disk and disk.unplug_seq == self.unplug_seq:
                log.info("raid disk %s is online, select it to rebuild raid %s" % (disk.location, self.name))
                execute('echo 0 > /sys/module/rqr/parameters/no_rqr')
                self._add_one_disk(disk, ROLE_DATA_SPARE)
                uevent.RaidRebuilding(uuid=self.uuid).notify()
            else:
                unavails = self.unavailable_disks
                if not unavails:
                    log.info("there is no unavail disk in raid %s" % self.name)
                    return

                log.info("try to find spare disk to rebuild raid %s" % self.name)
                for disk in self.spare_disks:
                    if disk.online and not disk.link:
                        self.adjust_disk_role(unavails[0])
                        disk.unplug_seq = self.unplug_seq
                        log.info("spare disk %s is unuse, select it to rebuild raid %s" % (disk.location, self.name))
                        execute('echo 0 > /sys/module/rqr/parameters/no_rqr')
                        self._add_one_disk(disk, ROLE_DATA_SPARE)
                        uevent.RaidRebuilding(uuid=self.uuid).notify()
                        return

                log.info("try to find global spare disk to rebuild raid %s" % self.name)
                for disk in Disk.global_spare_disks():
                    if disk.online and disk.cap == self.raid_disks[0].cap:
                        disk.save(role=ROLE_SPARE, raid=self)
                        Metadata.update(disk.md_path, raid_uuid=self.uuid)

                        self.adjust_disk_role(unavails[0])
                        disk.unplug_seq = self.unplug_seq
                        log.info("global spare disk %s is unuse, select it to rebuild raid %s" % (disk.location, self.name))
                        execute('echo 0 > /sys/module/rqr/parameters/no_rqr')
                        self._add_one_disk(disk, ROLE_DATA_SPARE)
                        uevent.RaidRebuilding(uuid=self.uuid).notify()
                        return


    def scan(self):
        with transaction():
            for disk in self.raid_disks:
                if not disk.online:
                    self.save(role=ROLE_DATA_SPARE)

            self.save(dev_name='', odev_name='')
        self.assemble()

    @classmethod
    def scan_all(cls):
        for raid in cls.all():
            raid.scan()
        cmd = 'pvscan'
        execute(cmd, False)

class Part(Admin):
    table = db.Part
    health = FieldAdapter(default=HEALTH_NORMAL)
    role = FieldAdapter(default=ROLE_UNUSED)
    link = FieldAdapter(default=False)
    unplug_seq = FieldAdapter(default=0)
    stub_dev = FieldAdapter(default='')
    disk = FieldAdapter('disk', lambda x: x.db if x else x, lambda x: Disk(db=x) if x else x)
    cap = FieldAdapter('cap_sector', lambda x: x.Sector, lambda x: Sector(x), Sector(0))
    off = FieldAdapter('off_sector', lambda x: x.Sector, lambda x: Sector(x), Sector(0))
    data = FieldAdapter('data_sector', lambda x: x.Sector, lambda x: Sector(x), Sector(0))
    rqr_count = FieldAdapter(default=0)
    primary_index = ('disk', 'partno')

    def __init__(self, rqr_reserved_ratio=config.raid.rqr.reserved_ratio, **kv):
        super(Part, self).__init__(**kv)
        self.rqr_reserved_ratio = rqr_reserved_ratio
        self.data_off = 0

    @property
    def dev_path(self):
        dm_path = '/dev/mapper/rqr-%s' % self.dev_name
        if os.path.exists(dm_path):
            return dm_path
        elif self.stub_dev:
            return '/dev/%s' % self.stub_dev
        else:
            return '/dev/%s' % self.dev_name

    @property
    def dm_path(self):
        try:
            s = os.stat(self.dev_path)
            rqr_devno = s.st_rdev
            for dev in glob.glob('/dev/dm-*'):
                s = os.stat(dev)
                if s.st_rdev == rqr_devno:
                    return dev
        except:
            pass
        return ''

    @property
    def base_path(self):
        return '/dev/%s' % self.dev_name

    def _next_stub_dev(self):
        nr = [int(md[2:]) for md in glob.glob1('/dev', 'md?*') if 'p' not in md]
        for i in range(0, pow(2,20)):
            if not i in nr: return 'md%s' % i

    def _create_stub(self):
        name = 'md%s' % (self.disk.stub_base + self.partno)
        cmd = 'mdadm -CR /dev/%s -lfaulty -n1 %s' % (name, self.base_path)
        _,o = execute(cmd)

        self.stub_dev = name
        return name

    def _create_rqr(self, target, data, data_off, meta_off1, meta_off2, meta, repl_off, repl):
        metadata = config.raid.rqr.metadata
        md_dev = '/dev/%s' % metadata.loop_dev if metadata.path else ''
        rule = "0 %s rqr %s %s %s %s %s %s %s 512 %s" % (data-data_off, target, data_off, meta_off1,\
                meta_off2, meta, repl_off, repl, md_dev)
        dmcreate('rqr-%s' % self.dev_name, rule)

    def _calc_metadata_idx(self):
        m = re.search('(\d+).(\d+).(\d+)', self.disk.location)
        return (int(m.group(3))-1) * config.disk.partition_max_nr + self.partno - 1

    def create(self):
        stub_name = '%s:%s' % (self.disk.location, self.partno)
        dev_name = self.dev_name
        data_off = 0
        if stub_name in config.disk.stub:
            dev_name = self._create_stub()
            data_off = MB(1).Sector

        cmd = 'cat /sys/class/block/%s/start' % self.dev_name
        _, o = execute(cmd)
        self.off = Sector(o)

        cmd = 'blockdev --getsz %s' % self.base_path
        _, o = execute(cmd)
        self.cap = Sector(o)

        cmd = 'blockdev --getsz /dev/%s' % dev_name
        _, o = execute(cmd)
        cap = Sector(o)

        align = Sector(31)
        repl = (cap * self.rqr_reserved_ratio).ceil(align)
        meta = Sector(int(repl / align))

        reserved = meta*2 + repl
        meta_off1 = cap - reserved
        meta_off2 = meta_off1 + meta
        repl_off = meta_off2 + meta
        self.data = meta_off1.floor(MB(1))
        self.data_off = data_off

        rqr = config.raid.rqr
        if rqr.metadata.path:
            meta_off1 = rqr.metadata.max_size * self._calc_metadata_idx()
            meta_off2 = meta_off1 + rqr.metadata.max_size
            cmd = "rqr_init /dev/%s %s %s %s" % (rqr.metadata.loop_dev,\
                    meta_off1.Sector, meta_off2.Sector, meta.Sector)
        else:
            cmd = "rqr_init /dev/%s %s %s %s" % (dev_name, meta_off1.Sector,\
                    meta_off2.Sector, meta.Sector)
        _, o = execute(cmd)

        self._create_rqr('/dev/%s'%dev_name, self.data.Sector, data_off,\
                meta_off1.Sector, meta_off2.Sector,\
                meta.Sector, repl_off.Sector, repl.Sector)

        self._rqr = {'meta_off1_sector':meta_off1.Sector,\
                     'meta_off2_sector':meta_off2.Sector,\
                     'meta_sector':meta.Sector,
                     'repl_off_sector':repl_off.Sector,\
                     'repl_sector':repl.Sector}

    def save(self, **kv):
        super(Part, self).save(**kv)
        rqr = getattr(self, '_rqr', None)
        if rqr:
            db.RQR.create(part=self.db, **rqr)

    def scan(self):
        stub_name = '%s:%s' % (self.disk.location, self.partno)
        dev_name = self.dev_name
        data_off = 0
        if stub_name in config.disk.stub:
            dev_name = self._create_stub()
            data_off = MB(1).Sector

        rqr = db.RQR.get(part=self.db)
        meta = rqr.meta_off2_sector - rqr.meta_off1_sector
        self._create_rqr('/dev/%s' % dev_name, self.data.Sector, data_off,\
                rqr.meta_off1_sector, rqr.meta_off2_sector,\
                meta, rqr.repl_off_sector, rqr.repl_sector)

    def delete(self):
        try:
            cmd = 'dmsetup remove rqr-%s' % self.dev_name
            _, o = execute(cmd)

            rqr = db.RQR.get(part=self.db)
            rqr.delete_instance()

            stub_name = '%s:%s' % (self.disk.location, self.partno)
            if stub_name in config.disk.stub:
                cmd = 'mdadm --stop /dev/%s' % self.stub_dev
                _,o = execute(cmd)

            super(Part, self).delete()
        except:
            pass

def scan_disk(disk):
    db.connect()
    try:
        ret = disk.scan()
        return ret
    except:
        return None, []
    finally:
        db.close()

class Disk(Admin):
    DISKTYPE_SATA = 'sata'
    DISKTYPE_SAS  = 'sas'
    DISKTYPE_SSD  = 'ssd'

    HOST_NATIVE  = 'native'
    HOST_LOCAL   = 'local'  #db has no this disk's data, but metadata host uuid equal with storage
    HOST_FOREIGN = 'foreign'
    HOST_USED    = 'used'

    HEALTH = ['failed', 'normal']

    ROLE = ['unused', 'data', 'spare', 'global spare']

    SLOT_INVALID = -1

    table = db.Disk
    health = FieldAdapter(default=HEALTH_NORMAL)
    role = FieldAdapter('role', default=ROLE_UNUSED)
    cap = FieldAdapter('cap_sector', lambda x: x.Sector, lambda x: Sector(x), Sector(0))
    raid = FieldAdapter('raid', lambda x: x.db if x else x, lambda x: Raid(db=x) if x else x)
    link = FieldAdapter(default=False)
    unplug_seq = FieldAdapter(default=0)
    raid_hint = FieldAdapter(default='')
    rqr_count = FieldAdapter(default=0)

    primary_index = 'uuid'

    def __init__(self, **kv):
        super(Disk, self).__init__(**kv)

    @classmethod
    def dmname_to_disk(cls, dm):
        devno = os.stat('/dev/%s' % dm).st_rdev
        for disk in cls.all():
            if os.stat(disk.dev_path).st_rdev == devno:
                return disk
        raise error.NotExistError(dm)

    @property
    def sb(self):
        if not hasattr(self, '_sb'):
            self._sb = mdp_superblock_1()
            self._sb.read_from(self.dev_path)
        return self._sb

    @property
    def md_path(self):
        return '/dev/%s' % self.dev_name

    @property
    def dev_path(self):
        dm_path = '/dev/mapper/s%s' % self.dev_name
        if os.path.exists(dm_path):
            return dm_path
        else:
            return '/dev/%s' % self.dev_name

    @property
    def parts(self):
        if hasattr(self, '_parts'): return self._parts
        if self.exists:
            self._parts = [Part(db=db) for db in self.db.parts]
        else:
            self._parts = []
        return self._parts

    @property
    def partitions(self):
        parts = []
        for dev in glob.glob1('/dev', '%s*' % self.dev_name):
            if dev == self.dev_name: continue
            s = os.stat('/dev/%s' % dev)
            parts.append((s.st_rdev, dev))
        return [dev for n, dev in sorted(parts)]

    def _classify(self):
        if len(self.partitions) == 0:
            try:
                md = Metadata.parse(self.md_path)
                if md.host_uuid == uuid.host_uuid():
                    if self.table.exists(db.Disk.uuid == md.disk_uuid):
                        return 'native', md
                    else:
                        return 'local', md
                else:
                    return 'foreign', md
            except:
                return 'new', None
        else:
            return 'used', None

    def _grab_disk_vpd(self):
        self.disktype = self.DISKTYPE_SATA
        self.rpm = 0
        self.vendor = 'UNKOWN'
        self.model  = 'UNKOWN'
        self.sn     = ''
        self.cap = Sector(0)

        cmd = 'hdparm -I /dev/%s' % self.dev_name
        _, o = execute(cmd, False, logging=False)
        try:
            model = re.search('Model Number:\s*(.+)', o).group(1).strip().split()
            self.vendor = model[0]
            self.model  = model[1]
            self.sn     = re.search('Serial Number:\s*(.+)', o).group(1).strip()
        except:
            pass

        try:
            cmd = 'blockdev --getsz %s' % self.dev_path
            _, o = execute(cmd, logging=False)
            self.cap = Sector(o)
        except:
            pass

    def _partition(self, size=config.disk.partition_size, max_nr=config.disk.partition_max_nr):
        part_size = unit(size)
        meta_size = MB(64)
        n = min(int((self.cap - meta_size) / part_size), max_nr)

        start = meta_size + Sector(1)
        for i in range(1, n):
            addpart(self.dev_path, i, start, part_size)
            start += part_size

        left = self.cap - start
        if left.Sector > 0:
            addpart(self.dev_path, n, start, left)

    def remove_dev(self):
        def remove_part(dev):
            if dev:
                dm_path = '/dev/mapper/rqr-%s' % dev
                if os.path.exists(dm_path):
                    dmremove(dm_path)

                part_path = '/dev/%s' % dev
                if os.path.exists(part_path):
                    delpart(part_path)

        try:
            dm_path = '/dev/mapper/s%s' % self.dev_name
            if os.path.exists(dm_path):
                dmremove(dm_path)

            for part in self.parts:
                remove_part(part.dev_name)

            for dev in self.partitions:
                remove_part(dev)
        except:
            pass

    def _init_used_disk(self):
        log.info('init used disk %s(%s)...' % (self.location, self.dev_name))

        s = os.stat(self.dev_path)
        self.uuid = uuid.uuid4()
        self.host = self.HOST_USED
        self.devno = s.st_rdev
        log.info('finish scan')
        return self, []

    def format_disk(self):
        host = self.host
        if host not in [self.HOST_USED, self.HOST_FOREIGN]:
            raise error.Disk.NeedNotFormat(self.location)

        self.remove_dev()
        try:
            execute('dd if=/dev/zero of=%s bs=4K count=16384 oflag=direct' % self.dev_path)
            execute('blockdev --rereadpt %s' % self.dev_path)
        except:
            raise error.InternalError()

        with transaction():
            uuid = self.uuid
            _, parts = self._init_new_disk()
            self.table.delete().where(db.Disk.uuid == uuid).execute()
            self.save(force_create=True, raid_hint='')
            for part in parts:
                part.save()

        log.journal_warning('Disk %s is formated.' % self.location)
        uevent.DiskFormated(uuid=self.uuid).notify()

    def set_role(self, role):
        if role not in [ROLE_UNUSED, ROLE_GLOBAL_SPARE]:
            raise error.InvalidParam('role', role)
        elif role == ROLE_GLOBAL_SPARE and self.role <> ROLE_UNUSED:
            raise error.Disk.Role(self.location, self.role, role)
        elif role == ROLE_UNUSED and self.role <> ROLE_GLOBAL_SPARE:
            raise error.Disk.Role(self.location, self.role, role)
        self.save(role=role)

        log.journal_info('Disk %s is changed to %s.' % (self.location, role))
        uevent.DiskRoleChanged(uuid=self.uuid).notify()


    @classmethod
    def global_spare_disks(cls):
        return [Disk(db=_db) for _db in Disk.table.select().\
                   where(db.Disk.role == ROLE_GLOBAL_SPARE).execute()]

    def _make_rules(self, parts):
        off = 0
        rules = []
        for part in parts:
            sector = part.data.Sector - part.data_off
            r = '%s %s linear %s 0' % (off, sector, part.dev_path)
            rules.append(r)
            off += sector
        return rules

    def _init_new_disk(self):
        log.info('init new disk %s(%s)...' % (self.location, self.dev_name))

        with Timer() as t:
            self._partition()
        log.info('partition disk %s, cost:%s secs' % (self.dev_name, t.secs))

        time.sleep(0.5)
        parts = []
        with Timer() as t:
            for nr, dev in enumerate(self.partitions, 1):
                part = Part(dev_name=dev, disk=self, partno=nr)
                s = os.stat(part.base_path)
                part.devno = s.st_rdev
                part.create()
                parts.append(part)
        log.info('create rqr dm, cost:%s secs' % t.secs)

        dmcreate('s%s' % self.dev_name, *self._make_rules(parts))

        with Timer() as t:
            md = DiskMetadata_1_1()
            md.disk_uuid = uuid.uuid4()
            md.partition_size = config.disk.partition_size
            md.partition_max_nr = config.disk.partition_max_nr
            md.rqr_reserved_ratio = config.raid.rqr.reserved_ratio
            md.save('/dev/%s' % self.dev_name, 1)
        log.info('save %s md, cost:%s secs' % (self.dev_name, t.secs))

        s = os.stat(self.dev_path)
        self.uuid = md.disk_uuid
        self.host = self.HOST_NATIVE
        self.devno = s.st_rdev
        log.info('%s finish scan' % self.dev_name)
        return self, parts

    def _init_native_disk(self):
        log.info('init native disk %s(%s)...' % (self.location, self.dev_name))
        self.uuid = self.md.disk_uuid
        self.host = self.HOST_NATIVE
        self.location = self.location
        s = os.stat(self.dev_path)
        self.devno = s.st_rdev
        if self.health <> HEALTH_FAILED:
            self.health = HEALTH_NORMAL

        with Timer() as t:
            for part in self.parts:
                addpart(self.dev_path, part.partno, part.off, part.cap)

        log.warning('partition disk %s, cost:%s secs' % (self.dev_name, t.secs))

        time.sleep(0.5)
        parts = []
        with Timer() as t:
            for part in self.parts:
                part.dev_name = '%s%s' % (self.dev_name, part.partno)
                s = os.stat(part.base_path)
                part.devno = s.st_rdev
                part.scan()
                parts.append(part)

        dmcreate('s%s' % self.dev_name, *self._make_rules(parts))

        log.warning('scan %s parts, cost:%s secs' % (self.dev_name, t.secs))
        return self, parts


    def _init_local_disk(self):
        return self._init_foreign_disk()

    def _init_foreign_disk(self):
        log.info('init foreign disk %s(%s)...' % (self.location, self.dev_name))
        self._partition(self.md.partition_size, self.md.partition_max_nr)

        time.sleep(0.5)
        parts = []
        for nr, dev in enumerate(self.partitions, 1):
            part = Part(self.md.rqr_reserved_ratio, dev_name=dev, disk=self, partno=nr)
            s = os.stat(part.base_path)
            part.devno = s.st_rdev
            part.create()
            parts.append(part)

        dmcreate('s%s' % self.dev_name, *self._make_rules(parts))

        s = os.stat(self.dev_path)
        self.uuid = self.md.disk_uuid
        self.host = self.HOST_FOREIGN
        self.devno = s.st_rdev
        self.raid_hint = self.md.raid_uuid
        return self, parts

    def fail(self):
        self.save(health=HEALTH_FAILED,link=False,role=ROLE_KICKED,raid=None)

    def scan(self):
        self._grab_disk_vpd()
        log.warning('scan disk %s(%s)...' % (self.location, self.dev_name))
        host, self.md = self._classify()
        init = getattr(self, '_init_%s_disk' % host, None)

        try:
            return init()
        except Exception as e:
            log.error(caused(e).detail)

    @classmethod
    def scan_all(cls):
        log.info('disk scan...')
        for disk in Disk.all():
            if disk.host <> cls.HOST_NATIVE:
                disk.db.delete_instance(recursive=True, delete_nullable=True)
        cls.table.update(location='', dev_name='', devno=0, link=False).execute()

        db.Part.update(dev_name='', devno=0, link=False, stub_dev='').execute()

        base = 1000

        with Timeout(60):
            m = lm.LocationMapping()
            while not m.mapping:
                time.sleep(1)
                m = lm.LocationMapping()

        m = lm.LocationMapping()
        count = len(m.mapping)
        while True:
            time.sleep(16)
            m = lm.LocationMapping()
            if count == len(m.mapping):
                break
            count = len(m.mapping)
            log.info('new disk online, wait again')

        mapping = m.mapping.copy()

        ssd = config.raid.ssd
        if ssd.location and mapping.has_key(ssd.location):
            del mapping[ssd.location]

        with Timer() as t:
            log.warning('mapping: %s' % mapping)
            if not mapping:
                raise error.Disk.NotFoundAnyDisk

            pool = mp.Pool(processes=len(mapping.keys()))
            gathers = []
            for loc, dev_name in mapping.items():
                disk = Disk(location=loc, dev_name=dev_name)
                disk.stub_base = base
                base += 1000
                gathers.append((disk, pool.apply_async(scan_disk, (disk,))))
            pool.close()
            pool.join()

            with transaction():
                for disk, gather in gathers:
                    try:
                        disk, parts = gather.get()
                        if disk:
                            disk.save(prev_location=disk.location)
                        for part in parts:
                            part.save()
                    except:
                        log.warning('scan disk %s failed' % disk.dev_name)

        cmd = 'sync'
        _,_ = execute(cmd)
        log.warning('scan all disks, cost:%s secs' % t.secs)

class Volume(Admin):
    NAME_PATTERN = '^[_a-zA-Z][-_a-zA-Z0-9]*$'
    NAME_MAX_LEN = 64

    table = db.Volume

    primary_index = 'name'

    health = FieldAdapter(default=HEALTH_NORMAL)
    used = FieldAdapter(default=False)
    #raid = FieldAdapter('raid', lambda x: x.db if x else x, lambda x: Raid(db=x) if x else x)
    owner_type = FieldAdapter(default='')

    def __init__(self, **kv):
        super(Volume, self).__init__(**kv)
        self._lvm_name = None
        self._dev_path = None
        self._raids = None
        self._normal_raid = None
        self._prog = 0.0

    def exists_get_db(self, cond):
        cond.update(deleted=0)
        return self.table.get(**cond)

    @property
    def normal_raid(self):
        if self._normal_raid is None:
            rv = db.RaidVolume.select().where((db.RaidVolume.volume == self.uuid) & (db.RaidVolume.type == RV_NORMAL)).first()
            self._normal_raid = Raid(db=rv.raid)
        return self._normal_raid

    @property
    def raids(self):
        if self._raids is not None:
            return self._raids
        if self.exists:
            self._raids = [Raid(db=rv.raid) for rv in db.RaidVolume.select().where(db.RaidVolume.volume == self.uuid)]
        else:
            self._raids = []
        return self._raids

    @classmethod
    def all(cls):
        return [cls(db=_db) for _db in cls.table.select().where(db.Volume.deleted == 0)]

    @classmethod
    def lookup(cls, **kv):
        kv.update(deleted=0)
        return super(Volume, cls).lookup(**kv)

    @property
    def initiators(self):
        if hasattr(self, '_initiators'): return self._initiators
        if self.exists:
            self._initiators = [Initiator(db=initr) for initr in self.db.initiators]
        else:
            self._initiators = []
        return self._initiators

    def _check_create_param(self):
        if not re.search(self.NAME_PATTERN, self.name):
            raise error.InvalidParam('name', self.name)

        if len(self.name) > self.NAME_MAX_LEN:
            raise error.NameTooLong(self.name, self.NAME_MAX_LEN)

        ext_nr = self.raid.free_cap
        if self.cap.upper() <> 'ALL':
            try:
                cap = unit(self.cap)
            except:
                raise error.InvalidParam('capacity', self.cap)
            if cap.Byte == 0:
                raise error.InvalidParam('capacity', self.cap)

            pe = config.lvm.vg.pe_size
            ext_nr = int(cap / pe)

        if ext_nr == 0:
            raise error.Volume.CapacityLessThanPE(self.cap, pe)
        if self.raid.free_cap < ext_nr:
            raise error.Volume.NotEnoughFreeCapacity(self.raid.free_cap*pe, cap)
        self.cap = ext_nr

    def import_volume(self):
        self.save(health=HEALTH_NORMAL)

    @classmethod
    def import_all(cls):
        cmd = 'lvs -o lv_uuid,lv_name,lv_size,vg_name,seg_pe_ranges'
        _,o = execute(cmd)

        vs = [l.split() for l in o.split('\n')[1:-1]]
        lvs = {}
        for v in vs:
            try:
                dev = re.findall('/(md\d+)', v[4])[0]
                lv = lvs.setdefault(v[0], {'uuid': v[0],
                                           'name': v[1],
                                           'size': v[2],
                                           'vg': v[3],
                                           'pe': []})
                lv['pe'].append(dev)
            except:
                continue

        for lv in lvs.values():
            try:
                u = uuid.normalize(lv['uuid'].lower())
                raidname = lv['vg'][3:]
                raid = Raid.lookup(name=raidname)
                cap = unit(lv['size']) / config.lvm.vg.pe_size
                vol = Volume(uuid=u, name=lv['name'], cap=cap, health=HEALTH_NORMAL)
                vol.save()
                db.RaidVolume.create(raid=raid.uuid, volume=u, type=RV_NORMAL)
                for pe in lv['pe']:
                    try:
                        r = Raid.lookup(dev_name=pe)
                        if r.uuid == raid.uuid:
                            continue
                        db.RaidVolume.create(raid=r.uuid, volume=u, type=RV_EXPANSION)
                    except:
                        continue
                vol.scan()
            except Exception as e:
                log.error(caused(e).detail)

    @with_transaction
    def _create(self):
        super(Volume, self).create()

        try:
            cmd = 'echo 1 > /sys/module/cn/parameters/lun_dm'
            execute(cmd)

            cmd = 'lvcreate -n %s -l %s %s' % (self.name, self.cap, self.raid.vg_name)
            execute(cmd)

            cmd = 'echo 0 > /sys/module/cn/parameters/lun_dm'
            execute(cmd)


            md = lvm.Metadata.get(self.raid.vg_name)
            id = md.lv(self.name)['id']
            u = uuid.normalize(id.lower())

            self.save(uuid=u, health=HEALTH_NORMAL)

            db.RaidVolume.create(raid=self.raid.uuid, volume=u, type=RV_NORMAL)

            self.raid.update_extents()
        except Exception as e:
            log.error(caused(e).detail)
            raise error.InternalError()

        sname = '/dev/mapper/%s' % self.raid.dev_name
        cmd = 'rm -rf %s' % sname
        execute(cmd, False)

        cmd = 'ln -s %s %s' % (self.dev_path, sname)
        execute(cmd, False)

        log.journal_info('Volume %s is created successfully.' % self.name)


    def create(self):
        self._create()
        uevent.VolumeCreated(uuid=self.uuid).notify()

    def _check_delete_param(self):
        if self.initiators:
            raise error.Volume.Mapped(self.name)
        if self.used:
            fs = MonFS.all()
            if len(fs) > 0 and fs[0].volume.uuid == self.uuid:
                raise error.Volume.HasFS(self.name)

    def deactive(self):
        try:
            if self.online:
                dmremove(self.dev_path)
                link_path = '/dev/%s/%s' % (self.vg_name, self.name)
                cmd = 'rm %s -f' % link_path
                execute(cmd, False)
        except Exception as e:
            log.error(caused(e).detail)

    @with_transaction
    def _delete(self):
        self._check_delete_param()

        self.save(deleted=1)
        if self.health == HEALTH_NORMAL:
            try:
                cmd = 'lvchange -an %s' % self.lvm_name
                execute(cmd)

                cmd = 'lvremove %s' % self.lvm_name
                execute(cmd)

                for raid in self.raids:
                    raid.update_extents()
                self.save(deleted=2)
            except Exception as e:
                self.deactive()
                log.error(caused(e).detail)
        else:
            self.deactive()

    def delete(self):
        self._delete()
        syncd.delete_sync_volume_task(self.name)
        log.journal_info('Volume %s is deleted successfully.' % self.name)
        uevent.VolumeRemoved(uuid=self.uuid).notify()

    def sync(self):
        syncd.sync_volume(self.name)
        uevent.VolumeSyncing(uuid=self.uuid).notify()

    @property
    def syncing(self):
        try:
            t = syncd.query_sync_progress(self.name)

            if t and t['status'] == 'inprogress':
                self._prog = float( '%0.2f' % (float(t['count'])/float(t['nr'])) )
                return True
            elif t and t['status'] == 'stop':
                self._prog = float( '%0.2f' % (float(t['count'])/float(t['nr'])) )
                return False
            elif t and t['status'] == 'completed':
                self._prog = 1.0
                return False
            else:
                self._prog = 0.0
                return False
        except Exception as e:
            log.error(caused(e).detail)
            self._prog = 0.0
            return False

    @property
    def sync_progress(self):
        return self._prog

    def stop_sync(self):
        for i in range(0, 10):
            time.sleep(0.5)
            cmd = 'ps -elf |grep dd |grep -v grep'
            _, o = execute(cmd)
            if self.dev_path in o:    
                syncd.stop_sync_volume(self.name)
            else:
                break

    @property
    def vg_name(self):
        return self.normal_raid.vg_name

    @property
    def lvm_name(self):
        if not self._lvm_name:
            self._lvm_name = '%s/%s' % (self.vg_name, self.name)
        return self._lvm_name

    @property
    def dev_path(self):
        if not self._dev_path:
            vg_name = self.vg_name.replace('-', '--')
            self._dev_path = '/dev/mapper/%s-%s' % (vg_name, self.name.replace('-', '--'))
        return self._dev_path

    def scan(self):
        try:
            runnable = all(raid.runnable for raid in self.raids)
            if not self.online and runnable:
                cmd = 'echo 1 > /sys/module/cn/parameters/lun_dm'
                execute(cmd)
                cmd = 'lvchange -ay %s' % self.lvm_name
                execute(cmd)
                cmd = 'echo 0 > /sys/module/cn/parameters/lun_dm'
                execute(cmd)
                self.save(health=HEALTH_NORMAL)
                if self.deleted == 1:
                    self._delete()
                elif self.deleted == 0:
                    uevent.VolumeOnline(uuid=self.uuid).notify()

                lraid = self.raids
                sname = '/dev/mapper/%s' % lraid[0].dev_name
                cmd = 'rm -rf %s' % sname
                execute(cmd, False)
                cmd = 'ln -s %s %s' % (self.dev_path, sname)
                execute(cmd, False)

        except Exception as e:
            log.error(caused(e).detail)

    @classmethod
    def scan_all(cls):
        for volume in cls.all():
            volume.scan()

        for _db in cls.table.select().where(db.Volume.deleted == 1):
            volume = Volume(db=_db)
            volume.scan()

class XFS(Admin):
    NAME_PATTERN = '^[_a-zA-Z][-_a-zA-Z0-9]*$'
    NAME_MAX_LEN = 31

    table = db.XFS

    primary_index = 'name'

    chunk = FieldAdapter('chunk_kb', lambda x: x.KB, lambda x: KB(x))
    volume = FieldAdapter('volume', lambda x: x.db if x else x, lambda x: Volume(db=x) if x else x)

    def _check_create_param(self):
        #if len(self.all()) > 0:
        #    raise error.FS.OnlySupportOne()

        if len(self.name) > self.NAME_MAX_LEN:
            raise error.NameTooLong(self.name, self.NAME_MAX_LEN)

        if not re.search(self.NAME_PATTERN, self.name):
            raise error.InvalidParam('name', self.name)

        if self.volume.health <> HEALTH_NORMAL:
            raise error.FS.VolumeUnnormal(self.volume.name)

        if self.volume.used:
            raise error.FS.VolumeUsed(self.volume.name)

        avails = self.avail_mountpoints()
        if len(avails) == 0:
            raise error.FS.NoMountPoint()

        self.mountpoint = avails[0]

        #raid = self.volume.raid
        #if not raid:
        #    raise error.FS.VolumeUnnormal(self.volume.name)
        #rv = db.RaidVolume.select().where((db.RaidVolume.volume == self.volume.uuid) & (db.RaidVolume.type == RV_NORMAL)).first()
        raid = self.volume.normal_raid

        self.chunk = raid.chunk
        self.raid_disks_nr = raid.raid_disks_nr

    def avail_mountpoints(self):
        '''avails = config.nas.mount_dirs[:]
        for fs in XFS.all():
            avails.remove(fs.mountpoint)
        for fs in MonFS.all():
            avails.remove(fs.mountpoint)'''
        return [self.mountpoint]

    def mount(self, created=False):
        nodisk = glob.glob1('/dev', 'sd?3')[0]
        logdev = nodisk[0:3]
        if 'sda' in config.xfs.mount_options:
           config.xfs.mount_options = config.xfs.mount_options.replace('sda', logdev)
        cmd = 'mount -o %s %s %s' % (config.xfs.mount_options, self.volume.dev_path, self.mountpoint)
        execute(cmd)

        if created:
            cmd = 'chmod 777 -R %s' % self.mountpoint
            execute(cmd)

        cmd = 'service smbd restart'
        execute(cmd, False)
        cmd = '/etc/init.d/smb restart'
        execute(cmd, False)
        cmd = 'modprobe nfs'
        execute(cmd, False)
        cmd = '/etc/init.d/rpcbind restart'
        execute(cmd, False)
        cmd = '/etc/init.d/rpcidmapd restart'
        execute(cmd, False)
        cmd = '/etc/init.d/nfs restart'
        execute(cmd, False)

    def repair(self):
        return
        cmd = 'xfs_repair -L  %s' % self.volume.dev_path
        execute(cmd, False)

    def umount(self):
        cmd = 'service smbd stop'
        execute(cmd, False)
        cmd = '/etc/init.d/smb stop'
        execute(cmd, False)
        cmd = '/etc/init.d/nfs stop'
        execute(cmd, False)

        cmd = 'lsof %s' % self.mountpoint
        e,_ = execute(cmd, False)
        if e == 0:
            cmd = 'service smbd start'
            execute(cmd, False)
            cmd = '/etc/init.d/smb start'
            execute(cmd, False)
            raise error.FS.MountedDirUsed(self.mountpoint)

        cmd = 'umount %s' % self.mountpoint
        e,o = execute(cmd, False)
        if e > 1:
            raise InternalError()

    @with_transaction
    def _create(self):
        super(XFS, self).create()

        try:
            nodisk = glob.glob1('/dev', 'sd?3')[0]
            logdev = nodisk[0:3]
            if 'sda' in config.xfs.make_options:
                config.xfs.make_options = config.xfs.make_options.replace('sda', logdev)
            cmd = 'mkfs -t xfs %s -f -d su=%sk -d sw=%s %s' % (config.xfs.make_options, self.chunk.KB, self.raid_disks_nr-1, self.volume.dev_path)
            #cmd = 'mkfs -t ext2 %s' % self.volume.dev_path
            execute(cmd)

            self.mount(created=True)
            self.volume.save(used=True, owner_type='xfs')
            self.save(uuid=uuid.uuid4())
        except Exception as e:
            log.error(caused(e).detail)
            raise error.InternalError()

        log.journal_info('Filesystem %s is created successfully.' % self.name)

    def create(self):
        self._create()
        uevent.FSCreated(type='xfs', volume=self.volume.name).notify()

    @with_transaction
    def _delete(self):
        self.volume.save(used=False, owner_type='')
        super(XFS, self).delete()

        self.umount()
        try:
            if self.volume.health <> HEALTH_FAILED and self.volume.online:
                cmd = 'dd if=/dev/zero of=%s bs=%sK count=1' % (self.volume.dev_path, self.chunk.KB)
                execute(cmd)
        except Exception as e:
            log.error(caused(e).detail)
            raise error.InternalError()

        log.journal_info('Filesystem %s is deleted successfully.' % self.name)

    def delete(self):
        self._delete()
        uevent.FSRemoved(type='xfs', volume=self.volume.name).notify()

    def scan(self):
        if self.volume.online:
            self.repair()
            self.mount()
            uevent.FSOnline(type='xfs', volume=self.volume.name).notify()

    @classmethod
    def scan_all(cls):
        for fs in cls.all():
            fs.scan()

    @classmethod
    def import_all(cls):
        pass

class MonFS(Admin):
    NAME_PATTERN = '^[_a-zA-Z][-_a-zA-Z0-9]*$'
    NAME_MAX_LEN = 31

    table = db.MonFS

    primary_index = 'name'

    chunk = FieldAdapter('chunk_kb', lambda x: x.KB, lambda x: KB(x))
    volume = FieldAdapter('volume', lambda x: x.db if x else x, lambda x: Volume(db=x) if x else x)

    def _check_create_param(self):
        if len(self.all()) > 0:
            raise error.FS.OnlySupportOne()

        if len(self.name) > self.NAME_MAX_LEN:
            raise error.NameTooLong(self.name, self.NAME_MAX_LEN)

        if not re.search(self.NAME_PATTERN, self.name):
            raise error.InvalidParam('name', self.name)

        if self.volume.health <> HEALTH_NORMAL:
            raise error.FS.VolumeUnnormal(self.volume.name)

        if self.volume.used:
            raise error.FS.VolumeUsed(self.volume.name)

        avails = self.avail_mountpoints()
        if len(avails) == 0:
            raise error.FS.NoMountPoint()

        self.mountpoint = avails[0]

        raid = self.volume.normal_raid
        if not raid:
            raise error.FS.VolumeUnnormal(self.volume.name)

        if raid.stripe_size < KB(512):
            raise error.FS.RaidStripeNotEnough(raid.name, str(raid.stripe_size.fit()))

        self.chunk = raid.chunk
        self.nr = raid.raid_disks_nr
        if config.monfs.mdev_glob:
            try:
                self.mdev_name = glob.glob1('/dev', config.monfs.mdev_glob)[0]
            except:
                raise InternalError
        else:
            self.mdev_name = config.monfs.mdev

    def avail_mountpoints(self):
        avails = config.nas.mount_dirs[:]
        for fs in XFS.all():
            avails.remove(fs.mountpoint)
        for fs in MonFS.all():
            avails.remove(fs.mountpoint)
        return avails

    def mount(self, created=False):
        cmd = 'mount -t monfs %s %s -o mdev=/dev/%s' %\
            (self.volume.dev_path, self.mountpoint, self.mdev_name)
        execute(cmd)

        if created:
            cmd = 'chmod 777 -R %s' % self.mountpoint
            execute(cmd)


    def umount(self):
        cmd = 'umount %s' % self.mountpoint
        e,o = execute(cmd, False)
        if e > 1:
            raise InternalError()

    @with_transaction
    def _create(self):
        super(MonFS, self).create()

        try:
            mkfs = os.path.join(config.monfs.tools.dir, 'mkfs.monfs')
            cmd = '%s -c %s -n %s -N %s -m /dev/%s %s' % (mkfs, self.chunk,\
                self.nr, self.name, self.mdev_name, self.volume.dev_path)
            _,o = execute(cmd)
            m = re.search('uuid:\s*([^\n]+)', o)
            uuid = m.group(1)
            m = re.search('export_meta_off:\s*([^\n]+)', o)
            off = long(m.group(1))
            m = re.search('export_meta_size:\s*([^\n]+)', o)
            size = long(Byte(m.group(1)).Sector)

            self.mount(created=True)
            self.volume.save(used=True, owner_type='monfs')
            self.save(uuid=uuid, meta_off_sector=off, meta_sector=size)
        except Exception as e:
            log.error(caused(e).detail)
            raise error.InternalError()

        log.journal_info('MonFS %s is created successfully.' % self.name)

    def create(self):
        self._create()
        uevent.MonFSCreated(uuid=self.uuid).notify()

    @with_transaction
    def _delete(self):
        self.volume.save(used=False, owner_type='')
        super(MonFS, self).delete()

        self.umount()
        try:
            sql = os.path.join(config.monfs.tools.dir, 'clean_monfs.sql')
            cmd = 'mysql -umonfs -pai80jfa -Dmonfsdb < %s' % sql
            execute(cmd)

            cmd = 'dd if=/dev/zero of=%s bs=%sK count=1' % (self.volume.dev_path, self.chunk.KB)
            execute(cmd)
        except Exception as e:
            log.error(caused(e).detail)
            raise error.InternalError()

        log.journal_info('MonFS %s is deleted successfully.' % self.name)

    def delete(self):
        self._delete()
        uevent.MonFSRemoved(uuid=self.uuid).notify()

    def scan(self):
        if self.volume.online:
            self.mount()
            uevent.MonFSOnline(uuid=self.uuid).notify()

    @classmethod
    def scan_all(cls):
        for fs in cls.all():
            fs.scan()

    @classmethod
    def backup_md(cls):
        fs = cls.all()
        if len(fs) == 0:
            return
        fs = fs[0]
        raid = fs.volume.raids[0]
        if not raid or raid.health not in [HEALTH_NORMAL, HEALTH_DEGRADED]:
            return

        fs.umount()

        backup_dev = 'monfs-backup'
        backup_dir = '/monfs-backup'
        monfsdb_sql = os.path.join(backup_dir, 'monfsdb.sql')
        mdev_mirror = os.path.join(backup_dir, 'mdev-mirror')
        rule = '0 %s linear %s %s' % (fs.meta_sector, fs.volume.dev_path, fs.meta_off_sector)
        dmcreate(backup_dev, rule)

        cmd = 'mkfs.ext3 /dev/mapper/%s' % backup_dev
        execute(cmd)

        if os.path.exists(backup_dir):
            os.rmdir(backup_dir)
        os.mkdir(backup_dir)

        cmd = 'mount /dev/mapper/%s %s' % (backup_dev, backup_dir)
        execute(cmd)

        cmd = 'mysqldump -uroot -ppasswd monfsdb > %s' % monfsdb_sql
        os.popen(cmd)

        cmd = 'dd if=/dev/%s of=%s bs=%sK' % (fs.mdev_name, mdev_mirror, raid.stripe_size.KB)
        execute(cmd)

        cmd = 'umount %s' % backup_dir
        execute(cmd)

        os.rmdir(backup_dir)
        dmremove('/dev/mapper/%s' % backup_dev)
        fs.mount()

    @classmethod
    def import_all(cls):
        def _clean(bdir, dev):
            cmd = 'umount %s' % bdir
            execute(cmd)

            os.rmdir(bdir)
            dmremove('/dev/mapper/%s' % dev)

        volumes = Volume.all()
        if len(volumes) <> 1:
            return
        volume = volumes[0]
        if volume.health <> HEALTH_NORMAL:
            return
        raid = volume.raids[0]
        if not raid or raid.health not in [HEALTH_NORMAL, HEALTH_DEGRADED]:
            return

        msb = monfs_superblock()
        msb.read_from(volume.dev_path, 8)

        if not msb.valid:
            return

        backup_dev = 'monfs-backup'
        backup_dir = '/monfs-backup'
        monfsdb_sql = os.path.join(backup_dir, 'monfsdb.sql')
        mdev_mirror = os.path.join(backup_dir, 'mdev-mirror')
        sector = long(Byte(msb.export_meta_size).Sector)
        rule = '0 %s linear %s %s' % (sector, volume.dev_path, msb.export_meta_off)
        dmcreate(backup_dev, rule)

        if os.path.exists(backup_dir):
            os.rmdir(backup_dir)
        os.mkdir(backup_dir)

        try:
            cmd = 'mount /dev/mapper/%s %s' % (backup_dev, backup_dir)
            execute(cmd)
        except:
            log.info('no filesystem found in export section')
            _clean(backup_dir, backup_dev)
            return

        if not os.path.exists(monfsdb_sql):
            log.info('no %s found in filesystem' % monfsdb_sql)
            _clean(backup_dir, backup_dev)
            return

        if not os.path.exists(mdev_mirror):
            log.info('no %s found in filesystem' % mdev_mirror)
            _clean(backup_dir, backup_dev)
            return

        cmd = 'mysql -uroot -ppasswd -Dmonfsdb < %s' % monfsdb_sql
        execute(cmd)

        cmd = 'dd if=%s of=/dev/%s bs=%sK' % (mdev_mirror, config.monfs.mdev, raid.stripe_size.KB)
        execute(cmd)

        _clean(backup_dir, backup_dev)

        fs = MonFS()
        fs.volume = volume
        fs.chunk = raid.chunk
        fs.nr = raid.raid_disks_nr
        fs.mdev_name = config.monfs.mdev
        fs.meta_off_sector = msb.export_meta_off
        fs.meta_sector = sector
        fs.uuid = msb.uuid
        fs.name = msb.name
        fs.save()
        volume.save(used=True)

        fs.mount()

class Initiator(Admin):
    NAME_PATTERN = '^[_a-zA-Z][-.:_a-zA-Z0-9]*$'
    NAME_MAX_LEN = 96

    table = db.Initiator
    primary_index = 'wwn'
    def __init__(self, **kv):
        super(Initiator, self).__init__(**kv)
        self._portals = []

    def _generate_wwn(self):
        postfix = uuid.uuid4()[-8:]
        self.wwn = 'iqn.2013-01.net.zstor.initiator:%s' % postfix

    @property
    def portals(self):
        if self._portals: return self._portals
        if self.exists:
            self._portals = [(str(ni.eth), ni.port) for ni in self.db.portals]
        return self._portals

    @portals.setter
    def portals(self, val):
        self._portals = val

    @property
    def active_session(self):
        try:
            _,o = execute('cat /sys/kernel/config/target/iscsi/%s/*/acls/*/info' % self.target_wwn, logging=False)
            return False if 'No active iSCSI Session' in o else True
        except:
            return False

    @property
    def volumes(self):
        if hasattr(self, '_volumes'): return self._volumes
        if self.exists:
            self._volumes = [Volume(db=v) for v in self.db.volumes]
        else:
            self._volumes = []
        return self._volumes

    def _check_create_param(self):
        if not self.wwn: self._generate_wwn()
        self.target_wwn = self.wwn.replace('initiator', 'target')
        if self.target_wwn == self.wwn:
            self.target_wwn = '%s.target' % self.wwn

        self.target_wwn = self.target_wwn + wwn_md5_file('/home/zonion/license/key')

        if not re.search(self.NAME_PATTERN, self.wwn):
            raise error.InvalidParam('wwn', self.wwn)

        if len(self.wwn) > self.NAME_MAX_LEN:
            raise error.NameTooLong(self.wwn, self.NAME_MAX_LEN)

        try:
            portals = []
            for portal in self.portals.rstrip(',').split(','):
                m = re.search('(\w+)', portal)
                if m:
                    eth = m.group()
                    port = 3260
                m = re.search('(\w+):(\d+)$', portal)
                if m:
                    eth = m.group(1)
                    port = int(m.group(2))
                portals.append((eth, port))
        except:
            raise error.InvalidParam('portals', self.portals)
        if not portals:
            raise error.InvalidParam('portals', self.portals)

        for eth, port in portals:
            _ifaces = ifaces()
            if eth not in _ifaces:
                raise error.InvalidParam('portals', self.portals)
            info = _ifaces[eth]
            if info.ipaddr == '':
                raise error.IFaceNotAvailable(eth)
        self.portals = portals

    def _create_rtsnode(self):
        iscsi = FabricModule('iscsi')

        try:
            target = Target(iscsi, self.target_wwn, mode='create')
            tpg = TPG(target, 1, 'create')
            tpg.enable = True
            tpg.set_attribute('authentication', '0')
            acl = NodeACL(tpg, self.wwn, mode="create")

            for eth, port in self.portals:
                info = ifaces()[eth]
                log.warning("create rtsnode ipaddr: %s" % info.ipaddr)
                portal = NetworkPortal(tpg, info.ipaddr, port, 'create')
        except Exception as e:
            try:
                target = Target(iscsi, self.target_wwn, mode='lookup')
                target.delete()
            except:pass
            raise caused(e)

    @with_transaction
    def _create(self):
        super(Initiator, self).create()

        self.save()
        for eth, port in self.portals:
            db.NetworkInitiator.create(eth=eth, port=port, initiator=self.wwn)
        self._create_rtsnode()

        log.journal_info('Initiator %s is created successfully.' % self.wwn)

    def create(self):
        self._create()
        uevent.InitiatorCreated(wwn=self.wwn).notify()

    def _check_delete_param(self):
        if self.volumes:
            raise error.Initiator.Mapping(self.wwn)
        if self.active_session:
            raise error.Initiator.ActiveSession(self.wwn)

    @with_transaction
    def _delete(self):
        db.NetworkInitiator.delete().where(db.NetworkInitiator.initiator==self.wwn).execute()
        super(Initiator, self).delete()

        try:
            iscsi = FabricModule('iscsi')
            target = Target(iscsi, self.target_wwn, mode='lookup')
            target.delete()
        except Exception as e:
            log.error(caused(e).detail)

        log.journal_info('Initiator %s is deleted successfully.' % self.wwn)

    def delete(self):
        self._delete()
        uevent.InitiatorRemoved(wwn=self.wwn).notify()

    @classmethod
    def scan_all(cls):
        for initiator in cls.all():
            initiator._create_rtsnode()

class VIMap(Admin):
    table = db.InitiatorVolume

    primary_index = ('initiator', 'volume')

    initiator = FieldAdapter('initiator', lambda x: x.db if x else x, lambda x: Initiator(db=x) if x else x)
    volume = FieldAdapter('volume', lambda x: x.db if x else x, lambda x: Volume(db=x) if x else x)
    def __init__(self, initiator=None, volume=None, **kv):
        super(VIMap, self).__init__(initiator=initiator, volume=volume, **kv)

    def _find_unused_idx(self, indexes):
        for idx in range(1048576):
            if idx not in indexes:
                return idx

    def _next_hba_index(self):
        indexes = [bs.index for bs in RTSRoot().backstores\
                if bs.plugin == 'fileio']
        return self._find_unused_idx(indexes)

    def _find_storage_object(self):
        for so in RTSRoot().storage_objects:
            if so.name == self.volume.name:
                return so
        return None

    def _add_storage_object(self):
        so = None
        lv_wwn= md5.new(self.volume.name).hexdigest()
        try:
            if config.iscsi.buf:
                so = FileIOStorageObject(self.volume.name, str(os.path.realpath(self.volume.dev_path)), wwn=lv_wwn)
                return so
            else:
                so = BlockStorageObject(self.volume.name, str(os.path.realpath(self.volume.dev_path)), wwn=lv_wwn)
                return so
        except Exception as e:
            if so:
                so.delete()
            raise caused(e)

    def _delete_storage_object(self):
        try:
            so = self._find_storage_object()
            so.delete()
        except Exception as e:
            log.error(caused(e))

    def _volume_initr_wwns(self):
        return list([initr.wwn for initr in db.Initiator.select()\
                .join(db.InitiatorVolume).join(db.Volume).\
                where(db.Volume.uuid==self.volume.uuid)])

    def _check_create_param(self):
        if self.initiator.wwn in self._volume_initr_wwns():
            raise error.VIMap.Mapping(self.initiator.wwn, self.volume.name)
        if self.initiator.active_session:
            raise error.Initiator.ActiveSession(self.initiator.wwn)

    def _create_rtsnode(self):
        newso = True if len(self._volume_initr_wwns()) == 1 else False

        if newso:
            so = self._add_storage_object()
        else:
            so = self._find_storage_object()
            if not so:
                so = self._add_storage_object()

        iscsi = FabricModule('iscsi')

        try:
            target = Target(iscsi, self.initiator.target_wwn, mode='lookup')
            tpg = TPG(target, 1, 'lookup')
            acl = NodeACL(tpg, self.initiator.wwn, mode='lookup')
        except Exception as e:
            if newso:
                self._delete_storage_object()
            raise caused(e)

        lun_idx = self._find_unused_idx([lun.lun for lun in tpg.luns])
        mlun_idx = self._find_unused_idx([mlun.mapped_lun for mlun in\
                acl.mapped_luns])

        try:
            lun = LUN(tpg, lun_idx, so)
        except Exception as e:
            if newso:
                self._delete_storage_object()
            raise caused(e)

        try:
            mlun = MappedLUN(acl, mlun_idx, lun_idx, write_protect=False)
        except Exception as e:
            if newso:
                self._delete_storage_object()
            lun.delete()
            raise caused(e)

    @with_transaction
    def _create(self):
        super(VIMap, self).create()

        self.save()
        self.volume.save(used=True, owner_type='iscsi')
        self._create_rtsnode()
        log.journal_info('Volume %s is mapped to initiator %s successfully.' % (self.volume.name, self.initiator.wwn))

    def create(self):
        self._create()
        uevent.VIMapped(initr=self.initiator.wwn, volume=self.volume.name).notify()

    def _check_delete_param(self):
        if not self.initiator.wwn in self._volume_initr_wwns():
            raise error.VIMap.NotMapped(self.initiator.wwn, self.volume.name)
        if self.initiator.active_session:
            raise error.Initiator.ActiveSession(self.initiator.wwn)

    def deactive(self):
        try:
            iscsi = FabricModule('iscsi')
            target = Target(iscsi, self.initiator.target_wwn, mode='lookup')
            tpg = TPG(target, 1, 'lookup')

            for lun in tpg.luns:
                if lun.storage_object.name == self.volume.name:
                    tpg_lun = LUN(tpg, lun.lun)
                    tpg_lun.delete()

            self._delete_storage_object()
        except Exception as e:
            pass

    @with_transaction
    def _delete(self):
        self.volume.save(used=False, owner_type='')
        super(VIMap, self).delete()

        try:
            iscsi = FabricModule('iscsi')
            target = Target(iscsi, self.initiator.target_wwn, mode='lookup')
            tpg = TPG(target, 1, 'lookup')

            for lun in tpg.luns:
                if lun.storage_object.name == self.volume.name:
                    tpg_lun = LUN(tpg, lun.lun)
                    tpg_lun.delete()
                    break
        except Exception as e:
            log.error(caused(e).detail)
        finally:
            if len(self._volume_initr_wwns()) == 0:
                self._delete_storage_object()

        log.journal_info('Volume %s is unmapped to initiator %s successfully.' % (self.volume.name, self.initiator.wwn))

    def delete(self):
        self._delete()
        uevent.VIUnmapped(initr=self.initiator.wwn, volume=self.volume.name).notify()

    def scan(self):
        if self.volume.online and self.volume.health == HEALTH_NORMAL:
            try:
                self._create_rtsnode()
                uevent.VIMapped(initr=self.initiator.wwn, volume=self.volume.name)
            except Exception as e:
                log.error(caused(e).detail)

    @classmethod
    def scan_all(cls):
        for vimap in cls.all():
            vimap.scan()

@exc2status
def scan_all():
    log.info("system start scan")
    if check_system_raid1():
        make_system_rd()
        check_system_rd()

    try:
        Disk.scan_all()
    except error.Disk.NotFoundAnyDisk or perf.TimeoutException as e:
        log.error(caused(e).detail)
        print 'not found any bcache'
    except Exception as e:
        log.error(caused(e).detail)

    if len(Raid.all()) == 0 and all(disk.host == Disk.HOST_FOREIGN for disk in Disk.all()):
        log.info("try import resource")
        Raid.import_all()
        if len(Raid.all()):
            Volume.import_all()
            Disk.table.update(host=Disk.HOST_NATIVE).execute()
            if len(Volume.all()):
                MonFS.import_all()
        open(config.boot.startup_file, 'w').close()
        uevent.SystemReady().notify()
        log.info("system ready")
        return

    try:
        Raid.scan_all()
    except Exception as e:
        log.error(caused(e).detail)
    try:
        Volume.scan_all()
    except Exception as e:
        log.error(caused(e).detail)

    if os.path.exists('/home/zonion/xfs'):
        return
    
    try:
        XFS.scan_all()
    except Exception as e:
        log.error(caused(e).detail)
    try:
        MonFS.scan_all()
    except Exception as e:
        log.error(caused(e).detail)
    try:
        Initiator.scan_all()
    except Exception as e:
        log.error(caused(e).detail)
    try:
        VIMap.scan_all()
    except Exception as e:
        log.error(caused(e).detail)

    open(config.boot.startup_file, 'w').close()
    uevent.SystemReady().notify()
    log.info("system ready")

def record_raid_recovery(raid):
    def resolve_correct_created_seq(seq, referred):
        diffs = list(set(referred).difference(set(seq)))
        if len(diffs) == 0:
            return None

        i = referred.index(diffs[0])
        news = list(set(seq).difference(set(referred)))
        _seq = referred[:]
        _seq[i] = news[0]
        return _seq

    recoveries = list(db.RaidRecovery.select().where(db.RaidRecovery.uuid==raid.uuid).\
        order_by(db.RaidRecovery.created_at.desc()))
    r = recoveries[0]

    seq = resolve_correct_created_seq([d.uuid for d in raid.raid_disks],\
            r.raid_disks.split(','))
    if seq:
        log.info('resolve correct created raid disks: %s' % seq)
    else:
        seq = r.raid_disks.split(',')

    db.RaidRecovery.create(uuid=r.uuid, name=r.name, level=r.level,
            chunk_kb=r.chunk_kb, raid_disks_nr=len(seq),
            raid_disks=','.join(seq),
            spare_disks_nr=len(raid.spare_disks),
            spare_disks=','.join(d.uuid for d in raid.spare_disks))


class Guard(object):
    def __init__(self):
        self._rqueue = {}

    def load(self):
        wait_secs = config.raid.rebuild.unplug_wait_secs
        for raid in Raid.all():
            if raid.health == HEALTH_DEGRADED:
                if raid.can_add_back_disk():
                    wait_secs = 8
                self._rqueue[raid.uuid] = (wait_secs, raid.uuid)

    def dequeue(self, raid_name):
        raid = Raid.lookup(name=raid_name)
        self._rqueue.dequeue(raid)

    def elapse(self, secs):
        for wait, uuid in self._rqueue.values():
            del self._rqueue[uuid]
            wait = max(0, wait-secs)
            if wait == 0:
                try:
                    raid = Raid.lookup(uuid=uuid)
                    raid.rebuild()
                except:
                    pass
            else:
                self._rqueue[uuid] = (wait, uuid)

    def _scan(self, disk, raid):
        if disk.role in [ROLE_DATA, ROLE_DATA_SPARE]:
            raid.scan()
            for v in raid.volumes:
                v.scan()
                for i in v.initiators:
                    vi = VIMap(i, v)
                    vi.scan()

    def plug(self, dev_name):
        log.info("==== plugging disk, dev:%s ====" % dev_name)

        m = lm.LocationMapping()
        locations = [loc for loc, dev in m.mapping.items() if dev == dev_name]
        if len(locations) == 0:
            return

        try:
            last = Disk.lookup(location=locations[0])
            log.warning("disk %s[%s] exists, host: %s." % (dev_name, locations[0], last.host))
            if last.devno:
                log.warning("disk %s[%s] exists, ignore pluging." % (dev_name, locations[0]))
                return
        except:
            last = None

        with transaction():
            disk = Disk(location=locations[0], dev_name=dev_name)
            _,parts = disk.scan()
            if disk.health <> HEALTH_FAILED:
                disk.health = HEALTH_NORMAL
            if last and disk.uuid <> last.uuid:
                last.save(location='', dev_name='', devno=0, link=False)
                for part in last.parts:
                    part.save(dev_name='', devno=0, link=False, stub_dev='')
            disk.save(prev_location=disk.location)
            for part in parts:
                part.save()

        log.info("==== complete plugging disk, uuid:%s location:%s dev:%s ====" % (disk.uuid, disk.location, dev_name))
        log.journal_info('Disk %s is plugged.' % disk.location)

        raid = disk.raid
        if not raid:
            uevent.DiskPlugged(uuid=disk.uuid).notify()
            return

        if not raid.online:
            self._scan(disk, raid)
            uevent.DiskPlugged(uuid=disk.uuid).notify()
            return

        self._plug(disk, raid)

    def _plug(self, disk, raid):
        volumes = raid.volumes()
        health = raid._health
        with transaction():
            wait_secs = config.raid.rebuild.unplug_wait_secs
            if raid.health == HEALTH_NORMAL:
                raid.adjust_disk_role(disk)
            elif raid.health == HEALTH_DEGRADED:
                if raid.rebuilding and raid.degraded == 1:
                    raid.adjust_disk_role(disk)
                else:
                    if disk.role == ROLE_DATA_SPARE:
                        self._rqueue[raid.uuid] = (4, raid.uuid)
                    elif raid.uuid not in self._rqueue:
                        self._rqueue[raid.uuid] = (wait_secs, raid.uuid)
            elif raid.health == HEALTH_FAILED and disk.role == ROLE_DATA_SPARE:
                while raid.health == HEALTH_FAILED:
                    if not raid.add_back_disk():
                        break
                if raid.health == HEALTH_DEGRADED:
                    if raid.can_add_back_disk():
                        wait_secs = 4
                    self._rqueue[raid.uuid] = (wait_secs, raid.uuid)
                    for lv in volumes:
                        lv.save(health=HEALTH_NORMAL)
                    for lv in raid.volumes(1):
                        lv.health = HEALTH_NORMAL
                        lv._delete()

                    try:
                        fs = XFS.all()
                        if len(fs) > 0:
                            for lv in volumes:
                                if lv.uuid == fs[0].volume.uuid:
                                    log.info("volume: %s become degraded, so restart smbd" % lv.name)
                                    cmd = '/etc/init.d/smb restart'
                                    execute(cmd, False)
                                    cmd = 'service smbd restart'
                                    execute(cmd, False)
                                    break
                    except:
                        pass
            raid.update_extents()
            raid.save(health=raid.health)

        uevent.DiskPlugged(uuid=disk.uuid).notify()
        if health <> HEALTH_DEGRADED and raid.health == HEALTH_DEGRADED:
            uevent.RaidDegraded(uuid=raid.uuid).notify()
        for lv in volumes:
            uevent.VolumeNormal(uuid=lv.uuid).notify()

    def _plug_r6(self, disk, raid):
        volumes = raid.volumes()
        health = raid._health
        with transaction():
            wait_secs = config.raid.rebuild.unplug_wait_secs
            if raid.health == HEALTH_NORMAL:
                raid.adjust_disk_role(disk)
            elif raid.health == HEALTH_DEGRADED:
                if raid.rebuilding and raid.degraded == 1:
                    raid.adjust_disk_role(disk)
                else:
                    if disk.role == ROLE_DATA_SPARE:
                        if disk.unplug_seq == 1:
                            for d in raid.raid_disks:
                                if d.unplug_seq == 2 and not d.link:
                                    d.save(unplug_seq=1)
                                    disk.save(unplug=2)
                                    break
                        self._rqueue[raid.uuid] = (4, raid.uuid)
                    elif raid.uuid not in self._rqueue:
                        self._rqueue[raid.uuid] = (wait_secs, raid.uuid)
            elif raid.health == HEALTH_FAILED and disk.role == ROLE_DATA_SPARE:
                while raid.health == HEALTH_FAILED:
                    if not raid.add_back_disk():
                        break
                if raid.health == HEALTH_DEGRADED:
                    if raid.can_add_back_disk():
                        wait_secs = 4
                    self._rqueue[raid.uuid] = (wait_secs, raid.uuid)
                    for lv in volumes:
                        lv.save(health=HEALTH_NORMAL)
                    for lv in raid.volumes(1):
                        lv.health = HEALTH_NORMAL
                        lv._delete()

                    try:
                        fs = XFS.all()
                        if len(fs) > 0:
                            for lv in volumes:
                                if lv.uuid == fs[0].volume.uuid:
                                    log.info("volume: %s become degraded, so restart smbd" % lv.name)
                                    cmd = '/etc/init.d/smb restart'
                                    execute(cmd, False)
                                    cmd = 'service smbd restart'
                                    execute(cmd, False)
                                    break
                    except:
                        pass
            raid.update_extents()
            raid.save(health=raid.health)

        uevent.DiskPlugged(uuid=disk.uuid).notify()
        if health <> HEALTH_DEGRADED and raid.health == HEALTH_DEGRADED:
            uevent.RaidDegraded(uuid=raid.uuid).notify()
        for lv in volumes:
            uevent.VolumeNormal(uuid=lv.uuid).notify()

    def unplug(self, dev_name):
        log.info("==== unplugging disk, dev:%s ====" % dev_name)
        try:
            disk = Disk.lookup(dev_name=dev_name)
        except:
            return

        volumes = []
        with transaction():
            health = ''
            raid = disk.raid
            if raid:
                health = raid._health
                if raid.online:
                    if raid.level <> 0 and disk.role == ROLE_DATA:
                        rdisk = raid.rebuilding_disk
                        if rdisk and rdisk.uuid <> disk.uuid:
                            raid.unplug(rdisk)
                    raid.unplug(disk)

                if health <> HEALTH_FAILED and raid.health == HEALTH_FAILED:
                    volumes = raid.volumes()
                    for lv in volumes:
                        lv.save(health=HEALTH_FAILED)
                raid.save(health=raid.health)


            disk.remove_dev()
            if disk.host in [Disk.HOST_FOREIGN, Disk.HOST_USED]:
                disk.db.delete_instance(recursive=True, delete_nullable=True)
            else:
                if disk.health <> HEALTH_FAILED:
                    disk.health = HEALTH_DOWN
                disk.save(devno=0, dev_name='')
                for part in disk.parts:
                    part.save(dev_name='', devno=0, link=False, stub_dev='')

        log.info("==== complete upplugging disk, uuid:%s location:%s dev:%s ====" % (disk.uuid, disk.location, dev_name))
        log.journal_warning('Disk %s is unplugged.' % disk.location)

        uevent.DiskUnplugged(uuid=disk.uuid, location=disk.location, dev_name=dev_name).notify()
        if health <> HEALTH_DEGRADED and raid and raid.health == HEALTH_DEGRADED:
            self._rqueue[raid.uuid] = (config.raid.rebuild.unplug_wait_secs, raid.uuid)
            uevent.RaidDegraded(uuid=raid.uuid).notify()
        elif health <> HEALTH_FAILED and raid and raid.health == HEALTH_FAILED:
            uevent.RaidFailed(uuid=raid.uuid).notify()
        for lv in volumes:
            uevent.VolumeFailed(uuid=lv.uuid).notify()


    def fail(self, dev_name):
        log.info("==== failing disk, dev:%s ====" % dev_name)
        try:
            disk = Disk.lookup(dev_name=dev_name)
            if disk.health == HEALTH_FAILED:
                return
        except:
            return

        volumes = raid.volumes()
        health = ''
        raid = disk.raid
        with transaction():
            if raid:
                health = raid._health
                if raid.online:
                    if raid.level <> 0 and disk.role == ROLE_DATA:
                        rdisk = raid.rebuilding_disk
                        if rdisk and rdisk.uuid <> disk.uuid:
                            raid.unplug(rdisk)
                    if disk.link:
                        raid.mdadm_remove(disk)

                if health <> HEALTH_FAILED and raid.health == HEALTH_FAILED:
                    for lv in volumes:
                        lv.save(health=HEALTH_FAILED)

                raid.save(health=raid.health)

            disk.fail()

        log.info("==== complete failing disk, uuid:%s location:%s dev:%s ====" % (disk.uuid, disk.location, dev_name))
        log.journal_warning('Disk %s is failed.' % disk.location)

        uevent.DiskIOError(uuid=disk.uuid).notify()
        if health <> HEALTH_DEGRADED and raid.health == HEALTH_DEGRADED:
            self._rqueue[raid.uuid] = (config.raid.rebuild.unplug_wait_secs, raid.uuid)
            uevent.RaidDegraded(uuid=raid.uuid).notify()
        elif health <> HEALTH_FAILED and raid.health == HEALTH_FAILED:
            uevent.RaidFailed(uuid=raid.uuid).notify()
        for lv in volumes:
            uevent.VolumeFailed(uuid=lv.uuid).notify()

    @with_transaction
    def complete_rebuilding(self, dev_name):
        try:
            log.info("==== handling raid rebuilding completed, dev:%s ====" % dev_name)
            with transaction():
                raid = Raid.lookup(dev_name=dev_name)
                disk = raid.rebuilding_disk
                if disk: disk.save(role = ROLE_DATA)

                if raid.health == HEALTH_DEGRADED:
                    wait_secs = config.raid.rebuild.unplug_wait_secs
                    if raid.can_add_back_disk():
                        wait_secs = 4
                    self._rqueue[raid.uuid] = (wait_secs, raid.uuid)
                    return
                elif raid.health <> HEALTH_NORMAL:
                    return

                if not raid.has_bitmap:
                    raid.create_bitmap()
                raid.save(health=raid.health)

            try:
                record_raid_recovery(raid)
            except Exception as e:
                log.error(caused(e).detail)

            log.info("==== complete handling raid rebuilding completed, uuid:%s name:%s dev:%s ====" % (raid.uuid, raid.name, dev_name))
            execute('echo 1 > /sys/module/rqr/parameters/no_rqr')
            uevent.RaidRebuildCompleted(uuid=raid.uuid).notify()
            uevent.RaidNormal(uuid=raid.uuid).notify()
        except:
            pass

@exc2status
@with_transaction
def change_passwd(name, old_password, new_password):
    try:
        old_passwd = str(old_password)
    except:
        raise error.OldPasswordWrong()

    try:
        new_passwd = str(new_password)
    except:
        raise error.NewPasswordInvalid()

    try:
        usr = db.User.get(name=name)
    except:
        raise error.NotExistError(name)

    digest = md5.new(old_passwd).hexdigest()
    if str(usr.crypted_passwd) <> digest:
        raise error.User.OldPasswordWrong()

    if len(new_passwd) > 32:
        raise error.User.NewPasswordInvalid()

    try:
        digest = md5.new(new_passwd).hexdigest()
        usr.crypted_passwd = digest
        usr.save()

        cmd = os.path.join(config.command.dir, 'change_linux_admin_passwd %s') % new_passwd
        execute(cmd)
    except:
        raise error.InternalError()


@exc2status
def create_raid(name, level, chunk, raid_disks, spare_disks, rebuild_priority, sync):
    log.info('==== creating raid, name:%s level:%s chunk:%s raid-disks:%s '\
            'spare-disks:%s rebuild-priority:%s sync:%s ===='\
            % (name, level, chunk, raid_disks, spare_disks, rebuild_priority, sync))

    raid_disks = [Disk.lookup(location=disk) for disk in raid_disks.split(',') if disk <> '']
    spare_disks = [Disk.lookup(location=disk) for disk in spare_disks.split(',') if disk <> '']
    raid = Raid(raid_disks, spare_disks, name=name)
    raid.level, raid.chunk, raid.rebuild_priority, raid.sync = level, chunk, rebuild_priority, sync
    raid.create()

    log.info('==== complete creating raid, name:%s ====' % name)

@exc2status
def delete_raid(name):
    log.info('==== deleting raid, name:%s ====' % name)

    raid = Raid.lookup(name=name)
    raid.delete()

    log.info('==== complete deleting raid, name:%s ====' % name)

@exc2status
def create_volume(name, raid, capacity):
    log.info('==== creating volume, name:%s raid:%s capacity:%s ====' % (name, raid, capacity))

    raid = Raid.lookup(name=raid)
    volume = Volume(name=name)
    volume.raid = raid
    volume.cap = capacity
    volume.create()

    log.info('==== complete creating volume, name:%s raid:%s capacity:%s ====' % (name, raid.name, capacity))

@exc2status
def delete_volume(name):
    log.info('==== deleting volume, name:%s ====' % name)

    volume = Volume.lookup(name=name)
    raids = [Raid(db=rv.raid) for rv in db.RaidVolume.select().where((db.RaidVolume.volume == volume.uuid) & (db.RaidVolume.type == RV_EXPANSION))]
    normal_raid = volume.normal_raid

    volume.delete()
    for raid in raids:
        raid.vg_name = normal_raid.vg_name
        raid.delete()

    log.info('==== complete deleting volume, name:%s' % name)

@exc2status
def create_fs(name, volume, type='xfs'):
    log.info('==== creating fs, name:%s volume:%s ====' % (name, volume))

    type = type or 'xfs'

    if type == 'xfs':
        fs = XFS(name=name)
    elif type == 'monfs':
        fs = MonFS(name=name)
    else:
        raise error.InternalError

    fs.volume = Volume.lookup(name=volume)
    fs.create()
    log.info('==== complete creating fs, name:%s volume:%s ====' % (name, volume))

@exc2status
def delete_fs(name):
    log.info('==== deleting fs, name:%s ====' % name)

    if 'xfs' in config.feature:
        fs = XFS.lookup(name=name)
    elif 'monfs' in config.feature:
        fs = MonFS.lookup(name=name)
    else:
        raise error.InternalError
    fs.delete()

    log.info('==== complete deleting fs, name:%s ====' % name)

@exc2status
def create_monfs(name, volume):
    log.info('==== creating volume, name:%s volume:%s ====' % (name, volume))

    fs = MonFS(name=name)
    fs.volume = Volume.lookup(name=volume)
    fs.create()

    log.info('==== complete creating volume, name:%s volume:%s ====' % (name, volume))

@exc2status
def delete_monfs(name):
    log.info('==== deleting monfs, name:%s ====' % name)

    fs = MonFS.lookup(name=name)
    fs.delete()

    log.info('==== complete deleting monfs, name:%s ====' % name)

@exc2status
def create_initiator(wwn, portals):
    log.info('==== creating Initiator, wwn:%s portals:%s ====' % (wwn, portals))

    err = None
    initr = Initiator()
    initr.wwn, initr.portals = wwn, portals
    initr.create()
    if not wwn:
        err = {'wwn': initr.wwn}

    log.info('==== complete creating Initiator, wwn:%s portals:%s ====' % (wwn, portals))
    return err

@exc2status
def delete_initiator(wwn):
    log.info('==== deleting Initiator, wwn:%s ====' % wwn)

    initiator = Initiator.lookup(wwn=wwn)
    initiator.delete()

    log.info('==== complete deleting Initiator, wwn:%s ====' % wwn)

@exc2status
def create_vimap(initr, volume):
    log.info('==== creating vimap, initr:%s volume:%s ====' % (initr, volume))

    initiator = Initiator.lookup(wwn=initr)
    volume = Volume.lookup(name=volume)
    vimap = VIMap(initiator, volume)
    vimap.create()

    log.info('==== complete creating vimap, initr:%s volume:%s ====' % (initr, volume.name))

@exc2status
def delete_vimap(initr, volume):
    log.info('==== deleting vimap, initr:%s volume:%s ====' % (initr, volume))

    initiator = Initiator.lookup(wwn=initr)
    volume = Volume.lookup(name=volume)
    try:
        vimap = VIMap.lookup(initiator=initiator, volume=volume)
        vimap.delete()
    except error.NotExistError:
        raise error.VIMap.NotMapping(initiator.wwn, volume.name)

    log.info('==== deleting vimap, initr:%s volume:%s ====' % (initr, volume.name))

@exc2status
def format_disk(locations):
    log.info("==== formating disk, locations:%s ====" % locations)

    if locations.lower() == 'all' or locations == '':
        for disk in Disk.all():
            if disk.host in [Disk.HOST_USED, Disk.HOST_FOREIGN]:
                disk.format_disk()
    else:
        locations = locations.split(',')
        locations = locations if isinstance(locations, list) else [locations]
        for loc in locations:
            disk = Disk.lookup(location=loc)
            disk.format_disk()

    log.info("==== complete formating disk, locations:%s ====" % locations)

@exc2status
def set_disk_role(location, role, raidname):
    log.info("==== set disk role, locations:%s role:%s raidname:%s ====" % (location, role, raidname))

    if role not in [ROLE_UNUSED, ROLE_GLOBAL_SPARE, ROLE_SPARE]:
        raise error.InvalidParam('role', role)

    disk = Disk.lookup(location=location)
    if role == ROLE_GLOBAL_SPARE:
        if disk.role not in [ROLE_UNUSED, ROLE_GLOBAL_SPARE]:
            raise error.Disk.Role(disk.location, disk.role, role)

        disk.save(role=ROLE_GLOBAL_SPARE)
    elif role == ROLE_SPARE:
        if disk.role <> ROLE_UNUSED:
            raise error.Disk.Role(disk.location, disk.role, role)

        raid = Raid.lookup(name=raidname)
        disk.save(role=ROLE_SPARE, raid=raid)
        if disk.online and disk.health <> HEALTH_FAILED:
            Metadata.update(disk.md_path, raid_uuid=raid.uuid)

        if disk.cap <> raid.raid_disks[0].cap:
            raise error.Raid.NotSameCapacityDisk

        try:
            record_raid_recovery(raid)
        except Exception as e:
            log.error(caused(e).detail)
    elif role == ROLE_UNUSED:
        if disk.role not in [ROLE_UNUSED, ROLE_GLOBAL_SPARE, ROLE_SPARE]:
            raise error.Disk.Role(disk.location, disk.role, role)

        if disk.role == ROLE_SPARE:
            raid = disk.raid
            disk.save(raid=None, link=False, unplug_seq=0, role=ROLE_UNUSED)
            if disk.online and disk.health <> HEALTH_FAILED:
                Metadata.update(disk.md_path, raid_uuid='')

            try:
                record_raid_recovery(raid)
            except Exception as e:
                log.error(caused(e).detail)
        else:
            disk.save(role=ROLE_UNUSED)

    log.journal_info('Disk %s is changed to %s.' % (disk.location, role))
    uevent.DiskRoleChanged(uuid=disk.uuid).notify()

    log.info("==== complete setting disk role, locations:%s, role:%s, raidname:%s ====" % (location, role, raidname))

@exc2status
def expand(vol_name):
    volume = Volume.lookup(name=vol_name)
    normal_raid = volume.normal_raid

    disks = [disk for disk in Disk.all() if disk.role == ROLE_UNUSED]
    if len(disks) <= 2:
        raise error.Raid.NeedMoreDisk(len(disks), 5)

    raidnames = [raid.name for raid in Raid.all()]
    for i in range(1, 1024):
        raidname = 'expand%s' % i
        if raidname not in raidnames:
            break

    raid = Raid(disks, [], name=raidname)
    raid.level, raid.chunk, raid.rebuild_priority, raid.sync = 5, '32KB', 'low', False
    raid.vg_name = normal_raid.vg_name
    raid.create()

    try:
        cmd = 'lvextend %s %s' % (volume.lvm_name, raid.odev_path)
        execute(cmd)
    except Exception as e:
        raid.delete()
        raise e

    db.RaidVolume.create(raid=raid.uuid, volume=volume.uuid, type=RV_EXPANSION)
    raid.save(used_cap=raid.cap)
    volume.save(cap=volume.cap+raid.cap)
    if volume.owner_type == 'xfs':
        cmd = 'xfs_growfs'
        execute(cmd)

@exc2status
def fast_create(raidname, volumename, fsname, chunk):
    raidnames = [raid.name for raid in Raid.all()]
    if raidname in raidnames:
        raise error.ExistError(raidname)

    volumenames = [volume.name for volume in Volume.all()]
    if volumename in volumenames:
        raise error.ExistError(volumename)

    if 'xfs' in config.feature:
        fsnames = [fs.name for fs in XFS.all()]
    elif 'monfs' in config.feature:
        fsnames = [fs.name for fs in MonFS.all()]
    else:
        raise error.InternalError

    if fsname in fsnames:
        raise error.ExistError(fsname)

    disks = [disk for disk in Disk.all() if disk.role == ROLE_UNUSED]
    raid = Raid(disks, [], name=raidname)
    raid.level, raid.chunk, raid.rebuild_priority, raid.sync = 5, chunk, 'low', False
    raid.create()

    volume = Volume(name=volumename)
    volume.raid = raid
    volume.cap = 'ALL'
    volume.create()

    if 'xfs' in config.feature:
        fs = XFS(name=fsname)
    elif 'monfs' in config.feature:
        fs = MonFS(name=fsname)
    fs.volume = volume
    fs.create()

@exc2status
def dispath_config(serverid, local_serverip, local_serverport, cmssverip, cmssverport):
    tree = ET.parse('/home/zonion/speedio/zxvnms_config.xml')
    root = tree.getroot()
    for server in root.findall('server'):
        server.find('serverid').text = serverid
        server.find('local_server')[0].text = local_serverip
        server.find('local_server')[1].text = local_serverport
        server.find('cmssver')[0].text = cmssverip
        server.find('cmssver')[1].text = cmssverport
    os.system('touch /opt/commonserver/dispath/zxvnms_config.xml')
    tree.write('/opt/commonserver/dispath/zxvnms_config.xml')

@exc2status
def store_config(serverid, local_serverip, local_serverport, cmssverip, cmssverport, directory):
    if len(directory.split(';')) != 2:
        raise error.InvalidParam('directory', directory)

    tree = ET.parse('/home/zonion/speedio/zxvnms_config.xml')
    root = tree.getroot()
    for server in root.findall('server'):
        server.find('serverid').text = serverid
        server.find('local_server')[0].text = local_serverip
        server.find('local_server')[1].text = local_serverport
        server.find('cmssver')[0].text = cmssverip
        server.find('cmssver')[1].text = cmssverport
    if directory != '':
        dirs = directory.split(';')
        for store in root.findall('store'):
            for i in range(1,len(dirs)+1):
                if store.find('devicepath%d'%i) is None:
                    newnode = ET.Element('devicepath%d'%i, {})
                    newnode.text = dirs[i-1]
                    store.append(newnode)
                else:
                    store.find('devicepath%d'%i).text = dirs[i-1]
    os.system('touch /opt/commonserver/store/zxvnms_config.xml')
    tree.write('/opt/commonserver/store/zxvnms_config.xml')

@exc2status
def detection_fs():
    broken_fs = []
    volumes = []
    mount_fs = []
    _,o = execute('df |grep /dev/mapper/VG-- |grep -v grep', False, logging=False)
    for line in o.rstrip().split('\n'):
        m=re.search(r'/dev/mapper/VG--\S+-(\S+)', line)
        if m is not None:
            mount_fs.append(m.group(1))
    for xfs in XFS.all():
        if xfs.volume.name not in mount_fs:
            volumes.append(xfs.volume.name)

    if len(volumes) > 0:
        execute('touch /home/zonion/xfs && rm /home/zonion/xfs')
        fd = open('/home/zonion/xfs', 'w')
        for lun_name in volumes:
            dev = Volume.lookup(name=lun_name).dev_path
            broken_fs.append(dev)
            fd.write(dev + '\n')
        fd.close()

    return broken_fs

@exc2status
def sync_lun(lun_name):
    log.info('==== sync_lun, name:%s ====' % lun_name)
    print 'hahahahahha'
    volume = Volume.lookup(name=lun_name)
    volume.sync()

@exc2status
def stop_sync_lun(lun_name):
    log.info('==== stop_sync_lun, name:%s ====' % lun_name)
    volume = Volume.lookup(name=lun_name)
    volume.stop_sync()

@exc2status
def force_stop_beep():
    stop_beep('0')

api = ['change_passwd', 'create_raid', 'delete_raid', 'create_volume', 'delete_volume',\
        'create_monfs', 'delete_monfs', 'create_initiator', 'delete_initiator',\
        'create_vimap', 'delete_vimap', 'format_disk', 'set_disk_role', 'create_fs',\
        'delete_fs', 'expand', 'fast_create', 'dispath_config', 'store_config',\
        'detection_fs', 'sync_lun', 'stop_sync_lun', 'force_stop_beep']

def shutdown():
    try:
        for info in ifaces().values():
            cmd = 'ifconfig %s down' % info.name
            execute(cmd, False)

        for vi in VIMap.all():
            vi.deactive()

        try:
            cmd = 'kill -9 `lsof -t %s`' % config.nas.mount_dir
            e, o = execute(cmd, False)

            cmd = 'umount %s' % config.nas.mount_dir
            e, o = execute(cmd, False)

            cmd = 'lsof /mnt'
            e, o = execute(cmd, False)
            if e == 0:
                for line in [1].splitlines()[1:]:
                    p = psutil.Process(pid=int(line.split()[1]))
                    p.kill()
        except:
            pass

        time.sleep(1)
        cmd = 'sync'
        execute(cmd, False)

        for fs in MonFS.all():
            try:
                fs.umount()
            except:
                pass

        for lv in Volume.all():
            lv.deactive()

        for rd in Raid.all():
            rd.deactive()
    except:
        pass

    time.sleep(1)
    cmd = 'sync'
    execute(cmd, False)

    cmd = 'rm -rf /home/zonion/bitmap.disk/*'
    execute(cmd, False, logging=False)

    cmd = 'cp -rf /home/zonion/bitmap/* /home/zonion/bitmap.disk/'
    execute(cmd, False, logging=False)

    cmd = 'rm /home/zonion/boot'
    execute(cmd, False, logging=False)

    time.sleep(2)

def poweroff():
    log.info('system poweroff')
    shutdown()

    log.journal_info('System poweroff.')

    cmd = 'poweroff'
    execute(cmd)

def reboot():
    log.info('system reboot')
    shutdown()

    log.journal_info('System reboot.')

    cmd = 'reboot'
    execute(cmd)

def wwn_md5_file(name):
    if not os.path.exists(name):
        name = '/home/zonion/speedio/adm.pyc'
    a_file = open(name, 'rb')
    digest = md5.new(a_file.read()).hexdigest()
    a_file.close()
    digest = digest[0:2]
    return digest

    

def raid1_map():
    map = {}
    disks = []
    nodisk = glob.glob1('/dev', 'sd?2')
    for disk in nodisk:
        cmd = "blockdev --getsz /dev/%s" % disk[0:3]
        s, o = execute(cmd, False, logging=False)
        o = o.strip('\n')
        if int(o) < 72533296*4:
            disks.append(disk[0:3])

    n = config.raid.sysrd.parts
    for i in range(len(n)):
        rd_obj = []
        for nn in disks:
            rd_obj.append('/dev/' + n[i].replace('sda', nn))
        map['md%s'%((i+1)*100)] = rd_obj
    return map

def make_system_rd():
    map_rd = raid1_map()
    for key in map_rd:
        cmd = 'mdadm --create %s --homehost="%s"  --level=1 '\
                  '--raid-disks=2 %s   --run --assume-clean --force -q  --bitmap=/home/zonion/bitmap/%s.bitmap --bitmap-chunk=16M'\
                % ('/dev/'+ key, config.raid.homehost, ' '.join(map_rd[key]), key)
        execute(cmd, False)

    cmd = 'mount /dev/md100 /opt'  
    execute(cmd, False)
    cmd = 'ln -s /dev/md200 /dev/meta'  
    execute(cmd, False)

def failed_system_rd():
    map_rd = raid1_map()
    for key in map_rd:
        cmd = 'mdadm /dev/%s --fail %s --remove %s'\
                  % (key, map_rd[key][0], map_rd[key][0])
        execute(cmd, False)

def check_system_rd():
    disks = []
    nodisk = glob.glob1('/dev', 'sd?2')
    for disk in nodisk:
        cmd = "blockdev --getsz /dev/%s" % disk[0:3]
        s, o = execute(cmd, False, logging=False)
        o = o.strip('\n')
        if int(o) < 72533296*4:
            disks.append(disk[0:3])

    rds = {
           '/dev/md0': '1',
           '/dev/md1': '2'
          }
    for rd in rds:
        for d in disks:
            cmd = 'mdadm -D  %s | grep %s'\
                  % (rd, d)
            _,o = execute(cmd, False, logging=False)
            m=re.search(d, o)
            if m is None:
                cmd = 'mdadm %s --add /dev/%s%s'\
                  % (rd, d, rds[rd])
                _,o = execute(cmd, False)

