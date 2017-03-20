import gnsq
from env import config

conn = gnsq.Nsqd(address=config.rozofs.ip, http_port=4151)
def pub_nsq(o):
    conn.publish('CloudEvent', o)

def pub_nsq_info(o):
    conn.publish('CloudInfo', o)

