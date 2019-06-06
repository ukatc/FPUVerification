# -*- coding: utf-8 -*-
"""Module to evaluate datum repeatability.

"""
from __future__ import division, print_function

import warnings


def eval_met_height_inspec(
    metht_small_target_height, metht_large_target_height, pars=None
):
    if (
        (metht_small_target_height > 0)
        and (metht_small_target_height <= pars.MET_HEIGHT_TOLERANCE)
        and (metht_large_target_height > 0)
        and (metht_large_target_height <= pars.MET_HEIGHT_TOLERANCE)
    ):

        return True
    else:
        return False
