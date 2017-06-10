from env import config
import json
from load import *
import logging
import network
import socket
import commands
import os

from daemon import Daemon, main
import time

class NsqCD(Daemon):
    def _run(self):
        time.sleep(config.consumerd.interval)
        print 8888





if __name__ == "__main__":
    main(config.consumerd.pidfile, NsqCD)







