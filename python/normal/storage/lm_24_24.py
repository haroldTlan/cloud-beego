import os
from os import path
import re
from env import config 
from util import execute

if config.env <> 'VMware':
    class LocationMapping(object):
        key_8_loc = { 
            '6-4':'1', 
            '6-0':'5', 
            '7-4':'9', 
            '7-0':'13', 
            '6-5':'2', 
            '6-1':'6', 
            '7-5':'10', 
            '7-1':'14', 
            '6-6':'3', 
            '6-2':'7', 
            '7-6':'11', 
            '7-2':'15', 
            '6-7':'4', 
            '6-3':'8', 
            '7-7':'12', 
            '7-3':'16' 
        } 
        key_16_loc = { 
            '27':'1', 
            '22':'5', 
            '17':'9', 
            '12':'13', 
            '0' :'2', 
            '2' :'6', 
            '7' :'10', 
            '11':'14', 
            '1' :'3', 
            '3' :'7', 
            '6' :'11', 
            '10':'15', 
            '4' :'4', 
            '5' :'8', 
            '8' :'12', 
            '9' :'16' 
        } 
        key_16_loc_ori_dh = { 
            '6-4':'4', 
            '6-0':'8', 
            '7-4':'12', 
            '7-0':'16', 
            '6-5':'3', 
            '6-1':'7', 
            '7-5':'11', 
            '7-1':'15', 
            '6-6':'2', 
            '6-2':'6', 
            '7-6':'10', 
            '7-2':'14', 
            '6-7':'1', 
            '6-3':'5', 
            '7-7':'9', 
            '7-3':'13' 
        } 
        key_16_loc_ori = { 
            '6-4':'1', 
            '6-0':'5', 
            '7-4':'9', 
            '7-0':'13', 
            '6-5':'2', 
            '6-1':'6', 
            '7-5':'10', 
            '7-1':'14', 
            '6-6':'3', 
            '6-2':'7', 
            '7-6':'11', 
            '7-2':'15', 
            '6-7':'4', 
            '6-3':'8', 
            '7-7':'12', 
            '7-3':'16' 
        } 
        key_24_loc = { 
            '10':'1', 
            '11':'2', 
            '13':'3', 
            '12':'4', 
            '9' :'5', 
            '16' :'6', 
            '15' :'7', 
            '14':'8', 
            '8' :'9', 
            '19' :'10', 
            '18' :'11', 
            '17':'12', 
            '3' :'13', 
            '22' :'14', 
            '21' :'15', 
            '20' :'16',
            '2' :'17', 
            '25':'18', 
            '24' :'19', 
            '23' :'20', 
            '1' :'21', 
            '0':'22', 
            '27' :'23', 
            '26' :'24'
        } 
     
        def _check_expander(self):
            chanel_list = []
            cmd = 'ls /sys/class/sas_expander'
            s, o = execute(cmd, False, logging=False)
            o = o.strip('\n')
            if o == '':
                return len(chanel_list), chanel_list

            for str in o.split('\n'):
                m = re.search('expander-\d+:(\d+)', str)
                chanel = m.group(1)
                if chanel not in chanel_list:
                    chanel_list.append(chanel)
            return len(chanel_list), chanel_list

        def _check_chanel(self):
            chanel_list = []
            chanel_phy = {}
            cmd = "ls -l /sys/block/ |grep 'port-6'"
            s, o = execute(cmd, False, logging=False)
            o = o.strip('\n')
            for str in o.split('\n'):
                m = re.search('port-\d+:(\d+)', str)
                chanel = m.group(1)
                if chanel not in chanel_list:
                    chanel_list.append(chanel)
            for c in chanel_list:
                phy_list = []
                cmd = 'ls /sys/class/sas_port/port-6:%s/device/' % c
                s, o = execute(cmd, False, logging=False)
                check = o.split('\n')
                for phy in check:
                    if 'phy' in phy:
                        phy_list.append(phy)
                chanel_phy[c] = self._judge_chanel(phy_list)
            return chanel_phy

        def _judge_chanel(self, list):
            if 'phy-6:0' in list:
                return 1
            if 'phy-6:1' in list:
                return 1
            if 'phy-6:2' in list:
                return 1
            if 'phy-6:3' in list:
                return 1
            return 2

        def make_mapping(self, chanel):
            slot = 24
            num = 0
            disk_list = []
            chanel_2_dsu = self._check_chanel()
            if chanel not in chanel_2_dsu:
                return
            lsi_chanel =  chanel_2_dsu[chanel]
            dsu = '1.%s' % lsi_chanel
            key = '%s:%s' % (6, chanel)

            cmd = "ls -l /sys/block/ |grep 'host[6-7]'"
            s, o = execute(cmd, False, logging=False)
            for nr in o.split('\n'):
                c = 'expander-%s' % key
                if c in nr:
                    n = nr.split()
                    blk = n[8]
                    loc = n[10]

                    m = re.search('port-\d+:\d+:\d+', loc)
                    port = m.group()
                    cmd = "ls /sys/class/sas_host/host6/device/port-%s/expander-%s/%s" % (key, key, port)
                    ss, oo = execute(cmd, False, logging=False)
                    idx = oo.split()[1]
                    cmd = "cat /sys/class/sas_phy/%s/phy_identifier" % (idx)
                    ss, phy_idx = execute(cmd, False, logging=False)
                    phy_idx = phy_idx.strip('\n')
                    if slot == 16:
                        disk_loc = '%s.%s' % (dsu, self.key_16_loc[phy_idx])
                    else:
                        disk_loc = '%s.%s' % (dsu, self.key_24_loc[phy_idx])

                    self.mapping[disk_loc] = blk
                    disk_list.append(disk_loc)

            self.dsu_list[dsu] = slot
         
        def __init__(self):
            self.mapping = {}
            self.dsu_list = {}
            self.dsu_list['1.1'] = 24
            self.dsu_list['1.2'] = 24
            cmd = "ls -l /sys/block/ |grep 'host[6-7]'" 
            s, o = execute(cmd, False, logging=False) 
            if not o: 
                return

            num, chanel =  self._check_expander()
            if num > 0:
                for ch in chanel:
                    self.make_mapping(ch)
            else:
                cmd = "ls -l /sys/block/ |grep 'host[6-7]'" 
                s, o = execute(cmd, False, logging=False) 
                for nr in o.split('\n'): 
                    n = nr.split() 
                    if len(n) == 11:
                        blk = n[8] 
                        loc = n[10] 
                        m = re.search('port-\d+:\d+', loc) 
                        port = m.group() 
                        cmd = "ls /sys/class/sas_port/"+port+"/device/phy-*\:*/sas_phy/" 
                        ss, phy = execute(cmd, False, logging=False) 
                        list = phy.split('-') 
                        phy_idx = list[1].replace(':', '-') 
                        phy_idx = phy_idx.strip('\n')
                        self.mapping['1.1.%s' % (self.key_8_loc[phy_idx])] = blk

                self.dsu_list['1.1'] = 8
                          
else:
    class LocationMapping(object):
        def __init__(self):
            mapping = {'1.1.1'  : 'sdb',
                       '1.1.2'  : 'sdc',
                       '1.1.3'  : 'sdd',
                       '1.1.4'  : 'sde',
                       '1.1.5'  : 'sdf',
                       '1.1.6'  : 'sdg',
                       '1.1.7'  : 'sdh',
                       '1.1.8'  : 'sdi',
                       '1.1.9'  : 'sdj',
                       '1.1.10' : 'sdk',
                       '1.1.11' : 'sdl',
                       '1.1.12' : 'sdm',
                       '1.1.13' : 'sdn',
                       '1.1.14' : 'sdo',
                       '1.1.15' : 'sdp',
                       '1.1.16' : 'sdq'}
            self.mapping = dict([(loc, dev) for loc, dev in mapping.items() if path.exists('/dev/%s' % dev)])
            self.dsu_list = {'1.1': 16}


