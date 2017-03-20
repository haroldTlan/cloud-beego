import adm
import db
import sys
import re
from md import Metadata
from util import execute

def usage():
    print '%s [recover id]' % sys.argv[0]
    print '%s list' % sys.argv[0]
    sys.exit(-1)

def exctract_from_log(log):
    m = re.search('raid=(.+?),name=(.+?),raid-disks=(\d+)\[(.+?)\],level=(.+?),chunk=(.+?)', log)
    if m:
        return m.groups
    else:
        return None

def show_created_raid_infos():
    fmt = '%8.8s%32.32s%24.24s'
    print fmt % ('ID', 'Name', 'Date')
    for rec in db.Recovery.select().order_by(db.Recovery.created_at.desc()):
        info = exctract_from_log(rec.log)
        if info:
            print fmt % (rec.id, info[0], m.created_at)

def recover_raid(id):
    try:
        rec = db.Recovery.get(id=id)
    except:
        print 'no such ID: %s' % id
        sys.exit(-1)

    name,nr,raid_disks,level,chunk = exctract_from_log(rec.log)
    disks = []

    try:
        raid = adm.Raid.lookup(name=name)
        if raid.online:
            print 'raid %s online' % raid.name
            sys.exit(-1)
        elif raid.health <> adm.HEALTH_FAILED:
            print 'raid %s is offline, but its health is not failed' % raid.name
            sys.exit(-1)
        else:
            for disk in raid.raid_disks + raid.spare_disks:
                disk.role = adm.ROLE_UNUSED
                disk.save(raid=None, link=False, unplug_seq=0)
                if disk.online and disk.health <> adm.HEALTH_FAILED:
                    Metadata.update(disk.md_path, raid_uuid='')
            raid.db.delete()
    except:
        pass

    for u in raid_disks.split(','):
        try:
            disk = adm.Disk.lookup(uuid=u)
            if disk.online:
                if disk.role == adm.ROLE_UNUSED:
                    disks.append(disk)
                else:
                    print 'disk:%s is used' % u
            else:
                print 'disk:%s is offline' % u
        except:
            print 'disk:%s is not found' % u

    disks = [disk.location for disk in disks]
    adm.create_raid(name, level, '%sKB'%chunk, ','.join(disks), '', 'low', sync='no')

    cmd = 'lvscan'
    execute(cmd, False)

    raid = adm.Raid.lookup(name=name)
    raid.update_extents()

def main():
    if len(sys.argv) == 2:
        if sys.argv[1] <> 'list':
            usage()
        show_created_raid_infos()
    elif len(sys.argv) == 3:
        if sys.argv[1] <> 'recover':
            usage()
        recover_raid(sys.argv[2])
    else:
        usage()

if __name__ == '__main__':
    main()
