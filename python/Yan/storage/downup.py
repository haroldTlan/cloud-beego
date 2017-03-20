import adm
import os

class Test(object):
    def __init__(self):
        self.du = adm.DownUp()

    def unplug(self, devname):
        import pdb
        pdb.set_trace()
        s = os.stat('/dev/%s' % devname)
        self.du.unplug(s.st_rdev)
        disk = adm.Disk(dev_name=devname)
        disk._rm_partition()

    def plug(self, devname):
        import pdb
        pdb.set_trace()
        s = os.stat('/dev/%s' % devname)
        self.du.plug(s.st_rdev)
