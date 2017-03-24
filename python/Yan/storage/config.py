# coding:utf-8
import re
import subprocess
import argparse

__author__ = 'bary'

parser = argparse.ArgumentParser()
parser.add_argument("-command", default="weed volume")
parser.add_argument("-index", default='"boltdb"')
parser.add_argument("--mserver", default='192.168.2.130:9333')
parser.add_argument("--port", default="9080")
parser.add_argument("--ip", default='192.168.2.131')


def run_command(cmd, shell=False, stdout=subprocess.PIPE,
                stderr=subprocess.PIPE, stdin=subprocess.PIPE, throw=True,
                log=False, input=None, needlog=True):
    cmd = map(str, cmd)
    p = subprocess.Popen(cmd, shell=shell, stdout=stdout, stderr=stderr,
                         stdin=stdin)
    out, err = p.communicate(input=input)
    out = out.split('\n')
    err = err.split('\n')
    rc = p.returncode
    return out, err, rc


def getmax():
    # cat /etc/supervisor/conf.d/weed_data.conf
    out, err, rc = run_command(["df"])
    dirr = []
    maxx = []
    for i in out[3:-1]:
        temp = [a for a in i.split(" ") if a]
        if re.search('/dev/mapper/VG--*', i):
            if re.search("/nvr/d*", i):
                dirr.append(temp[-1])
                maxx.append(str(int(int(temp[1]) * 0.99 / 30 / 1024 / 1024)))
    return ','.join(dirr), ','.join(maxx)


def pasetoconf(mserver, ip):
    dirr, maxx = getmax()
    first = "[program:weed_data]\n"
    second = 'command=weed  volume -index="boltdb" -images.fix.orientation=false  -dir={0}  -max={1} -mserver="{2}" -port=9080 -ip="{3}"\n'.format(
        dirr, maxx, mserver, ip)
    third = 'directory=/usr/local/bin\n'
    fouth = "user=root\n"

    five='''autostart = true
autorestart = true
startretries = 100'''
    with open("/etc/supervisor/conf.d/weed_data.conf", "w") as f:
        f.writelines(first)
        f.writelines(second)
        f.writelines(third)
        f.writelines(fouth)
        f.writelines(five) 


if __name__ == "__main__":
    args = parser.parse_args()
    pasetoconf(args.mserver, args.ip)
