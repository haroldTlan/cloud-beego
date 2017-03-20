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
        disk = adm.Disk(dev_name=dev)
        disk.remove_dev()
        
if __name__ == '__main__':
    main()
