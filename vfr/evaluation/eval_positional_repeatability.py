# -*- coding: utf-8 -*-
"""

Module to evaluate positional repeatability.

"""
from __future__ import division, print_function
from vfr.evaluation.measures import get_errors, get_grouped_errors, group_by_subkeys


def get_angular_error(dict_of_coords, idx, min_number_points=0, weighted_measures=False):
    """
    
    Calculate statistics for a given dictionary of coordinates.
    
    idx = 0 for the alpha dictionary.
    idx = 1 for the beta dictionary.
    
    The function ignores entries with fewer than min_number_points
    of entries. It returns two data structures:
    
    max_err_at_angle: The maximum error for each entry in the dictionary
    
    poserr_measures: A data structure containing maximum, mean and percentiles
    for all the entries in the dictionary.
    
    """
    
    #print("get_angular_error[%d]: dict_of_coords=" % idx)
    #for key,item in dict_of_coords.items():
    #    print("  %s : %s" % (str(key), str(item)))

    # Group together the measurements which have common coordinates.
    kfunc = lambda x: (x[0], x[1])
    coords_per_angvec = group_by_subkeys(dict_of_coords, kfunc)
    
    #print("coords_per_angvec=")
    #skipped = 0
    #for key,item in coords_per_angvec.items():
    #    nitems = len(list(item))
    #    if nitems >= min_number_points:
    #        print("  %s : %s" % (str(key), str(item)))
    #    else:
    #        skipped += 1
    #print("  plus %d short items (skipped)." % skipped)
    
    max_err_at_angle = {}
    for angvec, coords in coords_per_angvec.items():
        max_err_at_angle[angvec[idx]] = get_errors(coords).max

    poserr_measures = get_grouped_errors(
        coords_per_angvec.values(), min_number_points=min_number_points,
        weighted_measures=weighted_measures
    )

    return max_err_at_angle, poserr_measures


def evaluate_positional_repeatability(
    dict_of_coordinates_alpha, dict_of_coordinates_beta, pars=None
):
    """
    
    Takes two dictionaries. The keys of each dictionary
    are the (alpha, beta, i,j,k) coordinates; indices of the positional
    repeatability measurement, with one of the alpha/beta coordinates hold
    fixed.

    The values of the dictionary are a 6-tuple of the metrology target
    coordinates:

    (x_small_tgt, y_small_tgt, r_small, x_big_tgt, y_big_tgt, r_big).

    The units are always millimeter.
    
    pars is a data structure containing configurable parameters, such as
    pars.MIN_NUMBER_POINTS: the minimum number of points per data set.
    pars.WEIGHTED_MEASURES: weight measures by number of samples.

    The returned value are the specified values in millimeter:

    posrep_alpha_max_at_angle – maximum positional error at average
                                  of all points at alpha angle Φ

    posrep_beta_max_at_angle – maximum positional error at average
                                  of all points at beta angle Φ, where
                                  Φ depends on the configurable
                                  parameters in 2.10

    posrep_alpha_max – maximum alpha positional error at any angle

    posrep_beta_max – maximum beta positional error at any angle

    Any error should be signalled by throwing an Exception of class
    ImageAnalysisError, with a string member which describes the problem.

    """
    # Parameters must be provided
    assert pars is not None

    # Transform to lists of measurements for the same coordinates
    #print("\n######")
    #print("dict_of_coordinates_alpha=", dict_of_coordinates_alpha)
    #print("dict_of_coordinates_beta=", dict_of_coordinates_beta)
    posrep_alpha_max_at_angle, posrep_alpha_measures = get_angular_error(
        dict_of_coordinates_alpha, 0, min_number_points=pars.MIN_NUMBER_POINTS,
        weighted_measures=pars.WEIGHTED_MEASURES
    )
    #print("alpha: get_angular_error returns\n  " + \
    #      "posrep_alpha_max_at_angle=")
    #for key,item in posrep_alpha_max_at_angle.items():
    #    print("    %s : %s" % (str(key), str(item)))
    #print("  posrep_alpha_measures=%s" % str(posrep_alpha_measures))
        
    #print("\n######")
    posrep_beta_max_at_angle, posrep_beta_measures = get_angular_error(
        dict_of_coordinates_beta, 1, min_number_points=pars.MIN_NUMBER_POINTS,
        weighted_measures=pars.WEIGHTED_MEASURES
    )
    #print("beta: get_angular_error returns\n  " + \
    #      "posrep_beta_max_at_angle=")
    #for key,item in posrep_beta_max_at_angle.items():
    #    print("    %s : %s" % (str(key), str(item)))
    #print("  posrep_beta_measures=%s" % str(posrep_beta_measures))
    
    return (
        posrep_alpha_max_at_angle,
        posrep_beta_max_at_angle,
        posrep_alpha_measures,
        posrep_beta_measures,
    )
    
if __name__ == "__main__":
    # Run a test
    import numpy as np
    
    #TODO: Test not finished. What is the exact content of dict_of_coords?
    print("Testing get_angular_error function...")
    coord_entry = (20.0, 20.0, 0.4, 20.0, 20.0, 0.2)
    
    def generate_coord( entry, diffx, diffy ):
        result = list(entry)
        result[0] = entry[0] + diffx
        result[1] = entry[1] + diffx
        result[3] = entry[3] + diffy
        result[4] = entry[4] + diffy
        return result

    def generate_coord_list( entry, diffsx, diffsy ):
        coord_list = []
        for diffx, diffy in zip (diffsx, diffsy):
            newcoord = generate_coord( entry, diffx, diffy)
            coord_list.append( newcoord )
        return coord_list
    
    diffsx = [0.0, 1.0, 2.0, -1.0, 2.0, 0.0]
    diffsy = [0.0, 1.0, 2.0, -1.0, 2.0, 0.0]
    
    dict_of_coordinates = {}
    alpha = 1.0
    beta = 1.0
    i = j = k = 1
    for diffx, diffy in zip (diffsx, diffsy):
        newcoord = generate_coord( coord_entry, diffx, diffy)
        dict_of_coordinates[ (alpha,beta,i,j,k) ] = newcoord
        alpha += 1.0
        beta += 1.0
        i += 1
        j += 1
        k += 1

#     dict_of_coordinates = { (1.0, 1.0, 1, 1, 1) : generate_coord_list(coord_entry, diffsx, diffsy),
#                             (2.0, 2.0, 1, 1, 1) : generate_coord_list(coord_entry, diffsx, diffsy),
#                             (3.0, 3.0, 1, 1, 1) : generate_coord_list(coord_entry, diffsx, diffsy),
#                             (4.0, 4.0, 1, 1, 1) : generate_coord_list(coord_entry, diffsx, diffsy),
#                             }
    
    print("dict_of_coordinates=", dict_of_coordinates)

    max_at_angle, posrep_measures = get_angular_error(
        dict_of_coordinates, 0, min_number_points=5
    )
    print("get_angular_error returns\n  " + \
          "max_at_angle=")
    for key,item in max_at_angle.items():
        print("    %s : %s" % (str(key), str(item)))
    print("  posrep_measures=%s" % str(posrep_measures))
    
    