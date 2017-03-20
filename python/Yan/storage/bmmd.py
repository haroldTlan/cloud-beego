#!/usr/bin/env python
import adm
from adm import dmcreate, dmremove
import log
from util import execute
import os
import sys

# backup monfs metadata
def main():
    try:
        adm.MonFS.backup_md()
    except Exception as e:
        print e.message
        sys.exit(-1)

if __name__ == '__main__':
    main()
