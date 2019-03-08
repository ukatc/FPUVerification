from __future__ import print_function, division


"""this module simply bundles all real hardware access functions
so that they can be easily swapped out by mock-up functions."""

from vfr.tests_common import safe_home_turntable, turntable_safe_goto

from Lamps.lctrl import ( switch_fibre_backlight,
                          switch_ambientlight,
                          use_ambientlight,
                          switch_fibre_backlight_voltage,
                          switch_silhouettelight,
                          use_silhouettelight,
                          use_backlight)

from GigE.GigECamera import GigECamera
