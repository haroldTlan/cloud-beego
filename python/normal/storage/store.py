#import sys
#sys.path.append('/home/zonion/speedio')
import rest,os,adm
import subprocess
import random
import time

import argparse

parser = argparse.ArgumentParser(description="sample raid, vol, fs setting")
parser.add_argument("-remove", help="default: -remove=all", default=None)
parser.add_argument("-build", help="default: -build=all", default=None)
parser.add_argument("-level", help="default: -level=level", default=None)
parser.add_argument("-loc", help="default: -loc=loc", default=None)
parser.add_argument("-mount", help="default: -mount=mountpoint", default=None)


r = rest.rest()

def delete_all():
    for fs in r.filesystem.list():
        try:
            r.filesystem.delete(fs['name'])
            print 'delete fs: %s'% fs['name']
        except rest.ResponseError as e:
            if e.status == 400 and 'description' in e.content:
                print e.content['description']
            else:
                print 'unkown exception'

    for vol in r.volume.list():
        try:
            r.volume.delete(vol['name'])
            print 'delete volume: %s'% vol['name']

        except rest.ResponseError as e:
            if e.status == 400 and 'description' in e.content:
                print e.content['description']
            else:
                print 'unkown exception'

    for raid in r.raid.list():
        try:
            r.raid.delete(raid['name'])
            print 'delete raid: %s'% raid['name']

        except rest.ResponseError as e:
            if e.status == 400 and 'description' in e.content:
                print e.content['description']
            else:
                print 'unkown exception'

    return 'clear success'

def spare(same):
    count = 0
    free = []

    for k,v in same.items():
        if len(v)<3:
            del(same[k])
        else:
            r_name = 'raid' + str(count)
            v_name = 'volume' + str(count)
            f_name = 'fs' + str(count)
            count += 1
            
            if len(v) == 3:
                free.append(dict(name=r_name, loc=str(','.join(v)), spare='', vol=v_name, fs=f_name))
            else:
                spare = v.pop()
                free.append(dict(name=r_name, loc=str(','.join(v)), spare=spare, vol=v_name, fs=f_name))
 
    return free 

    
def none_spare(same):
    count = 0
    free,temp  = [],[]

    for k,v in same.items():
        if len(v)<3:
            del(same[k])
        else:
            if len(v) >= 3:
                free_disks = zip(*[v[i::3] for i in xrange(3)])
                for free_disk in free_disks:
                    r_name = 'raid' + str(count)
                    v_name = 'volume' + str(count)
                    f_name = 'fs' + str(count)
                    count += 1
                    free.append(dict(name=r_name, loc=str(','.join(free_disk)), spare='', vol=v_name, fs=f_name))
 
    return free 
    
def addDev(level, loc, mountpoint):
    if level == None or loc == None or mountpoint == None:
	print 'nothing happened'
	return

    r.disk.format('all')
    
    count = ''
    for i in range(2):
	count += str(random.randint(0, 9))
    r_name = 'raid' + count
    v_name = 'volume' + count
    f_name = 'fs' + count
    time.sleep(1)

    if True:
        try:
            a=r.raid.create(name=r_name, raid_disks=loc, level=level, chunk='32KB', spare_disks=None, rebuild_priority='low', sync='no')
            print 'success create raid: %s'% r_name
        except rest.ResponseError as e:
            if e.status == 400 and 'description' in e.content:
	        print e.content['description']
                return False, e.content['description']
            else:
                print 'unkown exception'
                return False, 'unkown exception'

        try:
            r.volume.create(name=v_name, raid=r_name, capacity='all')
            print 'success create volume: %s'% v_name
        except rest.ResponseError as e:
            if e.status == 400 and 'description' in e.content:
                print e.content['description']
                return False, e.content['description']
            else:
                print 'unkown exception'
                return False, 'unkown exception'

        try:
            fs = adm.XFS(name=f_name, mountpoint=mountpoint)
            fs.volume = adm.Volume.lookup(name=v_name)
            fs.create()
            print 'success create filesystem: %s'% f_name
	    return True, 'success'
        except rest.ResponseError as e:
            if e.status == 400 and 'description' in e.content:
                print e.content['description']
                return False, e.content['description']
            else:
                print 'unkown exception'
                return False, 'unkown exception'

def quick_create():
    disk = r.disk.list()
        
    free, same = [],{}
 
    for i in disk:
        cap = i['cap_sector']
        loc = i['location']
        if same.has_key(cap) and 'unused' in i['role']:
            same[cap].append(loc)
        else:
            same[cap]=[]
            same[cap].append(loc)

    free = none_spare(same)

    r.disk.format('all')
    if not free:
	print envCheck()
        #print 'no free disks'
        return

    for gro in free:
        try:
            r.raid.create(name=gro['name'], raid_disks=gro['loc'], level=5, chunk='32KB', spare_disks=gro['spare'], rebuild_priority='low', sync='no')
            print 'success create raid: %s'% gro['name']
        except rest.ResponseError as e:
            if e.status == 400 and 'description' in e.content:
                return e.content['description']
            else:
                print 'unkown exception'
                return

        try:
            r.volume.create(name=gro['vol'], raid=gro['name'], capacity='all')
            print 'success create volume: %s'% gro['vol']
        except rest.ResponseError as e:
            if e.status == 400 and 'description' in e.content:
                print e.content['description']
                return
            else:
                print 'unkown exception'
                return

        try:
            r.filesystem.create(name=gro['fs'], volume=gro['vol'], type='xfs')
            print 'success create filesystem: %s'% gro['fs']
        except rest.ResponseError as e:
            if e.status == 400 and 'description' in e.content:
                print e.content['description']
                return
            else:
                print 'unkown exception'
                return

    return 'build success'

def envCheck():
    p1 = subprocess.Popen(['df |grep /nvr/d'],shell=True ,stdout=subprocess.PIPE) 

    lines = p1.stdout.readlines()
    if len(lines) != 0 :
        return 'success'
    else:
        return 'failed'


if __name__ == '__main__':
    r = rest.rest()
    args = parser.parse_args()
    if args.build == 'all':
	quick_create()
    elif args.remove == 'all':
	delete_all()
    else:
	addDev(args.level, args.loc, args.mount)

