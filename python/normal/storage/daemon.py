#!/usr/bin/env python
import sys, os, time, atexit
from signal import SIGTERM
import signal
import re
from os.path import split, splitext
import traceback as tb

debuging = False

class Daemon:
    def __init__(self, pidfile, stdin='/dev/null', stdout='/dev/null', stderr='/dev/null'):
        self.stdin = stdin or sys.stdin
        self.stdout = stdout or sys.stdout
        self.stderr = stderr or sys.stderr
        self.pidfile = pidfile

    def init(self):
        pass
       
    def daemonize(self):
        try:
            pid = os.fork()
            if pid > 0:
                sys.exit(0)
        except OSError, e:
            sys.stderr.write("fork #1 failed: %d (%s)\n" % (e.errno, e.strerror))
            sys.exit(1)
       
        os.setsid()
        os.umask(0)
       
        try:
            pid = os.fork()
            if pid > 0:
                sys.exit(0)
        except OSError, e:
            sys.stderr.write("fork #2 failed: %d (%s)\n" % (e.errno, e.strerror))
            sys.exit(1)
       
        sys.stdout.flush()
        sys.stderr.flush()
        if isinstance(self.stdin, str):
            si = file(self.stdin, 'r')
            os.dup2(si.fileno(), sys.stdin.fileno())
        if isinstance(self.stdout, str):
            so = file(self.stdout, 'a+')
            os.dup2(so.fileno(), sys.stdout.fileno())
        if isinstance(self.stderr, str):
            se = file(self.stderr, 'a+', 0)
            os.dup2(se.fileno(), sys.stderr.fileno())
       
        atexit.register(self.delpid)
        pid = str(os.getpid())
        file(self.pidfile,'w+').write("%s\n" % pid)
       
    def delpid(self):
        os.remove(self.pidfile)
 
    def start(self):
        try:
            pf = file(self.pidfile,'r')
            pid = int(pf.read().strip())
            pf.close()
        except IOError:
            pid = None
       
        if pid:
            o = os.popen('ps aux|grep %s' % pid).read()
            script = splitext(split(sys.argv[0])[1])[0]
            if re.search('%s.+?python.+?%s.+?\n' % (pid, script), o):
                message = "pidfile %s already exist. Daemon already running?\n"
                sys.stderr.write(message % self.pidfile)
                sys.exit(1)
            else:
                os.remove(self.pidfile)
           
        self.daemonize()
        self.run()
 
    def stop(self):
        try:
            pf = file(self.pidfile,'r')
            pid = int(pf.read().strip())
            pf.close()
        except IOError:
            pid = None
       
        if not pid:
            message = "pidfile %s does not exist. Daemon not running?\n"
            sys.stderr.write(message % self.pidfile)
            return
 
        try:
            while 1:
                os.kill(pid, SIGTERM)
                time.sleep(0.1)
        except OSError, err:
            err = str(err)
            if err.find("No such process") > 0:
                if os.path.exists(self.pidfile):
                    os.remove(self.pidfile)
            else:
                print str(err)
                sys.exit(1)
 
    def restart(self):
        self.stop()
        self.start()
 
    def run(self):
        self.init()
        while True:
            try:
                self._run()
            except:
                global debuging
                if debuging:
                    debuging = False
                else:
                    tb.print_exc() 
                    break


    def _run(self):
        pass

def handle_pdb(sig, frame):
    import pdb
    print ''.join(tb.format_stack(frame))
    global debuging
    debuging = True
    pdb.Pdb().set_trace(frame)

def main(pidfile, daemon_class):
    if len(sys.argv) >= 2:
        if sys.argv[1] == 'fg':
            pid = str(os.getpid())
            with open(pidfile, 'w+') as fout:
                fout.write("%s\n" % pid)

            signal.signal(signal.SIGUSR1, handle_pdb)

            daemon = daemon_class(pidfile, stdin='', stdout='', stderr='')
            daemon.run()
            os.remove(pidfile)
            return

        daemon = daemon_class(pidfile)
        if sys.argv[1] == 'start':
            daemon.start()
        elif sys.argv[1] == 'stop':
            daemon.stop()
        elif sys.argv[1] == 'restart':
            daemon.restart()
        else:
            print "Unknown command"
            sys.exit(2)
        sys.exit(0)
    else:
        print "usage: %s start|stop|restart|fg" % sys.argv[0]
        sys.exit(2)
