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
# import json
import yaml
from collections import OrderedDict


def order_rep(dumper, data):
    return dumper.represent_mapping(u'tag:yaml.org,2002:map', data.items(), flow_style=False)

def ordered_puts(ordered):
    yaml.add_representer(OrderedDict, order_rep)
    # print >> sys.stdout, json.dumps(obj, indent=4, separators=(',', ':'))
    sys.stdout.write(yaml.dump(OrderedDict(ordered), default_flow_style=False))
    #sys.stdout.write(yaml.dump(OrderedDict(ordered)))

def puts(obj):
    sys.stdout.write(yaml.dump(obj))
