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
import gnsq
import network

import commands

import struct

#__version__ = 'v2.0.0' recover when no weed, str to float's bug

class Response(mq.IOHandler):
    def __init__(self,conn):
        self._sock = mq.rsp_socket('speedd')
        self._realtime = Realtime()
	self.conn = conn

    @property
    def fd(self):
        return self._sock

    def stat(self):
        self._realtime.stat()
	self.conn.publish('CloudInfo',json.dumps(list(self._realtime)[-1:]))
	#os.system("echo '%s'> /home/monitor/statistics"%json.dumps(list(self._realtime)[-5:]))


    def handle_statistics(self, kv):
        if 'time' not in kv:
            return {"status":"ok", "samples":list(self._realtime)[-60:]}
        elif kv['time'] == 'last':
            return {"status":"ok", "sample":self._realtime[-1]}
        else:
            return {"status":"ok", "sample":self._realtime[-1]}

    def handle_in(self, e):
        try:
            req = self._sock.recv_json()
            hdl = getattr(self, 'handle_%s' % req['cmd'])
            rsp = hdl(req.get('params', {}))

            self._sock.send_json(rsp)
        except:
            tb.print_exc()
            return

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
        self._cache_tbytes = 0
        self._cache_ubytes = 0
        self._ifaces = network.ifaces().values()
	self._tmp_total = 0
	self._tmp_used = 0
	self._tmp_used_per = 0
        self._vol_rbytes = 0
        self._vol_wbytes = 0
	self._df = []

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
                if 'bond' in iface['name']:
                    continue 
                rpath = '/sys/class/net/%s/statistics/tx_bytes' % iface['name']
                rsum += float(open(rpath).read())
                wpath = '/sys/class/net/%s/statistics/rx_bytes' % iface['name']
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

    def _stat_devices_flow(self):
        try:
            rsum, wsum = 0, 0
            r, w = 0, 0
            df = os.popen("iostat")
            line = df.readlines()[-2]
            rsum = int(line.split()[-2])
            wsum = int(line.split()[-1])

            interval = time.time() - self._timestamp
            if self._vol_rbytes <> 0:
                r = rsum - self._vol_rbytes
            if self._vol_wbytes <> 0:
                w = wsum - self._vol_wbytes
            self._vol_rbytes = rsum
            self._vol_wbytes = wsum
            return self._format_nr(r/interval/1024), self._format_nr(w/interval/1024)
        except:
            return 0,0

    def _stat_cache(self):
        try:
            tpath = '/sys/fs/rdcache/cache-!dev!md0/blk_total_nr' 
            self._cache_tbytes = float(open(tpath).read())
            upath = '/sys/fs/rdcache/cache-!dev!md0/blk_used_nr'
            self._cache_ubytes = float(open(upath).read())
            return self._cache_tbytes,self._cache_ubytes
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

    def _stat_df(self):
	result =[]
        df = os.popen("df")
        lines = df.readlines()
        for i in lines:
            if "/\n" in i:
                result.append(self._stat_df_temp(i,"system"))
            elif "/tmp\n" in i:
                result.append(self._stat_df_temp(i,"tmp"))
            elif "/docker\n" in i:
                result.append(self._stat_df_temp(i,"docker"))
            elif "/var\n" in i:
                result.append(self._stat_df_temp(i,"var"))
  	return result

    def _stat_gateway(self):
	res = []
	ifaces = ["eth0","eth1"]
	gateway = psutil.net_if_stats()
	for i in ifaces:
	    if gateway[i].isup and gateway[i].duplex!=0:
		res.append(dict(name=i,speed=gateway[i].speed))
	
	return res
		
    def _stat_df_temp(self,line,name):
        val = [val for val in line.split(" ") if val]
        tmp_name = name
        tmp_total = float(val[2]) + float(val[3])
        tmp_used = float(val[3])
        tmp_used_per = float(val[4][:-1])
	return dict(name=tmp_name, total=tmp_total, available=tmp_used, used_per=tmp_used_per)

    def _stat_weed_cpu(self):
       	total = 100.0
	used_per = psutil.cpu_percent(0)
	available = total - used_per
        try:
            name = 'weed_cpu'
            cpu = commands.getoutput("top -b -n 1 | grep 'minio' | head -1 | awk \'{printf(\"%0.1f\"),$9/8}\'")
            self._weed_cpu = float(cpu)

	except Exception as e:
            print e
	return dict(name=name, total=total, available=available, used_per=self._weed_cpu)

    def _stat_weed_mem(self):
        name = 'weed_mem'
        vm = psutil.virtual_memory()
	total = self._format_nr(float(vm.total)/1024/1024/1024)
        mem = commands.getoutput("top -b -n 1 | grep 'minio' | head -1 | awk '{print $6}'")
        per = commands.getoutput("top -b -n 1 | grep 'minio' | head -1 | awk '{print $10}'")
	try:
	    used_per = float(per)
            if 'g' in mem:
                self._weed_mem = float(mem[:-1])
            elif 't' in mem:
                self._weed_mem = float(mem[:-1])*1024
            elif 'm' in mem:
                self._weed_mem = float(mem[:-1])/1024
            elif 'p' in mem:
                self._weed_mem = float(mem[:-1])*1024*1024
            else: 
                self._weed_mem = float(mem)/1024/1024
        except:
                self._weed_mem = 0
	        used_per = 0.0
	available = self._format_nr(float(vm.total-vm.used)/vm.total*100)

        return dict(name=name, total=total, available=available, used_per=used_per)

    def _stat_ifaces_flow_dev(self):
        try:
            r, w = 0, 0

            wsum = psutil.net_io_counters().bytes_recv
            rsum = psutil.net_io_counters().bytes_sent

            interval = time.time() - self._timestamp
            if self._network_rbytes <> 0:
                r = rsum - self._network_rbytes
            if self._network_wbytes <> 0:
                w = wsum - self._network_wbytes
            self._network_rbytes = rsum
            self._network_wbytes = wsum
            return self._format_nr(r/interval/1024/1024), self._format_nr(w/interval/1024/1024)
        except Exception as e:
            print e
            return 0,0

    '''def _stat_ifaces_flow_dev(self):
        try:
            rsum, wsum = 0, 0
            r, w = 0, 0
            rsum, wsum = self._dev()
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

    def get_ip_address(self,ifname):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        return socket.inet_ntoa(fcntl.ioctl(
            s.fileno(),
            0x8915,  # SIOCGIFADDR
            struct.pack('256s', ifname[:15])
        )[20:24])'''

    def get_ip_address(self):
        INTERFACE = ['eth0','eth1']
        ifaces = network.ifaces().values()
        for i in INTERFACE:
            for j in ifaces:
                if j.name == i and j.link:
                    return j.ipaddr

    def _dev(self):
        try:
          r,w = 0,0
          fstat = open('/proc/net/dev').readlines()
          INTERFACE = ['eth0:','eth1:']
          for s in fstat:
              for i in INTERFACE:
                  if i in s:
                      w += float(s.split()[1])
                      r += float(s.split()[9])
          return r,w
	except:
            return 0,0

    def stat(self):
        if time.time() - self._timestamp < 1.0:
            return
        cpu = psutil.cpu_percent(0)
        vm = psutil.virtual_memory()
        temp = self._stat_temp()

        mem = self._format_nr(float(vm.used)/vm.total*100)
        mem_total = vm.total

        r, w = self._stat_flow()
        fr,fw = self._stat_fs_flow()
        nr,nw = self._stat_ifaces_flow_dev()				#export
        rvol,wvol = self._stat_devices_flow()
	df = self._stat_df()
	rd_t,rd_u = self._stat_cache()


	gate = self._stat_gateway()
	iface = self.get_ip_address()
        timestamp = self._format_nr(self._timestamp)
        self._timestamp = time.time()
        sample = {'ip' : iface,
                  'dev' : 'export',
		  'cpu' : cpu,
                  'mem' : mem,
                  'mem_total' : mem_total,
                  'temp': temp,
                  'read_mb': nr, 	#nread KB/s
                  'write_mb': nw,
                  'timestamp': timestamp,
                  'df':df,
		  'cache_total': rd_t,
		  'cache_used': rd_u,
                  'read_vol': rvol,
                  'write_vol': wvol,
		  'gateway': gate
                  }
	print sample
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
	conn = gnsq.Nsqd(address=config.zoofs.ip, http_port=config.zoofs.publish_port)
        self._rsp = Response(conn)
        self._poller.register(self._rsp)

    def _run(self):
        print 'info(%s) is running...' % os.getpid()
        while True:
            self._rsp.stat()
            self._poller.poll(config.info.interval*1000)


if __name__ == "__main__":
    main(config.info.pidfile, SpeedioDaemon)
