#!/usr/bin/env python
import adm
import glob
import os
import re
import db
import lm

def main():
    m = lm.LocationMapping()
    for loc, dev in m.mapping.items():
        try:
            disk = adm.Disk(dev_name=dev)
            disk.remove_dev()
        except:
            pass
        
        print 'init disk %s' % dev
        os.system('dd if=/dev/zero of=/dev/%s bs=1M count=16 oflag=direct' % dev)

    db.drop_data()

if __name__ == '__main__':
    main()
