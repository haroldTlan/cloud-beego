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

AGENT_PORT = 9999

PLATFORM_MANAGER = "platform"
EXPORTD_MANAGER = "exportd"
STORAGED_MANAGER = "storaged"
ROZOFSMOUNT_MANAGER = "zoofsmount"
NFS_MANAGER = "nfs"
# SHARE_MANAGER = "share"

LAYOUT_NONE = -1
LAYOUT_2_3_4 = 0
LAYOUT_4_6_8 = 1
LAYOUT_8_12_16 = 2

LAYOUT_INVERSE = 0
LAYOUT_FORWARD = 1
LAYOUT_SAFE = 2
LAYOUT_VALUES = [[2, 3, 4], [4, 6, 8], [8, 12, 16]]

EXPORTD_HOSTNAME = "exportd_hostname"
# PROTOCOLS = "protocols"
# PROTOCOLS_VALUES = ["nfs", "cifs", "afp"]
# only NFS for now
# PROTOCOLS_VALUES = ["nfs"]

NBCORES = "nbcores"

THREADS = "threads"
STORIO = "storio"
STORIO_VALID_VALUES = ["single", "multiple"]
SELF_HEALING="self-healing"
EXPORT_HOSTS="export-hosts"
CRC32C_CHECK = "crc32c_check"
CRC32C_GENERATE = "crc32c_generate"
CRC32C_HW_FORCED = "crc32c_hw_forced"
LISTEN = "listen"
LISTEN_ADDR = "addr"
LISTEN_PORT = "port"
STORAGES = "storages"
STORAGE_CID = "cid"
STORAGE_SID = "sid"
STORAGE_ROOT = "root"
STORAGE_DEV_T = "device-total"
STORAGE_DEV_M = "device-mapper"
STORAGE_DEV_R = "device-redundancy"


SID_MAX = 255
STORAGE_PORTS_MAX = 32

LAYOUT = "layout"
VOLUMES = "volumes"
VOLUME_VID = "vid"
VOLUME = "volume"
VOLUME_CIDS = "cids"
VOLUME_CID = "cid"
VOLUME_SIDS = "sids"
VOLUME_SID = "sid"
VOLUME_HOST = "host"
EXPORTS = "exports"
EXPORT_EID = "eid"
EXPORT_ROOT = "root"
EXPORT_MD5 = "md5"
EXPORT_HQUOTA = "hquota"
EXPORT_SQUOTA = "squota"

STORAGES_ROOT = "/srv/zoofs/storages"
EXPORTS_ROOT = "/srv/zoofs/exports"
