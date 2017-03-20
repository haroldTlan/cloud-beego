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

IFACE = [info.ipaddr for info in network.ifaces().values() if info.link]
