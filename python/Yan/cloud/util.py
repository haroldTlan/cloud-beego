import re
import uuid as _uuid
import md5
from caused import *
from env import config
import os
import commands
import log
import error
import subprocess as sp
from perf import Timeout
import signal
import hashlib

def eval_bool(b):
    b = str(b) if (b, unicode) else b
    if isinstance(b, bool): return b
    elif isinstance(b, str):
        if b.lower() in ['yes', 'y', 'true']: return True
        if b.lower() in ['no', 'n', 'false']: return False
    else:
        raise ValueError

def execute(cmd, raise_exc=True, timeout=0, logging=True):
    if logging:
        log.info(str(cmd[:]).encode('string_escape'))
    p = sp.Popen(cmd, shell=True, stdout=sp.PIPE, stderr=sp.PIPE, close_fds=True, preexec_fn=os.setpgrp)
    with Timeout(timeout) as t:
        s = p.wait()

    if t.exceeded:
        os.killpg(p.pid, signal.SIGTERM)
        p.wait()
        raise error.Timeout

    o = p.stdout.read() if s == 0 else p.stderr.read()
    if logging and o.strip() <> '':
        log.debug(o)
    if raise_exc and s <> 0:
        raise error.ShellError(cmd, s, o)
    return s,o

class uuid:
    LVM_FORMAT = '6-4-4-4-4-4-6'
    MDADM_FORMAT = '8:8:8:8'
    SPEEDIO_FORMAT = '8-4-4-4-12'
    VALID_CHAR = '[0-9|a-f|A-F]'
    __host_uuid = ''

    @classmethod
    def validate(cls, uuid, fmt=SPEEDIO_FORMAT):
        uuid = str(uuid)
        sep = re.search('\d+(.)', fmt).group(1)
        pattern = sep.join(['%s{%s}' % (cls.VALID_CHAR, nr) for nr in fmt.split(sep)])
        m = re.search(pattern, uuid)
        return m and True or False


    @classmethod
    def format(cls, fmt, uuid):
        sep = re.search('\d+(.)', fmt).group(1)
        segment_nr = [int(nr) for nr in fmt.split(sep)]

        m = re.search('\w+(.?)', uuid)
        sep1 = m and m.group(1) or ''
        uuid = uuid.replace(sep1, '')
        segment = []
        for nr in segment_nr:
            seg, uuid = uuid[0:nr], uuid[nr:]
            segment.append(seg)
        return sep.join(segment)

    @classmethod
    def normalize(cls, uuid):
        return cls.format(cls.SPEEDIO_FORMAT, uuid)

    @classmethod
    def host_uuid(cls):
        if not cls.__host_uuid:
            host_path = config['uuid']['host_path']
            if os.path.exists(host_path):
                with open(host_path, 'r') as f:
                    cls.__host_uuid = f.read()
                    if not cls.validate(cls.__host_uuid):
                        os.remove(host_path)
                        return cls.host_uuid()
            else:
                with open(host_path, 'w') as f:
                    cls.__host_uuid = cls.normalize(md5.new(str(_uuid.getnode())).hexdigest())
                    f.write(cls.__host_uuid)
        return cls.__host_uuid

    @classmethod
    def uuid4(cls):
        return str(_uuid.uuid4())

def check_system_raid1():
    _,o = execute('df |grep md0', False, logging=False)
    for line in o.rstrip().split('\n'):
        m=re.search(r'/dev/md0', line)
        if m is not None:
            return True
    return False

def get_sn():
    if check_system_raid1():
        _, o = execute('ifconfig eth0 |grep HW', logging=False)
        m = re.search('HWaddr\s+((\w+):(\w+):(\w+):(\w+):(\w+):(\w+))', o)
        sn = m.group(1)
        m2 = hashlib.md5()   
        m2.update(sn)   
        sn = m2.hexdigest()
    else:
        _, o = execute('hdparm -I /dev/sda |grep "Serial Num"', logging=False)

        m = re.search('Serial Number:\s+(\w+)', o)
        sn = m.group(1)
        m2 = hashlib.md5()
        m2.update(sn)
        sn = m2.hexdigest()

    return sn

