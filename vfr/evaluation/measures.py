# -*- coding: utf-8 -*-
"""

Module containing common grouping and statistical processing functions.

"""
from __future__ import division, print_function


import numpy as np
import math
import argparse

from vfr.conf import BLOB_WEIGHT_FACTOR, PERCENTILE_ARGS
from Gearbox.gear_correction import get_weighted_coordinates

NO_MEASURES = argparse.Namespace(
    max=np.NaN, mean=np.NaN, percentiles={p: np.NaN for p in PERCENTILE_ARGS}, N=0
)


def group_by_subkeys(ungrouped_values, key_func):
    """
    
    Takes a dictionary, computes a subkey for
    each key in it, and collects the items which match
    the same subkey into sequences which are the
    value for that key.
    
    """
    new_dict = {}

    for key, val in ungrouped_values.items():
        subkey = key_func(key)
        if not new_dict.has_key(subkey):
            new_dict[subkey] = []

        new_dict[subkey].append(val)

    return new_dict


def arg_max_dict(d):
    """
    
    Returns the key and value of the maximum value in a dictionary.
    
    """
    maxval = -np.Inf
    maxkey = None
    for k, v in d.items():
        if v > maxval:
            maxval = v
            maxkey = k
    return maxkey, maxval


def get_magnitudes(
    coordinate_sequence, centroid=None, weight_factor=BLOB_WEIGHT_FACTOR
):
    """
    
    Takes a list, set, or sequence of blob coordinates,
    and computes error magnitude of each point in the
    sequence relative to a zero point.
    Each element of the coordinate_sequencelist has the form

    (x1, y1, q1, x2, x2, q2)
    
    Where the (x1, y1) are coordinates of the small blobs,
    and (x2, y2) coordinates of the large blobs.

    centroid is a coordinate pair which serves
    as the zero point. If centroid is none,
    the arithmetic mean is used as the zero point.
    
    NOTE: If the sequence contains only only point, the error
    magnitude will always be zero. If the sequence contains
    only two points, the error magnitude will be HALF of the
    difference between the points (when centroid=None).
    
    """
    blob_coordinates = np.array(coordinate_sequence)

    assert blob_coordinates.shape[1] == 6, "wrong format for blob position list"

    # Combine position of large and small blob to
    # weighted position.
    #
    # (the rationale is that the error of the large blob is expected
    # to be smaller.)
    #
    # The quality factors are ignored.
    # NOTE that get_weighted_coordinates deliberately flips the Y axis of the
    # coordinates. This does not make a difference to the error magnitudes but
    # might look surprising.
    weighted_coordinates = get_weighted_coordinates(blob_coordinates, weight_factor)
    #print("get_magnitudes: weighted_coordinates=%s" % str(weighted_coordinates))

    # If the centroid (mean vector) is not defined, compute it.
    if centroid is None:
        centroid = np.mean(weighted_coordinates, axis=0)
    #print("get_magnitudes: centroid=%s" % str(centroid))

    # compute error vectors, as difference between samples and centroid
    error_vectors = weighted_coordinates - centroid
    #print("get_magnitudes: error_vectors=%s" % str(error_vectors))

    # Compute individual magnitudes of error vectors,
    # which results in a list of scalars
    error_magnitudes = map(np.linalg.norm, error_vectors)
    #print("get_magnitudes: error magnitudes=%s" % str(error_magnitudes))
    
#     comp_error_magnitudes = []
#     for err_vec in error_vectors:
#         err_mag = math.sqrt(err_vec[0]*err_vec[0] + err_vec[1]*err_vec[1])
#         comp_error_magnitudes.append( err_mag )
#     print("get_magnitudes: comparison error magnitudes=%s" % str(comp_error_magnitudes))

    return error_magnitudes


def get_measures(error_magnitudes):
    """
    
    Given a list of error magnitudes, calculates statistical
    parameters (maximum, mean and a selection of percentiles)
    and returns them in a data structure.
    
    The list of percentiles to be calculated is defined in
    the global constant, PERCENTILE_ARGS.
    
    """
    N = len(error_magnitudes)

    if N == 0:
        return NO_MEASURES

    # get the mean and maximum error
    max_error = max(error_magnitudes)
    mean_error = np.mean(error_magnitudes)

    percentile_vals = np.percentile(error_magnitudes, PERCENTILE_ARGS)

    # Convert the percentile list into a dictionary.
    percentiles = {k: v for k, v in zip(PERCENTILE_ARGS, percentile_vals)}

    return argparse.Namespace(
        max=max_error, mean=mean_error, percentiles=percentiles, N=N
    )


def get_errors(coordinate_sequence, centroid=None, weight_factor=BLOB_WEIGHT_FACTOR):
    """
    
    Takes a list, set, or sequence of blob coordinates,
    and computes error measures from them.
    Each element of the coordinate_sequence list has the form

    (x1, y1, q1, x2, x2, q2)
    
    Where the (x1, y1) are coordnates of the small blobs,
    and (x2, y2) coordinates of the large blobs.

    centroid is a coordinate pair which serves
    as the zero point. If centroid is none,
    the arithmetic mean is used as the zero point.
    
    """
    #print("get_errors: centroid=%s, coordinate_sequence=%s" % \
    #      (str(centroid), str(coordinate_sequence)))

    error_magnitudes = get_magnitudes(
        coordinate_sequence, centroid, weight_factor=weight_factor
    )
    #print("get_errors: error_magnitudes=%s" % str(error_magnitudes))

    return get_measures(error_magnitudes)


def get_grouped_errors(
    coordinate_sequence_list,
    list_of_centroids=None,
    weight_factor=BLOB_WEIGHT_FACTOR,
    min_number_points=0,
    weighted_measures=False
):
    """
    
    Takes a lists of lists, sets, or sequences of blob coordinates,
    and computes error measures from them.

    Each element of the coordinate_sequence_list is another list
    with elements of the form

    (x1, y1, q1, x2, x2, q2)
    
    Where the (x1, y1) are coordinates of the small blobs,
    and (x2, y2) coordinates of the large blobs.

    The functions computes the magnitudes of the error vectors within
    each group, taking the centroid of the group as center. It returns
    the statistical error measures for all magnitudes combined.

    """
    #print("get_grouped_errors: list_of_centroids=%s, coordinate_sequence_list=%s" % \
    #      (str(list_of_centroids), str(coordinate_sequence_list)))

    error_magnitudes = []
    for idx, coordinate_sequence in enumerate(coordinate_sequence_list):
        if list_of_centroids is None:
            centroid = None
        else:
            centroid = list_of_centroids[idx]
        #print("get_grouped_errors[%d]: centroid=%s, coordinate_sequence=%s" % \
        #      (idx, str(centroid), str(coordinate_sequence)))

        # Skip points which have less than required number of measurements
        # (this is relevant for the positional repeatability)
        num_samples = len(coordinate_sequence)
        if num_samples < min_number_points:
            #print("get_grouped_errors[%d]: fewer than min of %d points" % \
            #      (idx, min_number_points))
            continue
        
        err_mags = get_magnitudes(
                coordinate_sequence, centroid=centroid, weight_factor=weight_factor
            )
        error_magnitudes.extend( err_mags )
        if weighted_measures and num_samples > 2:
            for ii in range(2, num_samples):
                # Append multiple copies of the vectors to increase their weight.
                error_magnitudes.extend( err_mags )
        #print("get_grouped_errors[%d]:: error_magnitudes=%s" % \
        #       (idx, str(err_mags)))

    return get_measures(error_magnitudes)
