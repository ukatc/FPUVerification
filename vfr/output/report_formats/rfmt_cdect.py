# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function

CDECT_RESULT_NA = "beta collision  test      : n/a"

CDECT_RESULT_TERSE = (
    "collision detection     : result ="
    " {result} ({diagnostic}), time/record = {time:.16}/{record-count}"
)

CDECT_RESULT_COMPLETE = (
    "collision detection     : result ="
    " {result} @ {val:+8.4f} ({diagnostic}), time/record = {time:.16}/{record-count}"
)

CDECT_RESULT_LONG = CDECT_RESULT_COMPLETE

CDECT_RESULT_EXTENDED = CDECT_RESULT_LONG

CDECT_RESULT_NA_CSV = "beta collision  test,n/a"
CDECT_RESULT_CSV = (
    "collision detection,result,"
    "{val:+8.4f},{diagnostic},time/record,{time:.16},{record-count}"
)


LIMIT_RESULT_NA = "limit test {limit_name:9.9}      : n/a"

LIMIT_RESULT_TERSE = (
    "limit test              : {limit_name:9.9s} = {result}, "
    "limit = {val:+8.4f} ({diagnostic}), time/record = {time:.16}/{record-count}"
)

LIMIT_RESULT_COMPLETE = LIMIT_RESULT_TERSE

LIMIT_RESULT_LONG = LIMIT_RESULT_COMPLETE

LIMIT_RESULT_EXTENDED = LIMIT_RESULT_LONG

LIMIT_RESULT_NA_CSV = "limit test,{limit_name:9.9},n/a"

LIMIT_RESULT_CSV = (
    "limit test,{limit_name:9.9s},{result},"
    "limit,{val:+8.4f},{diagnostic},time,{time:.16},record,{record-count}"
)
