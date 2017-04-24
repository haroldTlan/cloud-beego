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

import sys
from zoofs.core.platform import Platform, Role, get_proxy
from zoofs.core.agent import ServiceStatus
from zoofs.core.constants import STORAGED_MANAGER
from zoofs.cli.output import puts
from zoofs.cli.output import ordered_puts
from collections import OrderedDict

def list(platform, args):
    e_host = platform._active_export_host
    configurations = platform.get_configurations([e_host], Role.EXPORTD)

    if configurations[e_host] is None:
        raise Exception("exportd node is off line.")

    configuration = configurations[e_host][Role.EXPORTD]

    export_l = {}
    list_l = []
    for vid, volume in configuration.volumes.items():
        volume_l = []
        if volume.layout is not None:
            volume_l.append({'LAYOUT' : volume.layout })
        else:
            volume_l.append({'LAYOUT' : configuration.layout })
        for cid, cluster in volume.clusters.items():
            cluster_l = []
            for sid, storage in cluster.storages.items():
                cluster_l.append({'STORAGE ' + str(sid): storage})
            volume_l.append({'CLUSTER ' + str(cid): cluster_l})
        list_l.append({'VOLUME ' + str(vid): volume_l})
    export_l.update({'EXPORTD on ' + str(e_host): list_l})
    ordered_puts(export_l)

def stat(platform, args):
    e_host = platform._active_export_host
    # Get configuration
    configurations = platform.get_configurations([e_host], Role.EXPORTD)
    if configurations[e_host] is None:
        raise Exception("exportd node is off line.")
    
    # Get statuses from storaged nodes
    statuses = {}
    for h, n in platform._nodes.items():
        if n.has_one_of_roles(Role.STORAGED):
            statuses[h] = n.get_statuses(Role.STORAGED)
    
    # Check if all storaged nodes running
    for host, status in statuses.items():
        try:
            if not status:
                print 'WARNING: %s is not reachable' % str(host)
                continue
            if not status[Role.STORAGED]: 
                print 'WARNING: storaged is not running on ' + str(host)
        except KeyError:
            raise Exception("storaged node is off line.")

    # configuration of exportd node
    configuration = configurations[e_host][Role.EXPORTD]
    if configuration.stats is None:
        ordered_puts({'EXPORTD on ' + str(args.exportd): "not running"})
        return
        
    export_l = {}
    stat_l = []
    for vid, vstat in configuration.stats.vstats.items():
        volume_l = []
        if configuration.volumes[vid].layout is not None:
            volume_l.append({'layout' : configuration.volumes[vid].layout })
        else:
            volume_l.append({'layout' : configuration.layout })
        volume_l.append({'bsize': vstat.bsize})
        volume_l.append({'bfree': vstat.bfree})
        volume_l.append({'blocks': vstat.blocks})
        for cid, cstat in vstat.cstats.items():
            cluster_l = []
            cluster_l.append({'size': cstat.size})
            cluster_l.append({'free': cstat.free})
            for sid, sstat in cstat.sstats.items():
                storage_l = []
                storage_l.append({'host': sstat.host})
                storage_l.append({'size': sstat.size})
                storage_l.append({'free': sstat.free})
                cluster_l.append({'STORAGE ' + str(sid): storage_l})
            volume_l.append({'CLUSTER ' + str(cid): cluster_l})
        stat_l.append({'VOLUME ' + str(vid): volume_l})
    export_l.update({'EXPORTD on ' + str(e_host): stat_l})
    ordered_puts(export_l)

def get(platform, args):
    e_host = platform._active_export_host
    configurations = platform.get_configurations([e_host], Role.EXPORTD)
    if configurations[e_host] is None:
        raise Exception("exportd node is off line.")

    configuration = configurations[e_host][Role.EXPORTD]
    get_l = []
    for vid in args.vid:

        if vid not in configuration.volumes:
            raise Exception("Unknown volume with vid=%d." % vid)

        vconfig = configuration.volumes[vid]
        vstat = configuration.stats.vstats[vid]
        volume_l = []
        if vconfig.layout is not None:
            volume_l.append({'layout' : vconfig.layout })
        else:
            volume_l.append({'layout' : configuration.layout })
        volume_l.append({'bsize': vstat.bsize})
        volume_l.append({'bfree': vstat.bfree})
        volume_l.append({'blocks': vstat.blocks})
        for cid, cstat in vstat.cstats.items():
            cluster_l = []
            cluster_l.append({'size': cstat.size})
            cluster_l.append({'free': cstat.free})
            for sid, sstat in cstat.sstats.items():
                storage_l = []
                storage_l.append({'host': sstat.host})
                storage_l.append({'size': sstat.size})
                storage_l.append({'free': sstat.free})
                cluster_l.append({'STORAGE ' + str(sid): storage_l})
            volume_l.append({'CLUSTER ' + str(cid): cluster_l})
        get_l.append({'VOLUME ' + str(vid): volume_l})

    ordered_puts({'' + str(e_host): get_l})

def expand(platform, args):
    for host in args.hosts:
        try:
            get_proxy(host, STORAGED_MANAGER).get_service_status()
        except:
            raise Exception("storage agent on the node \"%s\" is not reachable" % (host))

    if not args.vid:
        platform.add_nodes(args.hosts, None, args.layout, args.total, args.mapper, args.redundancy)
    else:
        platform.add_nodes(args.hosts, args.vid, args.layout, args.total, args.mapper, args.redundancy)

def remove(platform, args):
    for vid in args.vid:
        platform.remove_volume(vid)

def dispatch(args):
    p = Platform(args.exportd, Role.EXPORTD | Role.STORAGED)
    globals()[args.action.replace('-', '_')](p, args)
