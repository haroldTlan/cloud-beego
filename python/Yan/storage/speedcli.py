#!/usr/bin/env python
import re
from cmd import Cmd
import os
from ctypes import *
from xml.etree.ElementTree import parse, tostring, iterparse
import json
import time
import traceback
import math
import string
import sys
import readline
import rest
from collections import OrderedDict as odict
from unit import Sector
from util import execute
from getopt import getopt
import error
import zerod
from datetime import datetime, timedelta

class UnknownCmd(Exception):
    def __init__(self, msg):
        Exception.__init__(self, msg)

class UnknownArgument(Exception):
    def __init__(self, msg):
        Exception.__init__(self, msg)

class LackOfArgument(Exception):
    def __init__(self):
        Exception.__init__(self)

class CmdArgFormat(Exception):
    def __init__(self, msg):
        Exception.__init__(self, msg)

class CustomOutput(Exception):
    def __init__(self, msg):
        Exception.__init__(self, msg)

NoDefault = object()

class SpeedCli(Cmd):
    prompt = 'speed> '
    cmd_map = {}
    def __init__(self):
        self.rest = rest.rest('localhost')
        Cmd.__init__(self)

    @classmethod
    def init(cls):
        module = sys.modules[__name__]
        for name in dir(module):
            obj = eval(name)
            try:
                if issubclass(obj, SpeedCliCmd):
                    SpeedCli._install_cmd_class(obj)
            except:
                pass

    @classmethod
    def _install_cmd_class(cls, cmdclass):
        cmd = cmdclass()
        for attr in dir(cmd):
            method = getattr(cmd, attr)
            if callable(method) and attr.endswith('_cmd'):
                cls._install_cmd_method(cls.cmd_map, cmdclass, attr, method)
    
    @classmethod
    def _install_cmd_method(cls, cmd_map, cmdclass, attr, method):
        cmdname = attr.replace('_cmd', '')
        classname = cmdclass.__name__.lower() 
        cmd_map.setdefault(classname, {})
        cmd_map[classname][cmdname] = method.cmd_opts if hasattr(method, 'cmd_opts') else {}
        setattr(cls, 'complete_%s' % classname, cls._complete)
        setattr(cls, 'do_%s' % classname, cls._do)

    def _do(self, args):
        words = self.lastcmd.split()
        try:
            if len(words) >= 2:
                method = self._get_method(words)
                if '--help' in words:
                    print method.__doc__
                    return
                args = self._get_args(words[2:])
                self._check_method_args(method, args)
                o = method(**args)
                if o: print o
                print 'command success.'
        except UnknownCmd as e:
            print 'unknown command [%s].' % e.message
        except UnknownArgument as e:
            print 'unknown command argument [%s].' % e.message
        except CmdArgFormat as e:
            print 'command argument [%s] format error.' % e.message
        except LackOfArgument:
            print 'command lack of options.'
        except rest.NoResponse:
            print 'command failed, description: server no repsonse.'
        except rest.RequestTimeout:
            print 'command may be failed, description: repsonse timeout.'
        except rest.ResponseError as e:
            if e.status == 400 and 'description' in e.content:
                print 'command failed, description: %s' % e.content['description']
            else:
                print 'unkown exception.'
        except CustomOutput as e:
            print e.message
        except error.InvalidParam as e:
            print 'command failed, description: %s' % e.message
        except Exception:
            traceback.print_exc()
            print 'unkown exception.'

    def completenames(self, text, *ignored):
        dotext = 'do_'+text
        return ['%s ' % a[3:] for a in self.get_names() if a.startswith(dotext)]

    def _to_completion(self, cmd_opts, prefix=''):
        return ['%s='%opt if val is NoDefault else '%s=%s(*)'%(opt, val) for opt, val in cmd_opts if opt.startswith(prefix)]

    def _complete(self, text, line, begidx, endidx):
        words = line.split()
        verb_map = self.cmd_map[words[0]]
        completion = []

        if len(words) == 1:
            completion = verb_map.keys()
        elif len(words) == 2:
            completion = [verb for verb in verb_map if verb.startswith(words[1])]
            if len(completion) == 1:
                completion = ['%s ' % completion[0]]
            if words[1] in verb_map and line[-1] == ' ':
                completion = self._to_completion(verb_map[words[1]].items())
        else:
            pairs = re.findall('([-A-Za-z0-9]+)(?==)=\s*([-.,:A-Za-z0-9]*)', ' '.join(words[2:]))
            lastword = re.search('([-.,A-Za-z0-9]+)\s*$', line).group(1)
            opts = set([opt for opt, val in pairs])
            all_opts = set([opt for opt, val in verb_map[words[1]].items()])
            cand_opts = all_opts.difference(opts)
            cmd_opts = [(opt, verb_map[words[1]][opt]) for opt in cand_opts]
            if not pairs: #'name'
                completion = self._to_completion(cmd_opts, lastword)
            elif pairs[-1][1] <> '':
                if pairs[-1][1] <> lastword: #'name=lv raid'
                    completion = self._to_completion(cmd_opts, lastword)
                elif line[-1] <> ' ':#'name=lv'
                    completion = []
                elif len(cand_opts) <> 0: #'name=lv '
                    completion = self._to_completion(cmd_opts)

        if len(completion) == 1 and completion[0][-1] == ')':
            completion = [completion[0].split('=')[0]+'=']
        return completion

    def _get_method(self, words):
        try:
            cmdclass = eval(words[0].capitalize())
            rest = getattr(self.rest, words[0], None)
            cmd = cmdclass(self, rest)
            method = getattr(cmd, '%s_cmd' % words[1])
            return method
        except:
            traceback.print_exc()
            raise UnknownCmd('%s %s' % (words[0], words[1]))

    def _check_method_args(self, method, args):
        cmd_opts = method.cmd_opts if hasattr(method, 'cmd_opts') else {}
        opts = dict([(k.replace('-', '_'), v) for k, v in cmd_opts.items()])
        for k in args:
            if k not in opts:
                raise UnknownArgument(k)

        opts.update(args)
        for v in opts.values():
            if v is NoDefault:
                raise LackOfArgument() 

    def _get_args(self, words):
        pairs = re.findall('([-A-Za-z0-9]+)(?==)=\s*([-.,:A-Za-z0-9_]*)', ' '.join(words))
        return dict([(opt.replace('-','_'), val) for opt, val in pairs])

    def do_EOF(self, line):
        return True

    def do_help(self, line):
        return False

    def get_names(self):
        return [name for name in dir(self.__class__) if name <> 'do_help']

    def complete_help(self, *args):
        return []

    def emptyline(self):
        return False

    def preloop(self):
        readline.parse_and_bind("set show-all-if-unmodified on")
        readline.parse_and_bind("set show-all-if-ambiguous on")

    do_q = do_exit = do_quit = do_EOF

class SpeedCliCmd(object):
    def __init__(self, cli=None, rest=None):
        self.cli = cli
        self.rest = rest

    def _query(self, id):
        info = self.rest.query(id)
        return self._fmt_info(info)

    def _list(self, name):
        o = self.rest.list()
        return self._fmt_list(name, o)

    def _fmt_list(self, name, list_info):
        total = '%s Total: %s' % (name, len(list_info))
        if list_info:
            return '%s\n\n%s' %\
                ('\n\n'.join([self._fmt_info(info) for info in list_info]), total)
        else:
            return total

    def _fmt_info(self, info):
        max_key_len = max([len(name) for name in info.keys()])
        fmt = '%' + str(max_key_len) + 's : %-s'
        return '\n'.join([fmt % (name, self._fmt_attr(val, max_key_len)) for name, val in info.items()])

    def _fmt_attr(self, val, max_key_len):
        if not val: return 'N/A'
        elif isinstance(val, list):
            if max([len(e) for e in val]) > 20:
                return (',\n' + ' ' * (max_key_len + 3)).join(val)
            else:
                return ','.join(val)
        else: return val

def cmd_opts(*opts, **opt_dict):
    def _cmd_opts(func):
        def __cmd_opts(*vargs, **kv):
            return func(*vargs, **kv)
        __cmd_opts.cmd_opts = dict([(o.replace('_', '-'), NoDefault) for o in opts])
        for k, v in opt_dict.items():
            __cmd_opts.cmd_opts[k.replace('_', '-')] = v
        return __cmd_opts
    return _cmd_opts

def capitalize(s):
    s = ' '.join(w.capitalize() for w in s.split(' '))
    return '_'.join(w.capitalize() for w in s.split('_'))

class Disk(SpeedCliCmd):
    #@cmd_opts('location')
    #def query_cmd(self, location):
    #    return self._query(location)

    def list_cmd(self):
        return self._list('Disk')

    @cmd_opts(location='all')
    def format_cmd(self, location='all'):
        self.rest.format(location)

    @cmd_opts('location', role='global_spare')
    def set_cmd(self, location, role='global_spare'):
        self.rest.set_role(location, role)

    def zero_cmd(self):
        answer = raw_input('This command will cause data loss. Are you sure to continue?(Y/n):')
        while answer not in ['Y', 'n']:
            answer = raw_input('please input(Y/n):')
        if answer == 'n':
            raise CustomOutput('command is abandoned.')
        elif answer == 'Y':
            zerod.zero_disks()

    def query_zero_progress_cmd(self):
        def to_timedelta(total_sec):
            hours = total_sec / 3600
            mins = (total_sec-3600*hours)/60
            secs = total_sec-3600*hours-60*mins
            return timedelta(hours=hours,minutes=mins,seconds=secs)

        def fmt_progress(p):
            o = odict()
            o['Location'] = p['location']
            o['Capacity'] = p['capacity']
            o['Copied'] = p['copied']
            o['Cost Time'] = str(to_timedelta(p['cost']))
            o['Average Speed'] = p['avr_speed']
            o['Status']   = p['status']
            o['Begin Time'] = datetime.fromtimestamp(p['begin']).strftime('%Y/%m/%d %H:%M:%S')
            o['Progress'] = '%s%%' % p['progress']
            return super(Disk, self)._fmt_info(o)

        progress = zerod.query_zero_progress()
        i,c,e,io = 0,0,0,0
        for p in progress:
            if p['status'] == 'inprogress': i+=1
            elif p['status'] == 'completed': c+=1
            elif p['status'] == 'error': e+=1
            elif p['status'] == 'ioerror': io+=1
        detail = '\n\n'.join([fmt_progress(p) for p in progress])
        summary = 'Disk Total: %s, In Progress: %s, Completed: %s, Error: %s, IOError: %s' % \
                (len(progress), i, c, e, io)
        return '%s\n\n%s' % (detail, summary)

    def _fmt_info(self, disk):
        info = odict()
        info['Location'] = disk['location']
        info['Vendor'] = disk['vendor']
        info['RPM'] = disk['rpm']
        info['Health'] = disk['health'].capitalize()
        info['Role'] = capitalize(disk['role'])
        info['Host'] = disk['host'].capitalize()
        if 'raid' in disk:
            info['Raid'] = disk['raid']
        else:
            info['Raid'] = None
        return super(Disk, self)._fmt_info(info)

class Raid(SpeedCliCmd):
    #@cmd_opts('name')
    #def query_cmd(self, name):
    #    return self._query(name)

    def list_cmd(self):
        list_info = self.rest.list()
        map = {}
        for disk in self.cli.rest.disk.list():
            if disk['role'] == 'data' and disk['raid']:
                map.setdefault(disk['raid'], []).append(disk['location'])
        for raid in list_info:
            raid['raid-disks'] = map.get(raid['name'], [])
        return self._fmt_list('Raid', list_info)

    def _fmt_info(self, raid):
        info = odict()
        info['Name'] = raid['name']
        info['Level'] = raid['level']
        info['Chunk'] = '%sKB' % raid['chunk_kb']
        info['Health'] = raid['health'].capitalize()
        info['Capacity'] = str(Sector(raid['cap_sector']).fit())
        info['Used Capacity'] = str(Sector(raid['used_cap_sector']).fit())
        info['Raid-Disks'] = raid['raid-disks'] if raid.has_key('raid-disks') else None
        return super(Raid, self)._fmt_info(info)

    @cmd_opts('name', 'raid_disks', level=5, chunk='64KB', spare_disks='', rebuild_priority='low', sync='no')
    def create_cmd(self, name, raid_disks, level=5, chunk='64KB', spare_disks='', rebuild_priority='low', sync='no'):
        status = self.rest.create(name, level, chunk, raid_disks, spare_disks, rebuild_priority, sync)
        return status

    @cmd_opts('name')
    def delete_cmd(self, name):
        status = self.rest.delete(name)
        return status

class Volume(SpeedCliCmd):
    #@cmd_opts('name')
    #def query_cmd(self, name):
    #    return self._query(name)

    def list_cmd(self):
        list_info = self.rest.list()
        map = {}
        for initr in self.cli.rest.initiator.list():
            for v in initr['volumes']:
                map.setdefault(v, []).append(initr['wwn'])
        for volume in list_info:
            volume['initiators'] = map.get(volume['name'], [])
        return self._fmt_list('Volume', list_info)

    def _fmt_info(self, volume):
        info = odict()
        info['Name'] = volume['name']
        info['Health'] = volume['health'].capitalize()
        info['Capacity'] = str(Sector(volume['cap_sector']).fit())
        if volume['initiators']:
            info['Mapped'] = volume['initiators']
        else:
            info['Mapped'] = None
        return super(Volume, self)._fmt_info(info)

    @cmd_opts('name', 'raid', 'capacity')
    def create_cmd(self, name, raid, capacity):
        return self.rest.create(name, raid, capacity)

    @cmd_opts('name')
    def delete_cmd(self, name):
        return self.rest.delete(name)

    @cmd_opts('name')
    def expand_cmd(self, name):
        return self.rest.expand(name)

class Initiator(SpeedCliCmd):
    #@cmd_opts('wwn')
    #def query_cmd(self, wwn):
    #    return self._query(wwn)

    def list_cmd(self):
        return self._list('Initiator')

    def _fmt_info(self, initr):
        info = odict()
        info['WWN'] = initr['wwn']
        info['Portals'] = initr['portals']
        info['Mapping'] = initr['volumes']
        return super(Initiator, self)._fmt_info(info)

    @cmd_opts('portals', wwn='')
    def create_cmd(self, portals, wwn=''):
        status = self.rest.create(wwn, portals)
        if not wwn:
            return 'wwn %s is created.' % status['wwn']
        else:
            return status

    @cmd_opts('wwn')
    def delete_cmd(self, wwn):
        return self.rest.delete(wwn)

    @cmd_opts('wwn', 'volume')
    def map_cmd(self, wwn, volume):
        return self.rest.map(wwn, volume)

    @cmd_opts('wwn', 'volume')
    def unmap_cmd(self, wwn, volume):
        return self.rest.unmap(wwn, volume)

class Interface(SpeedCliCmd):
    #@cmd_opts('iface')
    #def query_cmd(self, iface):
    #    return self._query(eth)
    def list_cmd(self):
        return self._list('Interface')

    def _fmt_info(self, iface):
        info = odict()
        info['name']    = iface['id']
        info['type']    = iface['type']
        if iface['type'] == 'normal':
            info['ipaddr']  = iface['ipaddr']
            info['netmask'] = iface['netmask']
            info['link']    = iface['link']
            info['type']    = iface['type']
        elif iface['type'] == 'bond-master':
            info['ipaddr']  = iface['ipaddr']
            info['netmask'] = iface['netmask']
            info['link']    = iface['link']
            info['slaves']  = ','.join(iface['slaves'])
            info['mode']    = iface['mode']
        elif iface['type'] == 'bond-slave':
            info['ipaddr']  = 'N/A'
            info['netmask'] = 'N/A'
            info['master']  = iface['master']
        return super(Interface, self)._fmt_info(info)

    @cmd_opts('iface', 'address', 'netmask')
    def config_cmd(self, iface, address, netmask):
        try:
            return self.rest.config(iface, address, netmask)
        except rest.NoResponse:
            try:
                time.sleep(10)
                self._list('Interface')
            except:
                raise rest.NoResponse()

class Bond(SpeedCliCmd):
    @cmd_opts('address', 'netmask', mode='balance-rr', slaves='eth0,eth1')
    def create_cmd(self, address, netmask, mode='balance-rr', slaves='eth0,eth1'):
        try:
            return self.rest.create('bond0', slaves, address, netmask, mode)
        except rest.NoResponse:
            try:
                time.sleep(10)
                self._list('Interface')
            except:
                raise rest.NoResponse()

    @cmd_opts('address', 'netmask')
    def config_cmd(self, address, netmask):
        try:
            return self.rest.config('bond0', address, netmask)
        except rest.NoResponse:
            try:
                time.sleep(10)
                self._list('Interface')
            except:
                raise rest.NoResponse()

    @cmd_opts()
    def delete_cmd(self):
        try:
            return self.rest.delete('bond0')
        except rest.NoResponse:
            try:
                time.sleep(10)
                self._list('Interface')
            except:
                raise rest.NoResponse()

class Gateway(SpeedCliCmd):
    def query_cmd(self):
        gw = self.rest.query()
        return self._fmt_info(gw)

    @cmd_opts('address')
    def config_cmd(self, address):
        self.rest.config(address)

class System(SpeedCliCmd):
    def poweroff_cmd(self):
        self.cli.rest.command.poweroff()

    def reboot_cmd(self):
        self.cli.rest.command.reboot()

    def init_cmd(self):
        answer = raw_input('This command will cause data loss. Are you sure to continue?(Y/n):')
        while answer not in ['Y', 'n']:
            answer = raw_input('please input(Y/n):')
        if answer == 'n':
            raise CustomOutput('command is abandoned.')
        elif answer == 'Y':
            self.cli.rest.command.init()

    def status_cmd(self):
        #{'status': 'warning', 'disks': {'status': 'warning', 'list': [{'1.1.2': 'failed'}]},\
        # 'volumes': {'status': 'warning', 'list': [{'lv': 'failed'}]}}
        #Formatted Output:
        #Status: Warning
        #Disks: Warning
        #  1.1.2: Failed
        #Raids: Warning
        #  rd: Failed
        #Volumes: Warning
        #  lv: Failed
        ds = self.cli.rest.devicestatus.query()
        o = 'Status: %s' % ds['status'].capitalize()
        if ds['status'] == 'normal':
            return o
        else:
            if 'disks' in ds:
                o += '\nDisks: Warning'
                for disk in ds['disks']:
                    k,v = disk.items()[0]
                    o += '\n    %s: %s' % (k, v.capitalize())
            if 'raids' in ds:
                o += '\nRaids: Warning'
                for raid in ds['raids']:
                    k,v = raid.items()[0]
                    o += '\n    %s: %s' % (k, v.capitalize())
            if 'volumes' in ds:
                o += '\nVolumes: Warning'
                for volume in ds['volumes']:
                    k,v = volume.items()[0]
                    o += '\n    %s: %s' % (k, v.capitalize())
            return o

class User(SpeedCliCmd):
    @cmd_opts('name', 'old_password', 'new_password')
    def change_password_cmd(self, name, old_password, new_password):
        self.rest.change_password(name, old_password, new_password)

class Filesystem(SpeedCliCmd):
    def list_cmd(self):
        return self._list('Filesystem')

    def _fmt_info(self, fs):
        info = odict()
        info['Name'] = fs['name']
        info['Volume'] = fs['volume']
        info['Type'] = fs['type']
        return super(Filesystem, self)._fmt_info(info)

    @cmd_opts('name', 'volume', 'type')
    def create_cmd(self, name, volume, type):
        return self.rest.create(name, volume, type)

    @cmd_opts('name')
    def delete_cmd(self, name):
        return self.rest.delete(name)

    @cmd_opts('raidname', 'volumename', 'fsname', 'chunk')
    def fastcreate_cmd(self, raidname, volumename, fsname, chunk):
        return self.rest.fastcreate(raidname, volumename, fsname, chunk)

if __name__ == '__main__':
    SpeedCli.init()
    cli = SpeedCli()
    opts = dict(getopt(sys.argv[1:], 's')[0])
    if '-s' in opts:
        cli.prompt = ''
    try:
        cli.cmdloop()
    except:
        sys.exit(0)
