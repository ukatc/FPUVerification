# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function

from inspect import cleandoc

DAT_REP_NA = "datum repeatability       : n/a"
DAT_REP_NA_CSV = "datum repeatability,n/a"

DAT_REP_RESULT_TERSE = cleandoc(
    """
    datum repeatability     : {result},
    datum repeatability     : datum only max                = {datum_repeatability_only_max_mm:7.3} mm,
    datum repeatability     : datum only std                = {datum_repeatability_only_std_mm:7.3} mm,
    datum repeatability     : datum only max residual count = {datum_repeatability_max_residual_datumed},
    datum repeatability     : datum+move max                = {datum_repeatability_move_max_mm:7.3} mm,
    datum repeatability     : datum+move std                = {datum_repeatability_move_std_mm:7.3} mm,
    datum repeatability     : datum+move max residual count = {datum_repeatability_max_residual_moved},
    datum repeatability     : time/record                   = {time:.16}/{record-count}, version = {algorithm_version}"""
)

DAT_REP_RESULT_COMPLETE = cleandoc(
    """
    datum repeatability     : {result},
    datum repeatability     : threshold                      = {pass_threshold_mm:8.4f}
    datum repeatability     : datum only max                 = {datum_repeatability_only_max_mm:7.3} mm
    datum repeatability     : datum only std                 = {datum_repeatability_only_std_mm:7.3} mm
    datum repeatability     : datum only max residual count  = {datum_repeatability_max_residual_datumed}
    datum repeatability     : datum+move max                 = {datum_repeatability_move_max_mm:7.3} mm
    datum repeatability     : datum+move std                 = {datum_repeatability_move_std_mm:7.3} mm
    datum repeatability     : datum+move max residual count  = {datum_repeatability_max_residual_moved}
    datum repeatability     : datum only min quality         = {min_quality_datumed:8.4f}
    datum repeatability     : datum+move min quality         = {min_quality_moved:8.4f}
    datum repeatability     : time/record                    = {time:.16}/{record-count}
    datum repeatability     : git version                    = {git_version}
    datum repeatability     : image algorithm version        = {algorithm_version}"""
)

DAT_REP_RESULT_LONG = cleandoc(
    """
    datum repeatability     : {result},
    datum repeatability     : threshold                      = {pass_threshold_mm:8.4f}
    datum repeatability     : datum only max                 = {datum_repeatability_only_max_mm:7.3} mm
    datum repeatability     : datum only std                 = {datum_repeatability_only_std_mm:7.3} mm
    datum repeatability     : datum only max residual count  = {datum_repeatability_max_residual_datumed}
    datum repeatability     : datum+move max                 = {datum_repeatability_move_max_mm:7.3} mm
    datum repeatability     : datum+move std                 = {datum_repeatability_move_std_mm:7.3} mm
    datum repeatability     : datum+move max residual count  = {datum_repeatability_max_residual_moved}
    datum repeatability     : datum only min quality         = {min_quality_datumed:8.4f}
    datum repeatability     : datum+move min quality         = {min_quality_moved:8.4f}
    datum repeatability     : time/record                    = {time:.16}/{record-count}
    datum repeatability     : git version                    = {git_version}
    datum repeatability     : image algorithm version        = {algorithm_version}"""
)


DAT_REP_RESULT_EXTENDED = cleandoc(
    """
    datum repeatability     : {result},
    datum repeatability     : threshold                      = {pass_threshold_mm:8.4f}
    datum repeatability     : datum only max                 = {datum_repeatability_only_max_mm:7.3} mm
    datum repeatability     : datum only std                 = {datum_repeatability_only_std_mm:7.3} mm
    datum repeatability     : datum only max residual count  = {datum_repeatability_max_residual_datumed}
    datum repeatability     : datum+move max                 = {datum_repeatability_move_max_mm:7.3} mm
    datum repeatability     : datum+move std                 = {datum_repeatability_move_std_mm:7.3} mm
    datum repeatability     : datum+move max residual count  = {datum_repeatability_max_residual_moved}
    datum repeatability     : datum only min quality         = {min_quality_datumed:8.4f}
    datum repeatability     : datum+move min quality         = {min_quality_moved:8.4f}
    datum repeatability     : time/record                    = {time:.16}/{record-count}
    datum repeatability     : git version                    = {git_version}
    datum repeatability     : image algorithm version        = {algorithm_version}"""
)

DAT_REP_RESULT_CSV = cleandoc(
    """
    datum repeatability,{result},
    datum repeatability,threshold,{pass_threshold_mm:8.4f}
    datum repeatability,datum only max,{datum_repeatability_only_max_mm:7.3},mm
    datum repeatability,datum only std,{datum_repeatability_only_std_mm:7.3},mm
    datum repeatability,datum only max residual count,{datum_repeatability_max_residual_datumed[0]},{datum_repeatability_max_residual_datumed[1]}
    datum repeatability,datum+move max,{datum_repeatability_move_max_mm:7.3},mm
    datum repeatability,datum+move std,{datum_repeatability_move_std_mm:7.3},mm
    datum repeatability,datum+move max residual count,{datum_repeatability_max_residual_moved}
    datum repeatability,datum only min quality,{min_quality_datumed:8.4f}
    datum repeatability,datum+move min quality,{min_quality_moved:8.4f}
    datum repeatability,time,{time:.16},record,{record-count}
    datum repeatability,git version,{git_version}
    datum repeatability,image algorithm version,{algorithm_version}"""
)

DAT_REP_ERRMSG = (
    "datum repeatability     : {error_message}, time/record = {time:.16}/{record-count},"
    " version = TBD"
)

DAT_REP_ERRMSG_CSV = (
    "datum repeatability,{error_message},time,{time:.16},record,{record-count},"
    "version,TBD"
)


DAT_REP_IMAGES = "datum repeatability images : {!r}"

DAT_REP_COORDS = "datum repeatability coordinates : {coords}"

DAT_REP_COORDS_CSV = "datum repeatability coordinates,{coords}"
