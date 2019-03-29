from __future__ import division, print_function

from fpu_constants import (
    ALPHA_DATUM_OFFSET,
    BETA_DATUM_OFFSET,
    StepsPerDegreeAlpha,
    StepsPerDegreeBeta,
)

# exceptions which are raised if image analysis functions fail


class GearboxFitError(Exception):
    pass


# version number for gearbox correction algorithm
# (each different result for the same data
# should yield a version number increase)

GEARBOX_CORRECTION_VERSION = 0.1


def fit_gearbox_correction(dict_of_coordinates_alpha, dict_of_coordinates_beta):
    """Computes gearbox correction and returns correction coefficients
    as a dictionary.


    Input is a dictionary. The keys of the dictionary
    are the i,j,k indices of the positional repeteability measurement.
    Equal i and k mean equal step counts, and j indicates
    the arm and movement direction of the corresponding arm
    during measurement.

    The values of the dictionary are a 4-tuple
    (alpha_steps, beta_steps, x_measured_1, y_measured_1, x_measured_2, y_measured_2).

    Here, (alpha_steps, beta_steps) are the angle coordinates given by
    the motor step counts (measured in degrees), and (alpha_measured,
    beta_measured) are the cartesian values of the large (index 1) and
    the small (index 2) target measured from the images taken.


    The units are in degrees (for alpha_steps and beta_steps)
    and millimeter (for x_measured and y_measured).

    """
    return {
        "coeffs": [0.0, 0.0, 0.0, 0.0, 0.0],
        "version": GEARBOX_CORRECTION_VERSION,
        "algo": "unimplemented",
    }


def apply_gearbox_correction(incoords, coeffs=None):
    alpha, beta = incoords
    # naive linear correction (only for testing)
    alpha_steps = int(round((alpha - ALPHA_DATUM_OFFSET) * StepsPerDegreeAlpha))
    beta_steps = int(round((beta - BETA_DATUM_OFFSET) * StepsPerDegreeBeta))

    return (alpha_steps, beta_steps)
