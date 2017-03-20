#!/usr/bin/env python
import sys
import os

def main():
    dev = sys.argv[1]
    os.system('echo "EVENT:DISK@REMOVE=%s" > /sys/kernel/kobject_example/event_name' % dev)

if __name__ == '__main__':
    main()
