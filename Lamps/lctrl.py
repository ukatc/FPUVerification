from __future__ import print_function, division
from contextlib import contextmanager

import time

from vfr.conf import LAMP_WARMING_TIME_MILLISECONDS


# here a nice explanation how the context managers work:
# https://jeffknupp.com/blog/2016/03/07/python-with-context-managers/


def switch_fibre_backlight(state, manual_lamp_control=False):
    if manual_lamp_control:
        raw_input("switch state of backlight to %r and presse <enter>" % state)
        time.sleep(float(LAMP_WARMING_TIME_MILLISECONDS) / 1000)
    pass


def switch_fibre_backlight_voltage(voltage, manual_lamp_control=False):
    if manual_lamp_control:
        raw_input("switch voltage of backlight to %3.1f and presse <enter>" % voltage)
        time.sleep(float(LAMP_WARMING_TIME_MILLISECONDS) / 1000)
    pass


def switch_ambientlight(state, manual_lamp_control=False):
    if manual_lamp_control:
        raw_input("switch state of ambient light to %r and presse <enter>" % state)
    pass


def switch_silhouettelight(state, manual_lamp_control=False):
    if manual_lamp_control:
        raw_input("switch state of silhouette light to %r and presse <enter>" % state)
        time.sleep(float(LAMP_WARMING_TIME_MILLISECONDS) / 1000)
    pass


@contextmanager
def use_silhouettelight(manual_lamp_control=False):
    switch_silhouettelight("on", manual_lamp_control=manual_lamp_control)
    time.sleep(float(LAMP_WARMING_TIME_MILLISECONDS) / 1000)
    try:
        yield None

    finally:
        switch_silhouettelight("off", manual_lamp_control=manual_lamp_control)
        time.sleep(float(LAMP_WARMING_TIME_MILLISECONDS) / 1000)


@contextmanager
def use_backlight(voltage, manual_lamp_control=False):
    switch_fibre_backlight_voltage(voltage, manual_lamp_control=manual_lamp_control)
    switch_fibre_backlight("on", manual_lamp_control=manual_lamp_control)
    time.sleep(float(LAMP_WARMING_TIME_MILLISECONDS) / 1000)
    try:
        yield None

    finally:
        switch_fibre_backlight("off", manual_lamp_control=manual_lamp_control)
        time.sleep(float(LAMP_WARMING_TIME_MILLISECONDS) / 1000)


@contextmanager
def use_ambientlight(manual_lamp_control=False):
    switch_ambientlight("on", manual_lamp_control=manual_lamp_control)
    time.sleep(float(LAMP_WARMING_TIME_MILLISECONDS) / 1000)
    try:
        yield None

    finally:
        switch_ambientlight("off", manual_lamp_control=manual_lamp_control)
        time.sleep(float(LAMP_WARMING_TIME_MILLISECONDS) / 1000)
