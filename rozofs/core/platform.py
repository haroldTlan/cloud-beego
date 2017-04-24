# -*- coding: utf-8 -*-
#
# Copyright (c) 2013 Fizians SAS. <http://www.fizians.com>
# This file is part of Rozofs.
#
# Rozofs is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published
# by the Free Software Foundation, version 2.
#
# Rozofs is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see
# <http://www.gnu.org/licenses/>.

import Pyro.core
from Pyro.errors import PyroError, NamingError, ProtocolError
import subprocess
import time
import os

from zoofs.core.constants import STORAGED_MANAGER, EXPORTD_MANAGER, \
    AGENT_PORT, LAYOUT_VALUES, LAYOUT_SAFE, EXPORTS_ROOT, \
    STORAGES_ROOT, ROZOFSMOUNT_MANAGER
from zoofs.core.agent import ServiceStatus
from zoofs.core.exportd import VolumeConfig, ClusterConfig, ExportConfig
from zoofs.core.storaged import StorageConfig
from zoofs.core.zoofsmount import RozofsMountConfig
from socket import socket


class ConnectionError(Exception): pass

def check_reachability(host):
    with open('/dev/null', 'w') as devnull:
        if subprocess.call(['ping', '-c', '1', '-w', '2', host],
            stdout=devnull, stderr=devnull) is not 0:
                raise ConnectionError("host (%s) is not reachable" % host)

def get_proxy(host, manager):
    try:
        return Pyro.core.getProxyForURI('PYROLOC://%s:%s/%s' % (host, str(AGENT_PORT), manager))
    except:
        raise Exception("no agent %s reachable for %s" % (manager, host))

class Role(object):
    EXPORTD = 1
    STORAGED = 2
    ROZOFSMOUNT = 4
    ROLES = [1, 2, 4]

ROLES_STR = {Role.EXPORTD: "exportd", Role.STORAGED: "storaged", Role.ROZOFSMOUNT: "rozofsmount"}

class ExportStat(object):
    def __init__(self, eid= -1, vid= -1, bsize= -1, blocks= -1, bfree= -1, files= -1, ffree= -1):
        self.eid = eid
        self.vid = vid
        self.bsize = bsize
        self.blocks = blocks
        self.bfree = bfree
        self.files = files
        self.ffree = ffree

class StorageStat(object):
    def __init__(self, sid= -1, status= -1, size= -1, free= -1):
        self.sid = sid
        self.status = status
        self.size = size
        self.free = free

class VolumeStat(object):
    def __init__(self, vid= -1, bsize= -1, bfree= -1, sstats=[]):
        self.vid = vid
        self.bsize = bsize
        self.bfree = bfree
        self.sstats = sstats

class Node(object):

    def __init__(self, host, roles=0):
        self._host = host
        self._roles = roles
        # for all below key is Role
        self._proxies = {}
        # does our node is connected and running
        self._up = False

    def __del(self):
        self._release_proxies()

    def _initialize_proxies(self):
        try:
            if self.has_roles(Role.EXPORTD) and Role.EXPORTD not in self._proxies:
                self._proxies[Role.EXPORTD] = get_proxy(self._host, EXPORTD_MANAGER)
            if self.has_roles(Role.STORAGED) and Role.STORAGED not in self._proxies:
                self._proxies[Role.STORAGED] = get_proxy(self._host, STORAGED_MANAGER)
            if self.has_roles(Role.ROZOFSMOUNT) and Role.ROZOFSMOUNT not in self._proxies:
                self._proxies[Role.ROZOFSMOUNT] = get_proxy(self._host, ROZOFSMOUNT_MANAGER)
        except Exception as e:
            self._release_proxies()
            raise e

    def _release_proxies(self):
        for p in self._proxies.values():
            p.getProxy()._release()
        self._up = False

    def _try_up(self):
        """ check if a node is up if not try to set it up """
        if self._up == False:
            try:
                # is it reachable ?
                check_reachability(self._host)
                # yes, so try to connect to agents
                self._initialize_proxies()
            except:
                return False
            self._up = True

        return True

    def is_up(self):
        return self._up

    def set_roles(self, roles):
        self._roles = roles
        if self._up:
            self._release_proxies()

    def get_roles(self):
        return self._roles

    def has_roles(self, roles):
        return self._roles & roles == roles

    def has_one_of_roles(self, roles):
        for role in [r for r in Role.ROLES if r & roles == r]:
            if self._roles & role == role:
                return True
        return False

    def get_configurations(self, roles=Role.EXPORTD | Role.STORAGED | Role.ROZOFSMOUNT):

        configurations = {}

        if not self._try_up():
            for role in [r for r in Role.ROLES if r & roles == r and self.has_roles(r)]:
                configurations[role] = ConnectionError("host not reachable")
            return configurations

        for role in [r for r in Role.ROLES if r & roles == r and self.has_roles(r)]:
            try:
                configurations[role] = self._proxies[role].get_service_config()
            except NamingError as e:
                configurations[role] =  type(e)("no %s agent reachable" % (ROLES_STR[role]))
            except ProtocolError as e:
                configurations[role] =  type(e)("rozofs-manager agent is not reachable")
            except Exception as e:
                configurations[role] = type(e)(str(e))

        return configurations

    def set_configurations(self, configurations):
        statuses = {}
        if not self._try_up():
            for r in configurations.keys():
                if self.has_roles(r):
                    statuses[r] = ConnectionError("host not reachable")
            return statuses

        for r, c in configurations.items():
            if self.has_roles(r):
                try:
                    statuses[r] = self._proxies[r].set_service_config(c)
                except NamingError as e:
                    statuses[r] =  type(e)("no %s agent reachable" % (ROLES_STR[r]))
                except ProtocolError as e:
                    statuses[r] =  type(e)("rozofs-manager agent is not reachable")
                except Exception as e:
                    statuses[r] = type(e)(str(e))
        return statuses

    def get_statuses(self, roles=Role.EXPORTD | Role.STORAGED | Role.ROZOFSMOUNT):

        statuses = {}

        if not self._try_up():
            for role in [r for r in Role.ROLES if r & roles == r and self.has_roles(r)]:
                statuses[role] = ConnectionError("host not reachable")
            return statuses

        for role in [r for r in Role.ROLES if r & roles == r and self.has_roles(r)]:
            try:
                statuses[role] = self._proxies[role].get_service_status()
            except NamingError as e:
                statuses[role] = type(e)("no %s agent reachable" % (ROLES_STR[role]))
            except ProtocolError as e:
                statuses[role] = type(e)("rozofs-manager agent is not reachable")
            except Exception as e:
                statuses[role] = type(e)(str(e))

        return statuses

    def set_statuses(self, statuses):

        changes = {}

        if not self._try_up():
            for r, s in statuses.items():
                if self.has_roles(r):
                    changes[r] = ConnectionError("host not reachable")
            return changes

        for r, s in statuses.items():
            if self.has_roles(r):
                try:
                    changes[r] = self._proxies[r].set_service_status(s)
                except NamingError as e:
                    changes[r] = type(e)("no %s agent reachable" % (ROLES_STR[role]))
                except ProtocolError as e:
                    changes[r] = type(e)("rozofs-manager agent is not reachable")
                except Exception as e:
                    changes[r] = type(e)(str(e))

        return changes

    def set_rebuild(self, exports_list, cid, sid, device):
        if not self._try_up():
            raise Exception("%s is not reachable." % self._host)

        try:
            self._proxies[Role.STORAGED].start_rebuild(exports_list, cid, sid, device)
        except NamingError:
            raise Exception("no %s agent reachable for host: %s." % (ROLES_STR[Role.STORAGED], self._host))
        except ProtocolError:
            raise Exception("rozofs-manager agent is not reachable for host: %s." % self._host)
        except Exception:
            raise


class Platform(object):
    """ A rozofs platform."""

    def __init__(self, export_hosts=['localhost'], roles=Role.EXPORTD | Role.STORAGED | Role.ROZOFSMOUNT):
        """
        Args:
            export_hosts: list of export host (should be part of the platform !).
            roles: with which roles the platform must be built 
        """
        self._export_hosts = export_hosts
        self._active_export_host = self._get_active_export_host(export_hosts)
        self._nodes = self._get_nodes(self._active_export_host, roles)

    def _get_active_export_host(self, export_hosts):

        # Check duplicate value
        if len(export_hosts) != (len(set(export_hosts))):
            raise Exception('Duplicate export host.')

        valid_hosts = []
        unvalid_hosts = dict()

         # Check each export host
        for h in export_hosts:
            try :
                check_reachability(h)
                p = get_proxy(h, EXPORTD_MANAGER)
            except Exception as e:
                unvalid_hosts.update({h: e})
                continue
            try:
                try:
                    # If we can read the exportd config file:
                    # host is considered active
                    if p.get_service_config():
                        valid_hosts.append(h)
                except NamingError as e:
                    raise Exception("no %s agent reachable" % ROLES_STR[Role.EXPORTD])
                except ProtocolError as e:
                    raise Exception("rozofs-manager agent is not reachable")
            except Exception as e:
                unvalid_hosts.update({h: e})
                pass

        # Check nb. of active export
        if len(valid_hosts) == 1:
            return valid_hosts[0]
        elif len(valid_hosts) > 1:
            raise Exception('Several active export hosts simultaneously! Fix that!')
        else:
            errors =[]
            for h, e in unvalid_hosts.items():
                errors.append("%s: %s" % (h, e))
            raise Exception('Unable to get valid export configuration file.\n'+ "\n".join(errors))

    def _get_nodes(self, hostname, roles=Role.EXPORTD | Role.STORAGED | Role.ROZOFSMOUNT):
        nodes = {}

        exportd_node = Node(hostname, Role.EXPORTD)

        nodes[hostname] = exportd_node

        if Role.STORAGED & roles == Role.STORAGED:

            node_configs = exportd_node.get_configurations(Role.EXPORTD)
            if not node_configs:
                raise Exception("%s unreachable." % hostname)

            econfig = node_configs[Role.EXPORTD]

            if econfig is None:
                raise "exportd node is off line."

            for h in [s for v in econfig.volumes.values()
                            for c in v.clusters.values()
                            for s in c.storages.values()]:
                node_roles = Role.STORAGED
                node_roles = node_roles | Role.ROZOFSMOUNT
                if Role.ROZOFSMOUNT & roles == Role.ROZOFSMOUNT:
                    # check if has rozofsmount
                    try :
                        check_reachability(h)
                        p = get_proxy(h, ROZOFSMOUNT_MANAGER)
                        p.get_service_config()
                    except NamingError as e:
                        node_roles = node_roles ^ Role.ROZOFSMOUNT
                    except Exception as e:
                        pass

                if h in nodes:  # the exportd node !
                    nodes[h].set_roles(nodes[h].get_roles() | node_roles)
                else:
                    nodes[h] = Node(h, node_roles)

        return nodes

    def _check_nodes(self):
        """ Check if all nodes have a platform agent running """
        for n in self._nodes:
            if not n.check_platform_manager():
                raise Exception("%s: check platform failed." % n._host)

    # the first exportd nodes
    def _get_exportd_node(self):
        for n in self._nodes.values():
            if n.has_roles(Role.EXPORTD):
                return n

    def list_nodes(self, roles=Role.EXPORTD | Role.STORAGED | Role.ROZOFSMOUNT):
        """ Get all nodes managed by this platform

        Args:
            roles: roles that node should have

        Return:
            A dict: keys are host names, values are roles (as xored flags)
        """
        nodes = {}
        for h, n in self._nodes.items():
            if n.has_one_of_roles(roles):
                nodes[h] = n.get_roles()
        return nodes

    def get_statuses(self, hosts=None, roles=Role.EXPORTD | Role.STORAGED | Role.ROZOFSMOUNT):
        """ Get statuses for named nodes and roles

        Args:
            hosts : list of hosts to get statuses from, if None all host are
                    checked

            roles : for which roles statuses should be retrieved
                    if a given host doesn't have this role the return statuses
                    will not contain key for this role (and might be empty).

        Return:
            A dict: keys are host names, values are dicts {Role: ServiceStatus}
                    or None if node is off line
        """
        statuses = {}
        if hosts is None:
            for h, n in self._nodes.items():
                statuses[h] = n.get_statuses(roles)
        else:
            for h in hosts:
                if h not in self._nodes:
                    raise Exception("Unknown node: %s." % h)
                statuses[h] = self._nodes[h].get_statuses(roles)
        return statuses

    def set_statuses(self, statuses):
        """ Set statuses

        Args:
            statuses : A dict where keys are host names,
                       values are dicts {Role: ServiceStatus}
        Return:
            A dict: keys are host names, values are dicts {Role: True or False}
            or {Role: Exception} if a error occurred
        Warning:
            assuming user knows what he is doing start share before
            exportd or storaged will lead to errors
        """
        changes = {}
        for h, s in statuses.items():
            changes[h] = self._nodes[h].set_statuses(s)

        return changes

    def set_status(self, hosts=None, roles=Role.EXPORTD | Role.STORAGED | Role.ROZOFSMOUNT, status=ServiceStatus.STOPPED):
        """ Convenient method to set the same status to hosts.

        Args:
            hosts: list of hosts to set status , if None all host are set
            roles: for which roles status should be set
        Return:
            A dict: keys are host names, values are dicts {Role: True or False}
            or {Role: Exception} if a error occurred
        Warning:
            see set_statuses
        """
        # while Node set statuses is applied only if a node has this role
        # we just need to call set statuses on all nodes
        statuses_to_set = {}
        for role in [r for r in Role.ROLES if r & roles == r]:
            statuses_to_set[role] = status
        statuses = {}
        if hosts is None:
            for host in self._nodes.keys():
                statuses[host] = statuses_to_set
        else:
            for host in hosts:
                statuses[host] = statuses_to_set

        return self.set_statuses(statuses)

    def start(self, hosts=None, roles=Role.EXPORTD | Role.STORAGED | Role.ROZOFSMOUNT):
        """ Convenient method to start all nodes with a role
        Args:
            hosts: list of hosts to start , if None all host are started
            roles: which roles to start
        Return:
            A dict: keys are host names, values are dicts {Role: True or False}
            or {Role: Exception} if a error occurred
        """

        # check if hosts are managed
        if hosts is not None:
            for h in hosts:
                if h not in self._nodes.keys():
                    raise Exception("Unknown node: %s." % h)

        if hosts is None:
            hosts = self._nodes.keys()

        # Changes dict to return
        changes = {}

        # take care of the starting order
        if roles & Role.STORAGED == Role.STORAGED:
            changes = self.set_status(hosts, Role.STORAGED, ServiceStatus.STARTED)

        if roles & Role.EXPORTD == Role.EXPORTD:
            e_changes = self.set_status(hosts, Role.EXPORTD, ServiceStatus.STARTED)
            for h in set(changes) & set(e_changes):
                changes[h].update(e_changes[h].items())
            for h in set(changes) ^ set(e_changes):
                changes[h] = e_changes[h]

        if roles & Role.ROZOFSMOUNT == Role.ROZOFSMOUNT:
            time.sleep(1)
            r_changes = self.set_status(hosts, Role.ROZOFSMOUNT, ServiceStatus.STARTED)
            for h in set(changes) & set(r_changes):
                changes[h].update(r_changes[h].items())
            for h in set(changes) ^ set(r_changes):
                changes[h] = r_changes[h]

        return changes

    def stop(self, hosts=None, roles=Role.EXPORTD | Role.STORAGED | Role.ROZOFSMOUNT):
        """ Convenient method to stop all nodes with a role
        Args:
            the roles to be stopped
        """
        if hosts is None:
            hosts = self._nodes.keys()

        # Changes dict to return
        changes = {}

        # take care of the stopping order
        if roles & Role.ROZOFSMOUNT == Role.ROZOFSMOUNT:
            changes = self.set_status(hosts, Role.ROZOFSMOUNT, ServiceStatus.STOPPED)
        if roles & Role.EXPORTD == Role.EXPORTD:
            e_changes = self.set_status(hosts, Role.EXPORTD, ServiceStatus.STOPPED)
            for h in set(changes) & set(e_changes):
                changes[h].update(e_changes[h].items())
            for h in set(changes) ^ set(e_changes):
                changes[h] = e_changes[h]
        if roles & Role.STORAGED == Role.STORAGED:
            s_changes = self.set_status(hosts, Role.STORAGED, ServiceStatus.STOPPED)
            for h in set(changes) & set(s_changes):
                changes[h].update(s_changes[h].items())
            for h in set(changes) ^ set(s_changes):
                changes[h] = s_changes[h]

        return changes

    def rebuild_storage_node(self, host, cid=None, sid=None, device=None):
        """ Convenient method to rebuild all the storage node or only one
            storage or device of one storage node
        Args:
            host: storage host to rebuild
            cid: cluster id to rebuild
            sid: storage id to rebuild
            device: device nb. rebuild
        """

        # Check if known node
        if host not in self._nodes.keys():
            raise Exception("Unknown host: %s." % host)

        node = self._nodes[host]

        # Check if it's a storage node
        if node.has_one_of_roles(Role.STORAGED):

            # Check if we rebuild all the storage node
            if cid is None and sid is None and device is None:
                node.set_rebuild(self._export_hosts, None, None, None)
            else:
                # OK we want rebuild only one storage

                # Check if both cid and sid are defined
                if cid is None or sid is None:
                    raise Exception("cid and sid must be defined")

                # Get config
                sconfig = node.get_configurations(Role.STORAGED)

                # Check if the given storage is known by this host
                if (cid,sid) not in [(s.cid,s.sid) for s in sconfig[Role.STORAGED].storages.values()]:
                    raise Exception("Host: %s has not storage with cid=%d and sid=%d." % (host, cid, sid))

                if device is not None:
                    # Check invalid value
                    if device < 0:
                        raise Exception("Device number must be greater than 0.")

                    # Check if the given device is known
                    if device >= sconfig[Role.STORAGED].storages[(cid, sid)].device_t:
                        raise Exception("Host: %s has not a device with number=%d for storage (cid=%d,sid=%d)." % (host, device, cid, sid))

                node.set_rebuild(self._export_hosts, cid, sid, device)
        else:
            raise Exception("Host: %s is not a storage node." % host)

# Not need anymore ?
    def get_configurations(self, hosts=None, roles=Role.EXPORTD | Role.STORAGED | Role.ROZOFSMOUNT):
        """ Get configurations for named nodes and roles

        Args:
            hosts : list of hosts to get statuses from, if None all host are
                    checked

            roles : for which roles statuses should be retrieved
                    if a given host doesn't have this role the return statuses
                    will not contain key for this role.

        Return:
            A dict: keys are host names, values are dicts {Role: configuration}
                    or None if node is off line.
        """
        configurations = {}
        if hosts is None:
            for h, n in self._nodes.items():
                configurations[h] = n.get_configurations(roles)
        else:
            for h in hosts:
                if h not in self._nodes:
                    raise Exception("Unknown node: %s." % h)
                configurations[h] = self._nodes[h].get_configurations(roles)

        return configurations

    def set_layout(self, layout):

        # Check layout
        valid_layouts = [0, 1, 2]
        if not layout in valid_layouts:
            raise Exception("invalid layout: %d" % layout)

        # Get config
        node = self._get_exportd_node()
        configuration = node.get_configurations(Role.EXPORTD)

        # Check exception
        if isinstance(configuration[Role.EXPORTD], Exception):
            raise type(configuration[Role.EXPORTD])("%s: %s" % 
                                                    (self._active_export_host,
                                                    str(configuration[Role.EXPORTD])))

        # Check if we can change the layout
        if len(configuration[Role.EXPORTD].volumes) != 0:
            raise Exception("platform has configured volume(s) !!!")

        # Set layout
        configuration[Role.EXPORTD].layout = layout
        node.set_configurations(configuration)

    def get_layout(self):
        node = self._get_exportd_node()

        # Get config
        configuration = node.get_configurations(Role.EXPORTD)

        # Check exception
        if isinstance(configuration[Role.EXPORTD], Exception):
            raise type(configuration[Role.EXPORTD])("%s: %s" % 
                                                    (self._active_export_host,
                                                    str(configuration[Role.EXPORTD])))

        return configuration[Role.EXPORTD].layout

#    def list_volumes(self):
#        node = self._get_exportd_node()
#        configuration = node.get_configurations(Role.EXPORTD)
#
#        if configuration is None:
#            raise "exportd node is off line."
#
#        return configuration[Role.EXPORTD].volumes.keys()
#
#    def get_volume_stats(self, vid):
#        node = self._get_exportd_node()
#        configuration = node.get_configurations(Role.EXPORTD)
#
#        if configuration is None:
#            raise "exportd node is off line."
#
#        if vid not in configuration[Role.EXPORTD].volumes.keys():
#            raise Exception("unmanaged volme: %d" % vid)
#
#        return configuration[Role.EXPORTD].volumes[vid]

    def add_nodes(self, hosts, vid=None, layout=None, dev_t=1, dev_m=1, dev_r=1):
        """ Add storaged nodes to the platform

        Args:
            hosts: hosts to be added
            vid: volume to use, if none a new one will be created
            layout: specific layout to use, if none the default layout or
                    the layout of the already defined volume will be used
            dev_t: total number of devices
            dev_m: number of devices used for file to device mapping
            dev_r: number of copies of each file to device mapping file
        """
        enode = self._get_exportd_node()
        econfig = enode.get_configurations(Role.EXPORTD)

        if econfig is None:
            raise Exception("exportd node is off line.")
        
        # Find the default layout
        if layout is None:
            if ((vid is not None) and
                (vid in econfig[Role.EXPORTD].volumes) and
                (econfig[Role.EXPORTD].volumes[vid].layout is not None)):
                default_layout = econfig[Role.EXPORTD].volumes[vid].layout
            else:
                default_layout = econfig[Role.EXPORTD].layout
        else:
            default_layout = layout
        
        # Checks coherence between layout and size of cluster to add
        if len(hosts) < LAYOUT_VALUES[default_layout][LAYOUT_SAFE]:
            raise Exception('too few hosts: only %s hosts are specified '
                            '(%s are needed for the layout %s)' % (len(hosts),
                    LAYOUT_VALUES[default_layout][LAYOUT_SAFE], default_layout))

        # Checks coherence between layout and vid
        if vid is not None:
            # check if the given one is a new one 
            # else get the related VolumeConfig
            if vid in econfig[Role.EXPORTD].volumes:
                
                authorized_layout = econfig[Role.EXPORTD].layout
                if (econfig[Role.EXPORTD].volumes[vid].layout is not None):
                    authorized_layout = \
                        econfig[Role.EXPORTD].volumes[vid].layout

                if(authorized_layout != default_layout):
                    raise Exception('only the layout %s can be used for the '
                                    'volume %s' % ( authorized_layout, vid))
                vconfig = econfig[Role.EXPORTD].volumes[vid]
            else:
                if(layout == econfig[Role.EXPORTD].layout):
                    # avoid to set a specific layout if it's not necessary
                    vconfig = VolumeConfig(vid, None)
                else:
                    vconfig = VolumeConfig(vid, layout)
        else:
            vids = econfig[Role.EXPORTD].volumes.keys()
            if len(vids) != 0 :
                vid = max(vids) + 1
            else:
                vid = 1
            if(layout == econfig[Role.EXPORTD].layout):
                # avoid to set a specific layout if it's not necessary
                vconfig = VolumeConfig(vid, None)
            else:
                vconfig = VolumeConfig(vid, layout)

        # Check devices args
        if (dev_t < 1) or (dev_m < 1) or (dev_r < 1):
            raise Exception('device number(s) must be greater than 0')
        if (dev_t > 64) or (dev_m > 64) or (dev_r > 64):
            raise Exception('device number(s) must be lower or equal than 64')
        if (dev_t < dev_m):
            raise Exception('device-mapper must be lower than or equal to device-total')
        if (dev_r > dev_m):
            raise Exception('device-redundancy must be lower than or equal to device-mapper')

        # find a cluster id
        cids = [c.cid for v in econfig[Role.EXPORTD].volumes.values()
                      for c in v.clusters.values()]
        if len(cids) != 0:
            cid = max(cids) + 1
        else:
            cid = 1

        # as we create a new cluster sids always starts at 1
        sid = 1

        cconfig = ClusterConfig(cid)
        roles = Role.STORAGED

        for h in hosts:
            # if it's a new node register it
            # else just update its role
            if h not in self._nodes:
                self._nodes[h] = Node(h, roles)
            else:
                # maybe overkill since the node could already have this role
                self._nodes[h].set_roles(self._nodes[h].get_roles() | roles)
#	    print self._nodes[h].get_configurations
            # configure the storaged
            sconfig = self._nodes[h].get_configurations(Role.STORAGED)

            # Check if a storage is already configured for this node
            # If no storage configured crc32 activation is forced
#            print sconfig
            if len(sconfig[Role.STORAGED].storages) == 0:
                if sconfig[Role.STORAGED].crc32c_check is None:
                    sconfig[Role.STORAGED].crc32c_check = True
                if sconfig[Role.STORAGED].crc32c_generate is None:
                    sconfig[Role.STORAGED].crc32c_generate = True
                if sconfig[Role.STORAGED].crc32c_hw_forced is None:
                    sconfig[Role.STORAGED].crc32c_hw_forced = True

            sconfig[Role.STORAGED].storages[(cid, sid)] = StorageConfig(cid,
                                                                        sid,
                                                                        "%s/storage_%d_%d" % (STORAGES_ROOT, cid, sid),
                                                                        dev_t,
                                                                        dev_m,
                                                                        dev_r)
            self._nodes[h].set_configurations(sconfig)

            # add the storage to the cluster
            cconfig.storages[sid] = h
            sid += 1

        # add the cluster to the volume
        vconfig.clusters[cid] = cconfig
        # update the exportd config
        econfig[Role.EXPORTD].volumes[vid] = vconfig
        enode.set_configurations(econfig)

    def remove_volume(self, vid):
        """ Remove a volume

        Args:
            vid: the volume to be removed
        """
        enode = self._get_exportd_node()
        econfig = enode.get_configurations(Role.EXPORTD)

        if econfig is None:
            raise Exception("Exportd node is off line.")

        if vid not in econfig[Role.EXPORTD].volumes:
            raise Exception("Unknown volume with vid=%d." % vid)

        if [e for e in econfig[Role.EXPORTD].exports.values() if e.vid == vid]:
            raise Exception("Volume has configured export(s)")
        else:
            vconfig = econfig[Role.EXPORTD].volumes.pop(vid)
            for c in vconfig.clusters.values():
                for sid, host in c.storages.items():
                    sconfig = self._nodes[host].get_configurations(Role.STORAGED)
                    sconfig[Role.STORAGED].storages.pop((c.cid, sid))
                    self._nodes[host].set_configurations(sconfig)
            enode.set_configurations(econfig)

    def create_export(self, vid, name=None, passwd=None, squota="", hquota=""):
        """ Export a new file system

        Args:
            vid: the volume id to use the file system relies on
        """
        # exportd_hostname = self.get_exportd_hostname()
        enode = self._get_exportd_node()
        econfig = enode.get_configurations(Role.EXPORTD)

        if econfig is None:
            raise Exception("%s is not reachable" % enode._host)

        if vid not in econfig[Role.EXPORTD].volumes:
            raise Exception("Unknown volume: %d." % vid)

        # validate quotas
        if squota:
            if not squota[0].isdigit():
                raise Exception("Invalid squota format: %s." % squota)

            for c in squota:
                if not c.isdigit():
                    if c not in ['K', 'M', 'G', 'T']:
                        raise Exception("Invalid squota format: %s." % squota)
                    else:
                        break

        if hquota:
            if not hquota[0].isdigit():
                raise Exception("Invalid hquota format: %s." % hquota)


            for c in hquota:
                if not c.isdigit():
                    if c not in ['K', 'M', 'G', 'T']:
                        raise Exception("Invalid hquota format: %s." % squota)
                    else:
                        break

        # find an eid
        eids = econfig[Role.EXPORTD].exports.keys()
        if len(eids) != 0:
            eid = max(eids) + 1
        else:
            eid = 1

        # check name
        if name is None:
            name = "export_%d" % eid
        else:
            if "%s/%s" % (EXPORTS_ROOT, name) in [e.root for e in econfig[Role.EXPORTD].exports.values()]:
                raise Exception("Duplicate export name: %s" % name)

        # compute md5
        if passwd is None:
            md5 = ""
        else:
            with open('/dev/null', 'w') as devnull:
                md5 = subprocess.check_output(['md5pass', passwd, 'rozofs'],
                                   stderr=devnull)[11:].rstrip()

        # add this new export
        econfig[Role.EXPORTD].exports[eid] = ExportConfig(eid, vid, "%s/%s" % (EXPORTS_ROOT, name), md5, squota, hquota)
        enode.set_configurations(econfig)

    def update_export(self, eid, current=None, passwd=None, squota=None, hquota=None):
        """ Modify an exported file system

        Args:
            eid: the export id to modify
            current: current password (only need if passwd)
            passwd: password to set if None no modification is done
            squota: soft quota to set if None no modification is done
            hquota: hard quota to set if None no modification is done
        """
        enode = self._get_exportd_node()
        econfig = enode.get_configurations(Role.EXPORTD)

        if econfig is None:
            raise Exception("%s is not reachable" % enode._host)

        if eid not in econfig[Role.EXPORTD].exports.keys():
            raise Exception("Unknown export with eid=%d." % eid)

        # validate quotas
        if squota is not None:
            if squota:
                if not squota[0].isdigit():
                    raise Exception("Invalid squota format: %s." % squota)

                for c in squota:
                    if not c.isdigit():
                        if c not in ['K', 'M', 'G', 'T']:
                            raise Exception("Invalid squota format: %s." % squota)
                        else:
                            break
            econfig[Role.EXPORTD].exports[eid].squota = squota

        if hquota is not None:
            if hquota:
                if not hquota[0].isdigit():
                    raise Exception("Invalid hquota format: %s." % hquota)

                for c in hquota:
                    if not c.isdigit():
                        if c not in ['K', 'M', 'G', 'T']:
                            raise Exception("Invalid hquota format: %s." % squota)
                        else:
                            break
            econfig[Role.EXPORTD].exports[eid].hquota = hquota

        # compute md5
        if passwd is not None:
            if econfig[Role.EXPORTD].exports[eid].md5:
                if current is None:
                    raise "Current password needed."

                # check current passwd
                with open('/dev/null', 'w') as devnull:
                        if econfig[Role.EXPORTD].exports[eid].md5 != subprocess.check_output(['md5pass', current, 'rozofs'],
                                       stderr=devnull)[11:].rstrip():
                            raise "Permission denied."

            if passwd:
                with open('/dev/null', 'w') as devnull:
                    econfig[Role.EXPORTD].exports[eid].md5 = subprocess.check_output(['md5pass', passwd, 'rozofs'],
                                   stderr=devnull)[11:].rstrip()
            else:
                econfig[Role.EXPORTD].exports[eid].md5 = ""

        # update this export
        enode.set_configurations(econfig)

    def remove_export(self, eids=None, force=False):
        """ Remove exported file systems

        To not keep unused data stored, exports containing files will not be remove
        unless force is set to True.

        Args:
            eids: export ids to remove
            force: force removing of non empty exportd
        """

        enode = self._get_exportd_node()
        econfig = enode.get_configurations(Role.EXPORTD)

        if econfig is None:
            raise Exception("Exportd node is off line.")

        if eids is None:
            eids = econfig[Role.EXPORTD].exports.keys()

        # unmount if needed
        self.umount_export(eids)

        # sanity check
        for eid, estat in econfig[Role.EXPORTD].stats.estats.items():
            for eeid in eids:
                if eeid not in econfig[Role.EXPORTD].exports.keys():
                    raise Exception("Unknown export with eid=%d." % eid)
                if eid == eeid and estat.files != 0 and not force:
                    raise Exception("Can't remove non empty export (use --force=True)")


        # delete these exports from exportd configuration
        for eid in eids:
            econfig[Role.EXPORTD].exports.pop(eid)

        enode.set_configurations(econfig)

    def mount_export(self, eids=None, exports=None, hosts=None, mountpoints=None, options=None):
        """ Mount an exported rozo file system

        Only known (managed by this platform) hosts could mount a file system.

        Args:
            eids: list of specific eid(s) to mount.
                  (if eids and exports are None, all exports will be mount)
            exports: list of specific exports(s) name (dirname) to mount.
                  (if eids and exports are None, all exports will be mount)
            hosts: target hosts to mount on if None, exports will be mount on
                   all nodes (node with rozofsmount agent listener)
            mountpoints: list of path(s) to use for mount export on node(s)
            options: mount options to use for the list of export(s)
        """
        statuses = {}

        # Get export configuration
        enode = self._get_exportd_node()
        econfig = enode.get_configurations(Role.EXPORTD)
        # Check error
        if isinstance(econfig[Role.EXPORTD], Exception):
            raise type(econfig[Role.EXPORTD])(str(econfig[Role.EXPORTD]))

        # Check hosts arg
        if hosts is not None:
            for h in hosts:
                if h not in self._nodes:
                    raise Exception("Unknown host: %s." % h)
        else:
            # All nodes
            hosts = self._nodes.keys()

        # Check args eids and exports
        if eids is not None and exports is not None:
            raise Exception("eids and exports are mutually exclusive")
        elif eids is not None:
            # Check given eids
            for eid in eids:
                if eid not in econfig[Role.EXPORTD].exports.keys():
                    raise Exception("Unknown export with eid=%d." % eid)
        elif exports is not None:
            # Check given exports
            for export in exports:
                if export not in [os.path.basename(e.root) for e in econfig[Role.EXPORTD].exports.values()]:
                    raise Exception("Unknown export with name: %s." % export)
            eids=[]
            for export in exports:
                for i,e in econfig[Role.EXPORTD].exports.items():
                    if os.path.basename(e.root) == export:
                        eids.append(i)
        else:
            eids = econfig[Role.EXPORTD].exports.keys()

        mnt_path = {}
        # Check mountpoints
        if mountpoints:
            for mnt in mountpoints:
                if not os.path.isabs(mnt):
                    raise Exception('Mountpoint: %s is not '
                                    'an absolute pathname.' % mnt)
            if len(mountpoints) > len(eids):
                raise Exception('Too many mountpoint(s):'
                                ' %d given mountpoint(s) for %d export(s)' %
                                (len(mountpoints), len(eids)))
            idx = 0
            for eid in eids:
                if len(mountpoints) > idx:
                    mnt_path[eid] = mountpoints[idx]
                    idx +=1
                else:
                    mnt_path[eid] = None
        else:
            for eid in eids:
                mnt_path[eid] = None

        # Get current rozofsmount config on each node
        current_rconfig = {}
        for h in hosts:
            node = self._nodes[h]

            if node.has_one_of_roles(Role.ROZOFSMOUNT):
                rconfig = node.get_configurations(Role.ROZOFSMOUNT)
                # Check error
                if isinstance(rconfig[Role.ROZOFSMOUNT], Exception):
                    # Update statuses
                    statuses[h] = type(rconfig[Role.ROZOFSMOUNT])(str(rconfig[Role.ROZOFSMOUNT]))
                    continue
                current_rconfig[h] = rconfig

        # Set new rozo configs
        for h in hosts:

            # Check if we have config for this host
            if not current_rconfig.has_key(h):
                continue

            host_mnt_statuses = {}
            node = self._nodes[h]

            # Indicate if we add new config
            new_config = False
            old_config = False

            for eid in eids:

                # Build new config
                expconfig = econfig[Role.EXPORTD].exports[eid]
                rconfig = RozofsMountConfig("/".join(self._export_hosts) 
                                            , expconfig.root
                                            , -1
                                            , mountpoint=mnt_path[eid]
                                            , options=options)

                mnt_desc = {}
                mnt_desc['eid'] = eid
                mnt_desc['export_root'] = expconfig.root
                mnt_desc['export_host'] = self._export_hosts
                mnt_desc['options'] = options

                # Check already present mnt_desc
                if rconfig not in current_rconfig[h][Role.ROZOFSMOUNT]:
                    # Check if mounpoint is already used
                    if rconfig.mountpoint in [m.mountpoint for m in current_rconfig[h][Role.ROZOFSMOUNT]]:
                        mnt_desc['config'] = Exception("mountpoint: %s already exists" % rconfig.mountpoint)
                        mnt_desc['service'] = False
                        host_mnt_statuses[rconfig.mountpoint] = mnt_desc
                    else:
                        current_rconfig[h][Role.ROZOFSMOUNT].append(rconfig)
                        host_mnt_statuses[rconfig.mountpoint] = mnt_desc
                        new_config = True
                else:
                    old_config = True
                    for conf in current_rconfig[h][Role.ROZOFSMOUNT]:
                        if conf == rconfig:
                            mnt_desc['config'] = None
                            mnt_desc['service'] = None
                            host_mnt_statuses[conf.mountpoint] = mnt_desc

            if old_config:
                mnt_statuses = node.get_statuses(Role.ROZOFSMOUNT)
                for mnt, status in mnt_statuses[Role.ROZOFSMOUNT].items():
                    if host_mnt_statuses.has_key(mnt):
                        host_mnt_statuses[mnt].update({'service' : status})

            if new_config:
                resp = node.set_configurations(current_rconfig[h])
                # Check error
                if isinstance(resp[Role.ROZOFSMOUNT], Exception):
                    # Update statuses
                    statuses[h] = resp[Role.ROZOFSMOUNT]
                    continue
                for mnt, mnt_status in resp[Role.ROZOFSMOUNT].items():
                    # Update config
                    host_mnt_statuses[mnt].update(mnt_status)

            statuses[h] = host_mnt_statuses

        return statuses

    def umount_export(self, eids=None, exports=None, mountpoints=None, hosts=None):
        """ Unmount an exported rozo file system

        Only known (managed by this platform) hosts could umount a file system.

        Args:
            eids: list of specific eid(s) to unmount.
                  (if eids, exports and mountpoints are None,
                   all exports will be unmounted)
            exports: list of specific exports(s) name (dirname) to unmounted.
                  (if eids, exports and mountpoints are None,
                   all exports will be unmounted)
            mountpoints: list of specific mountpath to unmount
                          (if eids, exports and mountpoints are None,
                           all exports will be unmounted)
            hosts: target hosts to unmount, if None on all nodes will be
                   requested (nodes) with rozofsmount listener).
        """
        statuses = {}

        # Get export configuration
        enode = self._get_exportd_node()
        econfig = enode.get_configurations(Role.EXPORTD)
        # Check error
        if isinstance(econfig[Role.EXPORTD], Exception):
            raise type(econfig[Role.EXPORTD])(str(econfig[Role.EXPORTD]))

        # Check hosts arg
        if hosts is not None:
            for h in hosts:
                if h not in self._nodes:
                    raise Exception("Unknown host: %s." % h)
        else:
            # All nodes
            hosts = self._nodes.keys()

        # Check args eids, exports and mountpoints parameters
        if eids is not None and exports is not None :
            raise Exception("eids and exports are mutually exclusive")
        elif eids is not None and mountpoints is not None :
            raise Exception("eids and mounpoints are mutually exclusive")
        elif exports is not None and mountpoints is not None :
            raise Exception("exports and mountpoints are mutually exclusive")
        elif eids is not None:
            # Check given eids
            for eid in eids:
                if eid not in econfig[Role.EXPORTD].exports.keys():
                    raise Exception("Unknown export with eid=%d." % eid)
        elif exports is not None:
            # Check given exports
            for export in exports:
                if export not in [os.path.basename(e.root) for e in econfig[Role.EXPORTD].exports.values()]:
                    raise Exception("Unknown export with name: %s." % export)
            # Compute eids
            eids = []
            for export in exports:
                for i,e in econfig[Role.EXPORTD].exports.items():
                    if os.path.basename(e.root) == export:
                        eids.append(i)
        elif mountpoints is not None:
            # check mountpoints
            for mnt in mountpoints:
                if not os.path.isabs(mnt):
                    raise Exception('mountpoint: %s is not '
                                    'an absolute pathname.' % mnt)
        else:
            # All eids
            eids = econfig[Role.EXPORTD].exports.keys()

        # umount
        for h in hosts:

            node = self._nodes[h]

            if node.has_one_of_roles(Role.ROZOFSMOUNT):

                # Get current rozofsmount configs
                rconfigs = node.get_configurations(Role.ROZOFSMOUNT)
                # Check error
                if isinstance(rconfigs[Role.ROZOFSMOUNT], Exception):
                    # Update statuses
                    statuses[h] = rconfigs[Role.ROZOFSMOUNT]
                    continue

                host_mnt_statuses = {}

                # Indicate if we add new config
                new_config = False

                if mountpoints is not None:
                    # Build list of configs to remove
                    remove_conf_l = []
                    for mnt in mountpoints:
                        for r in rconfigs[Role.ROZOFSMOUNT]:
                            if r.mountpoint == mnt:
                                remove_conf_l.append(r)

                    for rem_c in remove_conf_l:
                        mnt_desc = {}
                        new_config = True
                        for e in econfig[Role.EXPORTD].exports.values():
                            if e.root == rem_c.export_path:
                                mnt_desc['eid'] = e.eid
                                break
                        mnt_desc['export_root'] = rem_c.export_path
                        mnt_desc['export_host'] = self._export_hosts
                        rconfigs[Role.ROZOFSMOUNT].remove(rem_c)
                        host_mnt_statuses[rem_c.mountpoint] = mnt_desc

                else:
                    for eid in eids:
                        # Find exp_path
                        exp_path = econfig[Role.EXPORTD].exports[eid].root
                        # Build list of configs to remove
                        remove_conf_l = [r for r in rconfigs[Role.ROZOFSMOUNT] if r.export_path == exp_path]

                        for rem_c in remove_conf_l:
                            mnt_desc = {}
                            new_config = True
                            mnt_desc['eid'] = eid
                            mnt_desc['export_root'] = exp_path
                            mnt_desc['export_host'] = self._export_hosts
                            rconfigs[Role.ROZOFSMOUNT].remove(rem_c)
                            host_mnt_statuses[rem_c.mountpoint] = mnt_desc

                if new_config:
                    # Send updated configuration
                    resp = node.set_configurations(rconfigs)
                    # Check error
                    if isinstance(resp[Role.ROZOFSMOUNT], Exception):
                        # Update statuses
                        statuses[h] = resp[Role.ROZOFSMOUNT]
                        continue

                    for mnt, mnt_status in resp[Role.ROZOFSMOUNT].items():
                        # Update config
                        host_mnt_statuses[mnt].update(mnt_status)

                statuses[h] = host_mnt_statuses

        return statuses
