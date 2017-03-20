import requests
import os
import traceback as tb
import sys
import json

class NoResponse(Exception):
    pass
class RequestTimeout(Exception):
    pass
class ResponseError(Exception):
    def __init__(self, status, content):
        self.status = status
        self.content = content
class Unauthorized(Exception):
    pass

def unicode_2_str(o):
    if isinstance(o, dict):
        for k, v in o.items():
            del o[k]
            o[str(k)] = v
            if isinstance(v, unicode):
                o[k] = str(v)
            elif isinstance(v, dict):
                o[k] = unicode_2_str(v)
    return o

default_host = 'localhost'

class HttpClient:
    def trace(func):
        def _trace(self, *vargs, **kv):
            try:
                ret = func(self, *vargs, **kv)
                return ret
            except requests.Timeout:
                raise RequestTimeout()
            except requests.HTTPError as e:
                rsp = e.response
                content = rsp.content
                if rsp.status_code == 400:
                    try:
                        content = json.loads(content)
                    except:
                        pass
                elif rsp.status_code == 401:
                    raise Unauthorized()
                raise ResponseError(rsp.status_code, content)
            except requests.RequestException:
                raise NoResponse()
            except Exception as e:
                raise e
            finally:
                if self.enable_trace:
                    tb.print_exc()
        return _trace

    def __init__(self, host, port='8081', ver='', fmt='json', enable_trace=False):
        self.host = host
        self.port = port
        self.cookies = {}
        self.fmt = fmt
        self.ver = ver
        self.headers = {'Accept':'application/%s'%fmt}
        self.enable_trace = enable_trace

    def _new_url(self, url):
        ver = '%s/' % self.ver if self.ver else ''
        new_url = 'http://%s:%s/api/%s%s' % (self.host, self.port, ver, url.lstrip('/').rstrip('/'))
        if self.enable_trace: print new_url
        return new_url

    @trace
    def get(self, url, getrsp=False):
        rsp = requests.get(self._new_url(url), cookies=self.cookies, headers=self.headers)
        rsp.raise_for_status()
        self.cookies = rsp.cookies
        if getrsp: return rsp
        else: return rsp.content

    @trace
    def post(self, url, data={}, getrsp=False):
        rsp = requests.post(self._new_url(url), cookies=self.cookies, data=data, headers=self.headers)
        rsp.raise_for_status()
        self.cookies = rsp.cookies
        if getrsp: return rsp
        else: return rsp.content

    @trace
    def put(self, url, data={}, getrsp=False):
        rsp = requests.put(self._new_url(url), cookies=self.cookies, data=data, headers=self.headers)
        rsp.raise_for_status()
        self.cookies = rsp.cookies
        if getrsp: return rsp
        else: return rsp.content

    @trace
    def delete(self, url, getrsp=False):
        rsp = requests.delete(self._new_url(url), cookies=self.cookies, headers=self.headers)
        rsp.raise_for_status()
        self.cookies = rsp.cookies
        if getrsp: return rsp
        else: return rsp.content

class RestObj(object):
    def __init__(self, client):
        module = sys.modules[__name__]
        for name in dir(module):
            if not name.endswith('Rest'): continue
            r = eval(name)
            if issubclass(r, BaseRest) and r <> BaseRest:
                name = r.__name__[:-len('Rest')].lower()
                setattr(self, name, r(client))

    def login(self, name, passwd):
        self.session.create(name, passwd)
        return self

def rest(host=default_host, port='8081', ver='', fmt='json', enable_trace=False):
    client = HttpClient(host=host, port=port, fmt=fmt, ver=ver, enable_trace=enable_trace)
    return RestObj(client)


def detail_json(func):
    def _detail_json(*vargs, **kv):
        o = func(*vargs, **kv)
        o = json.loads(o)
        if 'detail' in o:
            return unicode_2_str(o['detail'])
    return _detail_json

class BaseRest:
    def __init__(self, client = None):
        self.client = client if client else HttpClient(default_host)

    @detail_json
    def _list(self, model):
        return self.client.get(model)

    @detail_json
    def _query(self, model, id):
        return self.client.get('%s/%s' % (model, id))

    @detail_json
    def _create(self, model, data):
        return self.client.post(model, data)

    @detail_json
    def _delete(self, model, id):
        return self.client.delete('%s/%s' % (model, id))

class DiskRest(BaseRest):
    MODEL = 'disks'
    def list(self):
        return self._list(self.MODEL)

    def query(self, location):
        return self._query(self.MODEL, location) 

    def format(self, location):
        return self.client.put('/%s/%s' % (self.MODEL, location), {'host':'native'})

    def set_role(self, location, role):
        return self.client.put('/%s/%s' % (self.MODEL, location), {'role':role})

def rest_data(locals_, attrs):
    return dict([(attr, locals_[attr]) for attr in attrs])

class RaidRest(BaseRest):
    MODEL = 'raids'
    def list(self):
        return self._list(self.MODEL)

    def query(self, location):
        return self._query(self.MODEL, location) 

    def create(self, name, level, chunk, raid_disks, spare_disks, rebuild_priority, sync):
        data = rest_data(locals(), ['name', 'level', 'chunk', 'raid_disks', \
                'spare_disks', 'rebuild_priority', 'sync'])
        return self._create(self.MODEL, data)

    def delete(self, name):
        return self._delete(self.MODEL, name)

class VolumeRest(BaseRest):
    MODEL = 'volumes'
    def list(self):
        return self._list(self.MODEL)

    def query(self, location):
        return self._query(self.MODEL, location)

    def create(self, name, raid, capacity):
        data = rest_data(locals(), ['name', 'raid', 'capacity'])
        return self._create(self.MODEL, data)

    def delete(self, name):
        return self._delete(self.MODEL, name)

    @detail_json
    def expand(self, vol_name):
        return self.client.post('expansion', {'vol_name':vol_name})

class InitiatorRest(BaseRest):
    MODEL = 'initiators'
    def list(self):
        return self._list(self.MODEL)

    def query(self, location):
        return self._query(self.MODEL, location)

    def create(self, wwn, portals):
        data = rest_data(locals(), ['wwn', 'portals'])
        return self._create(self.MODEL, data)

    def delete(self, wwn):
        return self._delete(self.MODEL, wwn)

    @detail_json
    def map(self, wwn, volume):
        return self.client.post('%s/%s/luns' % (self.MODEL, wwn), {'volume':volume})

    @detail_json
    def unmap(self, wwn, volume):
        return self.client.delete('%s/%s/luns/%s' % (self.MODEL, wwn, volume))

class InterfaceRest(BaseRest):
    MODEL = 'interfaces'
    def list(self):
        return self._list(self.MODEL)

    def query(self, eth):
        return self._query(self.MODEL, eth)

    @detail_json
    def config(self, iface, address, netmask):
        data = {'address':address, 'netmask':netmask}
        return self.client.put('/network/%s/%s' % (self.MODEL, iface), data)

class GatewayRest(BaseRest):
    MODEL = 'gateway'
    @detail_json
    def query(self):
        return self.client.get('/network/%s' % self.MODEL)

    @detail_json
    def config(self, address):
        data = {'address': address}
        return self.client.put('/network/%s' % self.MODEL, data)

class CommandRest(BaseRest):
    MODEL = 'commands'
    def poweroff(self):
        return self.client.put('/%s/poweroff' % self.MODEL)

    def reboot(self):
        return self.client.put('/%s/reboot' % self.MODEL)

    def init(self):
        return self.client.put('/%s/init' % self.MODEL)

class SessionRest(BaseRest):
    MODEL = 'sessions'
    def create(self, name, password):
        data = rest_data(locals(), ['name', 'password'])
        return self._create(self.MODEL, data)

class UserRest(BaseRest):
    MODEL = 'users'
    @detail_json
    def change_password(self, name, old_password, new_password):
        data = rest_data(locals(), ['name', 'old_password', 'new_password'])
        return self.client.put('/%s/%s/password' % (self.MODEL, name), data)

class LicenseRest(BaseRest):
    MODEL = 'licenses'
    def create(self, sn):
        return self._create(self.MODEL, {'sn':sn})

class FilesystemRest(BaseRest):
    MODEL = 'filesystems'
    def list(self):
        return self._list(self.MODEL)

    def create(self, name, volume, type):
        data = rest_data(locals(), ['name', 'volume', 'type'])
        return self._create(self.MODEL, data)

    def delete(self, name):
        return self._delete(self.MODEL, name)

    def fastcreate(self, raidname, volumename, fsname, chunk):
        data = rest_data(locals(), ['raidname', 'volumename', 'fsname', 'chunk'])
        data.update(mode='fast')
        return self._create(self.MODEL, data)

class BondRest(BaseRest):
    MODEL = 'bond'
    def create(self, name, slaves, address, netmask, mode):
        data = rest_data(locals(), ['name', 'slaves', 'address', 'netmask', 'mode'])
        return self.client.post('/network/%s/%s' % (self.MODEL, name), data)

    def delete(self, name):
        return self.client.delete('/network/%s/%s' % (self.MODEL, name))

    def config(self, name, address, netmask):
        data = {'address':address, 'netmask':netmask}
        return self.client.put('/network/%s/%s' % (self.MODEL, name), data)

class DeviceStatusRest(BaseRest):
    MODEL = 'device-status'
    @detail_json
    def query(self):
        return self.client.get('/%s' % self.MODEL)

def list_disk():
    rest = DiskRest()
    return rest.list()

def list_raid():
    rest = RaidRest()
    return rest.list()

def create_raid(name, level, chunk, raid_disks, spare_disks, rebuild, sync):
    rest = RaidRest()
    return rest.create(name, level, chunk, raid_disks, spare_disks, rebuild, sync)

def delete_raid(name):
    rest = RaidRest()
    return rest.delete(name)

def list_volume():
    rest = VolumeRest()
    return rest.list()

def create_volume(name, capacity):
    rest = VolumeRest()
    return rest.create(name, capacity)

def delete_volume(name):
    rest = VolumeRest()
    return rest.delete(name)

def list_initiator():
    rest = InitiatorRest()
    return rest.list()

def create_initiator(wwn, portals):
    rest = InitiatorRest()
    return rest.create(wwn, portals)

def delete_initiator(wwn):
    rest = InitiatorRest()
    return rest.delete(wwn)

def map_volume(wwn, volume):
    rest = InitiatorRest()
    return rest.map(wwn, volume)

def unmap_volume(wwn, volume):
    rest = InitiatorRest()
    return rest.unmap(wwn, volume)

