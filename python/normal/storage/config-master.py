# coding:utf-8
import re
import subprocess
import argparse

__author__ = 'bary'

parser = argparse.ArgumentParser()
parser.add_argument("--ip", default='127.0.0.1')


def pasetoconf(ip):
    first = "[program:weed_meta]\n"
    second = 'command=weed master -ip={0} -mdir=/meta\n'.format(ip)
    third = 'directory=/usr/local/bin\n'
    fouth = "user=root\n"
    host = "node"+ip.split('.')[-1]
    with open("/etc/supervisor/conf.d/weed_meta.conf", "w") as f:
        f.writelines(first)
        f.writelines(second)
        f.writelines(third)
        f.writelines(fouth)

    with open("/etc/hostname", "w") as f:
        f.writelines(host)

if __name__ == "__main__":
    args = parser.parse_args()
    pasetoconf(args.ip)



































































