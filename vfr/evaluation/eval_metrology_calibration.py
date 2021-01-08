# -*- coding: utf-8 -*-
"""Module to evaluate metrology calibration.

"""
from __future__ import division, print_function

from math import asin, acos, pi
import numpy as np

RAD2DEG = 180.0 / pi

def fibre_target_distance(large_target_coords, small_target_coords, fibre_coords):
    """
    
    Takes coordinates of the large metrology target, the small metrology target,
    and the centre of the fibre, and returns

    1) the distance between the large  metrology target and the fibre aperture in millimeter.
    2) the distance between the small  metrology target and the fibre aperture in millimeter.
    3) the angle of ∠(large target - fibre - small target), in degrees.

    """
    # Authors: Stephen Watson (initial algorithm March 4, 2019)

    v_large = np.array(large_target_coords)
    v_small = np.array(small_target_coords)
    v_f = np.array(fibre_coords)

    # Small to large target vector and distance
    vt = v_small - v_large
    small_to_large = np.linalg.norm(vt)
    #print("small_to_large:", small_to_large)    

    # Fibre to large target vector and distance
    va = v_f - v_large
    fibre_to_large = np.linalg.norm(va)
    #print("fibre_to_large:", fibre_to_large)

    # Fibre to small target vector and distance.
    vb = v_f - v_small
    fibre_to_small = np.linalg.norm(vb)
    #print("fibre_to_small:", fibre_to_small)

    # Large target - fibre - small target angle in degrees.
    #target_vector_angle = asin(np.cross(va, vb) / (fibre_to_large * fibre_to_small)) * RAD2DEG
    
    # Alternative calculation using the triangular cosine rule
    target_vector_angle_cos = (fibre_to_small**2 + fibre_to_large**2 - small_to_large**2) / \
                              ( 2.0 * fibre_to_small * fibre_to_large)
    target_vector_angle = RAD2DEG * acos(target_vector_angle_cos)

    return (
        fibre_to_large,
        fibre_to_small,
        target_vector_angle,
    )
