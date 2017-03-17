
"""
Usage:
    Server.py runserver -s <ip> -p <port>
    Server.py -h
Options:
    -h,--help   Show this screen.
    --version   Show version.
"""

from docopt import docopt
from socketserver import ThreadingTCPServer
from core.ftpserver import FTPHandler


def run():
    """
    解析传入参数，并调用FTPHandler
    """
    args = docopt(__doc__, version="1.0")
    host = args.get("<ip>")
    port = int(args.get("<port>"))
    server = ThreadingTCPServer((host, port), FTPHandler)
    server.serve_forever()

if __name__ == '__main__':
    run()
