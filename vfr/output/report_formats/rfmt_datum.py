# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function

from inspect import cleandoc

DATUM_RESULT_NA = "datum test                : n/a"

DATUM_RESULT_NA_CSV = "datum test,n/a"

DATUM_RESULT_TERSE = cleandoc(
    """
    datum test              : result = {result} / {diagnostic}
    datum test              : alpha datumed = {datumed[0]}
    datum test              : beta datumed = {datumed[1]}
    datum test              : fpu_id/FPU state = {fpu_id} / {result_state}
    datum test              : counter deviations = {counter_deviation!r}
    datum test              : time/record = {time:.16}/{record-count}"""
)

DATUM_RESULT_COMPLETE = DATUM_RESULT_TERSE

DATUM_RESULT_LONG = DATUM_RESULT_COMPLETE

DATUM_RESULT_EXTENDED = DATUM_RESULT_LONG

DATUM_RESULT_CSV = cleandoc(
    """
    datum test,result,{result},diagnostic,{diagnostic}
    datum test,alpha datumed,{datumed[0]}
    datum test,beta datumed,{datumed[1]}
    datum test,fpu_id,{fpu_id},FPU state,{result_state}
    datum test,counter deviations,{counter_deviation[0]!r},{counter_deviation[1]!r}
    datum test,time,{time:.16},record,{record-count}"""
)
