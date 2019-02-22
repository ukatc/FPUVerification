from __future__ import print_function, division

import time

from vfr.conf import LAMP_WARMING_TIME_MILLISECONDS 

def switch_fibre_backlight(state, manual_lamp_control=False):
    if manual_lamp_control:
        raw_input("switch state of backlight to %r and presse <enter>" % state)
        time.sleep(LAMP_WARMING_TIME_MILLISECONDS / 1000)
    pass

def switch_fibre_backlight_voltage(voltage, manual_lamp_control=False):
    if manual_lamp_control:
        raw_input("switch voltage of backlight to %3.1f and presse <enter>" % voltage)
        time.sleep(LAMP_WARMING_TIME_MILLISECONDS / 1000)
    pass

def switch_ambientlight(state, manual_lamp_control=False):
    if manual_lamp_control:
        raw_input("switch state of ambient light to %r and presse <enter>" % state)
        time.sleep(LAMP_WARMING_TIME_MILLISECONDS / 1000)
    pass

def switch_silhouettelight(state, manual_lamp_control=False):
    if manual_lamp_control:
        raw_input("switch state of silhouette light to %r and presse <enter>" % state)
        time.sleep(LAMP_WARMING_TIME_MILLISECONDS / 1000)
    pass
