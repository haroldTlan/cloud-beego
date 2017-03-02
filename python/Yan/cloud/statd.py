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
import re
from log import log_exc
from caused import ignore_exc
from util import execute
import mq
import psutil
import json
#import network
import subprocess
import threading

lock = threading.RLock()

TMP = {}
threads = []
cpu_total = 0.0
mem_total = 0.0
#cpu_count = float(psutil.cpu_count())

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
	os.system("echo '%s'> /home/monitor/statictis"%json.dumps(list(self._realtime)[-20:]))

    def handle_statistics(self, kv):
	print kv
	print self._realtime
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

class ProcessInfo(psutil.Process):
    def run(self, inter):
        global TMP
        global cpu_total
        global mem_total
        try:
            tmp = float(self.memory_percent())
            temp = float(self.cpu_percent(inter))
        except:
            tmp =0.0
            temp = 0.0
        lock.acquire()
        cpu_total += temp
        mem_total += tmp
        TMP[self.name()] = {}
        TMP[self.name()]["%cpu"] = temp
        TMP[self.name()]["%mem"] = tmp
        lock.release()



class Realtime(object):
    def __init__(self):
        self._samples = deque(maxlen=1024)
        self._read_mbytes = 0
        self._write_mbytes = 0
        self._timestamp = time.time()
        self._fs_read_bytes = 0
        self._fs_write_bytes = 0
        self._network_rbytes = 0
        self._network_wbytes = 0
        self._ifaces = [dict(name="eth0"), dict(name="eth1")]
	self._tmp_total = 0
	self._tmp_used = 0
	self._tmp_used_per = 0
	self._cache = {}

    def _flow(self, path, prev):
        try:
            cmd = 'cat %s' % path
            _,o = execute(cmd, logging=False)
            flows = [int(nr) for nr in o.split()] 
            total = float(sum(flows))
            interval = time.time() - self._timestamp
            avg = (total - prev)/interval
            return avg, total
        except:
            return 0, 0

    def _stat_fs_flow(self):
        try:
            path = '/sys/fs/monfs/*/fio_r_bytes'
            r, self._fs_read_bytes = self._flow(path, self._fs_read_bytes)
            path = '/sys/fs/monfs/*/fio_w_bytes'
            w, self._fs_write_bytes = self._flow(path, self._fs_write_bytes)
            return self._format_nr(r/1024/1024), self._format_nr(w/1024/1024)
        except:
            return 0,0

    def _stat_flow(self):
        try:
            path = '/sys/kernel/config/target/core/fileio_*/*/statistics/scsi_lu/read_mbytes'
            r, self._read_mbytes = self._flow(path, self._read_mbytes)
            path = '/sys/kernel/config/target/core/fileio_*/*/statistics/scsi_lu/write_mbytes'
            w, self._write_mbytes = self._flow(path, self._write_mbytes)
            return self._format_nr(r), self._format_nr(w)
        except:
            return 0,0

    def _stat_ifaces_flow(self):
        try:
            rsum, wsum = 0, 0
            r, w = 0, 0
            for iface in self._ifaces:
                if 'bond' in iface.name:
                    continue 
                rpath = '/sys/class/net/%s/statistics/tx_bytes' % iface.name
                rsum += float(open(rpath).read())
                wpath = '/sys/class/net/%s/statistics/rx_bytes' % iface.name
                wsum += float(open(wpath).read())

            interval = time.time() - self._timestamp
            if self._network_rbytes <> 0:
                r = rsum - self._network_rbytes
            if self._network_wbytes <> 0:
                w = wsum - self._network_wbytes
            self._network_rbytes = rsum
            self._network_wbytes = wsum

            return self._format_nr(r/interval/1024/1024), self._format_nr(w/interval/1024/1024)
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

    def _stat_cache(self):
	p1 = subprocess.Popen(['df', '-h','/tmp'], stdout=subprocess.PIPE)
	lines = p1.stdout.readlines()
	if len(lines) == 0:
	    return 0,0,0
	else:
	    val = [val for val in lines[1].split(" ") if val]
	    tmp_total = float(val[1][:-1])*1024.0
	    tmp_used = float(val[2][:-1])/1024.0
   	    tmp_used_per = float(val[4][:-1])
	    self._cache = dict(total=tmp_total, used=tmp_used, used_per=tmp_used_per)

  	    return self._cache

    def _stat_process(self):
        process = []
        for i in psutil.pids():
            try:
               p = ProcessInfo(i)

            except psutil.NoSuchProcess:
                continue
            else:
                interval = time.time() - self._timestamp
                t = threading.Thread(target=p.run, args=(interval,))
                threads.append(t)
                t.start()

        for j in threads:
            if j.is_alive():
                j.join()

        info = sorted(TMP.iteritems(), key=lambda d: d[1]["%" + 'mem'], reverse=True)
        for i in range(len(info)):
            #cpu = float('%.4f' % ((info[i][1]["%cpu"]) / cpu_count))
            mem = float('%.4f' % (info[i][1]["%mem"]))
            name = "{0}".format(info[i][0])
            if cpu > 0 or mem > 0:

                process.append(dict(name=name, cpu=cpu, mem=mem))

        return process

    def stat(self):
        if time.time() - self._timestamp < 1.0:
            return
        cpu = psutil.cpu_percent(0)
        vm = psutil.virtual_memory()
        temp = self._stat_temp()

        mem = self._format_nr(float(vm.used)/vm.total*100)
        r, w = self._stat_flow()
        fr,fw = self._stat_fs_flow()
        nr,nw = self._stat_ifaces_flow()
        self._timestamp = time.time()
	cache = self._stat_cache()
	#process = self._stat_process()

        timestamp = self._format_nr(self._timestamp)
        sample = {'cpu' : cpu,
                  'mem' : mem,
                  'temp': temp,
                  'read_mb': r,
                  'write_mb': w,
                  'fread_mb': fr,
                  'fwrite_mb': fw,
                  'nread_mb': nr,
                  'nwrite_mb': nw,
                  'timestamp': timestamp,
		  'cache': cache}
		  #'process': process}
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
        print 'statd(%s) is running...' % os.getpid()
        while True:
            self._rsp.stat()
            self._poller.poll(config.statd.interval*1000)


if __name__ == "__main__":
    main(config.statd.pidfile, SpeedioDaemon)
