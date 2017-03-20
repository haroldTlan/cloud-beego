#!/usr/bin/env python
# -*- coding: utf-8 -*-
import socket
import json
import copy
import log
from daemon import Daemon, main
from env import config
from util import uuid
import network

# 监听端口
PORT = config.bcst.port

# JSON 识别码
HTTP_OK = 0
HTTP_ERROR = -1

# JSON 说明
HTTP_DESCRIPTION = 'san_addr'

# JSON 字典
JSON_OK = {
    'code': HTTP_OK,
    'description': HTTP_DESCRIPTION
}


class BroadCast(Daemon):

    """
    UDP Broadcast Class which is used to recieve requiring messages from Zadmin
    and send responses to it.
    """

    def init(self):
        self.uuid = uuid.host_uuid()
        # 创建UDP套接字
        self.server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # 绑定套接字端口号
        self.server_address = ('', PORT)
        self.server.bind(self.server_address)
        log.info('starting up on %s port %s' % (self.server_address, PORT))
        log.info('waiting to receive message')

    def _run(self):
        # 接收信息
        data, address = self.server.recvfrom(4096)
        try:
            json_data = json.loads(data)
            if json_data['request_type'] == 'bcst_request':
                self._response_bcst(address)
            if json_data['request_type'] == 'ip_request':
                self._response_ip(address)
        except:
            log.info('message is not valid.')

        log.info('received %s byte from %s' % (len(data), address))
        log.info(data)

    def _response_bcst(self, addr):
        message = copy.deepcopy(JSON_OK)
        message['uuid'] = self.uuid
        message['ifaces'] = self._getIfaces()
        self.server.sendto(json.dumps(message), addr)

    def _response_ip(self, addr):
        message = copy.deepcopy(JSON_OK)
        message['description'] = 'ip_addr'
        message['uuid'] = self.uuid
        message['ifaces'] = self._getIfaces()
        self.server.sendto(json.dumps(message), addr)

    def _getIfaces(self):
        return [info.ipaddr for info in network.ifaces().values() if info.link]

if __name__ == '__main__':
    main(config.bcst.pidfile, BroadCast)
