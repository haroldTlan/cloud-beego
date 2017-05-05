from perf import Timer
from db import with_transaction
import log
from caused import caused
import error
from error import exc2status
from env import config
import traceback as tb
import json
import mq

class APIContext(object):
    def _request(self, action, **kv):
        return mq.request('admd', {'action':action, 'params':kv})

    def reload_rqueue(self):
        return self._request('reload_rqueue')

    def scan_all(self):
        return self._request('scan_all')

    def create_raid(self, name, level, chunk, raid_disks, spare_disks, rebuild_priority, sync):
        return self._request('create_raid', name=name, level=level, chunk=chunk, 
                raid_disks=raid_disks, spare_disks=spare_disks,
                rebuild_priority=rebuild_priority, sync=sync)

    def delete_raid(self, name):
        return self._request('delete_raid', name=name)

    def create_volume(self, name, raid, capacity):
        return self._request('create_volume', name=name, raid=raid, capacity=capacity)

    def delete_volume(self, name):
        return self._request('delete_volume', name=name)

    def expand(self, vol_name):
        return self._request('expand', vol_name=vol_name)

    def create_initiator(self, wwn, portals):
        return self._request('create_initiator', wwn=wwn, portals=portals)

    def delete_initiator(self, wwn):
        return self._request('delete_initiator', wwn=wwn)

    def create_vimap(self, initr, volume):
        return self._request('create_vimap', initr=initr, volume=volume)

    def delete_vimap(self, initr, volume):
        return self._request('delete_vimap', initr=initr, volume=volume)

    def change_passwd(self, name, old_password, new_password):
        return self._request('change_passwd', name=name, old_password=old_password, new_password=new_password)

    def create_monfs(self, name, volume):
        return self._request('create_monfs', name=name, volume=volume)

    def delete_monfs(self, name):
        return self._request('delete_monfs', name=name)

    def config_interface(self, iface, address, netmask):
        return self._request('config_interface', iface=iface, address=address, netmask=netmask)

    def config_gateway(self, address):
        return self._request('config_gateway', address=address)

    def create_bond(self, name, slaves, address, netmask, mode):
        return self._request('create_bond', name=name, slaves=slaves, address=address, netmask=netmask, mode=mode)

    def config_bond(self, name, address, netmask):
        return self._request('config_bond', name=name, address=address, netmask=netmask)

    def delete_bond(self, name):
        return self._request('delete_bond', name=name)

    def format_disk(self, locations):
        return self._request('format_disk', locations=locations)

    def set_disk_role(self, location, role, raidname):
        return self._request('set_disk_role', location=location, role=role, raidname=raidname)

    def create_fs(self, name, volume, type):
        return self._request('create_fs', name=name, volume=volume, type=type)

    def delete_fs(self, name):
        return self._request('delete_fs', name=name)

    def fast_create(self, raidname, volumename, fsname, chunk):
        return self._request('fast_create', raidname=raidname, volumename=volumename, fsname=fsname, chunk=chunk)

    def dispath_config(self, serverid, local_serverip, local_serverport, cmssverip, cmssverport):
        return self._request('dispath_config', serverid=serverid, local_serverip=local_serverip, local_serverport=local_serverport, cmssverip=cmssverip, cmssverport=cmssverport)

    def store_config(self, serverid, local_serverip, local_serverport, cmssverip, cmssverport, directory):
        return self._request('store_config', serverid=serverid, local_serverip=local_serverip, local_serverport=local_serverport, cmssverip=cmssverip, cmssverport=cmssverport, directory=directory)

    def force_stop_beep(self):
        return self._request('force_stop_beep')

    def detection_fs(self):
        return self._request('detection_fs')

    def sync_lun(self, lun_name):
        return self._request('sync_lun', lun_name=lun_name)

    def stop_sync_lun(self, lun_name):
        return self._request('stop_sync_lun', lun_name=lun_name)
