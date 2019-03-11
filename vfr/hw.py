from __future__ import print_function, division


"""this module simply bundles all real hardware access functions
so that they can be easily swapped out by mock-up functions."""


from Lamps.lctrl import ( switch_fibre_backlight,
                          switch_ambientlight,
                          use_ambientlight,
                          switch_fibre_backlight_voltage,
                          switch_silhouettelight,
                          use_silhouettelight,
                          use_backlight)

from GigE.GigECamera import GigECamera

import pyAPT




def safe_home_turntable(gd, grid_state):
    gd.findDatum(grid_state, timeout=DATUM_TIMEOUT_DISABLE)
    
    with pyAPT.NR360S(serial_number=NR360_SERIALNUMBER) as con:
        print('\tHoming stage...', end=' ')
        con.home(clockwise=True)
        print('homed')

def turntable_safe_goto(gd, grid_state, stage_position):
    gd.findDatum(grid_state)
    with pyAPT.NR360S(serial_number=NR360_SERIALNUMBER) as con:
        print('Found APT controller S/N', NR360_SERIALNUMBER)
        con.goto(stage_position, wait=True)
        print('\tNew position: %.2fmm %s'%(con.position(), con.unit))
        print('\tStatus:',con.status())
        
def home_linear_stage():    
    with pyAPT.MTS50(serial_number=MTS50_SERIALNUMBER) as con:
        print('\tHoming linear stage...', end=' ')
        con.home(clockwise=True)
        print('homed')

def linear_stage_goto(stage_position):
    with pyAPT.MTS50(serial_number=MTS50_SERIALNUMBER) as con:
        print('Found APT controller S/N', MTS_SERIALNUMBER)
        con.goto(stage_position, wait=True)
        print('\tNew position: %.2fmm %s'%(con.position(), con.unit))
        print('\tStatus:',con.status())
        
