#!/usr/bin/env python
from daemon import Daemon, main
from env import config
import mq
import time
from util import execute
import re
import os
import log
import json
import adm
import network
import sys
import socket
import error
import db
from db import with_db

def stringify(d):
    for k, v in d.items():
        if isinstance(v, unicode):
            del d[k]
            d[str(k)] = str(v)
        elif isinstance(v, dict):
            d[str(k)] = stringify(v)
    return d

class KeventHandler(mq.IOHandler):
    def __init__(self, guard):
        self.guard = guard
        self._sock = socket.socket(socket.AF_NETLINK, socket.SOCK_DGRAM, 11)
        self._sock.bind((0,-1))
        self._timestamp = time.time()
        self.delayed_err = []

    @property
    def fd(self):
        return self._sock.fileno()

    @with_db
    def handle_in(self, e):
        patmap = { 'EVENT:DISK@CHANGE=([-0-9A-Za-z]+)' : self._disk_fail,
                   'EVENT:DISK@REMOVE=(\w+)'           : self._disk_remove,
                   'EVENT:DISK@ADD=(\w+)'              : self._disk_add,
                   'EVENT:RAID@recovery_done=(\w+)'    : self._raid_recovery_done,
                   'EVENT:MONFS@SYNC=(\d+)'                  : self._sync_mmap,
                   'EVENT:DSU@DOWN'                    : self._dsu_down}
        msg = self._sock.recv(256)
        for pat, action in patmap.items():
            try:
                m = re.search(pat, msg)
                if m:
                    action(*m.groups())
                    return
            except:
                pass

    def elapse(self):
        timestamp = time.time()
        timeout = [dev_name for dev_name,t in self.delayed_err if timestamp-t > config.disk.ioerror_unplug_interval]
        self.delayed_err[:] = [(n, t) for n,t in self.delayed_err if n not in timeout]
        for dev_name in timeout:
            log.info('handle disk:%s ioerror' % dev_name)
            self.guard.unplug(dev_name)

        timestamp = time.time()
        self.guard.elapse(int(timestamp-self._timestamp))
        self._timestamp = timestamp

    def _sync_mmap(self, dev_name):
        print 'EVENT:MONFS=%s' % dev_name
        name = '/root/test'
        cmd = 'cat /proc/`pidof chameleon`/maps |grep nvr |grep %s' % dev_name
        _, o = execute(cmd)
        p = re.search(r'/opt/(.*)', o)
        if p and p.groups()[0]:
            name = '/opt/'+p.groups()[0]

        cmd = 'sync_mmap %s' % (name)
        print cmd
        _, _ = execute(cmd)


    def _disk_remove(self, dev_name):
        print 'EVENT:DISK@REMOVE=%s' % dev_name
        for n, t in self.delayed_err:
            if n == dev_name:
                log.info('cancel disk:%s ioerror' % dev_name)
        self.delayed_err[:] = [(n, t) for n,t in self.delayed_err if n <> dev_name]
        self.guard.unplug(dev_name)

    def _disk_add(self, dev_name):
        print 'EVENT:DISK@ADD=%s' % dev_name
        self.guard.plug(dev_name)

    def _disk_fail(self, dm):
        print 'EVENT:DISK@CHANGE=%s' % dm
        disk = adm.Disk.dmname_to_disk(dm)
        log.info('delayed handle disk:%s(%s) ioerror' % (disk.location, disk.dev_name))
        self.delayed_err.append((disk.dev_name, time.time()))

    def _raid_recovery_done(self, dev_name):
        print 'EVENT:RAID@recovery_done=%s' % dev_name
        self.guard.complete_rebuilding(dev_name)

    def _dsu_down(self):
        log.warning('DSU down')
        log.journal_warning('DSU down')

class APIExist(Exception):
    def __init__(self, message):
        super(APIExist, self).__init__(message)

class APIHandler(mq.IOHandler):
    def __init__(self, guard):
        self.build_api_map()
        self.guard = guard
        self.sock = mq.rsp_socket('admd')

    def build_api_map(self):
        self.api_map = {}
        def _scan_api(api_module):
            for name in api_module.api:
                if name in self.api_map:
                    raise APIExist(name)
                func = getattr(api_module, name)
                self.api_map[name] = func
        _scan_api(adm)
        _scan_api(network)

    @property
    def fd(self):
        return self.sock

    def reload_rqueue(self):
        try:
            self.guard.load()
        except:
            pass
        return

    def scan_all(self):
        ret = adm.scan_all()
        try:
            self.guard.load()
        except:
            pass
        return ret

    def delete_raid(self, name):
        try:
            self.guard.dequeue(name)
        except:
            pass
        api = self.api_map['delete_raid']
        return api(name)

    def handle_in(self, e):
        msg = self.sock.recv()
        req = json.loads(msg)
        req = stringify(req)

        name = req['action']
        api = getattr(self, name, None)
        if not api:
            api = self.api_map.get(name, None)

        if api:
            if name == 'scan_all':
                ret = api(**req['params'])
            else:
                db.connect()
                ret = api(**req['params'])
                db.close()
            rsp = json.dumps(ret)
        else:
            rsp = json.dumps(error.internal_error)

        self.sock.send(rsp)

class Admd(Daemon):
    def init(self):
        guard = adm.Guard()
        self.khdl = KeventHandler(guard)
        apihdl = APIHandler(guard)

        self.poller = mq.Poller()
        self.poller.register(self.khdl)
        self.poller.register(apihdl)


    def _run(self):
        print 'admd(%s) is running...' % os.getpid()
        while True:
            self.poller.poll(config.admd.poll_timeout_secs*1000)
            self.khdl.elapse()

if __name__ == "__main__":
    main(config.admd.pidfile, Admd)

