from __future__ import absolute_import, division, print_function

import atexit
import os
import signal

# from numpy import zeros, nan
# from protectiondb import ProtectionDB as pdb
# from vfr.db import save_test_result, TestResult

cleanup_registered = False


def cleanup(path):
    try:
        os.unlink(path)
    except OSError:
        pass


def go_collision_test_pos_mockup(fpu_id):
    # notify mock gateway on FPU which should
    # signal a collision at 50 degrees
    idpath = "/var/tmp/colltest.fpuid"

    gw_pid = int(open("/var/tmp/mock-gateway.pid").readline())

    global cleanup_registered

    with open(idpath, "w") as f:
        if not cleanup_registered:
            atexit.register(cleanup, idpath)
            cleanup_registered = True

        f.write("%s\n" % fpu_id)
    os.kill(gw_pid, signal.SIGRTMIN)


def go_collision_test_pos(fpu_id, opts):
    if opts.mockup:
        go_collision_test_pos_mockup(fpu_id)
