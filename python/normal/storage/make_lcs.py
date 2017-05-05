#!/usr/bin/env python
import rest
import base64
import sys
import util
from env import config
import os
import hashlib
from util import execute
import re

def main():
    if not os.path.exists(config.license.sig_path):
        sn = util.get_sn()
        with open(config.license.key_path, 'w') as f:
            f.write(sn)
        r = rest.rest('192.168.2.218', port=8080)
        o = r.license.create(sn)
        with open(config.license.sig_path, 'w') as f:
            f.write(base64.b64decode(o['sig']))
if __name__ == '__main__':
    main()
