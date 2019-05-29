# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function

from argparse import Namespace

from vfr.db.colldect_limits import get_angular_limit
from vfr.db.datum import get_datum_result
from vfr.db.datum_repeatability import (
    get_datum_repeatability_images,
    get_datum_repeatability_result,
)
from vfr.db.metrology_calibration import (
    get_metrology_calibration_images,
    get_metrology_calibration_result,
)
from vfr.db.metrology_height import (
    get_metrology_height_images,
    get_metrology_height_result,
)
from vfr.db.positional_repeatability import (
    get_positional_repeatability_images,
    get_positional_repeatability_result,
)
from vfr.db.positional_verification import (
    get_positional_verification_images,
    get_positional_verification_result,
)
from vfr.db.pupil_alignment import (
    get_pupil_alignment_images,
    get_pupil_alignment_result,
)


def get_data(dbe, fpu_id):
    serial_number = dbe.fpu_config[fpu_id]["serialnumber"]
    count = dbe.opts.record_count

    data = Namespace(
        serial_number=serial_number,
        datum_result=get_datum_result(dbe, fpu_id, count=count),
        alpha_min_result=get_angular_limit(dbe, fpu_id, "alpha_min", count=count),
        alpha_max_result=get_angular_limit(dbe, fpu_id, "alpha_max", count=count),
        beta_min_result=get_angular_limit(dbe, fpu_id, "beta_min", count=count),
        beta_max_result=get_angular_limit(dbe, fpu_id, "beta_max", count=count),
        beta_collision_result=get_angular_limit(
            dbe, fpu_id, "beta_collision", count=count
        ),
        datum_repeatability_result=get_datum_repeatability_result(
            dbe, fpu_id, count=count
        ),
        datum_repeatability_images=get_datum_repeatability_images(
            dbe, fpu_id, count=count
        ),
        metrology_calibration_result=get_metrology_calibration_result(
            dbe, fpu_id, count=count
        ),
        metrology_calibration_images=get_metrology_calibration_images(
            dbe, fpu_id, count=count
        ),
        metrology_height_result=get_metrology_height_result(dbe, fpu_id, count=count),
        metrology_height_images=get_metrology_height_images(dbe, fpu_id, count=count),
        positional_repeatability_result=get_positional_repeatability_result(
            dbe, fpu_id, count=count
        ),
        positional_repeatability_images=get_positional_repeatability_images(
            dbe, fpu_id, count=count
        ),
        positional_verification_result=get_positional_verification_result(
            dbe, fpu_id, count=count
        ),
        positional_verification_images=get_positional_verification_images(
            dbe, fpu_id, count=count
        ),
        pupil_alignment_result=get_pupil_alignment_result(dbe, fpu_id, count=count),
        pupil_alignment_images=get_pupil_alignment_images(dbe, fpu_id, count=count),
    )

    return data
