#!/usr/bin/env python
# encoding: utf-8

import sys
import os
import adm
from util import execute
from datetime import datetime, timedelta
from env import config
import subprocess as sp
import zmq
import error
import mq
import signal
import fcntl
import errno
import log
from daemon import Daemon, main
from db import with_db
from unit import Byte, GB, MB, KB, Sector, Unit
import time

class ExitError(Exception):
    pass

class BeepProcess(object):
    def __init__(self, mod):
        self.mod = mod

        self.status = 'N/A'
        self.process = None
        self.begin = None
        self.end = None

    @property
    def exit(self):
        return self.status in ['stop']

    def start(self):
        if self.exit:
            raise ExitError
        self.status = 'inprogress'
        self.begin = datetime.now()
       
        cmd = ['./spk.sh %s' % self.mod]
        log.info('start beep, cmd(%s)' % cmd)
        self.process = sp.Popen(cmd, shell=True, cwd='/home/zonion/command')#return the child process

    def check_alive(self):
        return sp.Popen.poll(self.process) is None

    def _log_result(self):
        cost = self.end - self.begin
        i = {'mod'      : self.mod,
             'status'   : self.status,
             'begin'    : self.begin.strftime('%Y-%m-%d %H:%M:%S'),
             'cost'     : str(cost).split('.')[0]}

        log.info('finish beep %(mod)s:'\
                 'status: %(status)s, '\
                 'begin: %(begin)s, '\
                 'cost: %(cost)s, ' % i)

    def stop(self):
        if not self.exit:
            self.process.kill()
            #self.exitcode = self.process.wait()
            self.status = 'stop'
            self.end = datetime.now()
            self._log_result()
            

class BeepDaemon(Daemon):
    def init(self):
        self.poller = zmq.Poller()
        self.sub_poller = zmq.Poller()
        self.svr = mq.rsp_socket('beepd')
        self.poller.register(self.svr, zmq.POLLIN|zmq.POLLERR)
        self.beepp = None

    def _run(self):
        print 'Beepd(%s) is running...' % os.getpid()

        while True:
            fds = self.poller.poll(3000)
            if fds:
                _,mask = fds[0]
                if mask &  zmq.POLLIN:
                    self.handle_reqest()

    def handle_stop_beep(self, mod):
        print 'stop ..... beep (%s)' % mod
        if self.beepp:
            self.beepp.stop()
            self.beepp = None

    def handle_start_beep(self, mod):
        self.handle_stop_beep(mod)

        bp = BeepProcess(mod)
        self.beepp = bp

        bp.start()
        print "beep start...........(%s)" % mod

    def handle_reqest(self):
        o = self.svr.recv_json()
        try:
            hdl = getattr(self, 'handle_%s' % o['cmd'])
            rsp = hdl(o['mod'])
            self.svr.send_json(error.success(rsp))
        except Exception as e:
            print e
            self.svr.send_json(error.error(e))

def start_beep(mod):
    req = mq.Request('beepd')
    try:
        req.request({'cmd':'start_beep', 'mod':mod}, 10000)
    finally:
        req.close()

def stop_beep(mod):
    req = mq.Request('beepd')
    try:
        req.request({'cmd':'stop_beep', 'mod':mod}, 10000)
    finally:
        req.close()

def test1():
    bd = BeepDaemon('/tmp/p.pid')
    bd.init()
    bd.handle_start_beep('a')
    return bd

def test2():
    bp = BeepProcess()
    bp.start()
    time.sleep(1)
    return bp


if __name__ == '__main__':
    main(config.beepd.pidfile, BeepDaemon)
