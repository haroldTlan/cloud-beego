import ruamel.yaml
import ruamel.yaml.util
import re
import os
import commands
import argparse

parser = argparse.ArgumentParser(description="rozofs_1.0")
parser.add_argument("--ip", help="default: --ip=192.168.2.149", default='192.168.2.149')


def pre(ip):
    try:
        conf = open("/home/monitor/cloud/speedio.conf", "r")
        result, indent, block_seq_indent = ruamel.yaml.util.load_yaml_guess_indent(
            conf, preserve_quotes=True)
        conf.close()

        result['rozofs']['ip']= ip
        print result['rozofs']
        with open('/home/monitor/cloud/speedio.conf', 'w') as conf:
            ruamel.yaml.round_trip_dump(result, conf, indent=indent,block_seq_indent=block_seq_indent)
    finally:
        conf.close()


def getPid(process):
    cmd = "ps aux | grep '%s' " % process
    info = commands.getoutput(cmd)
    print info
    infos = [i.split()[1] for i in info.split("\n")]
    return infos

def killPid():
    os.system("python /home/monitor/cloud/nsq_eventd.py restart")
    menu = ["reader"]
    for pid in menu:
        pids = getPid(pid)
        print pid
        for i in pids:
            try:
                os.system("kill %s"%i)
            except:
                continue
   # os.system("python /home/monitor/cloud/reader.py &")

if __name__ == '__main__':
    args = parser.parse_args()
    pre(args.ip)
    killPid()
