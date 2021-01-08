# -*- coding: utf-8 -*-
"""Module to evaluate metrology calibration.

"""
from __future__ import division, print_function

from math import asin, pi
import numpy as np

DEG2RAD = 180.0 / pi

def fibre_target_distance(big_target_coords, small_target_coords, fibre_coords):
    """
    
    Takes coordinates of the big metrology target, the small metrology target,
    and the centre of the fibre, and returns

    1) the distance between the large  metrology target and the fibre aperture in millimeter.
    2) the distance between the small  metrology target and the fibre aperture in millimeter.
    3) the angle of ∠(large target - fibre - small target), in degrees.

    """
    # Authors: Stephen Watson (initial algorithm March 4, 2019)

    v_big = np.array(big_target_coords)
    v_small = np.array(small_target_coords)
    v_f = np.array(fibre_coords)

    # Fibre to large target vector and distance
    va = v_f - v_big
    fibre_large_target_dist = np.linalg.norm(va)

    # Fibre to small target vector and distance.
    vb = v_f - v_small
    fibre_small_target_dist = np.linalg.norm(vb)

    # Large target - fibre - small target angle in degrees.
    target_vector_angle = asin(np.cross(va, vb) / (fibre_large_target_dist * fibre_small_target_dist)) * DEG2RAD

    return (
        fibre_large_target_dist,
        fibre_small_target_dist,
        target_vector_angle,
    )
