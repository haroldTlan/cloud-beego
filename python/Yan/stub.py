#!/usr/bin/env python
import sys
import os
import re
from util import execute

# mdadm -CR /dev/md0 -lfaulty -n1 /dev/xxx 


def stub_w(path, off, c):
    cmd = 'mdadm -G %s -p wp1' % (path)
    print cmd
    _, o = execute(cmd)
    for i in range(0,c):
        cmd = 'dd if=/dev/zero of=%s bs=1b count=1  oflag=direct seek=%s' % (path, off+i)
        print cmd
        os.system(cmd)
        i = i+1

    cmd = 'mdadm -G %s -p none' % (path)
    print cmd
    _, o = execute(cmd)

def stub_r(path, off, c):
    cmd = 'mdadm -G %s -p rp1' % (path)
    print cmd
    _, o = execute(cmd)
    for i in range(0,c):
        cmd = 'dd of=/dev/zero if=%s bs=1b count=1 iflag=direct skip=%s' % (path, off+i)
        print cmd
        os.system(cmd)
        i = i+1

    cmd = 'mdadm -G %s -p none' % (path)
    print cmd
    _, o = execute(cmd)

def clear_stub(path):
    cmd = 'mdadm -G %s -p flush' % path
    _, o = execute(cmd)
    print o

def get_map_info():
    map = {}
    map_dev = {}
    cmd = 'ls /sys/block/|grep dm-'
    _, o = execute(cmd)
    dm = o.strip('\n').split('\n')
    for i in range(0,len(dm)): 
        cmd = 'cat /sys/block/%s/dm/name' % dm[i]
        _, oo = execute(cmd)
        map[dm[i]] = oo.strip('\n')
        cmd = 'cat /sys/block/%s/dev' % dm[i]
        _, oo = execute(cmd)
        map_dev[oo.strip('\n')] = dm[i]
    return map, map_dev
        

def get_data_info(dev, lba):
    map, map_dev = get_map_info()
    lba = int(lba)
    dict = {}
    cmd = 'mdadm -D %s' % (dev)
    _, o = execute(cmd)

    tmp = re.findall('.+active sync.+', o)
    for s in tmp:
        m = re.findall('.+?(\d+)\s+\sactive sync\s+/dev/(.+)', s)
        dict[int(m[0][0])] = m[0][1]

    chunk = re.search('Chunk Size : (\d+)K', o).group(1)
    ck = int(chunk)*2
    raid_disk = re.search('Raid Devices : (\d+)', o).group(1)
    r_d = int(raid_disk)
    d_d = r_d-1
    ck_offset=lba%ck
    ck_num=lba/ck
    stripe=ck_num/d_d
    idx=ck_num%d_d
    pd_idx=d_d-stripe/r_d
    idx=(pd_idx+1+idx)%r_d
    disk_lba=stripe*ck+ck_offset
    path = dev.split('/')
    ss = 'cat /sys/block/%s/md/*/offset' % (path[2])
    _, oo = execute(ss)
    d_offset = int(oo.split('\n')[0])
    print 'data_disk[%s] pd_disk[%s] lba[%s]' % (map[dict[idx]], map[dict[pd_idx]], disk_lba+d_offset)
    print disk_lba, d_offset
    ss = 'dmsetup table /dev/mapper/%s' % map[dict[idx]]
    _, oo = execute(ss)
    mm = re.search('.+?(\d+:\d+).+', oo).group(1)
    mm_dict = {}
    ss = 'cat /proc/partitions |grep md'
    _, oo = execute(ss)
    mmm = oo.strip('\n').split('\n')
    for i in range(0,len(mmm)): 
        l = mmm[i].split() 
        mm_dict[l[0]+':'+l[1]] = l[3]

    mm = '9:1001'
    if mm_dict.has_key(mm):
        return '/dev/'+mm_dict[mm], disk_lba+d_offset+2048

    print 'not correct stub disk: RaidDevice[%s] --> %s' % (idx, map[dict[idx]])
    return '', 0



if __name__ == "__main__":
	rw=sys.argv[1]
	if rw == 'P':
	    map = get_map_info()
	    print map 
	    exit()


	dev=sys.argv[2]
	if rw == 'C':
	    clear_stub(dev)
	    exit()


	n = len(sys.argv)
	if n != 5:
	    print 'param: rw dev lba count'
	    exit()

	lba=sys.argv[3]
	count=sys.argv[4]

	    


	disk, addr = get_data_info(dev, lba)
	if disk:
	    c=int(count)
	    if rw == 'c':
		clear_stub(disk)
	    elif rw == 'r':
		stub_r(disk, addr, c)
	    else:
		stub_w(disk, addr, c)
	else:
	    print 'please check lba!!!!!'




