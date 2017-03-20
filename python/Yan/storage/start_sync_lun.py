#!/usr/bin/env python
import sync_lun
import getopt
import sys
from unit import GB, MB, KB, Sector, Unit

DEFAULT_TOTAL_PER_WRITE = GB(16)
DEFAULT_SLEEP_SEC = 1

def main():
    optmap = dict(getopt.getopt(sys.argv[1:], 's:w:n:')[0])
    try:
        sleep_sec = float(optmap['-s'])
    except:
        sleep_sec = DEFAULT_SLEEP_SEC
    try:
        tpw = Unit(optmap['-w'])
    except:
        tpw = DEFAULT_TOTAL_PER_WRITE    

    lun_name = optmap['-n']

    sync_lun.zero_volume(lun_name, tpw, sleep_sec)

if __name__ == '__main__':
    main()
