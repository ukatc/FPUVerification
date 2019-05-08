# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function

from inspect import cleandoc

MET_CAL_NA = "metrology calibration     : n/a"
MET_CAL_NA_CSV = "metrology calibration,n/a"

MET_CAL_RESULT_TERSE = cleandoc(
    """
    metrology calibration   : metcal_fibre_large_target_distance = {metcal_fibre_large_target_distance_mm:8.4f} mm,
    metrology calibration   : metcal_fibre_small_target_distance = {metcal_fibre_small_target_distance_mm:8.4f} mm,
    metrology calibration   : metcal_target_vector_angle         = {metcal_target_vector_angle_deg:8.4f} degrees,
    metrology calibration   : time/record={time:.16}/{record-count}, version = {algorithm_version}"""
)

MET_CAL_RESULT_COMPLETE = cleandoc(
    """
    metrology calibration   : metcal_fibre_large_target_distance = {metcal_fibre_large_target_distance_mm:8.4f} mm
    metrology calibration   : metcal_fibre_small_target_distance = {metcal_fibre_small_target_distance_mm:8.4f} mm
    metrology calibration   : metcal_target_vector_angle         = {metcal_target_vector_angle_deg:8.4f} degrees
    metrology calibration   : coords large target                = {coords[target_big_xy]!r}
    metrology calibration   : coords small target                = {coords[target_small_xy]!r}
    metrology calibration   : quality small target               = {coords[target_small_q]:8.4f}
    metrology calibration   : quality large target               = {coords[target_big_q]:8.4f}
    metrology calibration   : quality fibre                      = {coords[fibre_q]:8.4f}
    metrology calibration   : git version                        = {git_version}
    metrology calibration   : time/record={time:.16}/{record-count}, version = {algorithm_version}"""
)

MET_CAL_RESULT_LONG = cleandoc(
    """
    metrology calibration   : metcal_fibre_large_target_distance = {metcal_fibre_large_target_distance_mm:8.4f} mm
    metrology calibration   : metcal_fibre_small_target_distance = {metcal_fibre_small_target_distance_mm:8.4f} mm
    metrology calibration   : metcal_target_vector_angle         = {metcal_target_vector_angle_deg:8.4f} degrees
    metrology calibration   : coords large target                = {coords[target_big_xy]!r}
    metrology calibration   : coords small target                = {coords[target_small_xy]!r}
    metrology calibration   : quality small target               = {coords[target_small_q]:8.4f}
    metrology calibration   : quality large target               = {coords[target_big_q]:8.4f}
    metrology calibration   : quality fibre                      = {coords[fibre_q]:8.4f}
    metrology calibration   : git version                        = {git_version}
    metrology calibration   : time/record={time:.16}/{record-count}, version = {algorithm_version}"""
)

MET_CAL_RESULT_EXTENDED = cleandoc(
    """
    metrology calibration   : metcal_fibre_large_target_distance = {metcal_fibre_large_target_distance_mm:8.4f} mm
    metrology calibration   : metcal_fibre_small_target_distance = {metcal_fibre_small_target_distance_mm:8.4f} mm
    metrology calibration   : metcal_target_vector_angle         = {metcal_target_vector_angle_deg:8.4f} degrees
    metrology calibration   : coords large target                = {coords[target_big_xy]!r}
    metrology calibration   : coords small target                = {coords[target_small_xy]!r}
    metrology calibration   : quality small target               = {coords[target_small_q]:8.4f}
    metrology calibration   : quality large target               = {coords[target_big_q]:8.4f}
    metrology calibration   : quality fibre                      = {coords[fibre_q]:8.4f}
    metrology calibration   : git version                        = {git_version}
    metrology calibration   : time/record={time:.16}/{record-count}, version = {algorithm_version}"""
)

MET_CAL_RESULT_CSV = cleandoc(
    """
    metrology calibration,metcal_fibre_large_target_distance,{metcal_fibre_large_target_distance_mm:8.4f},mm
    metrology calibration,metcal_fibre_small_target_distance,{metcal_fibre_small_target_distance_mm:8.4f},mm
    metrology calibration,metcal_target_vector_angle,{metcal_target_vector_angle_deg:8.4f},degrees
    metrology calibration,coords large target,{coords[target_big_xy]!r}
    metrology calibration,coords small target,{coords[target_small_xy]!r}
    metrology calibration,quality small target,{coords[target_small_q]:8.4f}
    metrology calibration,quality large target,{coords[target_big_q]:8.4f}
    metrology calibration,quality fibre,{coords[fibre_q]:8.4f}
    metrology calibration,git version,{git_version}
    metrology calibration,time,{time:.16},record,{record-count},version,{algorithm_version}
"""
)

MET_CAL_ERRMSG = (
    "metrology calibration   : {error_message}, time/record = {time:.16}/{record-count}, "
    "version = {algorithm_version}"
)

MET_CAL_ERRMSG_CSV = (
    "metrology calibration,{error_message},time,{time:.16},record,{record-count},"
    "version,{algorithm_version}"
)

MET_CAL_IMAGES = "metrology cal. images     : {!r}"
