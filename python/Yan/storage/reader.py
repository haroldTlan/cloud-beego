import nsq
from env import config
import json
from store import *
from load import *
import logging
import network
import socket


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
        manage(json.loads(message.body))
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


r = nsq.Reader(message_handler=handler,
        nsqd_tcp_addresses=[aim],
        topic='storages', channel=get_ip_address(), lookupd_poll_interval=15)
nsq.run()
