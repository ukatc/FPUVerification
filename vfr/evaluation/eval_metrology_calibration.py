# -*- coding: utf-8 -*-
"""Module to evaluate metrology calibration.

"""
from __future__ import division, print_function

from math import asin, pi
import numpy as np


def fibre_target_distance(big_target_coords, small_target_coords, fibre_coords):
    """
    takes coordinates of the big metrology target, the small metrology target,
    and the distance in millimeter, and returns

    1) the distance between the large  metrology target and the fibre aperture in millimeter.
    2) the distance between the small  metrology target and the fibre aperture in millimeter.
    3) the angle of ∠(large target - fibre - small target), in degrees.
    """

    # Authors: Stephen Watson (initial algorithm March 4, 2019)

    v_big = np.array(big_target_coords)
    v_small = np.array(small_target_coords)

    v_f = np.array(fibre_coords)

    va = v_f - v_big
    norm = np.linalg.norm
    metcal_fibre_large_target_distance = norm(va)

    vb = v_f - v_small
    metcal_fibre_small_target_distance = norm(vb)

    metcal_target_vector_angle = asin(np.cross(va, vb) / (norm(va) * norm(vb))) * (
        180.0 / pi
    )

    return (
        metcal_fibre_large_target_distance,
        metcal_fibre_small_target_distance,
        metcal_target_vector_angle,
    )
