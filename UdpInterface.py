# -*- coding: utf-8 -*-
# @Time    : 2019/2/20 8:44
# @Author  : Duan Ran
# @File    : baseMessage.py
# @Software: PyCharm
# @Desc    ：

import logging
from logging.config import fileConfig
import socket
import re
import os


# 用于ip地址字符串格式验证的正则表达式模板
ip_pattern = r'^([1-9]|[1-9][0-9]|1[0-9][0-9]|2[0-4][0-9]|25[0-5])\.' \
             r'([0-9]|[1-9][0-9]|1[0-9][0-9]|2[0-4][0-9]|25[0-5])\.' \
             r'([0-9]|[1-9][0-9]|1[0-9][0-9]|2[0-4][0-9]|25[0-5])\.' \
             r'([1-9]|[1-9][0-9]|1[0-9][0-9]|2[0-4][0-9]|25[0-5])$'


class UdpServer:
    """
    Udp socket 服务端类，用于监听端口
    """

    def __init__(self, port, log_config_path=None):
        """
        构造函数
        :param port: int, 要绑定监听的本地端口
        :param log_config_path: str, 日志系统配置文件路径，如缺省则不会记录日志，配置方法见logging类
        """
        if type(port) != int:
            raise ValueError("Server port format is incorrect")
        self.host_ip = socket.gethostbyname(socket.getfqdn(socket.gethostname()))
        self.host_port = port
        self.config_path = log_config_path
        self.flag_listen = True
        if self.config_path:
            if not os.path.exists('Log'):
                os.mkdir('Log')
            fileConfig(self.config_path)
            self.logger = logging.getLogger('serverLogger')

    def get_host_ip(self):
        """
        获取本地ip
        :return: str, 本地ip地址
        """
        return self.host_ip

    def get_host_port(self):
        """
        获取绑定的端口
        :return: int, 本地绑定监听的端口
        """
        return self.host_port

    def get_config_path(self):
        """
        获取日志系统配置文件地址
        :return: str, 配置文件地址
        """
        return self.config_path

    def set_host_port(self, new_port):
        """
        重新设置监听端口，需执行stop_listen()后生效
        :param new_port: int, 新的要监听的端口号
        :return: None
        """
        self.host_port = new_port

    def stop_listen(self):
        """
        停止监听循环
        :return: None
        """
        self.flag_listen = False

    def listen(self):
        """
        开始循环监听端口
        :return: str, tuple, 监听到的客户端消息，客户端地址(ip, port)
        """
        # addr = (self.host_ip, self.host_port)
        addr = ('127.0.0.1', self.host_port)
        server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        server.bind(addr)
        self.flag_listen = True
        while self.flag_listen:
            data, client_addr = server.recvfrom(4096)
            server.sendto(str(client_addr[1]).encode('utf-8'), client_addr)
            if self.config_path:
                self.logger.info('Receive:' + data.decode('utf-8') + '\nFrom:' + client_addr[0] + ':' + str(
                    client_addr[1]) + ' Send:' + str(client_addr[1]))
            # yield data.decode('utf-8'), client_addr
            yield data, client_addr


class UdpClient:
    """
    Udp socket 客户端类，用于向指定(ip, port)发送消息
    """

    def __init__(self, server_ip, server_port, log_config_path=None):
        """
        构造函数
        :param server_ip: str, 目标服务器ip
        :param server_port: int, 目标服务器端口
        :param log_config_path: str, 日志系统配置文件路径，如缺省则不会记录日志，配置方法见logging类
        """
        if type(server_ip) != str:
            raise ValueError("Server ip format is incorrect")
        if not re.match(ip_pattern, server_ip):
            raise ValueError("Server ip format is incorrect")
        if type(server_port) != int:
            raise ValueError("Server port format is incorrect")
        self.server_ip = server_ip
        self.host_ip = socket.gethostbyname(socket.getfqdn(socket.gethostname()))
        self.server_port = server_port
        self.host_port = 0
        self.config_path = log_config_path
        if self.config_path:
            if not os.path.exists('Log'):
                os.mkdir('Log')
            fileConfig(log_config_path)
            self.logger = logging.getLogger('clientLogger')

    def get_host_ip(self):
        """
        获取本地ip
        :return: str, 本地ip地址
        """
        return self.host_ip

    def get_host_port(self):
        """
        获取本地发送的端口，发送消息前为0，之后为服务端返回的端口
        :return: int, 本地发送的端口
        """
        return self.host_port

    def get_server_ip(self):
        """
        获取服务端ip
        :return: str, 服务端ip
        """
        return self.server_ip

    def get_server_port(self):
        """
        获取服务端端口
        :return: int, 服务端端口
        """
        return self.server_port

    def get_config_path(self):
        """
        获取日志系统配置文件地址
        :return: str, 配置文件地址
        """
        return self.config_path

    def set_server_ip(self, new_ip):
        """
        设置服务端ip
        :param new_ip: str, 新的服务端ip
        :return: None
        """
        if type(new_ip) != str:
            raise ValueError("Server ip format is incorrect")
        if not re.match(ip_pattern, new_ip):
            raise ValueError("Server ip format is incorrect")
        self.server_ip = new_ip

    def set_server_port(self, new_port):
        """
        设置服务端端口
        :param new_port: str, 新的服务端端口
        :return: None
        """
        if type(new_port) != int:
            raise ValueError("Server port format is incorrect")
        self.server_port = new_port

    def send(self, text, bind_port=None):
        """
        发送消息到已设定的服务端
        :param text: str, 要发送的消息
        :return: str, tuple, 服务端返回的消息（UdpServer返回UdpClient端口）， 服务端的地址(ip, port)
        """
        addr = (self.server_ip, self.server_port)
        client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        if bind_port:
            client.bind(("", bind_port))  # 参数是元组的形式
        client.sendto(text, addr)
        # client.sendto(text.encode('utf-8'), addr)
        # data, server_addr = client.recvfrom(4096)
        # self.host_port = int(data.decode('utf-8'))
        # if self.config_path:
        #     self.logger.info(
        #         'Send:' + text + ' to:' + server_addr[0] + ':' + str(server_addr[1]) + ' Receive:' + data.decode(
        #             'utf-8'))
        # return data.decode('utf-8'), server_addr


if __name__ == '__main__':
    # m = UdpServer(7777)  # 创建实例
    # a = m.listen()  # 开始监听
    # for b in a:  # 循环打印监听
    #     from ctype_pack import decode_box
    #     decode_box(b[0])
    #     # print(b[0], b[1])
    #     if b[0] == 'Message Over':  # 结束循环打印
    #         break
    # m.stop_listen()  # 停止监听
    #
    import time
    import struct
    from ctypes import create_string_buffer
    from ctype_pack import decode_box
    n = UdpClient('130.9.46.71', 7777) # 创建实例
    bbox = (10, 15, 100, 80)
    type = 1
    bak = 0
    head_length = 8
    cell_length = 48
    boxnum = 1
    body_length = boxnum * cell_length
    buf = create_string_buffer(head_length + body_length)
    idx = 0
    # 报文长度
    struct.pack_into("=H", buf, idx, body_length)
    # 报文标识
    idx = idx + 2
    struct.pack_into("=H", buf, idx, 1)
    # 目标数量
    idx = idx + 2
    struct.pack_into("=H", buf, idx, boxnum)
    # 一个检测目标的长度
    idx = idx + 2
    struct.pack_into("=H", buf, idx, cell_length)
    idx = idx + 2

    struct.pack_into("=2H5dI", buf, idx,
                     2,
                     type,
                     bbox[0],
                     bbox[1],
                     bbox[2],
                     bbox[3],
                     time.time(),
                     bak)
    while True:
        time.sleep(1)
        n.send(buf) # 发送消息
        decode_box(buf)
        # print('send buf')
    # print(send_port, server_addr)# 打印服务器返回消息
