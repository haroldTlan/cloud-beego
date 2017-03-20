#!/usr/bin/env python
from os.path import split, join
import sys
sys.path.append(join(split(__file__)[0], '..'))
import db
import os

def main():
    db.drop_tables()
    db.create_tables()
    os.system('mysql -uspeedio -ppasswd < init_session.sql')

if __name__ == '__main__':
    main()
