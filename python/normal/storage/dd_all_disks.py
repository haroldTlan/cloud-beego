#!/usr/bin/env python
import multiprocessing as mp
import lm
import log
from util import execute
from caused import caused

def dd_dev(dev):
    log.info('start to dd dev %s' % dev)
    try:
        execute('dd if=/dev/zero of=/dev/%s bs=128K' % dev)
    except Exception as e:
         log.error(caused(e).detail)
    log.info('complete to dd dev %s' % dev)


def main():
    log.info('start to dd all devs')
    mapping = lm.LocationMapping().mapping
    pool = mp.Pool(processes=len(mapping.keys()))
    for dev in mapping.values():
        pool.apply_async(dd_dev, (dev,))
    pool.close()
    pool.join()
    log.info('complete to dd all devs')

if __name__ == '__main__':
    main()
