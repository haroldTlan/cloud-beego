# coding:utf-8
from zoofs.core.platform import Platform, Role
import argparse
import re
import json

__author__ = 'harold'

parser = argparse.ArgumentParser(description="use rozofs interface to get configurations")
parser.add_argument("--ip", help="default(must be export's ip): --ip=192.168.2.136", default=None)



def AllConfig(ip=None):
    host_l = []
    storaged = []
    exportd = {}
    down, d = judge(ip)
    if down:
        return 0, d

    try:
        platform = Platform([ip])
    except Exception,ex:
        return 0, ex
    configs = platform.get_configurations(None,7)

    for h, c in configs.items():
        host = {}
        if c is None:
            host.update({ip:str(h),config:None})
            continue

        for role, config in c.items():
            #check exception
            if isinstance(config, Exception):
                #Get error msg
                host.update({'ip':str(h),'status':False,'error':str(config)})
                continue

            if (role & Role.EXPORTD == Role.EXPORTD):
                volume = []
                export = []
                #volume
                for v in config.volumes.values():
                    for cluster in v.clusters.values():
                        s_l = []
                        for s, hhh in cluster.storages.items():
                            s_l.append({s: hhh})
                        volume.append({'vid': v.vid, 'cid': cluster.cid, 'sid': s_l})
                #export
                if len(config.exports) != 0:
                    for e in config.exports.values():
                        export.append({'root': e.root, 'vid': e.vid})

                exportd.update({'volume': volume, 'export': export,'ip':str(h)})

            if (role & Role.STORAGED == Role.STORAGED):
                storage = {'ip': str(h), 'storage': []}
                keylist = config.storages.keys()
                keylist.sort()
                #storage
                for key in keylist:
                    st = config.storages[key]
                    storage['storage'].append({'cid': st.cid, 'sid': st.sid, 'root': st.root})
                storaged.append(storage)

    host.update({'storaged': storaged, 'exportd': exportd})
    return 1, host

def judge(ip):
    ip_re = re.compile(r"^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$")
    if  re.match(ip_re,ip):
        return 0, ""
    else:
        return 1, "Invaild Ip"



def JsonRes(ip):
    status,detail = AllConfig(ip)
    res = {}
    res["status"] = bool(status)
    res["detail"] = detail

    return json.dumps(res)

if __name__ == "__main__":
    args = parser.parse_args()
    
    print JsonRes(args.ip)

