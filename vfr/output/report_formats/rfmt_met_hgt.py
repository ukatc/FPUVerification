# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function

from inspect import cleandoc

MET_HEIGHT_NA = "metrology height          : n/a"

MET_HEIGHT_NA_CSV = "metrology height,n/a"

MET_HEIGHT_RESULT_TERSE = cleandoc(
    """
    metrology height        : small target = {small_target_height_mm:8.4f} mm,
    metrology height        : large target = {small_target_height_mm:8.4f} mm,
    metrology height        : time/record = {time:.16}/{record-count}, version = {algorithm_version}"""
)


MET_HEIGHT_RESULT_COMPLETE = cleandoc(
    """
    metrology height        : small target = {small_target_height_mm:8.4f} mm
    metrology height        : large target = {small_target_height_mm:8.4f} mm
    metrology height        : test result  = {test_result} mm
    metrology height        : git version  = {git_version}
    metrology height        : time/record  = {time:.16}/{record-count}, version = {algorithm_version}"""
)

MET_HEIGHT_RESULT_LONG = cleandoc(
    """
    metrology height        : small target = {small_target_height_mm:8.4f} mm
    metrology height        : large target = {small_target_height_mm:8.4f} mm
    metrology height        : test result  = {test_result} mm
    metrology height        : git version  = {git_version}
    metrology height        : time/record  = {time:.16}/{record-count}, version = {algorithm_version}"""
)


MET_HEIGHT_RESULT_EXTENDED = MET_HEIGHT_RESULT_LONG


MET_HEIGHT_RESULT_CSV = cleandoc(
    """
    metrology height,small target,{small_target_height_mm:8.4f}
    metrology height,large target,{small_target_height_mm:8.4f}
    metrology height,test result,{test_result}
    metrology height,git version,{git_version}
    metrology height,time,{time:.16},record,{record-count},version,{algorithm_version}"""
)

MET_HEIGHT_IMAGES = "metrology height images   : {!r}"

MET_HEIGHT_ERRMSG = (
    "metrology height      : error message = {error_message}, time/record = {time:.16}/{record-count},"
    " version = {algorithm_version}"
)
