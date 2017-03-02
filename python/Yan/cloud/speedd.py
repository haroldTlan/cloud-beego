#!/usr/bin/env python
import select
import subprocess as sub
import fcntl
import os
from collections import deque
import sys
import traceback as tb
import time
import json
import random
import socket
from env import config
import sys, time
from daemon import Daemon, main
import syslog
import adm
import re
from log import log_exc
from caused import ignore_exc
from util import execute
import mq
import psutil

__version__ = 'v1.0.0'

class Response(mq.IOHandler):
    def __init__(self):
        self._sock = mq.rsp_socket('speedd')
        self._realtime = Realtime()

    @property
    def fd(self):
        return self._sock

    def stat(self):
        self._realtime.stat()

    def handle_statistics(self, kv):
        if 'time' not in kv:
            return {"status":"ok", "samples":list(self._realtime)[-60:]}
        elif kv['time'] == 'last':
            return {"status":"ok", "sample":self._realtime[-1]}
        #elif kv['time'] <> 0:
        #    for sample in self._realtime:
        #        if sample['time'] >= kv['time']:
        #            break
        #    return {"status":"ok", "sample":sample}
        else:
            return {"status":"ok", "sample":self._realtime[-1]}

    def handle_in(self, e):
        try:
            req = self._sock.recv_json()
            print 'req %s' % req
            hdl = getattr(self, 'handle_%s' % req['cmd'])
            rsp = hdl(req.get('params', {}))
            print rsp

            self._sock.send_json(rsp)
        except:
            tb.print_exc()
            return

class Realtime(object):
    def __init__(self):
        self._samples = deque(maxlen=1024)
        self._total_read_mbytes = 0
        self._total_write_mbytes = 0
        self._timestamp = int(time.time())

    def _get_write_flow(self, prev, interval):
        cmd = 'cat /sys/kernel/config/target/core/fileio_*/*/statistics/scsi_lu/write_mbytes'
        s, o = execute(cmd)
        flows = [int(nr) for nr in o.split()] 
        total = float(sum(flows))
        avg = (total - prev)/interval
        return avg, total
    
    def _get_read_flow(self, prev, interval):
        cmd = 'cat /sys/kernel/config/target/core/fileio_*/*/statistics/scsi_lu/read_mbytes'
        s, o = execute(cmd)
        flows = [int(nr) for nr in o.split()] 
        total = float(sum(flows))
        avg = (total - prev)/interval
        return avg, total

    def _stat_flow(self, elapse):
        try:
            r, self._total_read_mbytes  = self._get_read_flow(self._total_read_mbytes,   elapse)
            w, self._total_write_mbytes = self._get_write_flow(self._total_write_mbytes, elapse)
            return r,w
        except:
            return 0,0

    def _format_nr(self, nr):
        return float('%0.2f'%float(nr))

    def _stat_temp(self):
        total, nr = 0, 1
        for s in self._samples:
            if 'cpu' in s:
                total += int(s['cpu'])
                nr += 1
        return 40 + (20 + random.randint(0,2)) * (total/nr) / 100

    def stat(self):
        cpu = psutil.cpu_percent(0)
        mem = psutil.virtual_memory().percent
        temp = self._stat_temp()

        timestamp = int(time.time())
        r, w = self._stat_flow(timestamp-self._timestamp)
        r = self._format_nr(r)
        w = self._format_nr(w)
        self._timestamp = timestamp
        
        sample = {'cpu' : cpu,
                  'mem' : mem,
                  'temp': temp,
                  'read_mb': r,
                  'write_mb': w,
                  'timestamp': timestamp}
        self._samples.append(sample)

    def __iter__(self):
        return iter(self._samples)

    def __getitem__(self, idx):
        return self._samples.__getitem__(idx)

    def __getslice__(self, sidx, eidx):
        return self._samples.__getslice__(sidx, eidx)

class SpeedioDaemon(Daemon):
    def init(self):
        self._poller = mq.Poller()
        self._rsp = Response()
        self._poller.register(self._rsp)

    def _run(self):
        print 'statd start...'
        while True:
            self._rsp.stat()
            self._poller.poll(2000)
            
 
if __name__ == "__main__":
    main(config.speedd.pidfile, SpeedioDaemon)
