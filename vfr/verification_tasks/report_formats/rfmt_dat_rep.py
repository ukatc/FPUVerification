# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function

from inspect import cleandoc

DAT_REP_NA = "datum repeatability       : n/a"

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

DAT_REP_ERRMSG = (
    "Datum repeatability     : {error_message}, time/record = {time:.16}/{record-count},"
    " version = TBD"
)


DAT_REP_IMAGES = "datum repetability images : {!r}"
