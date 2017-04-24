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
from zoofs.cli.output import ordered_puts
from zoofs.cli.output import puts
from collections import OrderedDict


def create(platform, args):
    platform.create_export(args.vid[0], args.name, args.passwd, args.squota, args.hquota)


def update(platform, args):
    platform.update_export(args.eid[0], args.current, args.passwd, args.squota, args.hquota)


def remove(platform, args):
    if not args.eids:
        args.eids = None

    platform.remove_export(args.eids, args.force)

def get(platform, args):

    e_host = platform._active_export_host
    configurations = platform.get_configurations([e_host], Role.EXPORTD)

    configuration = configurations[e_host][Role.EXPORTD]

    # Check exception
    if isinstance(configuration, Exception):
        raise type(configuration)(str(configuration))

    eids_l = []
    if not args.eids:
        eids_l = configuration.exports.keys()
    else:
        eids_l = args.eids

    list_l = {}
    exports_l = []
    for eid in eids_l:

        if eid not in configuration.exports:
            raise Exception("Unknown export with eid=%d." % eid)

        econfig = configuration.exports[eid]
        export_l = []
        export_l.append({'vid':econfig.vid})
        export_l.append({'root':econfig.root})
        export_l.append({'md5':econfig.md5})
        export_l.append({'squota':econfig.squota})
        export_l.append({'hquota':econfig.hquota})

        exports_l.append({'EXPORT '+ str(eid):export_l})
    list_l.update({'EXPORTS': exports_l})
    ordered_puts(list_l)

def dispatch(args):

    p = Platform(args.exportd, Role.EXPORTD)

    globals()[args.action.replace('-', '_')](p, args)
