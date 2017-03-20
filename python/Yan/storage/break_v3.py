#!/usr/bin/env python

import adm
import time
from util import *
import sys

def make_raid_break(raid_name):
    r = adm.Raid.lookup(name=raid_name)

    execute('echo 1 > /sys/module/rqr/parameters/io_err')
    time.sleep(5)

    execute('hexdump -C /dev/%s' % r.dev_name)
    time.sleep(3)

    print "the raid %s will be failed" % raid_name
    
    while True:
        try:
            cmd = "echo 'use speediodb; select * from raids;' | mysql -uroot -ppasswd | grep %s | grep failed" % r.uuid
            _, o = execute(cmd)
            if o == '':
                continue
            else:
                break
        except:
            pass

    time.sleep(5)
    for d in adm.Disk.all():
        if d.raid and d.raid.uuid == r.uuid and d.health == 'down':
            d.save(health='failed', role='kicked')

    time.sleep(8)
    print "the raid %s is failed" % raid_name

if __name__ == "__main__":
    make_raid_break(sys.argv[1])
