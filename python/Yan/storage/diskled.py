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
from util import execute
import uevent
import lm
import log
from beepd import *

class LEDCtrl(object):
    def __init__(self):
        self.enabled = False
        cmd = "ls /sys/class/scsi_host/ | wc -l"
        _,o = execute(cmd, False, logging=False)
        if int(o.strip('\n')) > 10:
            e,_ = execute('led-ctl-daemon -t 3U16-STANDARD', False)
            if e == 0:
                self.enabled = True

    def _ledget(self, led):
        cmd = 'ledget %s' % led
        _,o = execute(cmd, False)
        m = re.search('\[(\d+)\]', o)
        return int(m.group(1)) if m else 0

    def _ensure_ledset(self, op, led):
        for i in range(0, 32):
            cmd = 'ledset %s %s' % (led, op)
            print cmd
            execute(cmd, False)
            status = self._ledget(led)
            if status == op:
                return
            else:
                log.info('leget status: %s, op: %s, sleep and try again' % (status, op))
                time.sleep(0.5)

    def _ledset(self, op, leds):
        if not self.enabled:
            return
        for led in leds:
            self._ensure_ledset(op, led)

    def disk_leds(self, disks):
        leds = []
        for location in disks:
            try:
                ledid = lm.ledmap[location]
                leds.append(ledid)
            except:
                pass
        return leds

    def light_on(self, disks):
        log.info('%s light on' % disks)
        print '%s light on' % disks
        leds = self.disk_leds(disks)
        self._ledset(1, leds)

    def off(self, disks):
        log.info('%s light off' % disks)
        print '%s light off' % disks
        leds = self.disk_leds(disks)
        self._ledset(2, leds)

    def blink(self, disks):
        log.info('%s blink' % disks)
        print '%s blink' % disks
        leds = self.disk_leds(disks)
        self._ledset(5, leds)

    def blink_slow(self, disks):
        log.info('%s blink slow' % disks)
        print '%s blink slow' % disks
        leds = self.disk_leds(disks)
        self._ledset(6, leds)

class UEventSub(mq.Subscriber, mq.IOHandler):
    def __init__(self):
        super(UEventSub, self).__init__('uevent_pub')
        self.ledctrl = LEDCtrl()

    @property
    def fd(self):
        return self._socket

    def handle_in(self, e):
        patmap = {uevent.DiskIOError.event_name          : self._disk_ioerror,
                  uevent.DiskPlugged.event_name          : self._disk_plugged,
                  uevent.DiskUnplugged.event_name        : self._disk_unplugged,
                  uevent.RaidDegraded.event_name         : self._raid_degraded,
                  uevent.RaidFailed.event_name           : self._raid_failed,
                  uevent.RaidRebuilding.event_name       : self._raid_rebuilding,
                  uevent.RaidRebuildCompleted.event_name : self._raid_rebuild_completed,
                  uevent.RaidRemoved.event_name          : self._raid_removed,
                  uevent.SystemReady.event_name          : self._system_ready}

        o = self.recv()
        print o
        if len(o) is 0:
            return

        for e in patmap:
            try:
                if o.get('uevent') == e:
                    patmap[e](o)
            except:
                pass

    def _disk_ioerror(self, o):
        try:
            log.info("diskled handle disk ioerror")
            disk = adm.Disk.lookup(uuid=o['uuid'])
            self.ledctrl.light_on([disk.location])
        except Exception as e:
            print e

    def _disk_plugged(self, o):
        try:
            log.info("diskled handle disk plugged, time: %s" % time.time())
            disk = adm.Disk.lookup(uuid=o['uuid'])
            if disk.role == 'spare' or disk.role == 'global_spare':
                stop_beep('b')
            self.ledctrl.light_on([o['location']])
        except Exception as e:
            print e

    def _disk_unplugged(self, o):
        try:
            log.info("diskled handle disk unplugged, time: %s" % time.time())
            disk = adm.Disk.lookup(uuid=o['uuid'])
            if disk.role == 'spare' or disk.role == 'global_spare':
                start_beep('b')
            self.ledctrl.off([o['location']])
        except Exception as e:
            print e

    def _light_off_raid_disks(self, raid):
        disks = [disk.location for disk in raid.raid_disks]
        self.ledctrl.off(disks)
        time.sleep(2)

    def _raid_degraded(self, o):
        try:
            log.info("diskled handle raid degraded for beep.......")
            start_beep('a')
            #cmd = "nohup bash /home/zonion/command/spk.sh a &"
            #_,o = execute(cmd, False, logging=False)

            raid = adm.Raid.lookup(uuid=o['uuid'])
            self._light_off_raid_disks(raid)

            disks = [disk.location for disk in raid.raid_disks if disk.link and disk.online]
            self.ledctrl.blink_slow(disks)
        except Exception as e:
            print e

    def _raid_failed(self, o):
        try:
            log.info("diskled handle raid failed for beep..........")
            start_beep('d')
            #cmd = "nohup bash /home/zonion/command/spk.sh d &"
            #_,o = execute(cmd, False, logging=False)

            raid = adm.Raid.lookup(uuid=o['uuid'])
            self._light_off_raid_disks(raid)

            disks = [disk.location for disk in raid.raid_disks if disk.link and disk.online]
            self.ledctrl.light_on(disks)
        except Exception as e:
            print e

    def _raid_rebuilding(self, o):
        try:
            log.info("diskled handle raid rebuilding for beep..........")
            start_beep('c')
            raid = adm.Raid.lookup(uuid=o['uuid'])
            self._light_off_raid_disks(raid)

            disks = [disk.location for disk in raid.raid_disks if disk.link and disk.online]
            self.ledctrl.blink(disks)
        except Exception as e:
            print e

    def _raid_rebuild_completed(self, o):
        try:
            log.info("diskled handle raid rebuild completed")
            stop_beep('0')
            #cmd = "bash /home/zonion/command/spk.sh 0"
            #_,o = execute(cmd, False, logging=False)

            raid = adm.Raid.lookup(uuid=o['uuid'])
            self._light_off_raid_disks(raid)

            disks = [disk.location for disk in raid.raid_disks if disk.link and disk.online]
            self.ledctrl.off(disks)
        except Exception as e:
            print e

    def _raid_removed(self, o):
        try:
            log.info("diskled handle raid removed")
            disks = []
            for uuid in o['raid_disks']:
                try:
                    disk = adm.Disk.lookup(uuid=uuid)
                    disks.append(disk.location)
                except:
                    pass

            self.ledctrl.off(disks)
        except Exception as e:
            print e

    def _system_ready(self, o):
        try:
            log.info("diskled handle system ready")
            for raid in adm.Raid.all():
                print raid.name, raid.health
                if raid.health == 'degraded':
                    disks = [disk for disk in raid.raid_disks if disk.link and disk.online]
                    if raid.rebuilding:
                        self.ledctrl.blink(disks)
                    else:
                        self.ledctrl.blink_slow(disks)
                elif raid.health == 'failed':
                    disks = [disk for disk in raid.raid_disks if disk.health <> 'failed' and disk.online]
                    self.ledctrl.light_on(disks)
        except Exception as e:
            print e

class DiskLEDDaemon(Daemon):
    def init(self):
        self.poller = mq.Poller()
        self.usub = UEventSub()
        self.poller.register(self.usub)

    def _run(self):
        print 'diskled(%s) is running...' % os.getpid()

        while True:
            self.poller.poll()
            
 
if __name__ == "__main__":
    main(config.diskled.pidfile, DiskLEDDaemon)
