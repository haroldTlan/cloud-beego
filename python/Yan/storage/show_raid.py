#!/usr/bin/env python
import lm
from util import execute
from unit import Sector
import adm
import sys
import os

def dm_name(dm_path):
    try:
        return os.path.split(dm_path)[1]
    except:
        return ''

def main():
    if len(sys.argv) == 1:
        print 'usage: show_raid.py raid-name'
        return

    try:
        name = sys.argv[1]
        raid = adm.Raid.lookup(name=name)
    except:
        print '%s not found.' % name
        sys.exit(1)

    if not raid.online:
        print '%s is offline' % name
        return

    role_map = { adm.ROLE_DATA: 'D',
                 adm.ROLE_SPARE: 'S',
                 adm.ROLE_DATA_SPARE: 'DS' }
    online_map = { True: 'o', False: '' }
    print 'raid %s' % name
    for sraid in raid.subraids:
        print '%s: %s' % (sraid.dev_name, ' '.join(['%s(%s)[%s,%s]' %\
                (p.dev_name, dm_name(p.dm_path), role_map[p.role], online_map[p.online])\
                for p in sraid.parts]))

if __name__ == '__main__':
    main()
