# -*- coding: utf-8 -*-
"""Module to evaluate datum repeatability.

"""
from __future__ import division, print_function

import argparse

from vfr.evaluation.measures import get_errors, NO_MEASURES

NO_RESULT = argparse.Namespace(
    datum_only=NO_MEASURES, moved=NO_MEASURES, combined=NO_MEASURES
)


def evaluate_datum_repeatability(datumed_coords, moved_coords, pars=None):
    """Takes two lists of (x,y) coordinates : coordinates
    for unmoved FPU, for an FPU which was only datumed, for an FPU which
    was moved, then datumed.

    The units are in millimeter.

    The returned values corrspond to  repeatability value ins millimeter.
    For each of datumed-only set of coordinates, moved
    coordinates, and the combined list, the mean value, the
    maximum value, and a dict of precentile values for
    the set is returned.

    """

    all_coords = list(datumed_coords)
    all_coords.extend(moved_coords)
    return argparse.Namespace(
        datum_only=get_errors(datumed_coords),
        moved=get_errors(moved_coords),
        combined=get_errors(all_coords),
    )
