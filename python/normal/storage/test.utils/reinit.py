#!/usr/bin/env python
import os
import sys
sys.path.append('..')
import api
import glob
import adm

def stop(path):
    if os.path.exists(path):
        cmd = 'echo 1 > %s'%path
        os.system(cmd)

os.system('losetup -d /dev/loop*')
#stop('/sys/fs/bcache/37cc9798-b654-4bf5-bc5e-e140c850acb8/stop')
#for md in glob.glob('/sys/block/'):
#for r in adm.Raid.all():
#    r.delete()
os.system('mdadm --stop /dev/md*')
os.system('rm /home/zonion/vg/* -rf')
os.system('rm /home/zonion/bitmap/* -rf')
os.system('../init_disk.py')
os.system('../boot.py')

cxt = api.APIContext()
cxt.reload_rqueue()
#os.system('echo "raid create name=rd raid-disks=1.1.2,1.1.3,1.1.4 spare-disks=1.1.5\nq\n" | ../speedcli.py')
#os.system('echo "raid create name=rd raid-disks=1.1.2,1.1.3,1.1.4\nq\n" | ../speedcli.py')
