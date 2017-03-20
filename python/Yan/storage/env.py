from os import path
import os
import re
import yaml
from dotdict import DictDotLookup
from unit import Unit
import md5

proj_path = path.dirname(path.abspath(__file__))
def complete_path(config, prefix, path):
    for k in config:
        v = config[k]
        if isinstance(v, str) and prefix in v:
            config[k] = v.replace(prefix, path+'/')
        elif isinstance(v, dict):
            complete_path(v, prefix, path)

def complete_size(config):
    for k in config:
        v = config[k]
        if k.endswith('size'):
            try:
                config[k] = Unit(v)
            except:
                pass
        elif isinstance(v, dict):
            complete_size(v)

def detect_env(config):
    if 'env' in config and config['env']:
        return
    try:
        dmi = os.popen('dmidecode').read()
        m = re.search('System Information.+?Manufacturer: (\w+)', dmi, re.S)
        config['env'] = m.group(1)
    except:
        config['env'] = 'UNKOWN'

raw_config = None
with open(path.join(proj_path, 'speedio.conf'), 'r') as conf:
    raw_config = yaml.load(conf)
    etc = raw_config['etc']
    complete_path(raw_config, etc['path_prefix'], etc['path'])
    complete_size(raw_config)

    if not path.exists(etc['path']):
        os.mkdir(etc['path'])

    detect_env(raw_config)
    config = DictDotLookup(raw_config)

