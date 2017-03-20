import time
import sys
import signal

class Timer(object):
    def __init__(self, verbose=False):
        self.verbose = verbose

    def __enter__(self):
        self.start = time.time()
        return self

    @property
    def msecs(self):
        return self.secs * 1000

    def __exit__(self, *args):
        self.end = time.time()
        self.secs = self.end - self.start
        if self.verbose:
            print 'elapsed time: %f ms' % self.msecs

 
class TimeoutException(Exception): 
    pass 
 
def timeout_handler(signum, frame):
    raise TimeoutException()

class Timeout(object):
    def __init__(self, secs):
        self._timeout_secs = secs
        self.secs = 0
        self.exceeded = False

    def __enter__(self):
        self.start = time.time()
        if self._timeout_secs:
            self._old_handler = signal.signal(signal.SIGALRM, timeout_handler) 
            signal.alarm(self._timeout_secs)
        return self

    @property
    def msecs(self):
        return self.secs * 1000

    def __exit__(self, type, value, traceback):
        self.end = time.time()
        self.secs = self.end - self.start
        if self._timeout_secs:
            signal.alarm(0)
            signal.signal(signal.SIGALRM, self._old_handler)
            self.exceeded = isinstance(value, TimeoutException)
        return self.exceeded
