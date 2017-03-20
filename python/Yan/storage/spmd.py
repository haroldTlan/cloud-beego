#!/usr/bin/env python
from daemon import Daemon, main
from env import config
import time
from util import execute
import re
import os
import log
import os
import signal

class SPMD(Daemon):
    def _is_alive(self, proc):
        if not os.path.exists(proc['pidfile']):
            return False

        with open(proc['pidfile'], 'r') as fin:
            pid = int(fin.read().strip())

        _, o = execute('ps aux|grep %s' % pid, False, logging=False)
        return True if re.search('%s.+?python.+?%s.+?\n' % (pid, proc['daemon']), o) else False

    def _start_daemon(self, proc):
        print 'start %s' % proc['daemon']
        try:
            wd = os.path.split(proc['file'])[0]
            os.chdir(wd)
            _,o = execute(proc['run'], logging=False)
        except:
            msg = 'start %s failed, run command: %s' % (proc['daemon'], proc['run'])
            log.error(msg)
            print msg

    def init(self):
        self.procs = []
        for m in config.spmd.monitor:
            proc = {'pidfile':config[m].pidfile, 'file':config[m].file, 'daemon':m}
            proc['run']   = config[m].run if 'run' in config[m] else 'python %s start' % proc['file']
            proc['mtime'] = os.stat(proc['file']).st_mtime
            self.procs.append(proc)

    def _detect_file_change(self, proc):
        mtime = os.stat(proc['file']).st_mtime
        if proc['mtime'] <> mtime:
            print 'file change: %s' % proc['daemon']
            proc['mtime'] = mtime
            with open(proc['pidfile'], 'r') as fin:
                pid = int(fin.read().strip())
                os.kill(pid, signal.SIGTERM)

    def _run(self):
        time.sleep(config.spmd.detect_interval)
        for proc in self.procs:
            if config.spmd.detect_file_change:
                self._detect_file_change(proc)
            if not self._is_alive(proc):
                self._start_daemon(proc)
 
if __name__ == "__main__":
    main(config.spmd.pidfile, SPMD)
