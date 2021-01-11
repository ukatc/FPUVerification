# -*- coding: utf-8 -*-
"""Module to evaluate metrology calibration.

"""
from __future__ import division, print_function

import math
import numpy as np
import logging

RAD2DEG = 180.0 / math.pi
DEG2RAD = math.pi / 180.0

def fibre_target_distance(large_target_coords, small_target_coords, fibre_coords):
    """
    
    Takes coordinates of the large metrology target, the small metrology target,
    and the centre of the fibre, and returns

    1) the distance between the large  metrology target and the fibre aperture in millimeter.
    2) the distance between the small  metrology target and the fibre aperture in millimeter.
    3) the angle of ∠(small target - large target - fibre), in degrees.

    """
    # Authors: Stephen Watson (initial algorithm March 4, 2019)
    logger = logging.getLogger(__name__)

    v_large = np.array(large_target_coords)
    v_small = np.array(small_target_coords)
    v_f = np.array(fibre_coords)

    # Large to small target vector and distance
    vt = v_large - v_small
    large_to_small = np.linalg.norm(vt)
    #print("large_to_small:", large_to_small)    

    # Fibre to large target vector and distance
    va = v_large - v_f
    fibre_to_large = np.linalg.norm(va)
    #print("fibre_to_large:", fibre_to_large)

    # Fibre to small target vector and distance.
    vb = v_f - v_small
    fibre_to_small = np.linalg.norm(vb)
    #print("fibre_to_small:", fibre_to_small)

    logger.info("Distances in mm: large_to_small={}, fibre_to_small={}, fibre_to_large={},".format(
        large_to_small, fibre_to_small, fibre_to_large))

    # Use a vector cross product to derive the sign of the small target - large target - fibre angle.
    target_vector_cross = math.asin(np.cross(va, vt) / (fibre_to_large * large_to_small)) * RAD2DEG
    logger.debug("Target vector from cross product={} (deg)".format(target_vector_cross))
    #print("Target vector angle={} (deg)".format(target_vector_angle_deg))
    
    # Calculate the magnitude of the angle in degrees from the triangular cosine rule
    target_vector_angle_deg_cos = (large_to_small**2 + fibre_to_large**2 - fibre_to_small**2) / \
                              ( 2.0 * large_to_small * fibre_to_large)
    # Combine the magnitude and sign
    if target_vector_cross >= 0.0:
        target_vector_angle_deg = 180.0 - (RAD2DEG * math.acos(target_vector_angle_deg_cos))
    else:
        target_vector_angle_deg = (RAD2DEG * math.acos(target_vector_angle_deg_cos)) - 180.0
    logger.info("Target vector angle={} (deg)".format(target_vector_angle_deg))

    return (
        fibre_to_large,
        fibre_to_small,
        target_vector_angle_deg,
    )

def metrology_to_fibre( large_target_coords, small_target_coords,
                        fibre_to_large, fibre_to_small, target_vector_angle_deg):
    """
    
    Use the metrology calibration to derive the location of the fibre,
    given the location of the two metrology targets.
    
    """
    v_large = np.array(large_target_coords)
    v_small = np.array(small_target_coords)

    # Large to small target vector and distance
    vt = v_large - v_small
    large_to_small = np.linalg.norm(vt)
    lt_angle = math.atan2(vt[1], vt[0])
    #print("large_to_small:", large_to_small, "angle:", lt_angle)    

    lf_angle = lt_angle + (DEG2RAD * target_vector_angle_deg)
    
    fibre_x = v_large[0] + fibre_to_large * math.cos(lf_angle)
    fibre_y = v_large[1] + fibre_to_large * math.sin(lf_angle)
    
    fibre_coords = (fibre_x, fibre_y)
    return fibre_coords

if __name__ == "__main__":
    # Run a test
    import numpy as np
    
    print("Testing metrology calibration functions...")
    
    test_small = [(1.0, 10.0),
                  (1.0, 10.0),
                  (1.0, 10.0),
                  (1.0, 10.0),
                  (1.0, 10.0),
                  (1.0, 10.0),
                  (1.0, 10.0),
                  (1.0, 10.0),
                  (1.0, 10.0),
                  (1.0, 10.0),
                  (1.0, 10.0),
                  (1.0, 10.0)
                 ]
    
    test_large = [(5.0, 10.0), # Test large aligned with fibre
                  (5.0, 10.0),
                  (4.0, 10.0), # Test large to left of fibre
                  (4.0, 10.0),
                  (6.0, 10.0), # Test large to right of fibre
                  (6.0, 10.0),
                  (5.0, 10.0),
                  (5.0, 10.0),
                  (5.0, 10.0),
                  (7.2, 4.89) # No pattern
                 ]
    
    test_fibre = [(5.0, 13.0),  # Test fibre above metrology targets
                  (5.0,  7.0),  # test fibre below metrology targets
                  (5.0, 13.0),
                  (5.0,  7.0),
                  (5.0, 13.0),
                  (5.0,  7.0),
                  (8.0, 10.1),  # Test fibre almost perfectly aligned with targets
                  (8.0,  9.9),  # Test fibre almost perfectly aligned with targets
                  (8.0, 10.0),  # Test fibre perfectly aligned with targets
                  (7.77, 11.06) # No pattern
                  ]

    for (large_target_coords, small_target_coords, fibre_coords) in \
        zip(test_large, test_small, test_fibre):
    
        print("Large target coords:", large_target_coords)
        print("Small target coords:", small_target_coords)
        print("       Fibre coords:", fibre_coords)
        
        # Test the derivation of metrology calibration parameters
        (fibre_to_large, fibre_to_small, target_vector_angle_deg) = \
            fibre_target_distance(large_target_coords, small_target_coords, fibre_coords)
        print("Fibre to large distance=", fibre_to_large, "(mm)")
        print("Fibre to small distance=", fibre_to_small, "(mm)")
        print("Target vector angle (B)=", target_vector_angle_deg, "(deg)")
        
        # Test the reverse transformation
        new_fibre_coords = metrology_to_fibre( large_target_coords, small_target_coords,
                                               fibre_to_large, fibre_to_small,
                                               target_vector_angle_deg )
        print("   NEW fibre coords:", new_fibre_coords, "(calculated from metrology calibration)")
        assert( abs(fibre_coords[0] - new_fibre_coords[0]) < 0.001 )
        assert( abs(fibre_coords[1] - new_fibre_coords[1]) < 0.001 )
        print(" ")
