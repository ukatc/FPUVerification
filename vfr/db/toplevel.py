from __future__ import absolute_import, division, print_function

import os

# Import protection database functions from the FPU control software (fpu_driver)
from protectiondb import open_database_env

from vfr.options import load_config_and_sets
from vfr.db.snset import get_snset


class Database:
    def __init__(self, eval_fpuset=None, fpu_config=None, opts=None):

        database_file_name = os.environ.get("FPU_DATABASE", "")
        print("Opening FPU database:", database_file_name)

        self.opts = opts
        self.env = open_database_env(mockup=opts.mockup)

        if self.env is None:
            raise ValueError(
                "The environment variable FPU_DATABASE needs to"
                " be set to the directory path of the LMDB position database!"
            )

        self.vfdb = self.env.open_db("verification")
        self.fpudb = self.env.open_db("fpu")
        self.eval_fpuset = None
        self.fpu_config = None

    def load_fpu_config_and_sets(self, config_file_name, opts):
        all_serial_numbers = get_snset(self.env, self.vfdb, opts)
        fpu_config, measure_fpuset, eval_fpuset = load_config_and_sets(
            all_serial_numbers, config_file_name, opts
        )

        self.eval_fpuset = eval_fpuset
        self.fpu_config = fpu_config

        return fpu_config, measure_fpuset, eval_fpuset
