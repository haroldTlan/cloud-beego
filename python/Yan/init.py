#!/usr/bin/env python
import adm
import glob
import os
import re
import lm

def main():
    m = lm.LocationMapping()
    for loc, dev in m.mapping.items():
        print 'init disk %s' % dev
        os.system('dd if=/dev/zero of=/dev/%s bs=1M count=12 oflag=direct' % dev)
        os.system('sync')

    os.system('mysql -uroot -ppasswd < preinit/create_db.sql')
    os.system('mysql -uroot  < preinit/create_db.sql')

if __name__ == '__main__':
    main()
