# -*- coding: utf-8 -*-

import sys
sys.path.append('/root/code')
from o import *

import json
import os

def getInfo(items):
    info = []
    if len(items.host_ok)>0:
        for i in items.host_ok:
            a = i['result']._result['stdout']
            try:
                infos = infoTrans(i['task'], str(i['result']._result['stdout']))
                info.append(dict(type=str(i['task']), ip=str(i['ip']), result=infos, status="success"))
            except:
                pass

    if len(items.host_unreachable) >0:
        for i in items.host_unreachable:
            info.append(dict(type=str(i['task']), ip=str(i['ip']), status="unreachable"))

    if len(items.host_failed) >0:
        for i in items.host_failed:
            info.append(dict(type=str(i['task']), ip=str(i['ip']), status="failed"))
    infos = json.dumps(info)
    os.system("echo '%s' > static/static"%infos)

def infoTrans(dev, infos):
        return json.loads(infos)


if __name__ == '__main__':
    items = run_playbook("/root/code/yml/info/device.yml")
    getInfo(items)
