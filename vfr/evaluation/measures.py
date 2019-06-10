# -*- coding: utf-8 -*-
"""Module to evaluate datum repeatability.

"""
from __future__ import division, print_function


import numpy as np
import argparse

from vfr.conf import BLOB_WEIGHT_FACTOR, PERCENTILE_ARGS

NO_MEASURES = argparse.Namespace(max=np.NaN, mean=np.NaN, percentiles={}, N=0)


def group_by_subkeys(ungrouped_values, key_func):
    """takes a dictionary, computes a subkey for
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
    blob_coordinates = np.array(coordinate_sequence)

    assert blob_coordinates.shape[1] == 6, "wrong format for blob position list"

    # Combine position of large and small blob to
    # weighted position.
    #
    # (the rationale is that the error of the large blob is expected
    # to be smaller.)
    #
    # The quality factors are ignored.
    weighted_coordinates = (weight_factor * blob_coordinates[:, 3:5]) + (
        1.0 - weight_factor
    ) * blob_coordinates[:, :2]

    # If the centroid (mean vector) is not defined, compute it.
    if centroid is None:
        centroid = np.mean(weighted_coordinates, axis=0)

    # compute error vectors, as difference between samples and centroid
    error_vectors = weighted_coordinates - centroid

    # compute individual magnitudes of error vectors,
    # which results in a list of scalars
    error_magnitudes = map(np.linalg.norm, error_vectors)

    return error_magnitudes


def get_measures(error_magnitudes):
    N = len(error_magnitudes)

    if N == 0:
        return NO_MEASURES

    # get the mean and maximum error
    max_error = max(error_magnitudes)
    mean_error = np.mean(error_magnitudes)

    percentile_vals = np.percentile(error_magnitudes, PERCENTILE_ARGS)

    percentiles = {k: v for k, v in zip(PERCENTILE_ARGS, percentile_vals)}

    return argparse.Namespace(
        max=max_error, mean=mean_error, percentiles=percentiles, N=N
    )


def get_errors(coordinate_sequence, centroid=None, weight_factor=BLOB_WEIGHT_FACTOR):
    """
    Takes a list, set, por sequence of blob
    coordinates, and computes error measures from
    them.
    Each element of the list has the form

    (x1, y1, q1, x2, x2, q2)
    Where the (x1, y1) are coordnates of the small blobs,
    and (x2, y2) coordinates of the large blobs.

    centroid is a coordinate pair which serves
    as the zero point. If centroid is none,
    the arithmetic mean is used as the zero point.
    """

    error_magnitudes = get_magnitudes(
        coordinate_sequence, centroid, weight_factor=weight_factor
    )

    return get_measures(error_magnitudes)


def get_grouped_errors(
    coordinate_sequence_list, list_of_centroids=None, weight_factor=BLOB_WEIGHT_FACTOR
):
    """Takes a lists of lists, sets, or sequences of blob coordinates,
    and computes error measures from them.

    Each element of the list has the form

    (x1, y1, q1, x2, x2, q2)
    Where the (x1, y1) are coordnates of the small blobs,
    and (x2, y2) coordinates of the large blobs.

    The functions computes the magnitudes of the error vectors within
    each group, taking the centroid of the group as center. It returns
    the statistical error measures for all magnitudes compined.

    """

    error_magnitudes = []
    for idx, coordinate_sequence in enumerate(coordinate_sequence_list):
        if list_of_centroids is None:
            centroid = None
        else:
            centroid = list_of_centroids[idx]
        # skip points which have less than five measurements
        if len(coordinate_sequence) < 5:
            continue
        error_magnitudes.extend(
            get_magnitudes(
                coordinate_sequence, centroid=centroid, weight_factor=weight_factor
            )
        )

    return get_measures(error_magnitudes)
