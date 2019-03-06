from __future__ import print_function, division

import os
import ast
import lmdb
import platform
import subprocess

from vfr.tests_common import timestamp

DATABASE_FILE_NAME = os.environ.get("FPU_DATABASE")


GIT_VERSION = subprocess.check_output(["git", "describe"]).strip()

# needs 64 bit OS (specifically, large file support) for normal database size
if platform.architecture()[0] == "64bit":
    dbsize = 5*1024*1024*1024
else:
    dbsize = 5*1024*1024


env = lmdb.open(DATABASE_FILE_NAME, max_dbs=10, map_size=dbsize)

class TestResult:
    OK = "OK"
    FAILED = "FAILED"
    NA = "NA"


def  save_test_result(env, vfdb, fpuset, keyfunc, valfunc, verbosity=0):
    
    with env.begin(write=True,db=vfdb) as txn:
            
        for fpu_id in fpuset:

            keybase = keyfunc(fpu_id)
            key1 = str(keybase + ( 'ntests',))
            
            last_cnt = txn.get(key1)
            if last_cnt is None:
                count = 0
            else:
                count = int(last_cnt) + 1
                
            key2 = repr( keybase + ('data', count) )


            val = valfunc(fpu_id)            

            if verbosity > 2:
                print("putting %r : %r" % (key1, str(count)))
                print("putting %r : %r" % (key2, val))
            
            txn.put(key1, str(count))
            txn.put(key2, val)

            
def  get_test_result(env, vfdb, fpu_id, keyfunc, count=None, verbosity=0):
    
    with env.begin(write=False, db=vfdb) as txn:
            
        keybase = keyfunc(fpu_id)

        if count is None:
            key1 = str(keybase + ( 'ntests',))
        
            count = txn.get(key1)

        assert(count is not None)
            
        key2 = repr( keybase + ('data', count) )

        
        val = txn.get(key2, val)

        if val is not None:
            val = ast.literal_eval(val)
        
        
        if verbosity > 2:
            print("got %r : %r" % (key2, val))

    return val

            





    

