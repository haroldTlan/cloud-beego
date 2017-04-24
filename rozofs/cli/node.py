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
from zoofs.core.platform import Platform, Role
from zoofs.core.agent import ServiceStatus
from zoofs.core.constants import STORAGED_MANAGER, EXPORTD_MANAGER, \
ROZOFSMOUNT_MANAGER
import json
from zoofs.cli.output import ordered_puts
from zoofs.cli.exceptions import MultipleError
from collections import OrderedDict
import yaml

ROLES_STR = {Role.EXPORTD: "EXPORTD", Role.STORAGED: "STORAGED", Role.ROZOFSMOUNT: "ZOOFSMOUNT"}
STR_ROLES = {"exportd": Role.EXPORTD, "storaged": Role.STORAGED, "zoofsmount": Role.ROZOFSMOUNT}

def __roles_to_strings(roles):
    strs = []
    if roles & Role.EXPORTD == Role.EXPORTD:
        strs.append("EXPORTD")
    if roles & Role.STORAGED == Role.STORAGED:
        strs.append("STORAGED")
    if roles & Role.ROZOFSMOUNT == Role.ROZOFSMOUNT:
        strs.append("ZOOFSMOUNT")
    return strs

def __args_to_roles(args):
    roles = 0
    if args.roles:
        for r in args.roles:
            roles |= STR_ROLES[r]
    else:
        roles = Role.EXPORTD | Role.STORAGED | Role.ROZOFSMOUNT
    return roles

def list(platform, args):
    list_l = {}
    for h, r in platform.list_nodes(__args_to_roles(args)).items():
        role_l = []
        role_l.append(__roles_to_strings(r))
        list_l.update({h: role_l})
    ordered_puts(list_l)

def status(platform, args):

    statuses = platform.get_statuses(args.nodes, __args_to_roles(args))
    status_l = {}
    errors_l = {}

    for h, s in statuses.items():
        role_l = []
        role_err_l = []

        for role, status in s.items():

            # Check exception
            if isinstance(status, Exception):
                # Update standard output dict
                err_str = type(status).__name__ + ' (' + str(status) + ')'
                role_l.append({ROLES_STR[role]: err_str})
                # Update errors dict
                role_err_l.append({ROLES_STR[role]: err_str})
                errors_l.update({'NODE: ' + str(h) : role_err_l})
                continue
            if (role & Role.ROZOFSMOUNT == Role.ROZOFSMOUNT):
                mount_l = []
                if not status:
                    role_l.append({ROLES_STR[role]: 'no mountpoint configured'})
                else:
                    for m, s in status.items():
                        mount_l.append({m : 'mounted' if s else 'unmounted'})
                    role_l.append({ROLES_STR[role]: mount_l})
            else:
                if status:
                    role_l.append({ROLES_STR[role]: 'running'})
                else:
                    role_l.append({ROLES_STR[role]: 'not running'})

        if role_l:
            status_l.update({h:role_l})

    # Display output
    ordered_puts(status_l)

    # Check errors
    if errors_l:
     raise MultipleError(errors_l)

def start(platform, args):

    changes = platform.start(args.nodes, __args_to_roles(args))

    status_l = {}
    errors_l = {}

    for h, s in changes.items():
        role_l = []
        role_err_l = []

        for role, change in s.items():

            # Check exception
            if isinstance(change, Exception):
                # Update standard output dict
                err_str = type(change).__name__ + ' (' + str(change)  + ')'
                role_l.append({ROLES_STR[role]: 'failed, ' + err_str})
                # Update errors dict
                role_err_l.append({ROLES_STR[role]: err_str})
                errors_l.update({'NODE: ' + str(h) : role_err_l})
                continue

            if (role & Role.ROZOFSMOUNT == Role.ROZOFSMOUNT):
                mount_l = []
                for m, s in change.items():
                    mount_l.append({m : 'mounted' if s else 'already mounted'})
                role_l.append({ROLES_STR[role]: mount_l})
            else:
                if change:
                    role_l.append({ROLES_STR[role]: 'started'})
                else:
                    role_l.append({ROLES_STR[role]: 'already started'})

        if role_l:
            status_l.update({h:role_l})

    # Display output
    ordered_puts(status_l)

    # Check errors
    if errors_l:
     raise MultipleError(errors_l)


def stop(platform, args):

    changes = platform.stop(args.nodes, __args_to_roles(args))

    status_l = {}
    errors_l = {}

    for h, s in changes.items():
        role_l = []
        role_err_l = []

        for role, change in s.items():
            # Check exception
            if isinstance(change, Exception):
                # Update standard output dict
                err_str = type(change).__name__ + ' (' + str(change) + ')'
                role_l.append({ROLES_STR[role]: 'failed, ' + err_str})
                # Update errors dict
                role_err_l.append({ROLES_STR[role]: err_str})
                errors_l.update({'NODE: ' + str(h) : role_err_l})
                continue
            if (role & Role.ROZOFSMOUNT == Role.ROZOFSMOUNT):
                mount_l = []
                for m, s in change.items():
                    mount_l.append({m : 'unmounted' if s else 'already unmounted'})
                role_l.append({ROLES_STR[role]: mount_l})
            else:
                if change:
                    role_l.append({ROLES_STR[role]: 'stopped'})
                else:
                    role_l.append({ROLES_STR[role]: 'already stopped'})

        if role_l:
            status_l.update({h:role_l})

    # Display output
    ordered_puts(status_l)

    # Check errors
    if errors_l:
     raise MultipleError(errors_l)

def config(platform, args):
    if not args.roles:
        args.roles = [EXPORTD_MANAGER, STORAGED_MANAGER, ROZOFSMOUNT_MANAGER]

    configurations = platform.get_configurations(args.nodes, __args_to_roles(args))

    errors_l = {}
    host_l = {}

    for h, c in configurations.items():

        # Is-it necessary ?
        if c is None:
            host_l.update({'NODE: ' + str(h) : "not reachable"})
            continue

        role_l=[]
        role_err_l = []

        for role, config in c.items():
            # Check exception
            if isinstance(config, Exception):
                # Get error msg
                err_str = type(config).__name__ + ' (' + str(config) + ')'
                # Update standard output dict
                role_l.append({ROLES_STR[role]: err_str})
                host_l.update({'NODE: ' + str(h) : role_l})
                # Update errors dict
                role_err_l.append({ROLES_STR[role]: err_str})
                errors_l.update({'NODE: ' + str(h) : role_err_l})
                continue

            if (role & Role.EXPORTD == Role.EXPORTD):
                exportd_l = []
                volume_l = []
                for v in config.volumes.values():
                    cluster_l = []
                    for cluster in v.clusters.values():
                        s_l = []
                        for s, hhh in cluster.storages.items():
                            s_l.append({'sid ' + str(s): hhh})
                        cluster_l.append({'cluster ' + str(cluster.cid): s_l})
                    volume_l.append({'volume ' + str(v.vid): cluster_l})
                exportd_l.append({'VOLUME':volume_l})
                if len(config.exports) != 0:
                    for e in config.exports.values():
                        export_l = OrderedDict([
                            ('vid', e.vid),
                            ('root', e.root),
                            ('md5', e.md5),
                            ('squota', e.squota),
                            ('hquota', e.hquota)])
                        exportd_l.append({'EXPORT':export_l})
                role_l.append({'EXPORTD':exportd_l})

            if (role & Role.STORAGED == Role.STORAGED):
                options_l = []
                interface_l = []
                storage_l = []

                if config.nbcores is not None:
                    options_l.append({'nbcores' : config.nbcores})
                if config.threads is not None:
                    options_l.append({'threads' : config.threads})
                if config.storio is not None:
                    options_l.append({'storio' : config.storio})
                if config.self_healing is not None:
                    options_l.append({'self-healing' : config.self_healing})
                if config.export_hosts is not None:
                    options_l.append({'export-hosts' : config.export_hosts})

                options_l.append({'crc32c_check' : bool(config.crc32c_check)})
                options_l.append({'crc32c_generate' : bool(config.crc32c_generate)})
                options_l.append({'crc32c_hw_forced' : bool(config.crc32c_hw_forced)})
                storage_l.append({'OPTIONS':options_l})

                for lconfig in config.listens:
                    interface_l.append({lconfig.addr : lconfig.port})
                storage_l.append({'INTERFACE':interface_l})

                keylist = config.storages.keys()
                keylist.sort()
                st_l = []
                for key in keylist:
                    st = config.storages[key]

                    stor_l = OrderedDict([
                    ('root', st.root),
                    ('device-total', st.device_t),
                    ('device-mapper', st.device_m),
                    ('device-redundancy', st.device_r)])

                    st_l.append({'cid ' + str(st.cid) + ', sid '+
                        str(st.sid) : stor_l})

                storage_l.append({'STORAGE': st_l})

                role_l.append({'STORAGED': storage_l})

            if (role & Role.ROZOFSMOUNT == Role.ROZOFSMOUNT):
                exp_l = []
                if config:
                    for c in config:
                        mountdict = {}
                        mountdict["mountpoint"] = c.mountpoint
                        mountdict["export host"] = c.export_host
                        mountdict["export path"] = c.export_path
                        exp_l.append(mountdict)
                    role_l.append({'ZOOFSMOUNT': exp_l})

            host_l.update({'NODE: ' + str(h) : role_l})

    ordered_puts(host_l)

    if errors_l:
        raise MultipleError(errors_l)

def dispatch(args):
    p = Platform(args.exportd)
    globals()[args.action.replace('-', '_')](p, args)
