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

from zoofs.core.configuration import ConfigurationParser, ConfigurationReader, \
    ConfigurationWriter
from zoofs.core.libconfig import config_setting_add, CONFIG_TYPE_INT, \
    config_setting_set_int, CONFIG_TYPE_LIST, CONFIG_TYPE_GROUP, CONFIG_TYPE_STRING, \
    config_setting_set_string, config_lookup, config_setting_get_int, \
    config_setting_length, config_setting_get_elem, config_setting_get_member, \
    config_setting_get_string
from zoofs.core.constants import LAYOUT, VOLUME, VOLUME_VID, VOLUME_CID, \
    VOLUME_SIDS, VOLUME_SID, VOLUME_HOST, EXPORTS, EXPORT_EID, EXPORT_ROOT, \
    EXPORT_MD5, EXPORT_SQUOTA, EXPORT_HQUOTA, VOLUME_CIDS, LAYOUT_2_3_4, VOLUMES, \
    EXPORTD_MANAGER, LAYOUT_4_6_8, LAYOUT_8_12_16, NBCORES
from zoofs.core.daemon import DaemonManager
from zoofs import __sysconfdir__
import os
from zoofs.core.agent import Agent, ServiceStatus
import subprocess
import shutil

class StorageStat():
    def __init__(self, host="", size=0, free=0):
        self.host = host
        self.size = size
        self.free = free

class ClusterStat():
    def __init__(self, size=0, free=0, sstats=None):
        self.size = size
        self.free = free
        if sstats is None:
            self.sstats = {}
        else:
            self.sstats = sstats

class VolumeStat():
    def __init__(self, bsize=0, bfree=0, blocks=0, cstats=None):
        self.bsize = bsize
        self.bfree = bfree
        self.blocks = blocks
        if cstats is None:
            self.cstats = {}
        else:
            self.cstats = cstats

class ExportStat():
    def __init__(self, bsize=0, blocks=0, bfree=0, files=0, ffree=0):
        self.bsize = bsize
        self.blocks = blocks
        self.bfree = bfree
        self.files = files
        self.ffree = ffree

class ExportdStat():
    def __init__(self, vstats=None, estats=None):
        if vstats is None:
            self.vstats = {}
        else:
            self.vstats = vstats
        if estats is None:
            self.estats = {}
        else:
            self.estats = estats

class ClusterConfig():
    def __init__(self, cid, storages=None):
        self.cid = cid
        if storages is None:
            self.storages = {}
        else:
            self.storages = storages

    def __eq__(self, other):
        return self.__dict__ == other.__dict__


class VolumeConfig():
    def __init__(self, vid, layout=None, clusters=None):
        self.vid = vid
        self.layout = layout
        if clusters is None:
            self.clusters = {}
        else:
            self.clusters = clusters

    def __eq__(self, other):
        return self.__dict__ == other.__dict__


class ExportConfig():
    def __init__(self, eid, vid, root, md5, squota, hquota):
        self.eid = eid
        self.vid = vid
        self.root = root
        self.md5 = md5
        self.squota = squota
        self.hquota = hquota

    def __eq__(self, other):
        return self.__dict__ == other.__dict__


class ExportdConfig():
    def __init__(self, nbcores=None, layout=LAYOUT_2_3_4, volumes=None, exports=None, stats=None):
        self.nbcores = nbcores
        self.layout = layout
        if volumes is None:
            self.volumes = {}
        else:
            self.volumes = volumes
        if exports is None:
            self.exports = {}
        else:
            self.exports = exports
        if stats is None:
            self.stats = ExportdStat()
        else:
            self.stats = stats

    def __eq__(self, other):
        return self.__dict__ == other.__dict__


class ExportdConfigurationParser(ConfigurationParser):

    def parse(self, configuration, config):

        if configuration.nbcores is not None:
            nbcores_setting = config_setting_add(config.root, NBCORES, CONFIG_TYPE_INT)
            config_setting_set_int(nbcores_setting, int(configuration.nbcores))

        layout_setting = config_setting_add(config.root, LAYOUT, CONFIG_TYPE_INT)
        config_setting_set_int(layout_setting, int(configuration.layout))

        volumes_settings = config_setting_add(config.root, VOLUMES, CONFIG_TYPE_LIST)
        for volume in configuration.volumes.values():
            volume_settings = config_setting_add(volumes_settings, VOLUME, CONFIG_TYPE_GROUP)

            vid_setting = config_setting_add(volume_settings, VOLUME_VID, CONFIG_TYPE_INT)
            config_setting_set_int(vid_setting, int(volume.vid))
            
            if volume.layout is not None:
                volume_layout_setting = config_setting_add(volume_settings, LAYOUT, CONFIG_TYPE_INT)
                config_setting_set_int(volume_layout_setting, int(volume.layout))

            clusters_settings = config_setting_add(volume_settings, VOLUME_CIDS, CONFIG_TYPE_LIST)
            for cluster in volume.clusters.values():
                cluster_setting = config_setting_add(clusters_settings, '', CONFIG_TYPE_GROUP)
                cid_setting = config_setting_add(cluster_setting, VOLUME_CID, CONFIG_TYPE_INT)
                config_setting_set_int(cid_setting, int(cluster.cid))
                sids_setting = config_setting_add(cluster_setting, VOLUME_SIDS, CONFIG_TYPE_LIST)
                for sid, host in cluster.storages.items():
                    storage_setting = config_setting_add(sids_setting, '', CONFIG_TYPE_GROUP)
                    sid_setting = config_setting_add(storage_setting, VOLUME_SID, CONFIG_TYPE_INT)
                    config_setting_set_int(sid_setting, int(sid))
                    host_setting = config_setting_add(storage_setting, VOLUME_HOST, CONFIG_TYPE_STRING)
                    config_setting_set_string(host_setting, str(host))

        export_settings = config_setting_add(config.root, EXPORTS, CONFIG_TYPE_LIST)
        for export in configuration.exports.values():
            export_setting = config_setting_add(export_settings, '', CONFIG_TYPE_GROUP)
            eid_setting = config_setting_add(export_setting, EXPORT_EID, CONFIG_TYPE_INT)
            config_setting_set_int(eid_setting, int(export.eid))
            vid_setting = config_setting_add(export_setting, VOLUME_VID, CONFIG_TYPE_INT)
            config_setting_set_int(vid_setting, int(export.vid))
            root_setting = config_setting_add(export_setting, EXPORT_ROOT, CONFIG_TYPE_STRING)
            config_setting_set_string(root_setting, str(export.root))
            md5_setting = config_setting_add(export_setting, EXPORT_MD5, CONFIG_TYPE_STRING)
            config_setting_set_string(md5_setting, str(export.md5))
            sqt_setting = config_setting_add(export_setting, EXPORT_SQUOTA, CONFIG_TYPE_STRING)
            config_setting_set_string(sqt_setting, str(export.squota))
            hqt_setting = config_setting_add(export_setting, EXPORT_HQUOTA, CONFIG_TYPE_STRING)
            config_setting_set_string(hqt_setting, str(export.hquota))

    def unparse(self, config, configuration):

        nbcores_setting = config_lookup(config, NBCORES)
        if nbcores_setting is not None:
            configuration.nbcores = config_setting_get_int(nbcores_setting)

        layout_setting = config_lookup(config, LAYOUT)
        if layout_setting is not None:
            configuration.layout = config_setting_get_int(layout_setting)
        else:
            raise SyntaxError("can't lookup key '%s'" % LAYOUT)


        volumes_setting = config_lookup(config, VOLUMES)

        configuration.volumes = {}
        if volumes_setting is not None:
            for i in range(config_setting_length(volumes_setting)):

                volume_setting = config_setting_get_elem(volumes_setting, i)

                vid_setting = config_setting_get_member(volume_setting, VOLUME_VID)
                if vid_setting is not None:
                    vid = config_setting_get_int(vid_setting)
                else:
                    raise SyntaxError("can't lookup key '%s' in volume idx: %d"
                                       % (VOLUME_VID, i))

                layout = None
                volume_layout_setting =  config_setting_get_member(volume_setting, LAYOUT)
                if volume_layout_setting is not None:
                    layout = config_setting_get_int(volume_layout_setting)

                clusters_setting = config_setting_get_member(volume_setting, VOLUME_CIDS)
                if clusters_setting is not None:

                    clusters = {}
                    for j in range(config_setting_length(clusters_setting)):

                        cluster_setting = config_setting_get_elem(clusters_setting, j)

                        cid_setting = config_setting_get_member(cluster_setting, VOLUME_CID)
                        if cid_setting is not None:
                            cid = config_setting_get_int(cid_setting)
                        else:
                            raise SyntaxError("can't lookup key '%s'"
                                              " for volume idx: %d,"
                                              " cluster idx: %d" 
                                              % (VOLUME_CID, i, j))

                        storages = {}
                        sids_setting = config_setting_get_member(cluster_setting, VOLUME_SIDS)
                        if sids_setting is None:
                            raise SyntaxError("can't lookup key '%s'"
                                              " for volume idx: %d,"
                                              " cluster idx: %d" 
                                              % (VOLUME_SIDS, i, j))

                        for k in range(config_setting_length(sids_setting)):
                            storage_setting = config_setting_get_elem(sids_setting, k)
                            
                            sid_setting = config_setting_get_member(storage_setting, VOLUME_SID)
                            if sid_setting is not None:
                                sid = config_setting_get_int(sid_setting)
                            else:
                                raise SyntaxError("can't lookup key '%s' for"
                                                  " volume idx: %d,"
                                                  " cluster idx: %d,"
                                                  " storage idx: %d"
                                                   % (VOLUME_SID, i, j, k))

                            host_setting = config_setting_get_member(storage_setting, VOLUME_HOST)
                            if host_setting is not None:
                                host = config_setting_get_string(host_setting)
                            else:
                                raise SyntaxError("can't lookup key '%s' for"
                                                  " volume idx: %d,"
                                                  " cluster idx: %d,"
                                                  " storage idx: %d"
                                                   % (VOLUME_HOST, i, j, k))

                            storages[sid] = host
                            clusters[cid] = ClusterConfig(cid, storages)
                    configuration.volumes[vid] = VolumeConfig(vid, layout, clusters)
                else:
                    raise SyntaxError("can't lookup key '%s' in volume idx: %d"
                                      % (VOLUME_CIDS, i))

        export_settings = config_lookup(config, EXPORTS)
        configuration.exports = {}

        if export_settings is not None:
            for i in range(config_setting_length(export_settings)):
                export_setting = config_setting_get_elem(export_settings, i)

                eid_setting = config_setting_get_member(export_setting, EXPORT_EID)
                if eid_setting is not None:
                    eid = config_setting_get_int(eid_setting)
                else:
                    raise SyntaxError("can't lookup key '%s' in export idx: %d"
                                       % (EXPORT_EID, i))

                vid_setting = config_setting_get_member(export_setting, VOLUME_VID)
                if vid_setting is not None:
                    vid = config_setting_get_int(vid_setting)
                else:
                    raise SyntaxError("can't lookup key '%s' in export idx: %d"
                                       % (VOLUME_VID, i))

                root_setting = config_setting_get_member(export_setting, EXPORT_ROOT)
                if root_setting is not None:
                    root = config_setting_get_string(root_setting)
                else:
                    raise SyntaxError("can't lookup key '%s' in export idx: %d"
                                       % (EXPORT_ROOT, i))

                md5_setting = config_setting_get_member(export_setting, EXPORT_MD5)
                if md5_setting is not None:
                    md5 = config_setting_get_string(md5_setting)
                else:
                    raise SyntaxError("can't lookup key '%s' in export idx: %d"
                                       % (EXPORT_MD5, i))

                sqt_setting = config_setting_get_member(export_setting, EXPORT_SQUOTA)
                if sqt_setting is not None:
                    sqt = config_setting_get_string(sqt_setting)
                else:
                    raise SyntaxError("can't lookup key '%s' in export idx: %d"
                                       % (EXPORT_SQUOTA, i))

                hqt_setting = config_setting_get_member(export_setting, EXPORT_HQUOTA)
                if hqt_setting is not None:
                    hqt = config_setting_get_string(hqt_setting)
                else:
                    raise SyntaxError("can't lookup key '%s' in export idx: %d"
                                       % (EXPORT_HQUOTA, i))

                configuration.exports[eid] = ExportConfig(eid, vid, root,
                                                          md5, sqt, hqt)

class ExportdAgent(Agent):
    """ exportd agent """

    def __init__(self, config="%s%s" % (__sysconfdir__, '/zoofs/export.conf'), daemon='exportd'):
        Agent.__init__(self, EXPORTD_MANAGER)
        self._daemon_manager = DaemonManager(daemon, ["-c", config])
        self._reader = ConfigurationReader(config, ExportdConfigurationParser())
        self._writer = ConfigurationWriter(config, ExportdConfigurationParser())

    def _get_volume_stat(self, vid, vstat):
        # vstat = VolumeStat()
        # Did I ever understood python?
        # I can't figure out why the above line does not initialize
        # a new cstats (on second call)
        # vstat.cstats.clear()
        with open('/var/run/exportd/volume_%d' % vid, 'r') as input:
            cid = 0
            sid = 0
            for line in input:

                if line.startswith("bsize"):
                    vstat.bsize = int(line.split(':')[-1])
                if line.startswith("bfree"):
                    vstat.bfree = int(line.split(':')[-1])
                if line.startswith("blocks"):
                    vstat.blocks = int(line.split(':')[-1])
                if line.startswith("cluster"):
                    cid = int(line.split(':')[-1])
                    vstat.cstats[cid] = ClusterStat()
                    # vstat.cstats[cid].sstats.clear()
                if line.startswith("storage"):
                    sid = int(line.split(':')[-1])
                    vstat.cstats[cid].sstats[sid] = StorageStat()
                if line.startswith("host"):
                    vstat.cstats[cid].sstats[sid].host = line.split(':')[-1].rstrip()
                if line.startswith("size"):
                    if len(vstat.cstats[cid].sstats.keys()) == 0:
                        vstat.cstats[cid].size = int(line.split(':')[-1])
                    else:
                        vstat.cstats[cid].sstats[sid].size = int(line.split(':')[-1])
                if line.startswith("free"):
                    if len(vstat.cstats[cid].sstats.keys()) == 0:
                        vstat.cstats[cid].free = int(line.split(':')[-1])
                    else:
                        vstat.cstats[cid].sstats[sid].free = int(line.split(':')[-1])
        # return vstat

    def _get_export_stat(self, eid, estat):
        with open('/var/run/exportd/export_%d' % eid, 'r') as input:
            for line in input:
                if line.startswith("bsize"):
                    estat.bsize = int(line.split(':')[-1])
                if line.startswith("blocks"):
                    estat.blocks = int(line.split(':')[-1])
                if line.startswith("bfree"):
                    estat.bfree = int(line.split(':')[-1])
                if line.startswith("files"):
                    estat.files = int(line.split(':')[-1])
                if line.startswith("ffree"):
                    estat.ffree = int(line.split(':')[-1])
        # return estat

    def get_service_config(self):
        configuration = ExportdConfig()
        self._reader.read(configuration)
        if not self.get_service_status():
            configuration.stats = None
        else:
            for vid in configuration.volumes.keys():
                configuration.stats.vstats[vid] = VolumeStat()
                self._get_volume_stat(vid, configuration.stats.vstats[vid])
            for eid in configuration.exports.keys():
                configuration.stats.estats[eid] = ExportStat()
                self._get_export_stat(eid, configuration.stats.estats[eid])
        return configuration

    def set_service_config(self, configuration):
        current = ExportdConfig()
        self._reader.read(current)

        current_roots = [e.root for e in current.exports.values()]
        roots = [e.root for e in configuration.exports.values()]

        # create new ones
        for r in [r for r in roots if r not in current_roots]:
            if not os.path.isabs(r):
                raise Exception('%s: not absolute.' % r)

            if not os.path.exists(r):
                os.makedirs(r)

            if not os.path.isdir(r):
                raise Exception('%s: not a directory.' % r)

        self._writer.write(configuration)
        self._daemon_manager.reload()

        # delete no more used ones
        for r in [r for r in current_roots if r not in roots]:
            if os.path.exists(r):
                shutil.rmtree(r)

    def get_service_status(self):
        return self._daemon_manager.status()

    def set_service_status(self, status):
        current_status = self._daemon_manager.status()
        changes = None
        if status == ServiceStatus.STARTED:
            changes = self._daemon_manager.start()
        if status == ServiceStatus.STOPPED:
            changes = self._daemon_manager.stop()
        return changes


class ExportdPacemakerAgent(ExportdAgent):
    """ exportd managed thru pacemaker """

    def __init__(self, config='/zbx/etc/zoofs/export.conf', daemon='/usr/bin/exportd', resource='exportd-rozofs'):
        ExportdAgent.__init__(self, config, daemon)
        self._resource = resource

    def _start(self):
        cmds = ['crm', 'resource', 'start', self._resource]
        if self._daemon_manager.status() is False :
            with open('/dev/null', 'w') as devnull:
                p = subprocess.Popen(cmds, stdout=devnull,
                    stderr=subprocess.PIPE)
                if p.wait() is not 0 :
                    raise Exception(p.communicate()[1])
            return True
        else:
            return False

    def _stop(self):
        cmds = ['crm', 'resource', 'stop', self._resource]
        if self._daemon_manager.status() is True :
            with open('/dev/null', 'w') as devnull:
                p = subprocess.Popen(cmds, stdout=devnull,
                    stderr=subprocess.PIPE)
                if p.wait() is not 0 :
                    raise Exception(p.communicate()[1])
            return True
        else:
            return False

    def get_service_status(self):
        return self._daemon_manager.status()

    def set_service_status(self, status):
        current_status = self._daemon_manager.status()
        changes = None
        if status == ServiceStatus.STARTED:
            changes= self._start()
        if status == ServiceStatus.STOPPED:
            changes = self._stop()
        return changes


