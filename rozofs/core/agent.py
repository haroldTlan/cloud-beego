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
import sys
import syslog
import Pyro.core
import subprocess
import socket
from zoofs.core.constants import AGENT_PORT

class ServiceStatus:
    STARTED = True
    STOPPED = False

class Agent():
    """ An agent is responsible to manage a remote service """

    def __init__(self, name):
        self._name = name

    def get_name(self):
        return self._name

    def get_service_status(self):
        raise NotImplementedError()

    def set_service_status(self, status):
        raise NotImplementedError()

    def get_service_config(self):
        raise NotImplementedError()

    def set_service_config(self, configuration):
        raise NotImplementedError()

class AgentServer(object):
    """Daemon handling management request"""


    def __init__(self, pidfile='/var/run/zoo-agent.pid', agents=[]):
        """
        Args:
            pidfile: file used to track pid.
            agents: list of agents registered on this server.
        """
        self._pidfile = pidfile
        self._agents = agents


    def _daemonize(self):
        """
        Deamonize method. UNIX double fork mechanism.
        """

        try:
            pid = os.fork()
            if pid > 0:  # exit first parent
                sys.exit(0)
        except OSError as err:
            sys.stderr.write('fork #1 failed: {0}\n'.format(err))
            sys.exit(1)

        # decouple from parent environment
        os.chdir('/')
        os.setsid()
        oldmask = os.umask(022)

        # do second fork
        try:
            pid = os.fork()
            if pid > 0:  # exit from second parent
                sys.exit(0)
        except OSError as err:
            sys.stderr.write('fork #2 failed: {0}\n'.format(err))
            sys.exit(1)

        # redirect standard file descriptors
        sys.stdout.flush()
        sys.stderr.flush()
        si = open(os.devnull, 'r')
        so = open(os.devnull, 'a+')
        se = open(os.devnull, 'a+')

        os.dup2(si.fileno(), sys.stdin.fileno())
        os.dup2(so.fileno(), sys.stdout.fileno())
        os.dup2(se.fileno(), sys.stderr.fileno())

        # write pidfile
        # atexit.register(self.delpid)

        pid = str(os.getpid())
        with open(self._pidfile, 'w+') as pf:
            pf.write(pid + "\n")
            for s in [m.get_name() for m in self._agents]:
                pf.write(s + "\n")
        os.umask(oldmask)


    def start(self):
        """Start the server."""
        Pyro.core.initServer()
        # Check for a pidfile to see if the _daemon already runs
        (pid, none) = self.status()
        if pid is not None:
            return
        
        # Get hostname
        try:
            hostname = socket.gethostname()
        except socket.error as e:
            syslog.syslog("%s" % e)
            raise e

        # Check bind address
        try:
            socket.gethostbyname(hostname)
        except socket.error as e:
            syslog.syslog('Unable to bind on local address (no IP address found for hostname: %s)' % hostname)
            raise type(e)('Unable to bind on local address (no IP address found for hostname: %s)' % hostname)

        # Start the _daemon
        self._daemonize()

        try:
            daemon = Pyro.core.Daemon(port=AGENT_PORT)
            for a in self._agents:
                o = Pyro.core.ObjBase()
                o.delegateTo(a)
                daemon.connect(o, a.get_name())

            syslog.syslog('running on %s:%d listening:%s' % (daemon.hostname, daemon.port, [a.get_name() for a in self._agents]))
            daemon.requestLoop()
        except Exception as e:
            syslog.syslog(syslog.LOG_ERR, 'agent failed %s' % e)
        finally:
            syslog.syslog('shutdown')
            for oid in daemon.objectsById:
                daemon.unregister(oid)
            daemon.close()
            daemon.shutdown(True)
            sys.exit()


    def status(self):
        """Get the agent's status.
        Returns: pid and agents of the running instance or None.
        """
        try:
            with open(self._pidfile, 'r') as pf:
                pid = pf.readline().strip()
                agents = []
                line = pf.readline().strip()
                while line != "":
                    agents.append(line)
                    line = pf.readline().strip()
        except IOError:
            return (None, None)

        with open('/dev/null', 'w') as devnull:
            if os.path.exists("/proc/%s" %pid):
                return (pid, agents)
            else:
                return (None, None)


    def stop(self):
        """Stop the server."""
        (pid, agents) = AgentServer().status()
        if pid is not None:
            with open('/dev/null', 'w') as devnull:
                subprocess.check_call("kill %s && sleep 1" % pid, shell=True,
                    stdout=devnull, stderr=devnull)
            if os.path.exists(self._pidfile):
                os.remove(self._pidfile)

