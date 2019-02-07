from __future__ import print_function, division

import os
import lmdb
import platform

DATABASE_FILE_NAME = os.environ.get("FPU_DATABASE")

# needs 64 bit OS (specifically, large file support) for normal database size
if platform.architecture()[0] == "64bit":
    dbsize = 5*1024*1024*1024
else:
    dbsize = 5*1024*1024


env = lmdb.open(DATABASE_FILE_NAME, max_dbs=10, map_size=dbsize)
