#!/usr/bin/env python
from env import config
import os
import log
import glob
import db
import api
from util import execute
from caused import caused
import error
from unit import KB
from env import config
import os
import re
import util

def main():
    if config.env <> 'VMware':
        cmd = 'bash /etc/rc.key'
        os.system(cmd)
        cmd = 'rm -rf /dev/zstor'
        os.system(cmd)
        cmd = 'rm -rf /home/zonion/.llog'
        os.system(cmd)
        cmd = 'gpg --ignore-time-conflict --homedir /home/gpg  --verify /home/zonion/license/key.sig > /tmp/key 2>&1'
        _, o = execute(cmd, False, logging=False)
        cmd = 'cat  /tmp/key'
        _, o = execute(cmd, False)
        m = re.search('Good', o)
        if not m:
            cmd = 'touch /home/zonion/.llog'
            _, o = execute(cmd, False)
            print 'nokey'
        cmd = 'cat  /home/zonion/license/key'
        _, o = execute(cmd, False, logging=False)
        sn = util.get_sn()
        if sn != o.strip():
            cmd = 'touch /home/zonion/.llog'
            _, o = execute(cmd, False)
            print 'nokey'

        cmd = 'rm -rf /tmp/key'
        os.system(cmd)

    cmd = 'rm /home/zonion/bitmap.disk/*.bitmap -rf'
    execute(cmd, False)


    try:
        db.create_tables()
    except Exception as e:
        log.error(caused(e).detail)
        raise error.InternalError()

    if os.path.exists(config.boot.startup_file):
        log.journal_warning('System may not be poweroffed normally!')

    if 'monfs' not in config.feature:
        cmd = 'bash /home/zonion/command/ipsan.sh'
        os.system(cmd)

    is_die = os.path.exists('/home/zonion/.llog')
    if is_die:
        log.info('NO license.......')
        return

    cxt = api.APIContext()
    cxt.scan_all()

    log.info('System startup.')

if __name__ == '__main__':
    main()
