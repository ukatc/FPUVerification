from __future__ import absolute_import, division, print_function

from argparse import Namespace
from inspect import cleandoc

from vfr.db.colldect_limits import (
    get_anglimit_passed_p,
    get_angular_limit,
    get_colldect_passed_p,
)
from vfr.db.datum import get_datum_passed_p, get_datum_result
from vfr.db.datum_repeatability import (
    get_datum_repeatability_images,
    get_datum_repeatability_passed_p,
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
    get_positional_repeatability_passed_p,
    get_positional_repeatability_result,
)
from vfr.db.positional_verification import (
    get_positional_verification_images,
    get_positional_verification_result,
)
from vfr.db.pupil_alignment import (
    get_pupil_alignment_images,
    get_pupil_alignment_passed_p,
    get_pupil_alignment_result,
)


def get_data(ctx, fpu_id):
    serial_number = ctx.fpu_config[fpu_id]["serialnumber"]
    count=ctx.opts.record_count

    return Namespace(
        serial_number=serial_number,
        datum_result=get_datum_result(ctx, fpu_id, count=count),
        alpha_min_result=get_angular_limit(ctx, fpu_id, "alpha_min", count=count),
        alpha_max_result=get_angular_limit(ctx, fpu_id, "alpha_max", count=count),
        beta_min_result=get_angular_limit(ctx, fpu_id, "beta_min", count=count),
        beta_max_result=get_angular_limit(ctx, fpu_id, "beta_max", count=count),
        beta_collision_result=get_angular_limit(
            ctx, fpu_id, "beta_collision", count=count
        ),
        datum_repeatability_result=get_datum_repeatability_result(
            ctx, fpu_id, count=count
        ),
        datum_repeatability_images=get_datum_repeatability_images(
            ctx, fpu_id, count=count
        ),
        metrology_calibration_result=get_metrology_calibration_result(
            ctx, fpu_id, count=count
        ),
        metrology_calibration_images=get_metrology_calibration_images(
            ctx, fpu_id, count=count
        ),
        metrology_height_result=get_metrology_height_result(ctx, fpu_id, count=count),
        metrology_height_images=get_metrology_height_images(ctx, fpu_id, count=count),
        positional_repeatability_result=get_positional_repeatability_result(
            ctx, fpu_id, count=count
        ),
        positional_repeatability_images=get_positional_repeatability_images(
            ctx, fpu_id, count=count
        ),
        positional_verification_result=get_positional_verification_result(ctx, fpu_id, count=count),
        positional_verification_images=get_positional_verification_images(ctx, fpu_id, count=count),
        pupil_alignment_result=get_pupil_alignment_result(ctx, fpu_id, count=count),
        pupil_alignment_images=get_pupil_alignment_images(ctx, fpu_id, count=count),
        outfile=ctx.opts.output_file,
    )


def print_report_extended(
    serial_number=None,
    datum_result=None,
    alpha_min_result=None,
    alpha_max_result=None,
    beta_min_result=None,
    beta_max_result=None,
    beta_collision_result=None,
    datum_repeatability_result=None,
    metrology_calibration_result=None,
    metrology_height_result=None,
    positional_repeatability_result=None,
    positional_verification_result=None,
    pupil_alignment_result=None,
    datum_repeatability_images=None,
    metrology_calibration_images=None,
    metrology_height_images=None,
    positional_repeatability_images=None,
    positional_verification_images=None,
    pupil_alignment_images=None,
    outfile=None,
):

    print("*" * 60, "file=outfile")
    print("FPU %s" % serial_number, "file=outfile")
    if datum_result is None:
        print("Datum test: n/a", "file=outfile")
    else:
        print(
            cleandoc(
                """
                Datum test: alpha datumed = {datumed[0]}
                Datum test: beta datumed = {datumed[1]}
                Datum test: fpu_id/FPU state = {fpuid} / {result_state}
                Datum test: counter deviations = {counter_deviation!r}
                Datum test: time = {time}
                Datum test: result = {diagnostic}"""
            ).format(**datum_result),
            "file=outfile",
        )

    if beta_collision_result is None:
        print("Beta collision  test: n/a", "file=outfile")
    else:
        print(
            "Collision detection: result ="
            " {result} ({diagnostic}), time = {time}".format(**beta_collision_result),
            "file=outfile",
        )

    if alpha_min_result is None:
        print("Limit test:  alpha min n/a", "file=outfile")
    else:
        print(
            "Limit test: alpha min = {result}, "
            "limit = {val:7.3f} ({diagnostic}), time = {time}".format(
                **alpha_min_result
            ),
            "file=outfile",
        )

    if alpha_max_result is None:
        print("Limit test:  alpha max n/a", "file=outfile")
    else:
        print(
            "Limit test: alpha max = {result}, limit = {val:7.3f}"
            " ({diagnostic}), time = {time}".format(**alpha_max_result),
            "file=outfile",
        )

    if beta_min_result is None:
        print("Limit test: beta min n/a", "file=outfile")
    else:
        print(
            "Limit test: beta min = {result}, limit = {val:7.3} "
            "({diagnostic}), time = {time}".format(**beta_min_result),
            "file=outfile",
        )

    if beta_max_result is None:
        print("Limit test: beta max n/a", "file=outfile")
    else:
        print(
            "Limit test: beta max = {result}, limit = {val:7.3}"
            " ({diagnostic}), time = {time}".format(**beta_max_result),
            "file=outfile",
        )

    if datum_repeatability_result is None:
        print("Datum repeatability: n/a", "file=outfile")
    else:
        err_msg = datum_repeatability_result["error_message"]
        if not err_msg:
            print(
                "Datum repeatability: {result}, delta = {repeatability_millimeter:7.3f} mm, "
                "time = {time}, version = {algorithm_version}".format(
                    **datum_repeatability_result
                ),
                "file=outfile",
            )

            print(
                "Datum repeatability: coords = {coords}".format(
                    **datum_repeatability_result
                ),
                "file=outfile",
            )
        else:
            print(
                "Datum repeatability: {error_message}, time = {time},"
                " version = TBD".format(**datum_repeatability_result),
                "file=outfile",
            )

    if metrology_calibration_result is None:
        print("metrology calibration: n/a", "file=outfile")
    else:
        err_msg = metrology_calibration_result["error_message"]
        if not err_msg:
            print(
                "Metrology calibration:"
                " metcal_fibre_large_target_distance = {metcal_fibre_large_target_distance:7.3f} mm,"
                " metcal_fibre_small_target_distance = {metcal_fibre_small_target_distance:7.3f} mm,"
                " metcal_target_vector_angle = {metcal_target_vector_angle:6.3f} degrees,"
                " time={time}, version = {algorithm_version}".format(
                    **metrology_calibration_result
                ),
                "file=outfile",
            )
        else:
            print(
                "Metrology calibration: {error_message}, time = {time}, "
                "version = {algorithm_version}".format(metrology_calibration_result),
                "file=outfile",
            )

    print("metrology calibration images: {!r}".format(metrology_calibration_images))

    if metrology_height_result is None:
        print("metrology_height: n/a", "file=outfile")
    else:
        err_msg = metrology_height_result["error_message"]
        if not err_msg:
            print(
                "Metrology height: small target = {small_target_height:6.3f},"
                " large target = {small_target_height:6.3f}, "
                "time = {time}, version = {algorithm_version}".format(
                    **metrology_height_result
                ),
                "file=outfile",
            )
            print("metrology height images: {!r}".format(metrology_height_images))
        else:
            print(
                "Metrology height: fibre_distance = {error_message}, time = {time},"
                " version = {algorithm_version}".format(**metrology_height_result),
                "file=outfile",
            )

    if positional_repeatability_result is None:
        print("positional repeatability: n/a", "file=outfile")
    else:
        err_msg = positional_repeatability_result["error_message"]
        if not err_msg:
            print(
                cleandoc(
                    """
                    positional repeatability: passed = {result}, posrep_rss_mm = {posrep_rss_mm:6.2f} mm,
                    positional repeatability:  time = {time}, version = {algorithm_version}
                    Positional repeatability: calibration_pars = {calibration_pars!r}
                    Positional repeatability: analysis_results_alpha = {analysis_results_alpha!r}
                    Positional repeatability: analysis_results_beta = {analysis_results_beta!r}
                    Positional repeatability: gearbox_correction = {gearbox_correction!r}"""
                ).format(**positional_repeatability_result),
                "file=outfile",
            )
            print(
                "positional repeatability images: {!r}".format(
                    positional_repeatability_images
                )
            )
        else:
            print(
                "Positional repeatability: message = {error_message}, time = {time},"
                " version = {algorithm_version}".format(
                    **positional_repeatability_result
                ),
                "file=outfile",
            )

    if positional_verification_result is None:
        print("positional verification: n/a", "file=outfile")
    else:
        err_msg = positional_verification_result["error_message"]
        if not err_msg:
            print(
                cleandoc(
                    """
                    positional verification: passed = {result}, posver_error_max = {posver_error_max:6.3f} mm,
                    positional verification: time = {time}, version = {algorithm_version}
                    Positional verification: calibration_pars = {calibration_pars}
                    Positional verification: analysis_results = {analysis_results}
                    Positional verification: posver_errors = {posver_error}"""
                ).format(**positional_verification_result),
                "file=outfile",
            )
            if "gearbox_correction" not in positional_verification_images:
                positional_verification_images["gearbox_correction"] = None
            print(
                "positional verification images: {images!r}\n"
                "gearbox correction = {gearbox_correction!r}".format(
                    **positional_verification_images
                )
            )
        else:
            print(
                "Positional verification: message = {error_message}, time = {time},"
                " version = {algorithm_version}".format(
                    **positional_verification_result
                ),
                "file=outfile",
            )

    if pupil_alignment_result is None:
        print("pupil_alignment test: n/a", "file=outfile")
    else:
        err_msg = pupil_alignment_result["error_message"]
        if not err_msg:
            print(
                cleandoc(
                    """
                    pupil alignment: passed = %result, measures= {measures}, time = {time}
                    pupil alignment: coords = {coords!r}
                    pupil alignment: calibration_pars = {calibration_pars!r}"""
                ).format(**pupil_alignment_result),
                "file=outfile",
            )
            print("pupil alignment images: {!r}".format(pupil_alignment_images))
        else:
            print(
                "pupil alignment: message = {error_message}, time = {time}".format(
                    **pupil_alignment_result
                ),
                "file=outfile",
            )


def report(ctx):

    report_format = ctx.opts.report_format
    for count, fpu_id in enumerate(ctx.eval_fpuset):
        ddict = vars(get_data(ctx, fpu_id))

        if count > 0:
            print("\n", "file=opts.output_file")

        if report_format == "terse":
            print_report_extended(**ddict)
        elif report_format == "long":
            raise ValueError("option not implemented")
        else:
            print_report_extended(**ddict)


def dump_data(ctx):

    print("{", "file=opts.output_file")
    for count, fpu_id in enumerate(eval_fpuset):
        ddict = vars(get_data(ctx, fpu_id))
        if count > 0:
            print("\n\n", "file=opts.output_file")
        print("%r : %r," % (fpu_id, ddict), "file=opts.output_file")

    print("}", "file=opts.output_file")
