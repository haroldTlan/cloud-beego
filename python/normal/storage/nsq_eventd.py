#!/usr/bin/env python
import os
import sys
import traceback as tb
import time
import json
from env import config
import sys, time
from daemon import Daemon, main
import adm
import re
import mq
import socket
import uevent
from db import with_db

import gnsq
import network

class UserspaceEventSub(mq.Subscriber, mq.IOHandler):
    def __init__(self, pub):
        super(UserspaceEventSub, self).__init__('notification')
        self.pub = pub

    @property
    def fd(self):
        return self._socket

    def handle_in(self, e):
        o = self.recv()
        if len(o) is 0:
            return
        print o
        self.pub.send_json(o)

class UEventSub(mq.Subscriber, mq.IOHandler):
    def __init__(self, pub, conn):
        super(UEventSub, self).__init__('uevent_pub')
        self.pub = pub
        self.conn = conn
        self.watched_raids = {}
        self.watched_luns = {}

    @property
    def fd(self):
        return self._socket

    @with_db
    def handle_in(self, e):
        patmap = {uevent.DiskIOError.event_name          : self.send_json,
                  uevent.DiskUnplugged.event_name        : self.send_json,
                  uevent.DiskPlugged.event_name          : self.send_json,
                  uevent.DiskFormated.event_name         : self.send_json,
                  uevent.DiskRoleChanged.event_name      : self.send_json,
                  uevent.RaidNormal.event_name           : self.send_json,
                  uevent.RaidDegraded.event_name         : self.send_json,
                  uevent.RaidFailed.event_name           : self.send_json,
                  uevent.RaidRebuilding.event_name       : self._raid_rebuild,
                  uevent.RaidRebuildCompleted.event_name : self._raid_rebuild_completed,
                  uevent.RaidCreated.event_name          : self.send_json,
                  uevent.RaidRemoved.event_name          : self.raid_removed,
                  uevent.VolumeNormal.event_name         : self.send_json,
                  uevent.VolumeFailed.event_name         : self.send_json,
                  uevent.VolumeCreated.event_name        : self.send_json,
                  uevent.VolumeRemoved.event_name        : self.lun_removed,
                  uevent.VolumeSyncing.event_name        : self._lun_sync,
                  uevent.InitiatorCreated.event_name     : self.send_json,
                  uevent.InitiatorRemoved.event_name     : self.send_json,
                  uevent.VIMapped.event_name             : self.send_json,
                  uevent.VIUnmapped.event_name           : self.send_json,
                  uevent.FSCreated.event_name            : self.send_json,
                  uevent.FSRemoved.event_name            : self.send_json,
                  uevent.MonFSCreated.event_name         : self.send_json,
                  uevent.MonFSRemoved.event_name         : self.send_json,
                  uevent.UserLogin.event_name            : self.send_json}

        o = self.recv()
        if len(o) is 0:
            return

        for e in patmap:
            try:
                if o['uevent'] == e:
                    patmap[e](o)
            except:
                pass

    def get_ip_address(self):
        INTERFACE = ['eth0','br0','eth1','br1']
        ifaces = network.ifaces().values()
        for i in INTERFACE:
            for j in ifaces:
                if j.name == i and j.link:
                    return j.ipaddr

    def send_json(self, o):
        o['event'] = o['uevent']
        del o['uevent']
        o['ip'] = self.get_ip_address()
        result = json.dumps(o)
        print 'send json: %s' % result
        self.conn.publish('CloudEvent', str(result))


    def send_nsq(self, o):
        o['ip'] = self.get_ip_address()
        result = json.dumps(o)
        print 'send json: %s' % result
        self.conn.publish('CloudEvent', str(result))

    def _raid_rebuild(self, o):
        try:
            raid = adm.Raid.lookup(uuid=o['uuid'])
            e = {'event': 'raid.rebuild', 'raid':raid.uuid, 'health':raid.health, 'rebuilding': raid.rebuilding, 'rebuild_progress': 0}
            #self.pub.send_json(e)
            #if raid.support_rebuilding:
            self.watched_raids[raid.uuid] = (raid, 0)
            print e
            self.send_nsq(e)
        except:
            pass

    def _raid_rebuild_completed(self, o):
        try:
            raid = adm.Raid.lookup(uuid=o['uuid'])
            e = {'event': 'raid.rebuild_done', 'raid':raid.uuid, 'health':raid.health, 'rebuilding': raid.rebuilding, 'rebuild_progress': raid.rebuild_progress}
            self.pub.send_json(e)
            if self.watched_raids.has_key(raid.uuid):
                del self.watched_raids[raid.uuid]
            print e
            self.send_nsq(e)
        except:
            pass

    def raid_removed(self, o):
        if self.watched_raids.has_key(o['uuid']):
            del self.watched_raids[o['uuid']]
        self.send_json(o)

    def _lun_sync(self, o):
        try:
            print 'start sync'
            volume = adm.Volume.lookup(uuid=o['uuid'])
            e = {'event': 'volume.sync', 'lun':volume.uuid, 'sync_progress': volume.sync_progress, 'syncing': True}
            self.pub.send_json(e)
            self.watched_luns[volume.uuid] = (volume, 0)
            print e
            self.send_nsq(e)
        except:
            pass

    def lun_removed(self, o):
        if self.watched_luns.has_key(o['uuid']):
            del self.watched_luns[o['uuid']]
        self.send_json(o)

    def elapse(self):
        try:
            for u, (raid, prev) in self.watched_raids.items():
                if not raid.online:
                    del self.watched_raids[u]
                elif raid.rebuilding:
                    if prev <> raid.rebuild_progress:
                        e = {'event': 'raid.rebuild', 'raid':raid.uuid, 'health':raid.health, 'rebuilding': raid.rebuilding, 'rebuild_progress': raid.rebuild_progress}
                        self.pub.send_json(e)
                        self.watched_raids[u] = (raid, raid.rebuild_progress)
			print e
                        self.send_nsq(e)
                        print e

            for u, (lun, prev) in self.watched_luns.items():
                time.sleep(1)
                if lun.syncing:
                    if prev <> lun.sync_progress:
                        e = {'event': 'volume.syncing', 'lun':lun.uuid, 'sync_progress': lun.sync_progress, 'syncing': True}
                        self.pub.send_json(e)
                        self.watched_luns[u] = (lun, lun.sync_progress)
                        print e
                        self.send_nsq(e)
                else:
                    ee = {'event': 'volume.sync_done', 'lun':lun.uuid, 'sync_progress': lun.sync_progress, 'syncing': False}
                    self.pub.send_json(ee)
                    print ee
                    self.send_nsq(ee)
                    if self.watched_luns.has_key(lun.uuid):
                        del self.watched_luns[lun.uuid]
        except:
            pass


class KernelEventSub(mq.IOHandler):
    def __init__(self, pub):
        self._sock = socket.socket(socket.AF_NETLINK, socket.SOCK_DGRAM, 11)
        self._sock.bind((0,-1))
        self._pub = pub

    @property
    def fd(self):
        return self._sock.fileno()

    @with_db
    def handle_in(self, e):
        patmap = { 'EVENT:DISK@RQR=([^\[]+)\[(\d+)\]'   : self._disk_rqr,
                   'EVENT:TARGET@CHANGE=([_a-zA-Z][-.:_a-zA-Z0-9]*)' : self._initiator_session_change}

        msg = self._sock.recv(256)
        for pat, action in patmap.items():
            try:
                m = re.search(pat, msg)
                if m:
                    action(*m.groups())
                    return
            except:
                pass

    def _disk_rqr_demo(self, stub, count):
        print 'rqr demo %s' % stub
        #try:
        #    part = adm.Part.lookup(stub_dev='md1001')
        #except:
        #    return

        #self._handle_rqr_count(part.dev_name, count)
        self._handle_rqr_count('/dev/mapper/rqr-sdb1', count)

    def _handle_rqr_count(self, dev_name, count):
        try:
            part = adm.Part.lookup(dev_name=dev_name)
            if part.rqr_count <> count:
                part.save(rqr_count=count)

            disk = part.disk
            total = sum(part.rqr_count for part in disk.parts)
            if disk.rqr_count <> total:
                disk.save(rqr_count = total)

            raid = disk.raid
            if not raid: return

            total = sum(disk.rqr_count for disk in raid.disks)
            if raid.rqr_count <> total:
                raid.save(rqr_count=total)

            if count >= config.raid.rqr.low_warning_count:
                e = {'event': 'disk.rqr', 'disk':disk.uuid, 'rqr_count':disk.rqr_count}
                self._pub.send_json(e)
                print e

            e = {'event': 'raid.rqr', 'raid':raid.uuid, 'rqr_count':raid.rqr_count}
            self._pub.send_json(e)
            print e
        except Exception as e:
            print e
            pass

    def _disk_rqr(self, dev_path, count):
        if dev_path == 'md1001':
            self._disk_rqr_demo(dev_path, count)
            return

        m = re.search('(sd\w+)', dev_path)
        name = m.group(1) if m else ''
        self._handle_rqr_count(name, count)

    def _initiator_session_change(self, wwn):
        try:
            print 'initiator.session_change'
            initr = adm.Initiator.lookup(wwn=wwn)
            e = {'event': 'initiator.session_change', 'initiator':wwn, 'session':initr.active_session}
            self._pub.send_json(e)
            print e
        except:
            pass

class EventDaemon(Daemon):
    def init(self):
        self.poller = mq.Poller()
        conn = gnsq.Nsqd(address=config.zoofs.ip, http_port=4151)
	self.conn = conn
        pub = mq.pub_socket('eventd')
        self.ksub = KernelEventSub(pub)
        self.usub = UserspaceEventSub(pub)
        self.uevent = UEventSub(pub, conn)
        self.poller.register(self.ksub)
        self.poller.register(self.usub)
        self.poller.register(self.uevent)

    def _run(self):
        print 'NSQ_eventd(%s) is running...' % os.getpid()
	filename = '/home/monitor/rpc.log'
	file = open(filename,'r')

	#Find the size of the file and move to the end
	st_results = os.stat(filename)
	st_size = st_results[6]
	file.seek(st_size)

        while True:
            self.poller.poll(config.nsq_eventd.poll_timeout_secs*1000)
            self.uevent.elapse()

            where = file.tell()
            line = file.readline()
            if not line:
                time.sleep(1)
                file.seek(where)
            else:
                self.monitor(line)	    

    def monitor(self,line):
	print line,
	self.publish(line,)

    def get_ip_address(self):
        INTERFACE = ['eth0','br0','eth1','br1']
        ifaces = network.ifaces().values()
        for i in INTERFACE:
            for j in ifaces:
                if j.name == i and j.link:
                    return j.ipaddr

    def publish(self, result):
	o={}
	try:
    	    a=json.loads(result.replace("\n",""))
	except:
	    pass
	print a['event']
        o['event'] = a['event']
        o['ip'] = self.get_ip_address()
	o['detail'] = a['detail']
	o['result'] = a['status']
	try:
            result = json.dumps(o)
	except:
	    pass
        print 'send json: %s' % result
        self.conn.publish('CloudEvent', str(result))

if __name__ == "__main__":
    main(config.nsq_eventd.pidfile, EventDaemon)
