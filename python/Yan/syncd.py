#!/usr/bin/env python
import sys
import re
import adm
import lm
from env import config
import multiprocessing as mp
import os
import log
from util import execute
from unit import Byte, GB, MB, KB, Sector, Unit
import time
from datetime import datetime, timedelta
import error
import select
from daemon import Daemon, main
import subprocess as sp
import zmq
import mq
import signal
import fcntl
import errno
import log
from db import with_db
from env import config

import sync_lun

class SyncProcess(object):
    def __init__(self, volume):
        self.volume = volume
        self.process = None

    def start(self):
        sleep_second = config.volume.sync.sleep_sec
        tpw = config.volume.sync.total_per_write
        if not os.path.exists('%s/start_sync_lun.pyc' % os.getcwd()):
            log.info('file start_sync_lun.pyc not exists')
        else:
            cmd = ['python start_sync_lun.pyc -s %d -w %s -n %s' % (sleep_second, tpw, self.volume.name)]
            log.info('start sync volume %s(%s)' % (self.volume.name, self.volume.dev_path))
            self.process = sp.Popen(cmd, stdout=sp.PIPE, close_fds=True, shell=True, cwd='/home/zonion/speedio')

    def check_alive(self):
        return sp.Popen.poll(self.process) is None

    def stop(self):
        self.process.kill()

class SyncDaemon(Daemon):
    def init(self):
        self.poller = zmq.Poller()
        self.sub_poller = zmq.Poller()
        self.svr = mq.rsp_socket('syncd')
        self.poller.register(self.svr, zmq.POLLIN|zmq.POLLERR)
        self.syncp = {}

    def _run(self):
        print 'syncd(%s) is running...' % os.getpid()

        while True:
            fds = self.poller.poll(3000)
            if fds:
                _,mask = fds[0]
                if mask &  zmq.POLLIN:
                    self.handle_reqest()

    def handle_stop_sync_volume(self, lun):
        print 'stop ..... (%s)' % lun
        if self.syncp.has_key(lun):
            self.syncp[lun].stop()
            sync_lun.change_status_to_stop(lun)
            del self.syncp[lun]

    def handle_delete_sync_volume_task(self, lun):
        print 'delete sync task ..... (%s)' % lun
        self.handle_stop_sync_volume(lun)
        sync_lun.del_zero_volume(lun)

    @with_db
    def handle_sync_volume(self, lun):
        self.handle_stop_sync_volume(lun)
        try:
            volume = adm.Volume.lookup(name=lun)
        except:
            pass

        syp = SyncProcess(volume)
        self.syncp[lun] = syp
        syp.start()
        print 'sync lun start...........(%s)' % lun

    def handle_query_sync_progress(self, lun):
        
        try:
            progs = sync_lun.query_zero_progress()
        except Exception as e:
            log.info('%s'%e)
            return e
        for o in progs:
            if o['name'] == lun:
                return o
        
        return None

    def handle_reqest(self):
        o = self.svr.recv_json()
        try:
            hdl = getattr(self, 'handle_%s' % o['cmd'])
            rsp = hdl(o['name'])
            self.svr.send_json(error.success(rsp))
        except Exception as e:
            print e
            self.svr.send_json(error.error(e))


def sync_volume(name):
    req = mq.Request('syncd')
    try:
        req.request({'cmd':'sync_volume', 'name':name}, 10000)
    finally:
        req.close()

def stop_sync_volume(name):
    req = mq.Request('syncd')
    try:
        req.request({'cmd':'stop_sync_volume', 'name':name}, 10000)
    finally:
        req.close()

def delete_sync_volume_task(name):
    req = mq.Request('syncd')
    try:
        req.request({'cmd':'delete_sync_volume_task', 'name':name}, 10000)
    finally:
        req.close()

def query_sync_progress(name):
    req = mq.Request('syncd')
    try:
        #import pdb
        #pdb.set_trace()
        rsp = req.request({'cmd':'query_sync_progress', 'name':name}, 10000)
        if rsp and rsp['status'] == 'success':
            if rsp.has_key('detail'):
                return rsp['detail']
            else:
                return None
        else:
            raise Exception()
    finally:
        req.close()

if __name__ == '__main__':
    main(config.syncd.pidfile, SyncDaemon)
