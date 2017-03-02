#!/usr/bin/env python
from gevent import monkey; monkey.patch_all()
import gevent
from socketio import socketio_manage
from socketio.server import SocketIOServer
from socketio.namespace import BaseNamespace
import web
import os
import json
import socket
import random
import sys
import re
sys.path.append('../speedio')
import log
from caused import caused
from env import config
from util import execute, eval_bool
import db
import api
import adm
import error
from error import ExternalError
from error import InternalError
from web.webapi import HTTPError
from multiprocessing import Lock
import traceback as tb
import time
from lm import LocationMapping
from daemon import Daemon, main
import md5
from util import uuid
import network
import web.httpserver
import random
import uevent
import thread
import mq
import yaml

urls = (
    '/', 'Zadmin',
    '/zadmin', 'Zadmin',

    '/api/statistics', 'Statistics',
    '/api/realtime', 'Realtime',
    '/api/diagnosis', 'Diagnosis',
    '/api/upgrade', 'Upgrade',


    '/api/dsus', 'DSU',
    '/api/disks', 'Disk',
    '/api/disks/host', 'DiskHost',
    '/api/raids', 'Raid',
    '/api/volumes', 'Volume',
    '/api/initiators', 'Initiator',
    '/api/interfaces', 'Interface',
    '/api/journals', 'Journal',
    '/api/monfs', 'MonFS',
    '/api/filesystems', 'FileSystem',
    '/api/ifaces', 'Ifaces',

    '/api/disks/(.+)', 'Disk',
    '/api/raids/(.+)', 'Raid',
    '/api/volumes/(.+)', 'Volume',
    '/api/initiators/(.+?)/luns', 'Mapping',
    '/api/initiators/(.+?)/luns/(.+)', 'Mapping',
    '/api/initiators/(.+)', 'Initiator',
    '/api/network/interfaces/(.+)', 'Interface',
    '/api/network/bond/(.+)', 'Bond',
    '/api/monfs/(.+?)', 'MonFS',
    '/api/filesystems/(.+?)', 'FileSystem',
    '/api/network/gateway', 'Gateway',
    '/api/commands/(.+)', 'Command',
    '/api/expansion', 'VolumeExpansion',

    '/api/sessions', 'Session',
    '/api/users/(.+?)/password', 'UserPassword',
    '/api/zxconfig/dispath', 'Dispath',
    '/api/zxconfig/store', 'Store',
    '/api/systeminfo', 'SystemInfo',
    '/socket\.io/.*', 'SocketIO',
    '/api/device-status', 'DeviceStatus',
)

web.config.debug = False
app = web.application(urls, globals())
web.config.session_parameters['cookie_name'] = 'token'
web.config.session_parameters['ignore_change_ip'] = False
web.config.session_parameters['timeout'] = 3600 * 24
web.config.session_parameters['secret_key'] = 'dLjcfxqXtfNoIldAKop'

#webdb = web.database(dbn='mysql', db=config.database.name, user=config.database.usr, pw=config.database.passwd)
store = web.session.DiskStore('sessions')
session = web.session.Session(app, store)

apicxt = api.APIContext()

def format(supported=['json']):
    def _format(func):
        def __format(*vargs, **kv):
            fmt = 'json'
            m = re.search('application/(.+)', web.ctx.env.get('HTTP_ACCEPT'))
            if m: fmt = m.group(1)

            if supported and fmt not in supported: raise web.notacceptable()

            try:
                o = func(*vargs, **kv)
            except HTTPError as e:
                raise e
            except Exception as e:
                tb.print_exc()
                web.header('content-type', 'application/%s' % fmt)
                web.ctx.status = '400 bad request'
                return json.dumps(error.error(e))
            else:
                if isinstance(o, (str, unicode)):
                    return o
                elif isinstance(o, dict) and 'status' in o and o['status'] == 'error':
                    web.ctx.status = '400 bad request'
                web.header('content-type', 'application/%s' % fmt)
                return json.dumps(o)
        return __format
    return _format

def input(param):
    return str(web.input(**{param:''}).get(param))

def inputs(params):
    return dict([(p, input(p)) for p in params])


class HtmlTag:
    @classmethod
    def script(cls, dir, src):
        src = src if isinstance(src, list) else [src]
        return '\n'.join(['<script type="text/javascript" src="%s/%s.js?v=%s"></script>' % (dir, s, random.randint(0,1000))\
                for s in src])

    @classmethod
    def css(cls, dir, href):
        href = href if isinstance(href, list) else [href]
        return '\n'.join(['<link href="%s/%s.css?v=%s" rel="stylesheet">' % (dir, h, random.randint(0,1000))\
                for h in href])

class Index:
    def GET(self):
        render = web.template.render('templates', globals={'tag':HtmlTag})
        try:
            usr = db.User.get(perishable_token=session.perishable_token)
            render1 = web.template.render('templates', globals={'tag':HtmlTag, 'render':render})
            return render1.application()
        except:
            return render.login()

stat_lock = Lock()
class Statistics:
    @format()
    def GET(self):
        with stat_lock:
            try:
                time = input('time')
                req = {'cmd': 'statistics', 'params':{}}
                if time:
                    req['params'] = {'time':int(time)}
                web.header('content-type', 'application/json')
                return mq.request('speedd', req)
            except:
                tb.print_exc()
                return error.success([])

class Realtime:
    @format()
    def GET(self):
        try:
            time = web.input().get('time')
            req = {'cmd': 'realtime', 'params':{}, 'addr':SPEEDD_RSP}
            if time:
                req['params'] = {'time':int(time)}
            return mq.request('speedd', req)
        except:
            return error.error([])

class DSU:
    @format()
    def GET(self):
        lm = LocationMapping()
        return error.success([{'location': dsu, 'support_disk_nr': nr} for dsu, nr in lm.dsu_list.items()])

class DiskHost:
    @format()
    def PUT(self):
        return apicxt.format_disk(input('locations'))

class Disk:
    def _cmp_disk(self, a, b):
        a3 = re.findall('(\d+)\.(\d+)\.(\d+)', a.location)
        b3 = re.findall('(\d+)\.(\d+)\.(\d+)', b.location)
        if not a3 or not b3:
            return 0
        for x, y in zip(a3[0], b3[0]):
            if int(x) > int(y): return 1
            elif int(x) < int(y): return -1
        return 0

    @format()
    def PUT(self, location):
        params = web.input(host='', role='', raid='')
        if params.host == adm.Disk.HOST_NATIVE:
            return apicxt.format_disk(location)
        elif params.role <> '':
            return apicxt.set_disk_role(location, params.role, params.raid)
        else:
            raise error.UnkownOperation()

    @format()
    def GET(self):
        try:
            disks = []
            diskmap = dict((disk.location, disk) for disk in adm.Disk.all() if disk.online and disk.health <> adm.HEALTH_DOWN)
            for disk in adm.Disk.all():
                if disk.raid and not disk.raid.deleted and disk.health == adm.HEALTH_DOWN:
                    diskmap.setdefault(disk.prev_location, disk)

            disks = sorted(diskmap.values(), cmp=self._cmp_disk)
        except:
            tb.print_exc()
        return error.success([self._as_obj(disk) for disk in disks])

    def _as_obj(self, disk):
        obj = {'id': disk.uuid,
               'location' : disk.location or disk.prev_location,
               'vendor' : disk.vendor,
               'rpm' : disk.rpm,
               'health' : disk.health,
               'role' : disk.role,
               'cap_sector' : disk.cap.Sector,
               'host': disk.host,
               'rqr_count': disk.rqr_count}
        if disk.raid and not disk.raid.deleted:
            obj['raid'] = disk.raid.name
        else:
            obj['raid'] = ''
        return obj

class Raid:
    @format()
    def GET(self):
        return error.success([self._as_obj(raid) for raid in adm.Raid.all() if not raid.deleted])

    @format()
    def POST(self):
        return apicxt.create_raid(**inputs(['name', 'level', 'chunk', 'raid_disks', 'spare_disks', 'rebuild_priority', 'sync']))

    @format()
    def DELETE(self, name):
        status = apicxt.delete_raid(str(name))
        return status

    def _as_obj(self, raid):
        pe = config.lvm.vg.pe_size
        obj = {'id'              : raid.uuid,
               'name'            : raid.name,
               'blkdev'          : "/dev/mapper/" + raid.odev_name,
               'level'           : raid.level,
               'chunk_kb'        : raid.chunk.KB,
               'health'          : raid.health,
               'cap_sector'      : (raid.cap*pe).Sector,
               'used_cap_sector' : (raid.used_cap*pe).Sector,
               'rebuilding'      : raid.rebuilding,
               'rebuild_progress': raid.rebuild_progress,
               'rqr_count'       : raid.rqr_count,
               }
        return obj

class MonFS:
    @format()
    def GET(self):
        fs_list = adm.MonFS.all()
        if fs_list:
            return error.success(self._as_obj(fs_list[0]))
        else:
            return error.success({})

    @format()
    def POST(self):
        return apicxt.create_monfs(**inputs(['name', 'volume']))

    def _as_obj(self, fs):
        obj = {'id'      : fs.uuid,
               'volume'  : fs.volume.name,
               'chunk_kb': fs.chunk.KB,
               'nr'      : fs.nr,
               'name'    : fs.name}
        return obj

    @format()
    def DELETE(self, name):
        status = apicxt.delete_monfs(str(name))
        return status

class FileSystem:
    @format()
    def GET(self):
        filesystems = adm.XFS.all()
        filesystems.extend(adm.MonFS.all())

        return error.success([self._as_obj(fs) for fs in filesystems])

    @format()
    def POST(self):
        if input('mode') == 'fast':
            return apicxt.fast_create(**inputs(['raidname', 'volumename', 'fsname', 'chunk']))
        else:
            return apicxt.create_fs(**inputs(['name', 'volume', 'type']))

    def _as_obj(self, fs):     
        obj = {'id'      : fs.uuid,
               'volume'  : fs.volume.name,
               'name'    : fs.name,
               'type'    : fs.type}
        return obj

    @format()
    def DELETE(self, name):
        status = apicxt.delete_fs(str(name))
        return status

    @format()
    def PUT(self, choice):
        if choice == 'detection':
            return apicxt.detection_fs()

class Ifaces:
    @format()
    def GET(self):
        return error.success([str(info.ipaddr) for info in network.ifaces().values() if info.link])

class Volume:
    @format()
    def GET(self):
        return error.success([self._as_obj(volume) for volume in db.Volume.all() if volume.deleted == 0])

    @format()
    def POST(self):
        status = apicxt.create_volume(**inputs(['name', 'raid', 'capacity']))
        return status

    @format()
    def DELETE(self, name):
        status = apicxt.delete_volume(str(name))
        return status

    def _as_obj(self, volume):
        pe = config.lvm.vg.pe_size
            
        obj = {'id'     : volume.uuid,
               'name'   : volume.name,
               'health' : volume.health,
               'used'   : volume.used,
               'sync'   : False,
               'sync_progress'   : 0,
               'cap_sector' : (volume.cap*pe).Sector}
        return obj

class VolumeExpansion(object):
    @format()
    def POST(self):
        status = apicxt.expand(**inputs(['vol_name']))
        return status

class Initiator:
    @format()
    def GET(self):
        return error.success([self._as_obj(initr) for initr in db.Initiator.all()])

    @format()
    def POST(self):
        status = apicxt.create_initiator(**inputs(['wwn', 'portals']))
        return status

    @format()
    def DELETE(self, wwn):
        status = apicxt.delete_initiator(str(wwn))
        return status


    def _as_obj(self, o):
        volumes = [vi.volume for vi in db.InitiatorVolume\
            .select().where(db.InitiatorVolume.initiator==o)]

        initr = adm.Initiator(db=o)

        obj = {'id': o.wwn,
               'wwn' : o.wwn,
               'volumes' : [v.name for v in volumes],
               'portals' : [p.eth for p in o.portals],
               'active_session' : initr.active_session}
        return obj

class Mapping:
    @format()
    def POST(self, initr):
        params = dict([(k, str(v)) for k, v in web.input().items()])
        status = apicxt.create_vimap(str(initr), params.get('volume', ''))
        return status

    @format()
    def DELETE(self, initr, volume):
        status = apicxt.delete_vimap(str(initr), str(volume))
        return status

class Interface:
    @format()
    def GET(self):
        return self._GET()

    def _GET(self):
        ifaces = []
        for info in network.ifaces().values():
            o = {'id'     : info.name,
                 'iface'  : info.name,
                 'ipaddr' : info.ipaddr,
                 'netmask': info.netmask,
                 'slaves' : info.slaves,
                 'master' : info.master,
                 'type'   : info.type,
                 'link'   : info.link}
            if info.type == 'bond-master':
                bond = network.Bond(info.name)
                o['mode'] = bond.mode
            ifaces.append(o)
        return error.success(ifaces)

    @format()
    def PUT(self, iface):
        o = apicxt.config_interface(iface, **inputs(['address', 'netmask']))
        if o['status'] == 'error':
            return o
        else:
            gevent.hub.get_hub().parent.throw(SystemExit())

class Bond:
    @format()
    def POST(self, name):
        o = apicxt.create_bond(name, **inputs(['slaves', 'address', 'netmask', 'mode']))
        if o['status'] == 'error':
            return o
        else:
            gevent.hub.get_hub().parent.throw(SystemExit())

    @format()
    def DELETE(self, name):
        o = apicxt.delete_bond(name)
        if o['status'] == 'error':
            return o
        else:
            gevent.hub.get_hub().parent.throw(SystemExit())

    @format()
    def PUT(self, name):
        o = apicxt.config_bond(name, **inputs(['address', 'netmask']))
        if o['status'] == 'error':
            return o
        else:
            gevent.hub.get_hub().parent.throw(SystemExit())

class Gateway:
    @format()
    def GET(self):
        cmd = "bash /home/zonion/command/spk.sh 0"
        _,o = execute(cmd, False, logging=False)

        gw = network.Gateway()
        return error.success({'gateway': gw.ipaddr})

    @format()
    def PUT(self):
        return apicxt.config_gateway(input('address'))


class Journal:
    @format()
    def GET(self):
        params = web.input()
        if 'offset' not in params or 'limit' not in params:
            return error.success([self._as_obj(journal) for journal in db.Journal.select()\
                        .order_by(db.Journal.created_at.desc())])

        try:
            offset = int(params.offset)
            if offset < 0:
                raise error.InvalidParam('offset', params.offset) 
        except:
            raise error.InvalidParam('offset', params.offset) 
        try:
            limit = int(params.limit)
            if limit < 0:
                raise error.InvalidParam('limit', params.limit) 
        except:
            raise error.InvalidParam('limit', params.limit) 
        return error.success([self._as_obj(j) for j in db.Journal.select()\
                    .order_by(db.Journal.created_at.desc()).offset(offset).limit(limit)])

    def _as_obj(self, journal):
        obj = {'level' : journal.level,
               'message' : journal.message,
               'created_at' : int(journal.created_at.strftime('%s'))}
        return obj

class Diagnosis:
    def GET(self):
        path = os.path.join(config.etc.path, 'diagnosis.tar.gz')
        _, o = execute('../speedio/collect_diagnosis.sh')
        web.header('Content-Type','application/octet-stream')
        web.header('Content-disposition', 'attachment; filename=diagnosis.%s.tar.gz' % time.strftime('%Y%m%d%H%M%S'))
        stream = ''
        with open(path, 'rb') as fin:
            stream = fin.read()
        os.remove(path)
        return stream

class Zadmin:
    def GET(self):
        zip = 'Zadmin.zip'
        path = os.path.join(config.etc.path, zip)
        web.header('Content-Type','application/octet-stream')
        web.header('Content-disposition', 'attachment; filename=%s'%zip)
        stream = ''
        with open(path, 'rb') as fin:
            stream = fin.read()
        return stream

class Upgrade:
    @format([])
    def POST(self):
        params = web.input(files={})
        if 'files' in params:
            filename = params.files.filename.replace('\\', '/').split('/')[-1]
            savepath = os.path.join(config.upgrade.dir, filename)
            with open(savepath, 'w') as fout:
                content = params.files.file.read()
                size = len(content)
                fout.write(content)
            obj = {"files": [{
                       "name": filename,
                       "size": size,
                       "url": "",
                       "thumbnail_url": ""}]}
            return obj
        else:
            return error.internal_error

class Command:
    @format()
    def PUT(self, command):
        try:
            async = web.input(async=False).get('async')
            async = eval_bool(async)
        except:
            return json.dumps(error.InvalidParam('async', async))
        if re.search('^\w+$', command):
            pypath = os.path.join(config.command.dir, '%s.pyc' % command)
            shpath = os.path.join(config.command.dir, '%s.sh' % command)
            if os.path.exists(pypath):
                cmd = 'python %s' % pypath
            elif os.path.exists(shpath):
                cmd = '/bin/sh %s' % shpath
            else:
                return json.dumps(error.InvalidCommand(command))

            try:
                if async:
                    os.system('%s &' % cmd)
                    return json.dumps({})
                else:
                    _, o = execute(cmd)
                    return json.dumps(o)
            except ExternalError as e:
                return json.dumps(error.error(e))
            except:
                return error.internal_error

        return json.dumps(error.InvalidCommand(command))

class Session:
    @format()
    def POST(self):
        name, passwd = input('name'), input('password')
        try:
            usr = db.User.get(name=name)
            digest = md5.new(passwd).hexdigest()
            if str(usr.crypted_passwd) <> digest:
                raise error.LoginError()

            usr.perishable_token = md5.new(uuid.uuid4()).hexdigest()
            usr.save()
            session.perishable_token = usr.perishable_token
            login_id = random.randint(1, pow(2, 32))
            uevent.UserLogin(login_id=login_id).notify()
            return error.success({'login_id':login_id})
        except Exception as e:
            print e
            raise error.LoginError(name)

class UserPassword:
    @format()
    def PUT(self, name):
        try:
            old_password, new_password = input('old_password'), input('new_password')
            return apicxt.change_passwd(name, old_password, new_password)
        except Exception as e:
            tb.print_exc()

class Dispath:
    @format()
    def POST(self):
        try:
            serverid, local_serverip, local_serverport, cmssverip, cmssverport = input('serverid'), input('local_serverip'), input('local_serverport'), input('cmssverip'), input('cmssverport')
            return apicxt.dispath_config(serverid, local_serverip, local_serverport, cmssverip, cmssverport)
        except Exception as e:
            tb.print_exc()

class Store:
    @format()
    def POST(self):
        try:
            serverid, local_serverip, local_serverport, cmssverip, cmssverport, directory = input('serverid'), input('local_serverip'), input('local_serverport'), input('cmssverip'), input('cmssverport'), input('directory')
            return apicxt.store_config(serverid, local_serverip, local_serverport, cmssverip, cmssverport, directory)
        except Exception as e:
            tb.print_exc()

class SystemInfo:
    @format()
    def GET(self):
        try:
            with open('../version') as fin:
                ver = yaml.load(fin.read().strip())
            return error.success({'version': ver['system'], 'feature':config.feature, 'gui version': ver['gui min version']})
        except:
            return error.success({'version': 'UNKOWN', 'feature':config.feature, 'gui version': '1.0.0'})

class DeviceStatus:
    def temp_alert(self):
        try:
            req = mq.Request('speedd')
            msg = {'cmd': 'statistics', 'params':{'time': 'last'}}
            stat = req.request(msg, 1000)
            temp = stat['sample']['temp']
            if temp >= config.alert.temp_threshold:
                return 'warning', temp
            else:
                return 'normal', temp
        except:
            return 'warning', 'NA'

    @format()
    def GET(self):
        try:
            disks = [disk for disk in adm.Disk.all() if disk.health <> 'normal' and disk.raid and not disk.raid.deleted]
            raids = [raid for raid in adm.Raid.all() if raid.health <> 'normal']
            volumes = [volume for volume in adm.Volume.all() if volume.health <> 'normal']
            temp_status,temp = self.temp_alert()
            if not disks and not raids and not volumes and temp_status == 'normal':
                return error.success({'status': 'normal'})
            else:
                rsp = {'status': 'warning'}
                if disks:
                    rsp['disks'] = [{disk.prev_location:disk.health} for disk in disks]
                if raids:
                    rsp['raids'] = [{raid.name:raid.health} for raid in raids]
                if volumes:
                    rsp['volumes'] = [{volume.name:volume.health} for volume in volumes]
                if temp_status <> 'normal':
                    rsp['temp'] = temp
                return error.success(rsp)
        except Exception as e:
            log.error(caused(e).detail)
            return error.internal_error

class SocketIO:
    def GET(self):
        socketio_manage(web.ctx.env, {'/statistics': StatisticsNamespace, '/event': EventNamespace})

class WebNamespace(BaseNamespace):
    def initialize(self):
        self._exit = False
    def disconnect(self, silent):
        self._exit = True
        BaseNamespace.disconnect(self, silent)


class StatisticsNamespace(WebNamespace):
    def recv_connect(self):
        def send_statistics():
            req = mq.Request('speedd')
            while not self._exit:
                msg = {'cmd': 'statistics', 'params':{'time': 'last'}}
                try:
                    stat = req.request(msg, 1000)
                    self.emit('statistics', stat['sample'])
                except:
                    pass
                gevent.sleep(config.statd.interval)
        self.spawn(send_statistics)


class EventNamespace(WebNamespace):
    def recv_connect(self):
        def send_event():
            sub = mq.Subscriber('eventd')
            while not self._exit:
                try:
                    e = sub.recv(100)  # msecs
                    self.emit('event', e)
                except:
                    pass
                gevent.sleep(0.5)
        self.spawn(send_event)


def db_connect(handler):
    m1 = re.search('/socket\.io/.*', web.ctx.path)
    m2 = re.search('sessions', web.ctx.path)
    if m1 or m2:
        ret = handler()
    else:
        db.connect()
        ret = handler()
        db.close()
    return ret

def unauthorized_error():
    web.header('content-type', 'application/json')
    web.ctx.status = '401 Unauthorized'
    return json.dumps(error.error(error.Unauthorized()))

def authorize():
    if web.ctx.host == 'localhost:8081':
        return True
    path = re.sub('(/api)/\d+\.\d+', '\\1', web.ctx.path)
    if not path.startswith('/api') or path == '/api/sessions'\
       or path == '/api/systeminfo' or path == '/':
        return True
    if path.startswith('/api/ifaces'):
        return True

    try:
        usr = db.User.get(perishable_token=session.perishable_token)
        return True
    except:
        return False


def check_authorized(handler):
    if authorize():
        return handler()
    else:
        return unauthorized_error()


def check_api_version(handler):
    ver = '1.0'
    m = re.search('/api/(\d+\.\d+)', web.ctx.path)
    if m:
        ver = m.group(1)
        web.ctx.path = re.sub('(/api)/\d+\.\d+', '\\1', web.ctx.path)
    if ver <> '1.0': raise web.notfound()
    return handler()


class WebDaemon(Daemon):
    def _run(self):
        global app
        app.add_processor(check_api_version)
        app.add_processor(check_authorized)
        app.add_processor(db_connect)
        app = web.httpserver.StaticMiddleware(app.wsgifunc())
        SocketIOServer(('0.0.0.0', 8081), app, resource="socket.io").serve_forever()

if __name__ == "__main__":
    is_die = os.path.exists('/home/zonion/.llog')

    if not is_die:
        main(config.speedweb.pidfile, WebDaemon)
