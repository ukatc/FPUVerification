from __future__ import division, print_function

from numpy import asarray, sqrt, sum


class ImageAnalysisError(Exception):
    pass


def rss(values):
    vals = asarray(values)
    return sqrt(sum(vals ** 2))
