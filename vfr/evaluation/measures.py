# -*- coding: utf-8 -*-
"""Module to evaluate datum repeatability.

"""
from __future__ import division, print_function

import warnings

import numpy as np
import logging
import argparse

from vfr.conf import BLOB_WEIGHT_FACTOR, PERCENTILE_ARGS

NO_MEASURES = argparse.Namespace(
    max=np.NaN,
    mean=np.NaN,
    percentiles={},
)

def rss(values):
    vals = np.asarray(values)
    return np.linalg.norm(vals)

def arg_max_dict(d):
    maxval = -np.Inf
    maxkey = None
    for k, v in d.items():
        if v > maxval:
            maxval = v
            maxkey = k
    return maxkey, maxval


def get_errors(coordinate_sequence, centroid=None):
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
    blob_coordinates = np.array(coordinate_sequence)

    assert blob_coordinates.shape[1] == 6, "wrong format for blob position list"

    # Combine position of large and small blob to
    # weighted position.
    #
    # (the rationale is that the error of the large blob is expected
    # to be smaller.)
    #
    # The quality factors are ignored.
    weighted_coordinates = ((BLOB_WEIGHT_FACTOR * blob_coordinates[:, 3:5]) +
                      (1.0 - BLOB_WEIGHT_FACTOR ) * blob_coordinates[:,:2])

    # If the centroid (mean vector) is not defined, compute it.
    if centroid is None:
        centroid = np.mean(weighted_coordinates, axis=0)

    # compute error vectors, as difference between samples and centroid
    error_vectors = weighted_coordinates - centroid

    # compute individual magnitudes of error vectors,
    # which results in a list of scalars
    error_magnitudes = map(np.linalg.norm, error_vectors)

    # get the mean and maximum error
    max_error = max(error_magnitudes)
    mean_error = np.mean(error_magnitudes)

    percentile_vals = np.percentile(error_magnitudes, PERCENTILE_ARGS)

    percentiles = { k: v for k, v in zip(PERCENTILE_ARGS, percentile_vals) }

    return argparse.Namespace(
        max=max_error,
        mean=mean_error,
        percentiles=percentiles,
    )
