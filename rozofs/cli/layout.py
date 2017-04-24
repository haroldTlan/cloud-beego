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

def set(platform, args):
    platform.set_layout(args.layout[0])

def get(platform, args):
    layout = platform. get_layout()
    ordered_puts({'layout '+str(layout): OrderedDict([
          ("inverse", LAYOUT_VALUES[layout][0]),
          ("forward", LAYOUT_VALUES[layout][1]),
          ("safe", LAYOUT_VALUES[layout][2])
        ])})

def dispatch(args):
    p = Platform(args.exportd, Role.EXPORTD)
    globals()[args.action.replace('-', '_')](p, args)
