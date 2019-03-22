from __future__ import print_function, division
from numpy import nan, asarray, sum, sqrt


class ImageAnalysisError(Exception):
    pass


def rss(values):
    vals = asarray(values)
    return sqrt(sum(vals ** 2))
