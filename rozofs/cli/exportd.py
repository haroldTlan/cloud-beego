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

from zoofs.core.platform import Platform, Role
from zoofs.core.constants import LAYOUT_VALUES
from zoofs.cli.output import ordered_puts
from collections import OrderedDict
from zoofs.core.constants import NBCORES
from zoofs.cli.exceptions import MultipleError

def layout_set(platform, args):
    platform.set_layout(args.layout[0])
    ordered_puts({platform._active_export_host : {'layout '+str(layout): OrderedDict([
          ("inverse", LAYOUT_VALUES[layout][0]),
          ("forward", LAYOUT_VALUES[layout][1]),
          ("safe", LAYOUT_VALUES[layout][2])
        ])}})


def layout_get(platform, args):
    layout = platform.get_layout()
    ordered_puts({platform._active_export_host : {'layout '+str(layout): OrderedDict([
          ("inverse", LAYOUT_VALUES[layout][0]),
          ("forward", LAYOUT_VALUES[layout][1]),
          ("safe", LAYOUT_VALUES[layout][2])
        ])}})


def option_list(platform, args):

    e_host = platform._active_export_host
    configurations = platform.get_configurations([e_host], Role.EXPORTD)
    config = configurations[e_host][Role.EXPORTD]

    export_l={}
    errors_l={}

    # Check exception
    if isinstance(config, Exception):
        # Get error msg
        err_str = type(config).__name__ + ' (' + str(config) + ')'
        # Update standard output dict
        export_l.update({e_host: err_str})
        # Update errors dict
        errors_l.update({e_host : err_str})
    else:
        options_l = []
        options_l.append({'nbcores' : config.nbcores})
        export_l.update( {e_host :{'OPTIONS':options_l}})

    ordered_puts(export_l)

    if errors_l:
        raise MultipleError(errors_l)


def option_get(platform, args):

    # Check given option
    valid_opts = [NBCORES]
    if args.option not in valid_opts:
        raise Exception('invalid option: \'%s\' (valid value: %s).'
                        % (args.option, ', '.join(valid_opts)))

    e_host = platform._active_export_host
    configurations = platform.get_configurations([e_host], Role.EXPORTD)
    config = configurations[e_host][Role.EXPORTD]

    export_l={}
    errors_l={}

    # Check exception
    if isinstance(config, Exception):
        # Get error msg
        err_str = type(config).__name__ + ' (' + str(config) + ')'
        # Update standard output dict
        export_l.update({e_host: err_str})
        # Update errors dict
        errors_l.update({e_host : err_str})
    else:
        options_l = []
        if args.option == NBCORES:
            options_l.append({'nbcores' : config.nbcores})
        export_l.update( {e_host :{'OPTIONS':options_l}})

    ordered_puts(export_l)

    if errors_l:
        raise MultipleError(errors_l)


def option_set(platform, args):

    # Check given option
    valid_opts = [NBCORES]
    if args.option not in valid_opts:
        raise Exception('invalid option: \'%s\' (valid value: %s).'
                        % (args.option, ', '.join(valid_opts)))

    e_host = platform._active_export_host
    configurations = platform.get_configurations([e_host], Role.EXPORTD)

    config = configurations[e_host][Role.EXPORTD]

    export_l={}
    errors_l={}

    # Check exception
    if isinstance(config, Exception):
        # Get error msg
        err_str = type(config).__name__ + ' (' + str(config) + ')'
        # Update standard output dict
        export_l.update({e_host: err_str})
        # Update errors dict
        errors_l.update({e_host : err_str})
    else:
        options_l = []
        if args.option == NBCORES:
            config.nbcores = args.value

        configurations[e_host][Role.EXPORTD] = config
        platform._get_nodes(e_host)[e_host].set_configurations(configurations[e_host])
        options_l.append({args.option : int(args.value)})
        export_l.update( {e_host :{'OPTIONS':options_l}})

    ordered_puts(export_l)

    if errors_l:
        raise MultipleError(errors_l)


def dispatch(args):
    p = Platform(args.exportd, Role.EXPORTD)
    globals()[ "_".join([args.subtopic.replace('-', '_'), args.action.replace('-', '_')])](p, args)
