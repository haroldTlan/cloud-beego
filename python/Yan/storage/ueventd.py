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
from uevent import DiskUnplugged, RaidDegraded, RaidFailed

class UEventSvr(mq.IOHandler):
    def __init__(self):
        super(UEventSvr, self).__init__()
        self.sock = mq.socket(mq.PULL, 'uevent_svr')
        uevent.UEvent.bind_pub_socket()

    @property
    def fd(self):
        return self.sock

    def handle_in(self, e):
        try:
            o = self.sock.recv_json()
            if len(o) is 0:
                return

            u = uevent.get(o)
            print 'get: %s' % u.event_obj
            u.publish()
        except:
            tb.print_exc()
            return

class UEventDaemon(Daemon):
    def init(self):
        self.poller = mq.Poller()
        self.usvr = UEventSvr()
        self.poller.register(self.usvr)

    def _run(self):
        print 'ueventd(%s) is running...' % os.getpid()

        while True:
            self.poller.poll()


if __name__ == "__main__":
    main(config.ueventd.pidfile, UEventDaemon)
