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

def cmp_disk(a, b):
    a3 = re.findall('(\d+)\.(\d+)\.(\d+)', a['location'])
    b3 = re.findall('(\d+)\.(\d+)\.(\d+)', b['location'])
    for x, y in zip(a3[0], b3[0]):
        if int(x) > int(y): return 1
        elif int(x) < int(y): return -1
    return 0

class ExitError(Exception):
    pass

class ZeroProcess(object):
    def __init__(self, disk):
        self.disk = disk
        self.avr_speed = 'N/A'
        self.begin = None
        self.status = 'N/A'
        self.copied = Byte(0)
        self.process = None
        self.end = None

    @property
    def exit(self):
        return self.status in ['ioerror', 'error', 'completed', 'stop']

    @property
    def stderr(self):
        return self.process.stderr if self.process else None

    def prepare(self):
        if self.exit:
            raise ExitError
        self.status = 'prepare'
        self.disk.remove_dev()

    def start(self):
        if self.exit:
            raise ExitError
        self.status = 'inprogress'
        self.begin = datetime.now()
        cmd = ['/bin/dd', 'if=/dev/zero', 'of=/dev/%s' % self.disk.dev_name, 'bs=128K',
                'oflag=direct']
        log.info('start zero disk %s(%s)' % (self.disk.location, self.disk.dev_name))
        self.process = sp.Popen(cmd, stderr=sp.PIPE, close_fds=True)
        flags = fcntl.fcntl(self.stderr.fileno(), fcntl.F_GETFL)
        fcntl.fcntl(self.stderr.fileno(), fcntl.F_SETFL, flags| os.O_NONBLOCK)


    def query(self):
        if not self.exit:
            if datetime.now() - self.begin < timedelta(seconds=5):
                time.sleep(5)
            poller = zmq.Poller()
            poller.register(self.stderr.fileno(), zmq.POLLIN|zmq.POLLERR)
            try:
                self.process.send_signal(signal.SIGUSR1)
                fds = poller.poll(1000)
                if fds:
                    _, mask = fds[0]
                    if mask & zmq.POLLERR:
                        self.handle_err()
                    elif mask & zmq.POLLIN:
                        o = self.read_output()
                        self.stat_info(o)
            except Exception as e:
                print e
            poller.unregister(self.process.stderr.fileno())
        return Byte(self.copied), self.avr_speed

    def read_output(self):
        o = ''
        for i in range(0,32):
            try:
                o = self.stderr.read().rstrip()
                if 'copied' in o:
                    break
                time.sleep(0.01)
            except:
                time.sleep(0.01)

        return o

    def stat_info(self, o):
        '''0 bytes (0 B) copied, 0.0028287 s, 0.0 kB/s'''
        try:
            last_line = o.split('\n')[-1].rstrip()
            copied,_,speed = last_line.split(',')
            m = re.search('(\d+)\s*bytes', copied)
            self.copied = Byte(m.group(1))
            self.avr_speed = speed.lstrip()
        except:
            pass

    def check_alive(self):
        return sp.Popen.poll(self.process) is None

    def _log_result(self, o):
        cost = self.end - self.begin
        ratio = '%.1f' % (self.copied / self.disk.cap * 100)
        i = {'dev_name' : self.disk.dev_name,
             'location' : self.disk.location,
             'capacity' : str(self.disk.cap.fit()),
             'copied'   : str(self.copied.fit()),
             'status'   : self.status,
             'avr_speed': self.avr_speed,
             'begin'    : self.begin.strftime('%Y-%m-%d %H:%M:%S'),
             'cost'     : str(cost).split('.')[0],
             'progress' : ratio}

        log.info('finish zero disk %(location)s(%(dev_name)s):'\
                 'capacity: %(capacity)s, '\
                 'copied: %(copied)s, '\
                 'status: %(status)s, '\
                 'avr_speed: %(avr_speed)s, '\
                 'begin: %(begin)s, '\
                 'cost: %(cost)s, '\
                 'progress: %(progress)s' % i)
        log.info(o)

    def handle_err(self):
        if self.exit:
            return
        self.exitcode = sp.Popen.poll(self.process)
        if self.exitcode is None:
            self.stop()
            self.status = 'error'
            self.end = datetime.now()
        else:
            o = ''
            if self.exitcode <> -errno.ENOTBLK:
                for i in range(0, 4):
                    if '/bin/dd' not in o:
                        o = self.read_output()
                        time.sleep(0.05)

            if 'No space left on device' in o:
                self.status = 'completed'
            elif 'Input/output error' in o:
                self.status = 'ioerror'
            else:
                self.status = 'error'

            self.end = datetime.now()
            self.stat_info(o)
            self._log_result(o)

    def stop(self):
        if not self.exit:
            self.process.kill()
            self.exitcode = self.process.wait()
            self.status = 'stop'

class ZeroDaemon(Daemon):
    def init(self):
        self.poller = zmq.Poller()
        self.sub_poller = zmq.Poller()
        self.svr = mq.rsp_socket('zerod')
        self.poller.register(self.svr, zmq.POLLIN|zmq.POLLERR)
        self.zerop = {}

    def _run(self):
        print 'zerod(%s) is running...' % os.getpid()

        while True:
            fds = self.poller.poll(5000)
            if fds:
                _,mask = fds[0]
                if mask &  zmq.POLLIN:
                    self.handle_reqest()
            else:
                for zp in self.zerop.values():
                    if not zp.check_alive():
                        zp.handle_err()

    def handle_stop_zero(self, _=None):
        for zp in self.zerop.values():
            zp.stop()
        self.zerop = {}

    @with_db
    def handle_zero_disks(self, _=None):
        self.handle_stop_zero()

        mapping = lm.LocationMapping().mapping
        for dev_name in mapping.values():
            try:
                disk = adm.Disk.lookup(dev_name=dev_name)
            except:
                continue
            if disk.online:
                zp = ZeroProcess(disk)
                self.zerop[disk.location] = zp
                zp.prepare()

        for zp in self.zerop.values():
            zp.start()

    def handle_query_zero_progress(self, _=None):
        progress = []
        for location, zp in self.zerop.items():
            copied, speed = zp.query()
            if zp.status in ['inprogress', 'prepare']:
                cost = datetime.now() - zp.begin
            else:
                cost = zp.end - zp.begin
            ratio = '%.1f' % (zp.copied / zp.disk.cap * 100)
            p = {'location' : location,
                 'capacity' : str(zp.disk.cap.fit()),
                 'copied'   : str(copied.fit()),
                 'status'   : zp.status,
                 'avr_speed': speed,
                 'begin'    : int(zp.begin.strftime('%s')),
                 'cost'     : int(cost.total_seconds()),
                 'progress' : ratio}
            progress.append(p)
        progress = sorted(progress, cmp=cmp_disk)
        return progress

    def handle_reqest(self):
        o = self.svr.recv_json()
        try:
            hdl = getattr(self, 'handle_%s' % o['cmd'])
            rsp = hdl(o)
            self.svr.send_json(error.success(rsp))
        except Exception as e:
            print e
            self.svr.send_json(error.error(e))


def zero_disks():
    req = mq.Request('zerod')
    try:
        req.request({'cmd':'zero_disks'}, 10000)
    finally:
        req.close()

def query_zero_progress():
    req = mq.Request('zerod')
    try:
        rsp = req.request({'cmd':'query_zero_progress'}, 10000)
        if 'success' in rsp['status']:
            return rsp['detail']
        else:
            raise Exception()
    finally:
        req.close()

def test1():
    d = ZeroDaemon('/tmp/z.pid')
    d.init()
    d.handle_zero_disks()
    d.handle_query_zero_progress()
    return d

def test2():
    disk = adm.Disk.lookup(dev_name='sdg')
    zp = ZeroProcess(disk)
    zp.prepare()
    zp.start()
    time.sleep(1)
    return zp

if __name__ == '__main__':
    main(config.zerod.pidfile, ZeroDaemon)
