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
import ethtool

import commands
import struct
import rest
import db
from lm import LocationMapping
from multiprocessing import cpu_count #get cpu_count

#__version__ = 'v2.0.0' add w & r's average

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
	res = {}
	if len(list(self._realtime)) > 2:
	    res.update(list(self._realtime)[-1:][0])
	    res_before = list(self._realtime)[-1:][0]

	    res['write_mb'] = (res['write_mb'] + res_before['write_mb'])/2.0
	    res['read_mb'] = (res['read_mb'] + res_before['read_mb'])/2.0
	    res['read_vol'] = (res['read_vol'] + res_before['read_vol'])/2.0
	    res['write_vol'] = (res['write_vol'] + res_before['write_vol'])/2.0
        try:
            #self.conn.publish('CloudInfo',json.dumps(list(self._realtime)[-1:]))
            self.conn.publish('CloudInfo',json.dumps([res]))
	except Exception as e:
	    print e
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
	self._vol_rbytes = 0
        self._vol_wbytes = 0
        self._ifaces = network.ifaces().values()

    def _rest_loc(self):
        journals = []
        disks, raids, vols, inis, fs = [], [], [], [], []

        lm = LocationMapping()
        dsus = [{'location': dsu, 'support_disk_nr': nr} for dsu, nr in lm.dsu_list.items()]

        for disk_db in db.Disk.select():
            disk = {}
            if disk_db.health == 'down' and disk_db.role == 'unused' or disk_db.location == '':
                continue
            else:
                disk['dev_name'] = disk_db.dev_name
                disk['host'] = disk_db.host
                disk['health'] = disk_db.health
                disk['location'] = disk_db.location
                disk['cap_sector'] = disk_db.cap_sector
                disk['cap_mb'] = disk_db.cap_sector/1024/2.0
                disk['role'] = disk_db.role
                try:
                    disk['raid'] = disk_db.raid.name
                except:
                    disk['raid'] = ''
                disk['id'] = disk_db.uuid
                disk['sn'] = disk_db.sn
                disk['model'] = disk_db.model
                disk['vendor'] = disk_db.vendor
            disks.append(disk)


        for raid_db in db.Raid.select():
            raid = {}
            if not raid_db.deleted:
                raid['name'] = raid_db.name
                raid['id'] = raid_db.uuid
                raid['chunk_kb'] = raid_db.chunk_kb
                raid['level'] = raid_db.level
                raid['health'] = raid_db.health
                raid['cap_mb'] = raid_db.cap*1024*1024*2
                raid['cap_sector'] = raid_db.cap*1024
                raid['used_cap_mb'] = raid_db.used_cap*1024
                raid['used_cap_sector'] = raid_db.used_cap*1024*1024*2
                raid['rqr_count'] = raid_db.rqr_count
                raids.append(raid)

        for vol_db in db.Volume.select():
            vol = {}
            if not vol_db.deleted:
                vol['name'] = vol_db.name
                vol['health'] = vol_db.health
                vol['used'] = vol_db.used
                vol['cap_sector'] = vol_db.cap*1024*1024*2
                vol['cap_mb'] = vol_db.cap*1024
                vol['id'] = vol_db.uuid
                try:
                    for i in db.RaidVolume.select():
                        if i.volume.uuid == vol_db.uuid:
                            vol['owner'] = i.raid.name
                except:
                    vol['owner'] = ''
                vols.append(vol)

        for ini_db in db.Initiator.select():
            ini = {}
            ini['wwn'] = ini_db.wwn
            ini['id'] = ini_db.wwn
            ini['volumes'] = []
            ini['portals'] = []
            for i in db.InitiatorVolume.select():
                if i.initiator.wwn == ini_db.wwn:
                    ini['volumes'].append(i.volume.name)
            for j in db.NetworkInitiator.select():
                if j.initiator.wwn == ini_db.wwn:
                    ini['portals'].append(j.eth)
            ini['active_session'] = False      #!!

            inis.append(ini)

        for fs_db in db.XFS.select():
            f = {}
            f['id'] = fs_db.uuid
            f['type'] = fs_db.type
            f['name'] = fs_db.name
            try:
                f['volume'] = fs_db.volume.name
            except:
                f['volume'] = ''
            fs.append(f)

        for i in db.Journal.select():
            journals.append(dict(message=i.message,created_at=int(i.created_at.strftime('%s')),level=i.level))

        loc = dict(dsus=dsus,disk=disks,raid=raids,volume=vols,initiator=inis,filesystem=fs,journal=journals)

	return loc
	
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
                if 'bond'  in iface.name:
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
        except Exception as e:
            print e
            return 0,0

    def _stat_devices_flow(self):
        try:
            rsum, wsum = 0, 0
            r, w = 0, 0
            df = os.popen("iostat")
            lines = df.readlines()
	    interval = time.time() - self._timestamp

            for line in lines:
                if 'md' in line:
		    rsum += int(line.split()[-2])
	            wsum += int(line.split()[-1])
	            if self._vol_rbytes <> 0:
	                r = rsum - self._vol_rbytes
	            if self._vol_wbytes <> 0:
	                w = wsum - self._vol_wbytes
	    self._vol_rbytes = rsum
	    self._vol_wbytes = wsum
	    
            return self._format_nr(r/interval/1024), self._format_nr(w/interval/1024)
        except Exception as e:
            print e
            return 0,0

    '''def _stat_devices_flow(self):
        try:
            rsum, wsum = 0, 0
            r, w = 0, 0

            total = psutil.disk_io_counters(perdisk=True)
            for i in total:
                if 'md' in i:
                    rsum = total[i].read_bytes
                    wsum = total[i].write_bytes

            interval = time.time() - self._timestamp

            if self._vol_rbytes <> 0:
                r = rsum - self._vol_rbytes
            if self._vol_wbytes <> 0:
                w = wsum - self._vol_wbytes
            self._vol_rbytes = rsum
            self._vol_wbytes = wsum

            return self._format_nr(r/interval/1024/1024), self._format_nr(w/interval/1024/1024)
        except Exception as e:
            print e
            return 0,0'''


    def _stat_cache(self):
        try:
            tpath = '/sys/fs/rdcache/cache-!dev!md0/blk_total_nr' 
            self._cache_tbytes = float(open(tpath).read())
            upath = '/sys/fs/rdcache/cache-!dev!md0/blk_used_nr'
            self._cache_ubytes = float(open(upath).read())
            return self._cache_tbytes,self._cache_ubytes
        except Exception as e:
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

    def _stat_fs(self):
	result =[]
        df = os.popen("df")
        lines = df.readlines()
        for i in lines:
            for vol_db in db.Volume.select():
                if vol_db.name in i and vol_db.deleted == 0 and vol_db.used:
                    result.append(self._stat_df_temp(i,vol_db.name))
	return result

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

    def _stat_df_temp(self,line,name):
        val = [val for val in line.split(" ") if val]
        tmp_name = name
        tmp_total = float(val[2]) + float(val[3])
        tmp_used = float(val[3])
        tmp_used_per = float(val[4][:-1])
	return dict(name=tmp_name, total=tmp_total, available=tmp_used, used_per=tmp_used_per)

    def _stat_weed_cpu(self):
   	total = 100.0
        weed_cpu_used = 0.0
        name = 'weed_cpu'
        _used_per = psutil.cpu_percent(0)
	available = total - _used_per
        try:
            cpu = commands.getoutput("top -b -n 1 | grep 'weed'")
	    if len(cpu) >0:
                for line in cpu.split('\n'):
        	    weed_cpu_used += float(line.split()[8])/float(cpu_count())
	except Exception as e:
            print e
	return dict(name=name, total=total, available=available, used_per=weed_cpu_used)

    def _stat_weed_mem(self):
        name = 'weed_mem'
        vm = psutil.virtual_memory()
	total = self._format_nr(float(vm.total)/1024/1024/1024)
	available = self._format_nr(float(vm.total-vm.used)/1024/1024/1024)
        used_per = 0.0
	try:
            weed = commands.getoutput("top -b -n 1 | grep 'weed'")
	    if len(weed) >0:
                for line in weed.split('\n'):
                    used_per += float(line.split()[9])
        except Exception as e:
            print e
	    used_per = 0

        return dict(name=name, total=total, available=available, used_per=used_per)

    def _weed_mem(self, mem):
        if 'g' in mem:
            _mem = float(mem[:-1])
        elif 't' in mem:
            _mem = float(mem[:-1])*1024
        elif 'm' in mem:
            _mem = float(mem[:-1])/1024
        elif 'p' in mem:
            _mem = float(mem[:-1])*1024*1024
        else: 
            _mem = float(mem)/1024/1024
	return _mem

    def _stat_ifaces_flow_dev(self):
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

    def _stat_gateway(self):
        res = []
	speeds = ''
        ifaces = ethtool.get_active_devices()

        for i in ifaces:
	    eth = os.popen("ethtool "+ i).readlines()
	    for j in eth:
		if 'Speed' in j:
		    speeds = j
		    speed = filter(str.isdigit,j)
		    if len(speed) > 0:
                        res.append(dict(name=i,speed=int(speed)))

        return res

    def polls(self):
        mem_total = []
        cpu_total = []

        procs = []
        for p in psutil.process_iter():
            try:
                p.dict = p.as_dict(['username', 'nice',
                                    'get_memory_percent', 'get_cpu_percent',
                                    'name', 'status'])
            except psutil.NoSuchProcess:
                pass
            else:
                procs.append(p)

        # return processes sorted by CPU percent usage
        cpu_processes = sorted(procs, key=lambda p: p.dict['cpu_percent'],
                           reverse=True)[:5]
        mem_processes = sorted(procs, key=lambda p: p.dict['memory_percent'],
                           reverse=True)[:5]
        for i in mem_processes:
            mem_total.append(dict(name=i.dict['name'], used=i.dict['memory_percent']))
        for i in cpu_processes:
            cpu_total.append(dict(name=i.dict['name'], used=i.dict['cpu_percent']))
        return cpu_total, mem_total

    def stat(self):
        iface = ""
        if time.time() - self._timestamp < 1.0:
            return


        cpu = psutil.cpu_percent(0)
        vm = psutil.virtual_memory()
        temp = self._stat_temp()
        mem = vm.percent
        mem_total = vm.total
	cpu_process, mem_process =self.polls()

        r, w = self._stat_flow()
        fr,fw = self._stat_fs_flow()
        #_nr,_nw = self._stat_ifaces_flow()       #Yan 0.7 storage
	#nr,nw = 0.7*_nr, 0.7*_nw
        nr,nw = self._stat_ifaces_flow()       # storage
#        nr,nw = self._stat_ifaces_flow_dev()				#export
        rvol,wvol = self._stat_devices_flow()
	df = self._stat_df()
	rd_t,rd_u = self._stat_cache()
	iface = self.get_ip_address()
	fs = self._stat_fs()

	#Yan
	df.append(self._stat_weed_cpu())
	df.append(self._stat_weed_mem())
	gate = self._stat_gateway()
	
	#rest
        loc = self._rest_loc()
        timestamp = self._format_nr(self._timestamp)
        self._timestamp = time.time()
        sample = {'ip' : iface,
		  'dev' : 'storage',
		  'cpu' : cpu,
                  'mem' : mem,
                  'mem_total' : mem_total,
                  'temp': temp,
                  #'read_mb': r,
                  #'write_mb': w,
                  #'fread_mb': fr,
                  #'fwrite_mb': fw,
                  'read_mb': nr, 	#nread MB/s
                  'write_mb': nw,       #      MB/s
                  'timestamp': timestamp,
                  'df':df,              #KB
		  'cache_total': rd_t,
		  'cache_used': rd_u,
                  'read_vol': rvol,	#MB/s
                  'write_vol': wvol,	#MB/s
		  'loc': loc,
		  'gateway': gate,
		  'fs': fs,
		  'process': dict(cpu=cpu_process, mem=mem_process)
                  }
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
