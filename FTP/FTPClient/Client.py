# _*_ coding:utf-8 _*_
"""
Usage:
    Client.py -s <server_ip> -p <server_port>
    Client.py -h
Options:
    -h,--help   Show this screen.
    --version   Show version.
"""

from socket import *
from docopt import docopt
import json
import struct
import os
import hashlib

# define receive buffer size
BUFFER_SIZE = 1024

# parse input parameter
args = docopt(__doc__, version="1.0")
server_ip = args.get("<server_ip>")
server_port = int(args.get("<server_port>"))


# define status code
STATUS_CODE = {
    200: "Task finished",
    250: "Invalid cmd format, e.g: {'action':'get','filename':'test.py','size':344}",
    251: "Invalid cmd",
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


class FTPClient(object):
    """
    FTPClient
    """
    def __init__(self):
        self.user = None
        self.is_authentication = False
        self.terminal_display = None
        self.client = socket(AF_INET, SOCK_STREAM)
        self.client.connect((server_ip, server_port))

    def _help(self, *args):
        supported_actions = """
        get filename    #get file from FTP server
        put filename    #upload file to FTP server
        ls              #list files in current dir on FTP server
        pwd             #check current path on server
        cd path         #change directory , same usage as linux cd command
        """
        print(supported_actions)

    def authentication(self):
        tries = 3
        while True:
            username = input("please input username:").strip()
            password = input("please input password:").strip().encode("utf-8")
            auth_data = {
                "action": "auth",
                "username": username,
                "password": hashlib.md5(password).hexdigest(),
            }
            self.send_response(auth_data)
            data = self.get_response()
            if data.get("status_code") == 254:
                self.user = username
                self.is_authentication = True
                print(STATUS_CODE.get(254))
                return
            else:
                tries -= 1
                print(STATUS_CODE.get(data.get("status_code")))

            if tries == 0:
                exit()

    def interactive(self):
        if self.is_authentication is False:
            self.authentication()
        self.terminal_display = "[%s]$:" % self.user
        while True:
            cmd = input(self.terminal_display).strip()
            if not cmd:
                continue

            cmd_list = cmd.split()
            if hasattr(self, "_%s" % cmd_list[0]):
                func = getattr(self, "_%s" % cmd_list[0])
                func(cmd_list)
            else:
                print("\033[31mInvalid cmd, type 'help' to check available commands.\033[0m")

    def get_response(self):
        """
        向Server接收数据包
        """
        head_len = self.client.recv(4)
        data_size = struct.unpack("i", head_len)[0]
        data = self.client.recv(data_size)
        data = json.loads(data.decode())
        return data

    def send_response(self, data):
        """
        向Server发送数据包
        """
        data = json.dumps(data).encode()
        self.client.send(struct.pack("i", len(data)))
        self.client.send(data)

    def _md5_require(self, cmd_list):
        if "__md5" in cmd_list:
            return True

    def print_progress(self, total_size):
        """
        打印进度条
        """
        received_size = 0
        current_percent = 0
        while received_size < total_size:
            new_size = yield
            if int((received_size / total_size) * 100) > current_percent:
                print("#", end="", flush=True)
                current_percent = int((received_size / total_size) * 100)
            received_size += new_size

    def _cd(self, *args):
        if len(args[0]) > 1:
            path = args[0][1]
        else:
            path = ""
        data = {"action": "change_dir", "path": path}
        self.send_response(data)
        response = self.get_response()
        if response.get("status_code") == 260:
            self.terminal_display = "%s:" % response.get('data').get("current_path")

    def _pwd(self, *args):
        data = {"action": "pwd"}
        self.send_response(data)
        response = self.get_response()
        has_err = False
        if response.get("status_code") == 200:
            data = response.get("data")
            if data:
                print(data)
            else:
                has_err = True
        else:
            has_err = True

        if has_err:
            print("Error: Something Wrong!")

    def _ls(self, *args):
        data = {"action": "listdir"}
        self.send_response(data)
        response = self.get_response()
        has_err = False
        if response.get("status_code") == 200:
            data = response.get("data")
            if data:
                print(data[1])
            else:
                has_err = True
        else:
            has_err = True

        if has_err:
            print("Error: Something Wrong!")

    def _get(self, *args):
        """
        download file
        """
        print(args)
        if len(args[0]) > 1:
            file_name = args[0][1]
        else:
            print(STATUS_CODE.get(255))
            return
        data_head = {
            'action': 'get',
            'file_name': file_name
        }
        self.send_response(data_head)
        data = self.get_response()
        if data.get("status_code") == 256:
            print(STATUS_CODE.get(256))
            return
        file_size = data["data"].get("file_size")
        rec_size = 0
        progress = self.print_progress(file_size)
        progress.__next__()
        with open(file_name, "wb") as f:
            while rec_size < file_size:
                res = self.client.recv(BUFFER_SIZE)
                f.write(res)
                rec_size += len(res)
                try:
                    progress.send(len(res))
                except StopIteration:
                    print("[100%]")

    def _put(self, *args):
        """
        upload file
        """
        print(args)
        if len(args[0]) > 1:
            file_name = args[0][1]
        else:
            print(STATUS_CODE.get(255))
            return
        try:
            print(file_name)
            file_size = os.path.getsize(file_name)
        except FileNotFoundError:
            print("File doesn't exist")
            return
        data_head = {
            'action': 'put',
            'file_size': file_size,
            'file_name': file_name
        }
        self.send_response(data_head)
        send_size = 0
        print(file_size)
        progress = self.print_progress(file_size)
        progress.__next__()
        with open(file_name, 'rb') as f:
            for line in f:
                self.client.send(line)
                send_size += len(line)
                try:
                    progress.send(len(line))
                except StopIteration:
                    print("[100%]")


if __name__ == '__main__':
    ftp = FTPClient()
    ftp.interactive()


