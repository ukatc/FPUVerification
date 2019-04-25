from camera_calibration.configuration import Config, Corners
from camera_calibration.correction import (
    correct_point,
    correct_points,
    correct_image,
    Correction,
)

# make pyflakes happy
assert (
    Config or Corners or correct_point or correct_points or correct_image or Correction
)
