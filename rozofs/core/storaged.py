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

import os
from zoofs.core.configuration import ConfigurationParser, ConfigurationReader, \
    ConfigurationWriter
from zoofs.core.libconfig import config_setting_add, CONFIG_TYPE_INT, \
    config_setting_set_int, CONFIG_TYPE_LIST, CONFIG_TYPE_GROUP, \
    CONFIG_TYPE_STRING, CONFIG_TYPE_BOOL, \
    config_setting_set_string, config_lookup, config_setting_get_int, \
    config_setting_length, config_setting_get_elem, config_setting_get_member, \
    config_setting_get_string, config_setting_set_int_elem, \
    config_setting_get_int_elem, config_setting_get_bool, \
    config_setting_set_bool
from zoofs.core.daemon import DaemonManager
from zoofs.core.constants import LAYOUT, STORAGES, STORAGE_SID, STORAGE_CID, STORAGE_ROOT, \
    LAYOUT_2_3_4, STORAGED_MANAGER, LAYOUT_4_6_8, LAYOUT_8_12_16, LISTEN, \
    LISTEN_ADDR, LISTEN_PORT, THREADS, NBCORES, STORIO, CRC32C_CHECK, \
    CRC32C_GENERATE, CRC32C_HW_FORCED, STORAGE_PORTS_MAX, STORAGE_DEV_T, \
    STORAGE_DEV_M, STORAGE_DEV_R, SELF_HEALING, EXPORT_HOSTS
from zoofs.core.agent import Agent, ServiceStatus
from zoofs import __sysconfdir__
import collections
import syslog
import subprocess


class StorageConfig():
    def __init__(self, cid=0, sid=0, root="", device_t=1, device_m=1, device_r=1):
        self.cid = cid
        self.sid = sid
        self.root = root
        self.device_t = device_t
        self.device_m = device_m
        self.device_r = device_r

class ListenConfig():
    def __init__(self, addr="*", port=41001):
        self.addr = addr
        self.port = port

class StoragedConfig():
    def __init__(self, threads=None, nbcores=None, storio=None,
                 crc32c_check=None, crc32c_generate=None, crc32c_hw_forced=None,
                 self_healing=None, export_hosts=None,
                 listens=[], storages={}):
        self.threads = threads
        self.nbcores = nbcores
        self.storio = storio
        self.crc32c_check = crc32c_check
        self.crc32c_generate = crc32c_generate
        self.crc32c_hw_forced = crc32c_hw_forced
        self.self_healing = self_healing
        self.export_hosts = export_hosts
        # keys is a tuple (cid, sid)
        self.storages = storages
        self.listens = listens

class StoragedConfigurationParser(ConfigurationParser):

    def parse(self, configuration, config):

        if configuration.threads is not None:
            threads_setting = config_setting_add(config.root, THREADS, CONFIG_TYPE_INT)
            config_setting_set_int(threads_setting, int(configuration.threads))

        if configuration.nbcores is not None:
            nbcores_setting = config_setting_add(config.root, NBCORES, CONFIG_TYPE_INT)
            config_setting_set_int(nbcores_setting, int(configuration.nbcores))

        if configuration.storio is not None:
             storio_setting = config_setting_add(config.root, STORIO, CONFIG_TYPE_STRING)
             config_setting_set_string(storio_setting, configuration.storio)

        if configuration.self_healing is not None:
             self_healing_setting = config_setting_add(config.root, SELF_HEALING, CONFIG_TYPE_INT)
             config_setting_set_int(self_healing_setting, configuration.self_healing)

        if configuration.export_hosts is not None:
             export_hosts_setting = config_setting_add(config.root, EXPORT_HOSTS, CONFIG_TYPE_STRING)
             config_setting_set_string(export_hosts_setting, configuration.export_hosts)

        if configuration.crc32c_check is not None:
             crc32c_check_setting = config_setting_add(config.root, CRC32C_CHECK, CONFIG_TYPE_BOOL)
             config_setting_set_bool(crc32c_check_setting, configuration.crc32c_check)

        if configuration.crc32c_generate is not None:
             crc32c_gen_setting = config_setting_add(config.root, CRC32C_GENERATE, CONFIG_TYPE_BOOL)
             config_setting_set_bool(crc32c_gen_setting, configuration.crc32c_generate)

        if configuration.crc32c_hw_forced is not None:
             crc32c_hw_forced_setting = config_setting_add(config.root, CRC32C_HW_FORCED, CONFIG_TYPE_BOOL)
             config_setting_set_bool(crc32c_hw_forced_setting, configuration.crc32c_hw_forced)

        listen_settings = config_setting_add(config.root, LISTEN, CONFIG_TYPE_LIST)
        for listen in configuration.listens:
            listen_setting = config_setting_add(listen_settings, '', CONFIG_TYPE_GROUP)
            addr_setting = config_setting_add(listen_setting, LISTEN_ADDR, CONFIG_TYPE_STRING)
            config_setting_set_string(addr_setting, listen.addr)
            port_setting = config_setting_add(listen_setting, LISTEN_PORT, CONFIG_TYPE_INT)
            config_setting_set_int(port_setting, listen.port)

        storage_settings = config_setting_add(config.root, STORAGES, CONFIG_TYPE_LIST)
        for storage in configuration.storages.values():
            storage_setting = config_setting_add(storage_settings, '', CONFIG_TYPE_GROUP)
            cid_setting = config_setting_add(storage_setting, STORAGE_CID, CONFIG_TYPE_INT)
            config_setting_set_int(cid_setting, storage.cid)
            sid_setting = config_setting_add(storage_setting, STORAGE_SID, CONFIG_TYPE_INT)
            config_setting_set_int(sid_setting, storage.sid)
            root_setting = config_setting_add(storage_setting, STORAGE_ROOT, CONFIG_TYPE_STRING)
            config_setting_set_string(root_setting, storage.root)
            device_t_setting = config_setting_add(storage_setting, STORAGE_DEV_T, CONFIG_TYPE_INT)
            config_setting_set_int(device_t_setting, storage.device_t)
            device_m_setting = config_setting_add(storage_setting, STORAGE_DEV_M, CONFIG_TYPE_INT)
            config_setting_set_int(device_m_setting, storage.device_m)
            device_r_setting = config_setting_add(storage_setting, STORAGE_DEV_R, CONFIG_TYPE_INT)
            config_setting_set_int(device_r_setting, storage.device_r)

    def unparse(self, config, configuration):

        threads_setting = config_lookup(config, THREADS)
        if threads_setting is not None:
            configuration.threads = config_setting_get_int(threads_setting)

        nbcores_setting = config_lookup(config, NBCORES)
        if nbcores_setting is not None:
            configuration.nbcores = config_setting_get_int(nbcores_setting)

        storio_setting = config_lookup(config, STORIO)
        if storio_setting is not None:
            configuration.storio = config_setting_get_string(storio_setting)

        self_healing_setting = config_lookup(config, SELF_HEALING)
        if self_healing_setting is not None:
            configuration.self_healing = config_setting_get_int(self_healing_setting)

        export_hosts_setting = config_lookup(config, EXPORT_HOSTS)
        if export_hosts_setting is not None:
            configuration.export_hosts = config_setting_get_string(export_hosts_setting)

        crc32c_check_setting = config_lookup(config, CRC32C_CHECK)
        if crc32c_check_setting is not None:
            configuration.crc32c_check = config_setting_get_bool(crc32c_check_setting)

        crc32c_gen_setting = config_lookup(config, CRC32C_GENERATE)
        if crc32c_gen_setting is not None:
            configuration.crc32c_generate = config_setting_get_bool(crc32c_gen_setting)

        crc32c_hw_forced_setting = config_lookup(config, CRC32C_HW_FORCED)
        if crc32c_hw_forced_setting is not None:
            configuration.crc32c_hw_forced = config_setting_get_bool(crc32c_hw_forced_setting)


        listen_settings = config_lookup(config, LISTEN)
        if listen_settings is not None:

            nb_io_addr = config_setting_length(listen_settings)

            if nb_io_addr == 0:
                raise SyntaxError("no IO listen address defined")

            if nb_io_addr > STORAGE_PORTS_MAX:
                raise SyntaxError("too many IO listen addresses defined.%d "
                                  "while max is %d." 
                                  % (nb_io_addr, STORAGE_PORTS_MAX))

            configuration.listens = []
            for i in range(config_setting_length(listen_settings)):

                listen_setting = config_setting_get_elem(listen_settings, i)

                if listen_setting is not None:

                    addr_setting = config_setting_get_member(listen_setting,
                                                             LISTEN_ADDR)
                    if addr_setting is not None:
                        addr = config_setting_get_string(addr_setting)
                    else:
                        raise SyntaxError("can't lookup key '%s' in IO address "
                                          "(idx: %d)" % (LISTEN_ADDR, i))

                    port_setting = config_setting_get_member(listen_setting,
                                                             LISTEN_PORT)
                    if port_setting is not None:
                        port = config_setting_get_int(port_setting)
                    else:
                        raise SyntaxError("can't lookup key '%s' in IO address "
                                          "(idx: %d)" % (LISTEN_PORT, i))

                    configuration.listens.append(ListenConfig(addr, port))

                else:
                    raise SyntaxError("can't fetch IO listen address(es)"
                                      " settings (idx: %d)" % i);
        else:
            raise SyntaxError("can't fetch '%s' settings" % LISTEN)


        storage_settings = config_lookup(config, STORAGES)

        if storage_settings is not None:

            configuration.storages = {}

            for i in range(config_setting_length(storage_settings)):

                storage_setting = config_setting_get_elem(storage_settings, i)

                cid_setting = config_setting_get_member(storage_setting,
                                                        STORAGE_CID)
                if cid_setting is not None:
                    cid = config_setting_get_int(cid_setting)
                else:
                    raise SyntaxError("can't lookup key '%s' for "
                                      "storage (idx: %d)" % (STORAGE_CID, i))

                sid_setting = config_setting_get_member(storage_setting,
                                                        STORAGE_SID)
                if sid_setting is not None:
                    sid = config_setting_get_int(sid_setting)
                else:
                    raise SyntaxError("can't lookup key '%s' for "
                                      "storage (idx: %d)" % (STORAGE_SID, i))

                root_setting = config_setting_get_member(storage_setting,
                                                         STORAGE_ROOT)
                if root_setting is not None:
                    root = config_setting_get_string(root_setting)
                else:
                    raise SyntaxError("can't lookup key '%s' for "
                                      "storage (idx: %d)" % (STORAGE_ROOT, i))

                device_t_setting = config_setting_get_member(storage_setting,
                                                        STORAGE_DEV_T)
                if device_t_setting is not None:
                    device_t = config_setting_get_int(device_t_setting)
                else:
                    raise SyntaxError("can't lookup key '%s' for "
                                      "storage (idx: %d)" % (STORAGE_DEV_T, i))

                device_m_setting = config_setting_get_member(storage_setting,
                                                        STORAGE_DEV_M)
                if device_m_setting is not None:
                    device_m = config_setting_get_int(device_m_setting)
                else:
                    raise SyntaxError("can't lookup key '%s' for "
                                      "storage (idx: %d)" % (STORAGE_DEV_M, i))

                device_r_setting = config_setting_get_member(storage_setting,
                                                        STORAGE_DEV_R)
                if device_r_setting is not None:
                    device_r = config_setting_get_int(device_r_setting)
                else:
                    raise SyntaxError("can't lookup key '%s' for "
                                      "storage (idx: %d)" % (STORAGE_DEV_R, i))

                configuration.storages[(cid, sid)] = StorageConfig(cid,
                                                                   sid,
                                                                   root,
                                                                   device_t,
                                                                   device_m,
                                                                   device_r
                                                                   )

        else:
            raise SyntaxError("can't fetch '%s' settings" % STORAGES)

class StoragedAgent(Agent):

    def __init__(self, config="%s%s" % (__sysconfdir__, '/zoofs/storage.conf'), daemon='storaged'):
        Agent.__init__(self, STORAGED_MANAGER)
        self._daemon_manager = DaemonManager(daemon, ["-c", config], 5)
        self._reader = ConfigurationReader(config, StoragedConfigurationParser())
        self._writer = ConfigurationWriter(config, StoragedConfigurationParser())
        self._rebuilder = "storage_rebuild"

    def get_service_config(self):
        configuration = StoragedConfig()
        return self._reader.read(configuration)

    def set_service_config(self, configuration):

        for s in configuration.storages.values():
            if not os.path.isabs(s.root):
                raise Exception('%s: not absolute.' % s.root)
            if not os.path.exists(s.root):
                os.makedirs(s.root)
            if not os.path.isdir(s.root):
                raise Exception('%s: not a directory.' % s.root)
            
            for dev in range(0, s.device_t):
                dev_path="%s/%s" % (s.root, str(dev))
                if not os.path.isabs(dev_path):
                    raise Exception('%s: not absolute.' % dev_path)
                if not os.path.exists(dev_path):
                    os.makedirs(dev_path)
                if not os.path.isdir(dev_path):
                    raise Exception('%s: not a directory.' % dev_path)

        self._writer.write(configuration)
        self._daemon_manager.restart()

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

    def start_rebuild(self, exports_list, cid=None, sid=None, device=None):
        if cid is not None and sid is not None:
            if device is not None:
                cmds = self._rebuilder + ' -s ' + str(cid) + '/' + str(sid) + ' -d ' + str(device) + " -r " + "/".join(exports_list)
            else:
                cmds = self._rebuilder + ' -s ' + str(cid) + '/' + str(sid) + " -r " + "/".join(exports_list)
        else:
            cmds = self._rebuilder + " -r " + "/".join(exports_list)

        p = subprocess.Popen(cmds, shell=True, stdin=None, stdout=None, stderr=None, close_fds=True)
