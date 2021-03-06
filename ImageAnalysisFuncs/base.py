from __future__ import division, print_function

from numpy import array
import numpy as np


class ImageAnalysisError(Exception):
    pass


def get_min_quality(list_of_coords):
    """compute minimum quality from a set of coordinate / quality triple
    pairs, as computed by posRepCoordinates()

    """

    cord_array = array(list_of_coords)
    q_small = np.min(cord_array[:, 2])
    q_large = np.min(cord_array[:, 5])
    return min(q_small, q_large)
