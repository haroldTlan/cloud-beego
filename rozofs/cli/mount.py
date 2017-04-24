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
from zoofs.core.platform import Platform
from zoofs.cli.output import ordered_puts
from zoofs.cli.exceptions import MultipleError
from collections import OrderedDict
import os
import yaml

def create(platform, args):
    if not args.eids:
        args.eids = None

    statuses = platform.mount_export(args.eids, args.exports, args.nodes,
                                      args.mountpoints, args.options)
    host_statuses_l = {}
    host_errors_l = {}

    for h, s in statuses.items():

        # Check exception
        if isinstance(s, Exception):
            # Update standard output dict
            err_str = type(s).__name__ + ' (' + str(s) + ')'
            host_statuses_l.update({str(h): err_str})
            host_errors_l.update({str(h) : err_str})
            continue

        mount_statuses_l = []
        mount_errors_l = []

        for mountpoint, status in s.items():

            mountpoint_status = {}
            mountpoint_error = {}

            # Check config status
            if status['config'] is True:
                mountpoint_status.update({'configuration' : 'added'})
            elif status['config'] is None:
                mountpoint_status.update({'configuration' : 'already present'})
            else:
                # Check exception
                if isinstance(status['config'], Exception):
                    # Update standard output dict
                    err_str = type(status['config']).__name__ + ' (' + str(status['config']) + ')'
                    mountpoint_status.update({'configuration' : 'failed, ' + err_str })
                    # Update errors dict
                    mountpoint_error.update({'configuration' : 'failed, ' + err_str })

            # Check service status
            if status['service'] is True:
                mountpoint_status.update({'status' : 'mounted'})
            elif status['service'] is False:
                mountpoint_status.update({'status' : 'unmounted'})
            elif status['service'] is None:
                mountpoint_status.update({'status' : 'already mounted'})
            else:
                # Check exception
                if isinstance(status['service'], Exception):
                    # Update standard output dict
                    err_str = type(status['service']).__name__ + ' (' + str(status['service']) + ')'
                    mountpoint_status.update({'status' : 'failed, ' + err_str })
                    # Update errors dict
                    mountpoint_error.update({'status' : 'failed, ' + err_str })

            # Update list of mountpoint statuses 
            export_name = os.path.basename(status['export_root'])
            mnt_config = {"export " + export_name + ' (eid=' + str(status['eid']) + ') on ' + mountpoint : mountpoint_status}
            mount_statuses_l.append(mnt_config)
            if mountpoint_error:
                mnt_config_err = {"export " + export_name + ' (eid=' + str(status['eid']) + ') on ' + mountpoint : mountpoint_error}
                mount_errors_l.append(mnt_config_err)

        # Update host
        host_statuses_l.update({str(h) :mount_statuses_l})
        if mount_errors_l:
            host_errors_l.update({str(h) : mount_errors_l})

    # Display output
    ordered_puts(host_statuses_l)

    # Check errors
    if host_errors_l:
     raise MultipleError(host_errors_l)



def remove(platform, args):
    if not args.eids:
        args.eids = None

    statuses = platform.umount_export(args.eids, args.exports, args.mountpoints, args.nodes)

    host_statuses_l = {}
    host_errors_l = {}

    for h, s in statuses.items():

        # Check exception
        if isinstance(s, Exception):
            # Update standard output dict
            err_str = type(s).__name__ + ' (' + str(s) + ')'
            host_statuses_l.update({str(h): err_str})
            host_errors_l.update({str(h) : err_str})
            continue

        mount_statuses_l = []
        mount_errors_l = []


        if not s:
            host_statuses_l.update({str(h) : "no mountpoint to remove"})
            continue

        for mountpoint, status in s.items():

            mountpoint_status = {}
            mountpoint_error = {}

            # Check config status
            if status['config'] is True:
                mountpoint_status.update({'configuration' : 'removed'})
            elif status['config'] is False:
                mountpoint_status.update({'configuration' : 'not removed'})
            elif status['config'] is None:
                mountpoint_status.update({'configuration' : 'already removed'})
            else:
                # Check exception
                if isinstance(status['config'], Exception):
                    # Update standard output dict
                    err_str = type(status['config']).__name__ + ' (' + str(status['config']) + ')'
                    mountpoint_status.update({'configuration' : 'failed, ' + err_str })
                    # Update errors dict
                    mountpoint_error.update({'configuration' : 'failed, ' + err_str })

            # Check service status
            if status['service'] is True:
                mountpoint_status.update({'status' : 'unmounted'})
            elif status['service'] is False:
                mountpoint_status.update({'status' : 'not unmounted'})
            elif status['service'] is None:
                mountpoint_status.update({'status' : 'already unmounted'})
            else:
                # Check exception
                if isinstance(status['service'], Exception):
                    # Update standard output dict
                    err_str = type(status['service']).__name__ + ' (' + str(status['service']) + ')'
                    mountpoint_status.update({'status' : 'failed, ' + err_str })
                    # Update errors dict
                    mountpoint_error.update({'status' : 'failed, ' + err_str })

            # Update list of mountpoint statuses 
            export_name = os.path.basename(status['export_root'])
            mnt_config = {"export " + export_name + ' (eid=' + str(status['eid']) + ') on ' + mountpoint : mountpoint_status}
            mount_statuses_l.append(mnt_config)
            if mountpoint_error:
                mnt_config_err = {"export " + export_name + ' (eid=' + str(status['eid']) + ') on ' + mountpoint : mountpoint_error}
                mount_errors_l.append(mnt_config_err)

        # Update host
        host_statuses_l.update({str(h) :mount_statuses_l})
        if mount_errors_l:
            host_errors_l.update({str(h) : mount_errors_l})

    # Display output
    ordered_puts(host_statuses_l)

    # Check errors
    if host_errors_l:
     raise MultipleError(host_errors_l)

def dispatch(args):
    p = Platform(args.exportd)
    globals()[args.action.replace('-', '_')](p, args)
