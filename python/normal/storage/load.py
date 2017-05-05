import re
import os
import ruamel.yaml
import ruamel.yaml.util


STORAGE = "/zbx/etc/zoofs/storage.conf"
SPEEDIO = "/home/zonion/speedio/speedio.conf"

def loading():
    try:
        storages = open(STORAGE)
        speedio = open(SPEEDIO,"r")

        pattern = r'root = "(.*?)"'
        root = re.search(pattern, storages.read())

        result, indent, block_seq_indent = ruamel.yaml.util.load_yaml_guess_indent(
            speedio, preserve_quotes=True)
        speedio.close()

        result['nas']['mount_dirs'][0]= ruamel.yaml.scalarstring.SingleQuotedScalarString(root.group(1) + '/0')
        with open(SPEEDIO, 'w') as speedio_two:
            ruamel.yaml.round_trip_dump(result, speedio_two, indent=indent,block_seq_indent=block_seq_indent)
        speedio_two.close()

    except Exception as e:
        storages.close()
        speedio.close()
        speedio_two.close()

    finally:
        os.system("python /home/zonion/speedio/admd.pyc restart")

if __name__ == '__main__':
    loading()
