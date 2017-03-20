from db import SlaveOrigin, with_transaction
import log
import glob
from util import execute
from unit import unit, Byte, KB, MB, GB, Sector
from env import config
from ipaddr import IPv4Network, IPAddress
from collections import OrderedDict as odict
import os
import ethtool
import re
import shutil
from error import exc2status
import error

is_centos = os.path.exists('/etc/sysconfig/network-scripts')

class IFaceInfo(object):
    def __init__(self, name, ipaddr, netmask, subnet, link, type, slaves=[], master=''):
        self.name    = name
        self.ipaddr  = ipaddr
        self.netmask = netmask
        self.subnet  = subnet
        self.link    = link
        self.type    = type
        self.slaves  = slaves
        self.master  = master

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        return 'IFaceInfo(name=%s, ipaddr=%s, netmask=%s, subnet=%s, link=%s, type=%s, slaves=%s, master=%s)' %\
            (self.name, self.ipaddr, self.netmask, self.subnet, self.link, self.type,
             self.slaves, self.master)


class NoBondAttr(Exception):
    pass

def read_bond_attr(name, attr):
    if os.path.exists('/sys/class/net/%s/bonding' % name):
        with open('/sys/class/net/%s/bonding/%s' % (name, attr)) as fout:
            return fout.read().rstrip()
    else:
        raise NoBondAttr

def ifaces():
    _ifaces = []
    for iface in config.ifaces.available:
        try:
            ipaddr  = ethtool.get_ipaddr(iface)
            netmask = ethtool.get_netmask(iface)
            ipv4 = IPv4Network('%s/%s' % (ipaddr, netmask))
            _, o = execute('ethtool %s' % iface, logging=False)
            link = True if re.search('Link detected:\\s+(yes)', o) else False
            info = IFaceInfo(type='normal', name=iface, ipaddr=ipaddr,
                             netmask=netmask, subnet=str(ipv4.network),
                             link=link, slaves=[], master='')
            if iface.startswith('bond'):
                try:
                    slaves = read_bond_attr(iface, 'slaves')
                    info.slaves = slaves.split(' ') if slaves else []
                    info.type   = 'bond-master'
                except Exception as e:
                    print e
                    pass
            _ifaces.append((iface, info))
        except Exception as e:
            if not iface.startswith('bond'):
                info = IFaceInfo(type='normal', name=iface, ipaddr='',
                                 netmask='', subnet='', link=False, slaves=[],
                                 master='')
                _ifaces.append((iface, info))

    bonds = [info for _,info in _ifaces if info.type == 'bond-master']
    eths =  [info for _,info in _ifaces if info.type == 'normal']
    for eth in eths:
        for bond in bonds:
            if eth.name in bond.slaves:
                eth.master = bond.name
                eth.type   = 'bond-slave'
    return odict(_ifaces)


class IPChecker(object):
    def __init__(self, ipaddr, netmask):
        self.ipaddr  = ipaddr
        self.netmask = netmask
        try:
            ipv4 = IPv4Network('%s/%s' % (self.ipaddr, self.netmask))
            self.subnet = str(ipv4.network)
        except:
            raise error.Network.IPAdressError(ipaddr)

    def check_conflict(self, excludes = []):
        for n, info in ifaces().items():
            if n not in excludes and info.subnet == self.subnet:
                raise error.Network.SameSubnet(self.subnet)

if is_centos:
    def write_os_cnf():
        _ifaces = []
        for n, info in ifaces().items():
            if info.type == 'normal' or info.type == 'bond-slave':
                _ifaces.append(Eth(n))
            else:
                _ifaces.append(Bond(n))

        for iface in _ifaces:
            cnf_path = '/etc/sysconfig/network-scripts/ifcfg-%s' % iface.name
            tmp_path = '/tmp/%s.tmp' % iface.name
            with open(tmp_path, 'w') as fout:
                fout.write(iface.os_cnf + '\n')

            shutil.copyfile(tmp_path, cnf_path)

        for cnf in glob.glob('/etc/sysconfig/network-scripts/ifcfg-eth*'):
            name = os.path.split(cnf)[-1].split('-')[-1]
            if name not in [iface.name for iface in _ifaces]:
                os.remove(cnf)

        for cnf in glob.glob('/etc/sysconfig/network-scripts/ifcfg-bond*'):
            name = os.path.split(cnf)[-1].split('-')[-1]
            if name not in [iface.name for iface in _ifaces]:
                os.remove(cnf)

        cnf_path = '/etc/sysconfig/network'
        tmp_path = '%s.tmp' % cnf_path
        gw = Gateway()
        with open(tmp_path, 'w') as fout:
            fout.write(gw.os_cnf+'\n')
        shutil.copyfile(tmp_path, cnf_path)
else:
    def write_os_cnf():
        tmp_path = '/tmp/interfaces'
        cnf_path = '/etc/network/interfaces'
        _ifaces = []
        for n, info in ifaces().items():
            if info.type == 'normal' or info.type == 'bond-slave':
                _ifaces.append(Eth(n))
            else:
                _ifaces.append(Bond(n))

        with open(tmp_path, 'w') as fout:
            fout.write('auto lo\niface lo inet loopback\n')
            gw = Gateway()

            for i in _ifaces:
                fout.write('\n')
                fout.write(i.os_cnf+'\n')
            if gw.exists:
                fout.write('\n')
                fout.write(gw.os_cnf+'\n')
        shutil.copyfile(tmp_path, cnf_path)

class GatewayBase(object):
    def __init__(self):
        cmd = 'route'
        _, o = execute(cmd, logging=False)
        m = re.search('default\\s+([0-9.]+)\\s+', o)
        self.dest = m.group(1) if m else ''

    @property
    def ipaddr(self):
        return self.dest

    @property
    def os_cnf(self):
        return ''

    @property
    def exists(self):
        return self.dest != ''

    def check_config(self, ipaddr):
        try:
            IPAddress(ipaddr)
        except:
            raise error.Network.IPAdressError(ipaddr)

        for _, info in ifaces().items():
            if not info.ipaddr:
                continue
            ipv4 = IPv4Network('%s/%s' % (ipaddr, info.netmask))
            if info.subnet == str(ipv4.network):
                return

        raise error.Network.GatewayUnreachable(ipaddr)

    def route_add(self, ipaddr):
        try:
            cmd = 'route add default gw %s' % ipaddr
            execute(cmd)
        except:
            pass

    def config(self, ipaddr):
        self.check_config(ipaddr)
        try:
            if self.dest == ipaddr:
                return
            cmd = 'route del default gw %s' % self.dest
            execute(cmd)
        except:
            pass

        self.route_add(ipaddr)

        write_os_cnf()
        log.journal_info('Gateway is configured successfully, ipaddr: %s.' % ipaddr)


class IFace(object):
    def __init__(self, name, log = True):
        self.name = name
        self.log = log

    def check_used(self):
        try:
            db.NetworkInitiator.get(eth=self.name)
        except:
            pass
        else:
            raise error.Network.InitiatorOnIFace(self.name)

    def check_config(self, ipaddr, netmask):
        if not self.exists:
            raise error.NotExistError(self.name)

        self.check_used()

        checker = IPChecker(ipaddr, netmask)
        checker.check_conflict(excludes=[self.name])

    def config(self, ipaddr, netmask):
        self.check_config(ipaddr, netmask)

        gw = Gateway()

        cmd = 'ifconfig %s %s netmask %s' % (self.name, ipaddr, netmask)
        execute(cmd)

        if gw.dest:
            gw.route_add(gw.dest)

        write_os_cnf()
        log.journal_info('Iface %s is configured successfully, ipaddr: %s, netmask: %s.' % (self.name, ipaddr, netmask))

class EthBase(IFace):
    def __init__(self, name, log = True):
        if not name.startswith('eth'):
            raise error.InvalidParam('name', name)
        super(EthBase, self).__init__(name, log)
        self.master = ''
        self.exists = False

        _ifaces = ifaces()
        if name in _ifaces:
            eth = _ifaces[name]
            self.ipaddr  = eth.ipaddr
            self.netmask = eth.netmask
            self.exists  = True
            self.master  = eth.master

    @property
    def os_cnf(self):
        return ''

class BondBase(IFace):
    MODES = {'balance-rr': 0, 'active-backup': 1, '802.3ad': 4}
    def __init__(self, name):
        if not name.startswith('bond'):
            raise error.InvalidParam('name', name)
        super(BondBase, self).__init__(name)
        _ifaces = ifaces()
        self.exists = False
        if name in _ifaces:
            bond = _ifaces[name]
            self.ipaddr = bond.ipaddr
            self.netmask = bond.netmask
            self.slaves = bond.slaves
            self.exists = True
            try:
                self.mode = read_bond_attr(name, 'mode').split()[0]
            except:
                pass

    @property
    def os_cnf(self):
        return ''

    def save_slave_db(self, slaves):
        for sname in slaves:
            SlaveOrigin.delete().where(SlaveOrigin.eth == sname).execute()
            slave = Eth(sname)
            SlaveOrigin.create(eth=sname, ipaddr=slave.ipaddr, netmask=slave.netmask)

    def delete_slave_db(self):
        for sname in self.slaves:
            SlaveOrigin.delete().where(SlaveOrigin.eth == sname).execute()

    def check_create(self, slaves, ipaddr, netmask, mode):
        if self.exists:
            raise error.ExistError(self.name)

        if mode not in self.MODES:
            raise error.InvalidParam('mode', mode)

        for sname in slaves:
            slave = Eth(sname)
            if not slave.exists:
                raise error.NotExistError(sname)
            slave.check_used()

        checker = IPChecker(ipaddr, netmask)
        checker.check_conflict(excludes=slaves + [self.name])

    def create(self, slaves, ipaddr, netmask, mode):
        slaves = slaves.split(',')
        if not isinstance(slaves, list):
            slaves = [slaves]
        self.check_create(slaves, ipaddr, netmask, mode)

        self.save_slave_db(slaves)

        cmd = 'rmmod bonding'
        execute(cmd, False)

        cmd = 'modprobe bonding mode=%s miimon=100' % self.MODES[mode]
        execute(cmd)

        gw = Gateway()

        for sname in slaves:
            cmd = 'ifconfig %s down' % sname
            execute(cmd, False)
            cmd = 'ifdown %s' % sname
            execute(cmd, False)

        cmd = 'ifconfig %s %s netmask %s' % (self.name, ipaddr, netmask)
        execute(cmd)

        cmd = 'ifenslave %s %s' % (self.name, ' '.join(slaves))
        execute(cmd)

        if gw.dest:
            gw.route_add(gw.dest)

        write_os_cnf()
        log.journal_info('Bond %s is created successfully, slaves: %s, mode: %s, ipaddr: %s, netmask: %s.' %
                (self.name, slaves, mode, ipaddr, netmask))


    def active_bond(self, ipaddr, netmask, slaves):
        pass

    def check_delete(self):
        if not self.exists:
            raise error.NotExistError(self.name)
        self.check_used()

    def delete(self):
        self.check_delete()

        gw = Gateway()

        cmd = 'ifconfig %s down' % self.name
        execute(cmd)

        cmd = 'rmmod bonding'
        execute(cmd)

        for sname in self.slaves:
            try:
                db = SlaveOrigin.get(eth=sname)
                eth = Eth(sname, log=False)
                eth.config(db.ipaddr, db.netmask)
            except:
                pass

        self.delete_slave_db()

        if gw.dest:
            gw.route_add(gw.dest)

        write_os_cnf()
        log.journal_info('Bond %s is deleted successfully.' % self.name)

if is_centos:
    class Gateway(GatewayBase):
        @property
        def os_cnf(self):
            return 'GATEWAY=%s' % self.dest if self.dest != '' else ''

    class Eth(EthBase):
        @property
        def os_cnf(self):
            if self.master:
                cnf = ['DEVICE=%s' % self.name,
                       'MASTER=%s' % self.master,
                       'SLAVE=yes',
                       'ONBOOT=yes',
                       'USERCTL=no',
                       'BOOTPROTO=none']
                return '\n'.join(cnf)
            elif not self.ipaddr:
                return ''
            else:
                cnf = ['DEVICE=%s' % self.name,
                       'IPADDR=%s' % self.ipaddr,
                       'NETMASK=%s' % self.netmask,
                       'TYPE=Ethernet',
                       'ONBOOT=yes',
                       'USERCTL=no',
                       'BOOTPROTO=static']
                return '\n'.join(cnf)

    class Bond(BondBase):
        @property
        def os_cnf(self):
            cnf = ['DEVICE=%s' % self.name,
                   'BONDING_OPTS="mode=%s miimon=100"' % self.mode,
                   'IPADDR=%s' % self.ipaddr,
                   'NETMASK=%s' % self.netmask,
                   'ONBOOT=yes',
                   'USERCTL=no',
                   'BOOTPROTO=none']
            return '\n'.join(cnf)

        def active_bond(self, ipaddr, netmask, slaves):
            cmd = 'ifup %s' % self.name
            execute(cmd)

else:
    class Gateway(GatewayBase):
        @property
        def os_cnf(self):
            return 'up route add default gw %s' % self.dest

    class Eth(EthBase):
        @property
        def os_cnf(self):
            if self.master:
                cnf = ['auto %s' % self.name,
                       'iface %s inet manual' % self.name,
                       'bond-master %s' % self.master]
                return '\n'.join(cnf)
            elif not self.ipaddr:
                return ''
            else:
                cnf = ['auto %s' % self.name,
                       'iface %s inet static' % self.name,
                       'address %s' % self.ipaddr,
                       'netmask %s' % self.netmask]
                return '\n'.join(cnf)

    class Bond(BondBase):
        @property
        def os_cnf(self):
            cnf = ['auto %s' % self.name,
                   'iface %s inet static' % self.name,
                   'address %s' % self.ipaddr,
                   'netmask %s' % self.netmask,
                   'bond-slaves %s' % ' '.join(self.slaves),
                   'bond-miimon 100',
                   'bond-mode %s' % self.mode]
            return '\n'.join(cnf)

        def active_bond(self, ipaddr, netmask, slaves):
            cmd = 'ifconfig %s %s netmask %s' % (self.name, ipaddr, netmask)
            execute(cmd)

            cmd = 'ifenslave %s %s' % (self.name, ' '.join(slaves))
            execute(cmd)

@exc2status
@with_transaction
def config_interface(iface, address, netmask):
    try:
        eth = Eth(iface)
        eth.config(address, netmask)
    except error.InternalError as e:
        log.error(caused(e).detail)
        raise error.InternalError()

@exc2status
@with_transaction
def create_bond(name, slaves, address, netmask, mode):
    try:
        bond = Bond(name)
        bond.create(slaves, address, netmask, mode)
    except error.InternalError as e:
        log.error(caused(e).detail)
        raise error.InternalError()

@exc2status
@with_transaction
def config_bond(name, address, netmask):
    try:
        bond = Bond(name)
        bond.config(address, netmask)
    except error.InternalError as e:
        log.error(caused(e).detail)
        raise error.InternalError()

@exc2status
@with_transaction
def delete_bond(name):
    try:
        bond = Bond(name)
        bond.delete()
    except error.InternalError as e:
        log.error(caused(e).detail)
        raise error.InternalError()

@exc2status
@with_transaction
def config_gateway(address):
    try:
        gw = Gateway()
        gw.config(address)
    except error.InternalError as e:
        log.error(caused(e).detail)
        raise error.InternalError()

api = ['config_interface', 'create_bond', 'config_bond', 'delete_bond', 'config_gateway']
