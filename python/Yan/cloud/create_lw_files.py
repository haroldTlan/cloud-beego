#-*- coding: UTF-8 -*-
import sys
sys.path.append('/home/zonion/speedio')
from util import execute
import os
import subprocess as sp
import time
import re
import mq
import random

def main():
    pub = mq.pub_socket('notification')
    pub.send_json({})
    time.sleep(0.5)
    progid = random.randint(0, pow(2,16))
    pub.send_json({'status' : 'inprogress',
                   'ratio'  : 0,
                   'event'  : 'notification',
                   'message': '正在进行预分配文件',
                   'type'   : 'progress',
                   'id'     : progid})

    p = sp.Popen('/home/zonion/command/prealloc_lw_files.sh', shell=True, stdin=sp.PIPE)
    p.stdin.write('\n')
    while sp.Popen.poll(p) is None:
        time.sleep(4)
        _,o = execute('df /nvr', False)
        m = re.search('(\d+)%', o)
        if m:
            ratio = float(m.group(1))/100
            pub.send_json({'status' : 'inprogress',
                           'ratio'  : ratio,
                           'event'  : 'notification',
                           'message': '正在进行预分配文件',
                           'type'   : 'progress',
                           'id'     : progid})

    time.sleep(4)
    pub.send_json({'status' : 'completed',
                   'ratio'  : 1,
                   'event'  : 'notification',
                   'message': '完成预分配文件',
                   'type'   : 'progress',
                   'id'     : progid})


if __name__ == '__main__':
    main()
