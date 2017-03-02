#!/usr/bin/env python
import lm
from util import execute
from unit import Sector

def main():
    loc = lm.LocationMapping()
    m = loc.mapping
    dsu = loc.dsu_list
    keys = sorted(m.keys())
    print dsu
    for k in keys:
        _, o = execute('blockdev --getsz /dev/%s' % m[k])
        print '%s: %s %s' % (k, m[k], Sector(o).fit())

if __name__ == '__main__':
    main()
