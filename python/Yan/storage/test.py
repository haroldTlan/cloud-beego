import adm
import lm
from collections import Counter

def filter_disks(raid_disks):
    most = Counter(str(bytearray(disk.sb.dev_roles)) for disk in raid_disks).most_common(1)
    rdisks  = []
    sdisks = []
    for disk in raid_disks:
        if str(bytearray(disk.sb.dev_roles)) == most[0][0]:
            rdisks.append(disk)
        else:
            sdisks.append(disk)
    return rdisks, sdisks

m = lm.LocationMapping()

raid_disks = [adm.Disk(location=loc, dev_name=dev_name) for loc, dev_name in m.mapping.items()]
rds, sds = filter_disks(raid_disks)
print 'raid disks:'
for disk in rds:
    print '\t%s' % disk.dev_name
print 'spare disks:'
for disk in sds:
    print '\t%s' % disk.dev_name
