import gnsq
import logging
import network
from store import *
from publish import *
from load import *
from env import config
import json

logging.basicConfig()
logger = logging.getLogger('nsq')
fh = logging.FileHandler('/var/log/nsq.log')
logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
logger.addHandler(fh)

iface = [info.ipaddr for info in network.ifaces().values() if info.link]
print iface[0]
print config.rozofs.ip
reader = gnsq.Reader('storage', iface[0], config.rozofs.ip + ':4150')

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


def pub_manage(ip, result):
    o = {}
    o['ip'] = ip
    if result == 'build success':
        o['event'] = 'rozofs.created'
    elif result == 'clear success':
        o['event'] = 'rozofs.removed'
    pub_nsq(json.dumps(o))


@reader.on_message.connect
def handler(reader, message):
    try:
        manage(json.loads(message.body))
        print 'got message:', message.body
    except Exception,ex:
        logger.info(ex)


reader.start()

