#!/usr/bin/env python
import sys
import pickle
import os
import time
from rtslib.utils import is_dev_in_use
import sys
sys.path.append('..')
import adm

SETTINGS_PATH = '/test-data/settings'

if not os.path.exists('/test-data'):
    os.mkdir('/test-data')

def load_settings():
    if not os.path.exists(SETTINGS_PATH):
        save_settings({})

    return pickle.load(open(SETTINGS_PATH, 'r'))

def save_settings(settings):
    pickle.dump(settings, open(SETTINGS_PATH, 'w'))

def change(dev, no):
    s = os.stat('/dev/%s%s' % (dev, no))
    major = os.major(s.st_rdev)
    minor = os.minor(s.st_rdev)

    os.system('echo "EVENT:DISK@CHANGE=%s:%s" > /sys/kernel/kobject_example/event_name' % (major, minor))

def main():
    settings = load_settings()
    if 'alias' in sys.argv:
        alias = sys.argv[2]
        dev = sys.argv[3]

        s = os.stat('/dev/%s' % dev)
        major = os.major(s.st_rdev)
        minor = os.minor(s.st_rdev)

        settings[alias] = (dev, major, minor)
        save_settings(settings)
    elif 'remove' in sys.argv: 
        dev,_,_ = settings[sys.argv[2]]
        disk = adm.Disk.lookup(dev_name=dev)
        os.system('../remove_disk.py %s' % dev)
        time.sleep(5)
        os.system('rm /dev/%s -rf' % dev)
    elif 'add' in sys.argv:
        dev,major,minor = settings[sys.argv[2]]
        os.system('mknod /dev/%s b %s %s' % (dev, major, minor))
        time.sleep(0.1)
        os.system('../add_disk.py %s' % dev)
    elif 'change' in sys.argv:
        dev,major,minor = settings[sys.argv[2]]
        change(dev, sys.argv[3])
    elif 'reinit' in sys.argv:
        os.system('./reinit.py')
    elif 'unalias' in sys.argv:
        del settings[sys.argv[2]]
        save_settings(settings)
    elif 'show' in sys.argv:
        try:
            if sys.argv[2] == 'all':
                for k, v in settings.items():
                    print '%s=%s' % (k, v[0])
            else:
                print '%s=%s' % (sys.argv[2], settings[sys.argv[2]][0])
        except:
            print '%s not in settings' % sys.argv[2]
    elif 'reset' in sys.argv:
        save_settings({})
        
if __name__ == '__main__':
    main()
