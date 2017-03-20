#!/usr/bin/env python
import mq
import log
import sys
import time
import json
import zmq
import threading

class UnkownUevent(Exception):
    pass

local = threading.local()
local.uevent = {}

def pusher():
    _pusher = local.uevent.get('pusher', None)
    if not _pusher:
        _pusher = mq.Push('uevent_svr')
        local.uevent['pusher'] = _pusher
    return _pusher

def get(o):
    try:
        return eventmap[o['uevent']](**o)
    except:
        raise UnkownUevent

eventmap = {}

class UEvent(object):
    pub = None
    @classmethod
    def bind_pub_socket(cls):
        cls.pub = mq.pub_socket('uevent_pub')

    def __init__(self, event_name):
        self.event_name = event_name

    def notify(self):
        try:
            pusher().send(self.event_obj)
            log.info("uevent %s notified" % self.event_obj)
        except Exception as e:
            print e

    def publish(self):
        self.pub.send_json({})
        self.pub.send_json(self.event_obj)
        log.info("uevent %s published" % self.event_obj)

    @property
    def event_obj(self):
        return {'uevent':self.event_name}

class SystemReady(UEvent):
    event_name = 'system.ready'
    def __init__(self, **kv):
        super(SystemReady, self).__init__(self.event_name)

class UUIDUEvent(UEvent):
    def __init__(self, **kv):
        super(UUIDUEvent, self).__init__(self.event_name)
        self.uuid = kv['uuid']

    @property
    def event_obj(self):
        e = super(UUIDUEvent, self).event_obj
        e.update(uuid=self.uuid)
        return e

class DiskIOError(UUIDUEvent):
    event_name = 'disk.ioerror'
    def __init__(self, **kv):
        super(DiskIOError, self).__init__(**kv)

class DiskFormated(UUIDUEvent):
    event_name = 'disk.formated'
    def __init__(self, **kv):
        super(DiskFormated, self).__init__(**kv)

class DiskRoleChanged(UUIDUEvent):
    event_name = 'disk.role_changed'
    def __init__(self, **kv):
        super(DiskRoleChanged, self).__init__(**kv)

class DiskPlugged(UUIDUEvent):
    event_name = 'disk.plugged'
    def __init__(self, **kv):
        super(DiskPlugged, self).__init__(**kv)

class DiskUnplugged(UUIDUEvent):
    event_name = 'disk.unplugged'
    def __init__(self, **kv):
        super(DiskUnplugged, self).__init__(**kv)
        self.location = kv['location']
        self.dev_name = kv['dev_name']

    @property
    def event_obj(self):
        e = super(DiskUnplugged, self).event_obj
        e.update(location=self.location, dev_name=self.dev_name)
        return e

class RaidOnline(UUIDUEvent):
    event_name = 'raid.online'
    def __init__(self, **kv):
        super(RaidOnline, self).__init__(**kv)

class RaidNormal(UUIDUEvent):
    event_name = 'raid.normal'
    def __init__(self, **kv):
        super(RaidNormal, self).__init__(**kv)

class RaidDegraded(UUIDUEvent):
    event_name = 'raid.degraded'
    def __init__(self, **kv):
        super(RaidDegraded, self).__init__(**kv)

class RaidFailed(UUIDUEvent):
    event_name = 'raid.failed'
    def __init__(self, **kv):
        super(RaidFailed, self).__init__(**kv)

class RaidRebuilding(UUIDUEvent):
    event_name = 'raid.rebuilding'
    def __init__(self, **kv):
        super(RaidRebuilding, self).__init__(**kv)

class RaidRebuildCompleted(UUIDUEvent):
    event_name = 'raid.rebuild_completed'
    def __init__(self, **kv):
        super(RaidRebuildCompleted, self).__init__(**kv)

class RaidCreated(UUIDUEvent):
    event_name = 'raid.created'
    def __init__(self, **kv):
        super(RaidCreated, self).__init__(**kv)

class RaidRemoved(UUIDUEvent):
    event_name = 'raid.removed'
    def __init__(self, **kv):
        super(RaidRemoved, self).__init__(**kv)
        self.raid_disks = kv['raid_disks'][:]

    @property
    def event_obj(self):
        e = super(RaidRemoved, self).event_obj
        e.update(uuid=self.uuid, raid_disks=self.raid_disks)
        return e

class VolumeOnline(UUIDUEvent):
    event_name = 'volume.online'
    def __init__(self, **kv):
        super(VolumeOnline, self).__init__(**kv)

class VolumeFailed(UUIDUEvent):
    event_name = 'volume.failed'
    def __init__(self, **kv):
        super(VolumeFailed, self).__init__(**kv)

class VolumeNormal(UUIDUEvent):
    event_name = 'volume.normal'
    def __init__(self, **kv):
        super(VolumeNormal, self).__init__(**kv)

class VolumeCreated(UUIDUEvent):
    event_name = 'volume.created'
    def __init__(self, **kv):
        super(VolumeCreated, self).__init__(**kv)

class VolumeRemoved(UUIDUEvent):
    event_name = 'volume.removed'
    def __init__(self, **kv):
        super(VolumeRemoved, self).__init__(**kv)

class VolumeSyncing(UUIDUEvent):
    event_name = 'volume.syncing'
    def __init__(self, **kv):
        super(VolumeSyncing, self).__init__(**kv)

class InitiatorUEvent(UEvent):
    def __init__(self, **kv):
        super(InitiatorUEvent, self).__init__(self.event_name)
        self.wwn = kv['wwn']

    @property
    def event_obj(self):
        e = super(InitiatorUEvent, self).event_obj
        e.update(wwn=self.wwn)
        return e

class InitiatorCreated(InitiatorUEvent):
    event_name = 'initiator.created'
    def __init__(self, **kv):
        super(InitiatorCreated, self).__init__(**kv)

class InitiatorRemoved(InitiatorUEvent):
    event_name = 'initiator.removed'
    def __init__(self, **kv):
        super(InitiatorRemoved, self).__init__(**kv)

class NameUEvent(UEvent):
    def __init__(self, **kv):
        super(NameUEvent, self).__init__(self.event_name)
        self.name = kv['name']

    @property
    def event_obj(self):
        e = super(NameUEvent, self).event_obj
        e.update(name=self.name)
        return e

class BondCreated(NameUEvent):
    event_name = 'bond.created'
    def __init__(self, **kv):
        super(BondCreated, self).__init__(**kv)

class BondRemoved(NameUEvent):
    event_name = 'bond.removed'
    def __init__(self, **kv):
        super(BondRemoved, self).__init__(**kv)

class BondUpdated(NameUEvent):
    event_name = 'bond.updated'
    def __init__(self, **kv):
        super(BondUpdated, self).__init__(**kv)

class EthUpdated(NameUEvent):
    event_name = 'eth.updated'
    def __init__(self, **kv):
        super(EthUpdated, self).__init__(**kv)

class VIUEvent(UEvent):
    def __init__(self, **kv):
        super(VIUEvent, self).__init__(self.event_name)
        self.initr = kv['initr']
        self.volume = kv['volume']

    @property
    def event_obj(self):
        e = super(VIUEvent, self).event_obj
        e.update(initr=self.initr, volume=self.volume)
        return e

class VIMapped(VIUEvent):
    event_name = 'vi.mapped'
    def __init__(self, **kv):
        super(VIMapped, self).__init__(**kv)

class VIUnmapped(VIUEvent):
    event_name = 'vi.unmapped'
    def __init__(self, **kv):
        super(VIUnmapped, self).__init__(**kv)

class MonFSOnline(UUIDUEvent):
    event_name = 'monfs.online'
    def __init__(self, **kv):
        super(MonFSOnline, self).__init__(**kv)

class MonFSCreated(UUIDUEvent):
    event_name = 'monfs.created'
    def __init__(self, **kv):
        super(MonFSCreated, self).__init__(**kv)

class MonFSRemoved(UUIDUEvent):
    event_name = 'monfs.removed'
    def __init__(self, **kv):
        super(MonFSRemoved, self).__init__(**kv)

class FSUEvent(UEvent):
    def __init__(self, **kv):
        super(FSUEvent, self).__init__(self.event_name)
        self.type   = kv['type']
        self.volume = kv['volume']

    @property
    def event_obj(self):
        e = super(FSUEvent, self).event_obj
        e.update(type=self.type, volume=self.volume)
        return e

class FSCreated(FSUEvent):
    event_name = 'fs.created'
    def __init__(self, **kv):
        super(FSCreated, self).__init__(**kv)

class FSRemoved(FSUEvent):
    event_name = 'fs.removed'
    def __init__(self, **kv):
        super(FSRemoved, self).__init__(**kv)

class FSOnline(FSUEvent):
    event_name = 'fs.online'
    def __init__(self, **kv):
        super(FSOnline, self).__init__(**kv)

def fds():
    import os
    from util import execute
    _, o = execute('ls /proc/%s/fd' % os.getpid())
    return sorted([int(i) for i in o.split('\n') if i])

class UserLogin(UEvent):
    event_name = 'user.login'
    def __init__(self, **kv):
        super(UserLogin, self).__init__(self.event_name)
        self.login_id = kv['login_id']

    def notify(self):
        try:
            pusher = mq.Push('uevent_svr')
            pusher.send(self.event_obj)
            log.info("uevent %s notified" % self.event_obj)
        except Exception as e:
            print e
        finally:
            if pusher:
                pusher.close()
            return

    @property
    def event_obj(self):
        e = super(UserLogin, self).event_obj
        e.update(login_id=self.login_id)
        return e

def build_eventmap():
    self = sys.modules[__name__]
    for name in dir(self):
        try:
            obj = getattr(self, name)
            if isinstance(obj, type) and issubclass(obj, UEvent) and hasattr(obj, 'event_name'):
                eventmap[getattr(obj, 'event_name')] = obj
        except:
            pass

build_eventmap()
