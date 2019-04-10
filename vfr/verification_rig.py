#!/usr/bin/env python

from __future__ import absolute_import, division, print_function

import atexit
import os
import sys

from protectiondb import open_database_env
import devicelock
from vfr import hw as real_hw
from vfr import hwsimulation

from vfr.connection import init_driver
from vfr.task_config import MEASUREMENT_TASKS
from vfr.tests_common import find_datum

class Rig:
    def __init__(self, rig_pars, fpu_config=None):

        # first, lock the rig hardware to ensure exclusive access
        groupname = os.environ.get("MOONS_GATEWAY_ACCESS_GROUP","moons")
        # acquire a unique inter-process lock for the rig
        lockname = 'moons-verification-rig'
        if rig_pars.opts.mockup:
            lockname += "-mockup"
        dl = devicelock.DeviceLock(lockname, groupname)


        if rig_pars.opts.mockup:
            hw = hwsimulation
        else:
            hw = real_hw

        self.measure_fpuset = rig_pars.measure_fpuset
        self.opts = rig_pars.opts
        self.hw=hw
        self.gd=None
        self.rd=None
        self.lctrl=None
        self.grid_state=None
        self.fpu_config=fpu_config

        if self.opts.mockup:
            lctrl = self.hw.lampController()
        else:
            if opts.manual_lamp_control:
                lctrl = self.hw.manualLampController()
            else:
                lctrl = self.hw.lampController()

            # make sure that lamps are switched off on program exit
            lamps_off = lambda : lctrl.switch_all_off()

            atexit.register(lamps_off)

        self.lctrl = lctrl


    def init_driver(self, protected=True, env=None):
        N = max(self.measure_fpuset)

        self.rd, self.gd = None, None

        if not protected:
            self.rd, self.grid_state = init_driver(
                self.opts,
                N,
                protected=protected)
        else:
            self.gd, self.grid_state = init_driver(self.opts, N, env=env, protected=True)

            self.gd.readSerialNumbers(self.grid_state)


    def __del__(self):
        del self.rd
        del self.gd
