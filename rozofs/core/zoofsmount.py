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

from zoofs.core.agent import Agent, ServiceStatus
from zoofs.core.constants import ROZOFSMOUNT_MANAGER
import os
import subprocess
from zoofs.ext.fstab import Fstab, Line

class RozofsMountConfig(object):
    def __init__(self, export_host, export_path, instance, mountpoint=None, options=None):

        self.export_host = export_host
        self.export_path = export_path
        self.instance = instance

        if mountpoint is None:
            self.mountpoint = os.path.join('/mnt/zoofs@%s' % export_host.replace('/','-'), export_path.split('/')[-1])
        else:
            self.mountpoint = mountpoint
        if options is None:
            self.options = []
        else:
            self.options = options

    def __eq__(self, other):
        return self.export_host == other.export_host and self.export_path == other.export_path and self.mountpoint == other.mountpoint

class RozofsMountAgent(Agent):
    '''
    Managed zoofsmount via fstab
    '''

    __FSTAB = '/etc/fstab'
    __MTAB = '/etc/mtab'
    __FSTAB_LINE = "rozofsmount\t%s\trozofs\texporthost=%s,exportpath=%s,instance=%d%s,_netdev\t0\t0\n"

    def __init__(self, mountdir='/mnt'):
        """
        ctor
        @param mountdir : the parent directory name for rozofs mount points
        """
        Agent.__init__(self, ROZOFSMOUNT_MANAGER)
        self._mountdir = mountdir

    def _mount_path(self, export_host, export_path):
        return os.path.join(self._mountdir, "rozofs@%s" % export_host.replace('/','-'),
                            export_path.split('/')[-1])

    #
    # mount points management
    #
    def _mount(self, path):
        cmds = ['mount', path]
        with open('/dev/null', 'w') as devnull:
            p = subprocess.Popen(cmds, stdout=devnull, stderr=subprocess.PIPE)
            if p.wait() is not 0 :
                raise Exception(p.communicate()[1])
        return True

    def _umount(self, path):
        cmds = ['umount', path]
        with open('/dev/null', 'w') as devnull:
            p = subprocess.Popen(cmds, stdout=devnull, stderr=subprocess.PIPE)
            if p.wait() is not 0 :
                raise Exception(p.communicate()[1])
        return True

    def _list_mount(self):
        with open(self.__MTAB, 'r') as mtab:
            mount = [l.split()[1] for l in mtab if l.split()[0] == "rozofs"]
        return mount

#    def _is_mount(self, share):
#        return self._mount_path(share) in self._list_mount()

    def _add_mountpoint(self, config, instance):
        fstab = Fstab()
        fstab.read(self.__FSTAB)

        mount_path = self._mount_path(config.export_host, config.export_path)

        # Create mountpoint
        if not os.path.exists(config.mountpoint):
            os.makedirs(config.mountpoint)
        else:
            if not os.path.isdir(config.mountpoint):
                raise Exception('mountpoint: %s is not a directory.'
                                 % config.mountpoint)
                # Check if empty
        # add a line to fstab
        if not config.options:
            stroptions=""
        else:
            stroptions = ',' + ','.join(config.options)
        print self.__FSTAB_LINE
        fstab.lines.append(Line(self.__FSTAB_LINE % (config.mountpoint,
                                                     config.export_host,
                                                     config.export_path,
                                                     instance,
                                                     stroptions)))
        print Line(self.__FSTAB_LINE % (config.mountpoint,
                                                     config.export_host,
                                                     config.export_path,
                                                     instance,
                                                     stroptions))
        fstab.write(self.__FSTAB)

    def _remove_mountpoint(self, config):
        fstab = Fstab()
        fstab.read(self.__FSTAB)
        mount_path = self._mount_path(config.export_host, config.export_path)
        if os.path.exists(config.mountpoint):
            os.rmdir(config.mountpoint)
        # remove the line from fstab
        newlines = [l for l in fstab.lines if l.directory != config.mountpoint]
        fstab.lines = newlines
        fstab.write(self.__FSTAB)

    def _list_mountpoint(self):
        fstab = Fstab()
        fstab.read(self.__FSTAB)
        return [l.directory for l in fstab.get_rozofs_lines()]

    def get_service_config(self):
        fstab = Fstab()
        fstab.read(self.__FSTAB)
        configurations = []
        for l in fstab.get_rozofs_lines():
            o = l.get_rozofs_options()
            configurations.append(RozofsMountConfig(o["host"], o["path"],
                                                    o["instance"],
                                                    o["mountpoint"]))
        return configurations

    def set_service_config(self, configurations):
        responses = {}
        instance = 0
        currents = self.get_service_config()

        # find an instance
        if currents:
            instance = max([int(c.instance) for c in currents]) + 1

        # For added mountpoint(s)
        for config in [c for c in configurations if c not in currents]:
            mnt_statuses = {}
            mnt_statuses['config'] = True
            mnt_statuses['service'] = True
            # Add the mountpoint
            try:
                self._add_mountpoint(config, instance)
            except Exception as e:
                mnt_statuses['config'] = type(e)(str(e))
            # Mount it
            if mnt_statuses['config'] is True:
                try:
                    self._mount(config.mountpoint)
                except Exception as e:
                    mnt_statuses['service'] = type(e)(str(e))
            else:
                mnt_statuses['service'] = False

            # Add mnt statuses to response
            responses[config.mountpoint] = mnt_statuses
            instance = instance + 1

        # For removed mountpoint(s)
        for config in [c for c in currents if c not in configurations]:
            mnt_statuses = {}
            mnt_statuses['config'] = True
            mnt_statuses['service'] = True
            # Umount this mountpoint
            try:
                self._umount(config.mountpoint)
            except Exception as e:
                mnt_statuses['service'] = type(e)(str(e))
            # Remove it from fstab
            if mnt_statuses['service'] is True:
                try:
                    self._remove_mountpoint(config)
                except Exception as e:
                    mnt_statuses['config'] = type(e)(str(e))
            else:
                mnt_statuses['config'] = False
            # Add mnt statuses to response
            responses[config.mountpoint] = mnt_statuses

        return responses

    def get_service_status(self):
        statuses = {}
        for m in self._list_mountpoint():
            if m in self._list_mount():
                statuses[m] = ServiceStatus.STARTED
            else:
                statuses[m] = ServiceStatus.STOPPED
        return statuses

    def set_service_status(self, status):
        changes = {}

        if status == ServiceStatus.STARTED:
            # For each mountpoint defined in fstab
            for mp in self._list_mountpoint():
                # Check it's already mounted
                if mp in self._list_mount():
                    changes[mp] = False
                else:
                    changes[mp]= self._mount(mp)

        if status == ServiceStatus.STOPPED:
            # For each mountpoint defined in fstab
            for mp in self._list_mountpoint():
                # Check it's not mounted
                if mp not in self._list_mount():
                    changes[mp] = False
                else:
                    changes[mp]= self._umount(mp)

        return changes
