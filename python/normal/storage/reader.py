import nsq
from env import config
import json
from store import *
from load import *
import logging
import network
import socket
import commands
import os

logging.basicConfig()
logger = logging.getLogger('nsq')
fh = logging.FileHandler('/var/log/nsq.log')
logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
logger.addHandler(fh)


iface = [info.ipaddr for info in network.ifaces().values() if info.link]
aim = config.zoofs.ip + ':' + str(config.zoofs.consumer_port)
if len(iface)<0:
    logger.error("no useful ip")
    exit()
print aim

def handler(message):
    try:
        #manage(json.loads(message.body))
        cmd(json.loads(message.body))
        return True
    except Exception,ex:
        print ex
 	return False

def manage(events):
    if events['ip'] in iface:
        logger.info(events)
        if events['event'] == 'storage.init':
            result = delete_all()
        elif events['event'] == 'storage.build':
            loading()
            result = quick_create()
        else:
            result = 'unknown event'
#        pub_manage(events['ip'], result)
        logger.info(result)

def get_ip_address():
    INTERFACE = ['eth0','br0','eth1']
    ifaces = network.ifaces().values()
    for i in INTERFACE:
        for j in ifaces:
            if j.name == i and j.link:
                return j.ipaddr
    return 'unknow'

def cmd(events):
    if events['ip'] in iface:
	logger.info(events)
        if events['event'] == 'cmd.client.add':
            result = commands.getoutput("zoofsmount -H %s  -E /srv/zoofs/exports/export_1/ /mnt/zoofs/"%events['status'])
	    if result == '':
		os.system("echo 'zoofsmount -H %s  -E /srv/zoofs/exports/export_1/ /mnt/zoofs/' >> /etc/rc.step3"%events['status'])
		os.system("service samba restart")
		os.system("chmod 777 -R /mnt/zoofs")
		pub('cmd.client.add',True,"success")
	    else:
		pub('cmd.client.add',False, ','.join(result.split('\n')))

        elif events['event'] == 'cmd.client.remove':
	    result = commands.getoutput("umount zoofs")
	    os.system("sed -i '/zoofsmount/d' /etc/rc.step3")
	    if result == '':
		pub('cmd.client.remove',True,"success")
	    else:
		pub('cmd.client.add',False, ','.join(result.split('\n')))

        elif events['event'] == 'cmd.storage.build':
	    level = events['status'].split("*")[0]
	    loc = events['status'].split("*")[1]

	    status, detail = addDev(level, loc, mountpoint)
	    pub('cmd.storage.build', status, detail)

        elif events['event'] == 'cmd.storage.remove':
	    delete_all()
	    pub('cmd.storage.remove', False, "success")


def pub(event, status,detail):
    back = {}
    back['event']= event
    back['status']=status
    back['detail']=detail.replace("'","")

    os.system("echo \'%s\' >> /home/monitor/rpc.log"%json.dumps(back).replace("'","\""))

r = nsq.Reader(message_handler=handler,
        nsqd_tcp_addresses=[aim],
        topic='storages', channel=get_ip_address(), lookupd_poll_interval=15)
nsq.run()
