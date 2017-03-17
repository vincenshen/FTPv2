import os
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


BUFFER_SIZE = 1024
USER_HOME = "%s\home" % BASE_DIR
ACCOUNT_FILE = "%s/conf/accounts.cfg" % BASE_DIR

