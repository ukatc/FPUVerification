from __future__ import print_function, division

def positional_repeatability_image_analysis(ipath):
    """Takes full path name of an image, and returns the (x, Y) coordinates
    of the fibre in millimeter. The coordinates need only to be relative
    to the camera position."""

    return (0.0, 0.0)


def evaluate_datum_repeatability(unmoved_coords, datumed_coords, moved_coords):
    """Takes three lists of (x,y) coordinates : coordinates
    for unmoved FPU, for an FPU which was only datumed, for an FPU which
    was moved, then datumed.

    The units are in millimeter.

    The returned value is the repeatability value in millimeter.
    
    """

    return 0.005
