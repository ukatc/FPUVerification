# -*- coding: utf-8 -*-
"""Module to evaluate datum repeatability.

"""
from __future__ import division, print_function

import warnings

import numpy as np
import logging


def evaluate_datum_repeatability(datumed_coords, moved_coords, pars=None):
    """Takes two lists of (x,y) coordinates : coordinates
    for unmoved FPU, for an FPU which was only datumed, for an FPU which
    was moved, then datumed.

    The units are in millimeter.

    The returned value is the repeatability value in millimeter.

    Any error should be signalled by throwing an Exception of class
    ImageAnalysisError, with a string member which describes the problem.

    """

    # get data, omitting quality factors
    xy_datumed = np.array(datumed_coords)
    xy_moved = np.array(moved_coords)

    datumed_mean = np.mean(xy_datumed, axis=0)  # averages both small and big targets
    moved_mean = np.mean(xy_moved, axis=0)

    norm = np.linalg.norm
    datumed_errors_small = map(norm, xy_datumed[:, :2] - datumed_mean[:2])
    datumed_errors_big = map(norm, xy_datumed[:, 2:] - datumed_mean[2:])
    moved_errors_small = map(norm, xy_moved[:, :2] - moved_mean[:2])
    moved_errors_big = map(norm, xy_moved[:, 2:] - moved_mean[2:])

    datumed_errors = np.hstack([datumed_errors_big, datumed_errors_small])
    moved_errors = np.hstack([moved_errors_big, moved_errors_small])
    datrep_dat_only_max = max(datumed_errors)
    datrep_dat_only_std = np.std(datumed_errors)
    datrep_move_dat_max = max(moved_errors)
    datrep_move_dat_std = np.std(moved_errors)

    return (
        datrep_dat_only_max,
        datrep_dat_only_std,
        datrep_move_dat_max,
        datrep_move_dat_std,
        datumed_errors,
        moved_errors,
    )
