# _*_ coding:utf-8 _*_
from socketserver import StreamRequestHandler
import configparser
import os
import subprocess
import hashlib
import re
import json
import struct

from conf import settings


STATUS_CODE = {
    200: "Task finished",
    250: "Invalid cmd format, e.g: {'action':'get','filename':'test.py','size':344}",
    251: "Invalid cmd ",
    252: "Invalid auth data",
    253: "Wrong username or password",
    254: "Passed authentication",
    255: "Filename doesn't provided",
    256: "File doesn't exist on server",
    257: "ready to send file",
    258: "md5 verification",
    259: "path doesn't exist on server",
    260: "path changed",
}


class FTPHandler(StreamRequestHandler):
    home_dir = None
    current_dir = None
    user = None

    def handle(self):
        while True:
            print("connect from:", self.client_address)
            head_len = self.request.recv(4)
            if not head_len:
                break
            head_size = struct.unpack("i", head_len)[0]
            data_json = self.request.recv(head_size)
            data = json.loads(data_json.decode())
            if data.get("action") is None:
                continue
            if hasattr(self, "_%s" % data.get("action")):
                func = getattr(self, "_%s" % data.get("action"))
                func(data)

    def send_response(self, code, data=None):
        """
        向客户端返回数据
        """
        send_data = {"status_code": code}
        if data:
            send_data.update({"data": data})
        send_data = json.dumps(send_data).encode()
        self.request.send(struct.pack("i", len(send_data)))
        self.request.send(send_data)

    def _auth(self, *args):
        auth_data = args[0]
        username = auth_data.get("username")
        password = auth_data.get("password")
        self.user = self.authentication(username, password)
        if self.user is None:
            self.send_response(253)
        else:
            self.home_dir = "%s\%s" % (settings.USER_HOME, self.user)
            self.current_dir = self.home_dir
            self.send_response(254)

    def authentication(self, username, password):
        """
        从配置文件中验证用户
        """
        config = configparser.ConfigParser()
        config.read(settings.ACCOUNT_FILE)
        if username in config.sections():
            _password = config[username]["Password"]
            hash_password = hashlib.md5(bytes(_password, "utf-8")).hexdigest()
            if password == hash_password:
                return config[username]["username"]

    def _listdir(self, *args):
        res = self.run_cmd("dir /b %s" % self.current_dir)
        self.send_response(200, data=res)

    def _change_dir(self, *args):
        if args[0]:
            dest_path = "%s\%s" % (self.current_dir, args[0].get("path"))
        else:
            dest_path = self.home_dir

        real_path = os.path.realpath(dest_path)
        if real_path.startswith(self.home_dir):
            if os.path.isdir(real_path):
                self.current_dir = real_path
                current_relative_dir = self.get_relative_path(self.current_dir)
                self.send_response(260, {'current_path': current_relative_dir})
            else:
                self.send_response(259)
        else:
            print("has no permission....to access ", real_path)
            current_relative_dir = self.get_relative_path(self.current_dir)
            self.send_response(260, {'current_path': current_relative_dir})

    def _pwd(self, *args):
        current_relative_dir = self.get_relative_path(self.current_dir)
        self.send_response(200, data=current_relative_dir)

    def run_cmd(self, cmd):
        cmd_res = subprocess.getstatusoutput(cmd)
        return cmd_res

    def get_relative_path(self, abs_path):
        relative_path = abs_path.replace(settings.USER_HOME, '')
        return relative_path

    def _get(self, *args):
        """
        download file
        """
        file_name = args[0].get("file_name")
        if not os.path.isfile("%s/%s" % (self.current_dir, file_name)):
            self.send_response(256)
        file_size = os.path.getsize("%s/%s" % (self.current_dir, file_name))
        data_head = {"file_size": file_size}
        self.send_response(257, data=data_head)
        with open("%s/%s" % (self.current_dir, file_name), 'rb') as f:
            while True:
                data = f.read(settings.BUFFER_SIZE)
                if not data:
                    break
                self.request.send(data)

    def _put(self, *args):
        """
        download file
        """
        file_name = args[0].get("file_name")
        file_size = args[0].get("file_size")
        file_path = "%s/%s" % (self.current_dir, file_name)
        rec_size = 0
        with open(file_path, "wb") as f:
            while rec_size < file_size:
                res = self.request.recv(settings.BUFFER_SIZE)
                f.write(res)
                rec_size += len(res)

