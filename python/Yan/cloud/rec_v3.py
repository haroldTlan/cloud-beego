#!/usr/bin/env python

import sys
import os
from util import *
import adm
import time

#To get the failed raids
def get_failed_raids():
    _, results = execute("echo 'use speediodb; select * from raids;' | mysql -uroot -ppasswd | grep failed")
    raids = []
    for result in results.rstrip().split('\n'):
        o = result.split('\t')
        raids.append({'uuid': o[0], 'dev_name': o[12], 'name': o[3]})
        
    return raids

#To judge if all the disks in the raid with uuid 'raid_uuid' are plugged
#recovery_logs comes from the raid_recoveries in mysqldump
#raid_uuid is the uuid of the failed raid
def check_disk_nr(recovery_logs, raid_uuid):
    recs_about_raid = [rec for rec in recovery_logs if rec['raid_uuid'] == raid_uuid]
    
    _, results = execute("echo 'use speediodb; select * from disks;' | mysql -uroot -ppasswd |grep %s" % raid_uuid)

    disks_in_db = {}
    for result in results.rstrip().split('\n'):
        disks_in_db[result.split('\t')[0]] = result.split('\t')[17] 

    _, disks_exist_now = execute('ls /dev/sd[a-z]')
    for disk_uuid in recs_about_raid[-1]['data_disks']:
        if disks_in_db[disk_uuid] in disks_exist_now:
            continue
        else:
            return False

    return True

#To find the latest recovery log about the raid with the raid_uuid input
def check_raid_recovery_log():
    _, results = execute("mysqldump -uroot -ppasswd speediodb | grep 'INSERT INTO' | grep raid_recoveries | sed 's/),(/)\t(/g'")
    if results == '':
        return False

    recs = []
    for result in results.rstrip().split('\t'):
        obs = re.search(r'\(([^\(\)]+)\)', result).group(1).split(',')
        o = [ob.strip('[\']') for ob in obs]
        ddisk = [o[8+i] for i in range(0, int(o[7]))]
        sdisk = o[-1]
        recs.append({'raid_uuid': o[3], 'raid_name': o[4], 'data_disks': ddisk, 'spare_disks': sdisk, 'time': o[1]})

    return recs

#According to the raid_rec input to change information in database
def add_disk(recovery_logs, raid_uuid):
    recs_about_raid = [rec for rec in recovery_logs if rec['raid_uuid'] == raid_uuid]
    raid_rec = recs_about_raid[-1]
    
    try:
        for disk_uuid in raid_rec['data_disks']:
            disk = adm.Disk.lookup(uuid=disk_uuid)
            disk.save(health='normal', role='data', unplug_seq=0)
        rd = adm.Raid.lookup(uuid=raid_rec['raid_uuid'])
        rd.save(health='normal', unplug_seq=0)

        _, results = execute("echo 'use speediodb; flush privileges;' |mysql -uroot -ppasswd")
        return True
    except:
        return False

def touch_file():
    os.system('touch /home/zonion/boot')

if __name__ == "__main__":
    failed_raids = get_failed_raids()
    recs = check_raid_recovery_log()
    if check_disk_nr(recs, failed_raids[0]['uuid']):
        print 'OK! all the disk in the failed raid are plugged'
    else:
        print 'Please plug all the disk of the failed raid %s. And try again.' % failed_raids[0]['name']
        exit(1)

    if add_disk(recs, failed_raids[0]['uuid']):
        print 'Added disks success!'
    else:
        print 'Added disks failed!'
        exit(1)

    touch_file()

    for i in range(0, 10):
        print '.'
        time.sleep(1)
    execute('/sbin/reboot')

