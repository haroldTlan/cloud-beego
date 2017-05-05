import error
from env import config
import sys
import json
import re

if 'gevent' in sys.modules:
    import zmq.green as zmq
else:
    import zmq

POLLIN  = zmq.POLLIN
POLLOUT = zmq.POLLOUT

REQ  = zmq.REQ
PUB  = zmq.PUB
PULL = zmq.PULL
PUSH = zmq.PUSH

ctx =  zmq.Context()

class JSON(object):
    def encode(self, obj):
        return json.dumps(obj)

    def decode(self, msg):
        return json.loads(msg)

class RAW(object):
    def encode(self, obj):
        return obj

    def decode(self, msg):
        return msg

def get_fmt_obj(fmt):
    return getattr(sys.modules[__name__], fmt.upper())()

def get_protocol(url, repl='*'):
    return url if re.search('\w+://', url) else\
            config.protocols[url].replace('*', repl)

class Push(object):
    def __init__(self, channel, fmt='json'):
        self._channel = channel
        self._fmt = fmt

        self._protocol = get_protocol(channel, 'localhost')
        self._fo = get_fmt_obj(fmt)

        self._socket = ctx.socket(zmq.PUSH)
        self._socket.connect(self._protocol)

    def send(self, msg):
        self._socket.send(self._fo.encode(msg))

    def close(self):
        self._socket.close()

class Request(object):
    def __init__(self, channel, fmt='json'):
        self._channel = channel
        self._fmt = fmt

        self._protocol = get_protocol(channel, 'localhost')
        self._fo = get_fmt_obj(fmt)

        self._socket = ctx.socket(zmq.REQ)  
        self._socket.setsockopt(zmq.LINGER, 0)  
        self._socket.connect(self._protocol)

        self._poller = zmq.Poller()  
        self._poller.register(self._socket, zmq.POLLIN)  


    def request(self, msg, timeout=-1):
        self._socket.send(self._fo.encode(msg))
        if self._poller.poll(timeout):
            rsp = self._socket.recv()  
            return self._fo.decode(rsp)
        else:  
            raise error.Timeout()

    def close(self):
        self._socket.close()

class Subscriber(object):
    def __init__(self, channel, fmt='json', filter=''):
        self._channel = channel
        self._fmt = fmt

        self._protocol = get_protocol(channel, 'localhost')
        print self._protocol
        self._fo = get_fmt_obj(fmt)

        self._socket = ctx.socket(zmq.SUB)
        self._socket.setsockopt(zmq.SUBSCRIBE, filter)
        self._socket.connect(self._protocol)

        self._poller = zmq.Poller()  
        self._poller.register(self._socket, zmq.POLLIN)  

    def recv(self, timeout=-1):
        if self._poller.poll(timeout):
            topics = self._socket.recv()  
            return self._fo.decode(topics)
        else:  
            raise error.Timeout()

    def close(self):
        self._socket.close()

def request(channel, msg, timeout=-1, fmt='json'):
    socket = ctx.socket(zmq.REQ)  
    socket.setsockopt(zmq.LINGER, 0)  
    
    protocol = get_protocol(channel)
    fo = get_fmt_obj(fmt)

    socket.connect(protocol.replace('*', 'localhost'))
    poller = zmq.Poller()
    poller.register(socket, zmq.POLLIN)  

    socket.send(fo.encode(msg))

    if poller.poll(timeout):
        rsp = socket.recv()  
    else:  
        socket.close()  
        raise error.Timeout()
  
    socket.close()
    return fo.decode(rsp)

def socket(sock_type, channel):
    socket = ctx.socket(sock_type)
    socket.bind(get_protocol(channel))
    return socket

def rsp_socket(channel):
    socket = ctx.socket(zmq.REP)
    socket.bind(get_protocol(channel))
    return socket

def pub_socket(channel):
    socket = ctx.socket(zmq.PUB)
    socket.bind(get_protocol(channel))
    return socket

class Poller(object):
    def __init__(self):
        self._poller = zmq.Poller()
        self._handlers = {}

    def register(self, handler):
        fd   = handler.fd
        mask = handler.mask
        self._poller.register(fd, handler.mask)
        self._handlers[fd] = (handler, mask)

    def unregister(self, handler):
        self._poller.unregister(handler)
        del self._handlers[handler.fd]
        handler.unregister()

    def poll(self, timeout=-1):
        fds = self._poller.poll(timeout)
        if not fds: return False
        for fd, e in fds:
            hdl, mask = self._handlers[fd]
            try:
                if e & POLLIN:
                    hdl.handle_in(e)
            except:
                pass
            try:
                if e & POLLOUT:
                    hdl.handle_out(e)
            except:
                pass
            if hdl.mask <> mask:
                self.unregister(hdl)
                if hdl.mask <> 0:
                    self.register(hdl)

class IOHandler(object):
    @property
    def fd(self):
        raise NotImplemented
    @property
    def mask(self):
        return POLLIN

    def handle_in(self, e):
        raise NotImplemented

    def handle_out(self, e):
        raise NotImplemented

    def unregister(self):
        pass
