from __future__ import print_function, division
from numpy import nan

def metrology_calibration_find_targets(ipath,
                                       METCAL_SMALL_TARGET_DIA_LOWER_THRESH=nan,
                                       METCAL_SMALL_TARGET_DIA_UPPER_THRESH=nan,
                                       METCAL_LARGE_TARGET_DIA_LOWER_THRESH=nan,
                                       METCAL_LARGE_TARGET_DIA_UPPER_THRESH=nan,
                                       METCAL_TARGET_CIRCULARITY_THRESH=nan,
                                       METCAL_THRESHOLD_VAL=nan,
                                       METCAL_PLATESCALE=nan):
    
    """Takes full path name of an image, – to find coordinates for the metrology 
    targets in real space using the met-cal camera. Coordinates are in millimeters."""


    return ((0.0, 0.0), (0.0, 0.0))



def metrology_calibration_find_fibre(ipath,
                                     METCAL_FIND_GAUSSIAN_BOX_SIZE=nan,
                                     METCAL_PLATESCALE=nan):
    
    """Takes full path name of an image, – to find coordinates for the backlit fibre 
    in real space using the met-cal camera. Coordinates are in millimeters."""


    return (0.0, 0.0)



def fibre_target_distance(big_target_coords, small_target_coords, fibre_coords):
    """
    takes coordinates of the big metrology target, the small metrology target,
    and the distance in millimeter, and returns the distance between the
    metrology targets and the fibre aperture in millimeter.
    """

    return 10.0
