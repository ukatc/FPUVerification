from __future__ import print_function, division

import argparse
import sys
from os import environ

from ast import literal_eval

from fpu_constants import *

from vfr.conf import ( DEFAULT_TASKS,
                       TST_GATEWAY_CONNECTION, 
                       TST_CAN_CONNECTION,     
                       TST_DATUM,              
                       TST_ALPHA_MIN,          
                       TST_ALPHA_MAX,
                       TST_BETA_MAX,           
                       TST_BETA_MIN,
                       TST_FUNCTIONAL,
                       TST_INIT,
                       TST_FLASH,
                       TST_INITPOS,
                       TST_DATUM_REP,
                       TST_LIMITS)

from vfr.tasks import *

from helptext import summary

def parse_args():
    try:
        DEFAULT_VERBOSITY = int(environ.get("VFR_VERBOSITY", "0"))
    except:
        print("VFR_VERBOSITY has invalid value, setting verbosity to one")
        DEFAULT_VERBOSITY = 1
                                     
    parser = argparse.ArgumentParser(description='test FPUs in verification rig', description=summary)
    
    parser.add_argument('tasks',  nargs='*',
                        default=DEFAULT_TASKS, 
                        help="""list of tasks to perform (default: %(default)s)""")
    
    parser.add_argument('-f', '--setup-file',   default="fpus_batch0.cfg", type=str,
                        help='set FPU flashing and measurement configuration file')
    
    parser.add_argument('-F', '--report-format',   default="terse", choices=['terse', 'long', 'extensive']
                        help="output format of 'report' task (one of 'terse', 'long', 'extensive', default is 'terse')")

    parser.add_argument('-m', '--mockup',   default=False, action='store_true',
                        help='set gateway address to use mock-up gateway and FPU')

    parser.add_argument('-M', '--manual-lamp-control',   default=False, action='store_true',
                        help='switch to manual lamp control')

    parser.add_argument('-r', '--resetFPUs',   default=False, action='store_true',
                        help='reset all FPUs so that earlier aborts / collisions are ignored')

    parser.add_argument('-ra', '--alwaysResetFPUs',   default=False, action='store_true',
                        help='reset FPUs between each step of functional tests so that previous aborts / collisions are ignored')

    parser.add_argument('-R', '--re-initialize',   default=False, action='store_true',
                        help='re-initialize FPU counters even if entry exists')

    parser.add_argument('-S', '--snset', default=None, 
                        help="""apply tasks only to passed set of serial numbers, passed as "['MP001', 'MP002', ...]" """)
    
    parser.add_argument('-o', '--output-file', default=None, type=str,
                        help='output file for report and dump (defaults to stdout)')

    parser.add_argument('-s', '--reuse-serialnum', default=False, action='store_true',
                        help='reuse serial number')
    
    parser.add_argument('-p', '--repeat-passed-tests', default=False, action='store_true',
                        help='repeat tests which were already passed successfully')

    parser.add_argument('-u', '--update-protection-limits', default=False, action='store_true',
                        help='update range limits to protection database, even if already set')    

    parser.add_argument('-t', '--protection-tolerance',  type=float, default=0.2,
                        help='tolerance used when deriving protection limits from empirical range (default: %(default)s).')
    
    parser.add_argument('-i', '--reinit-db', default=False, action='store_true',
                        help='reinitialize posiiton database entry')

    parser.add_argument('-w', '--rewind_fpus', default=False, action='store_true',
                        help='rewind FPUs to datum position at start')

    parser.add_argument('-p', '--gateway_port', metavar='GATEWAY_PORT', type=int, default=4700,
                        help='EtherCAN gateway port number (default: %(default)s)')

    parser.add_argument('-a', '--gateway_address', metavar='GATEWAY_ADDRESS', type=str, default="192.168.0.10",
                        help='EtherCAN gateway IP address or hostname (default: %(default)r)')
    
    parser.add_argument('-N', '--NUM_FPUS',  metavar='NUM_FPUS', dest='N', type=int, default=6,
                        help='Number of adressed FPUs (default: %(default)s).')    
        
    parser.add_argument('-D', '--bus-repeat-dummy-delay',  metavar='BUS_REPEAT_DUMMY_DELAY',
                        type=int, default=2,
                        help='Dummy delay inserted before writing to the same bus (default: %(default)s).')        
            
    parser.add_argument('--alpha_min', metavar='ALPHA_MIN', type=float, default=ALPHA_MIN_DEGREE,
                        help='minimum alpha value  (default: %(default)s)')
    
    parser.add_argument('--alpha_max', metavar='ALPHA_MAX', type=float, default=ALPHA_MAX_DEGREE,
                        help='maximum alpha value  (default: %(default)s)')
    
    parser.add_argument('--beta_min', metavar='BETA_MIN', type=float, default=BETA_MIN_DEGREE,
                        help='minimum beta value  (default: %(default)s)')
    
    parser.add_argument('--beta_max', metavar='BETA_MAX', type=float, default=BETA_MAX_DEGREE,
                        help='maximum beta value  (default: %(default)s)')        

    parser.add_argument('-v', '--verbosity', metavar='VERBOSITY', type=int,
                        default=3,
                        help='verbosity level of progress messages (default: %(default)s)')
    
    
    args = parser.parse_args()

    if len(args.tasks) == 0:
        args.tasks = DEFAULT_TASKS
    
    if args.mockup:
        args.gateway_address = "127.0.0.1"
        args.gateway_port = 4700

    if not (args.fpuset is None):
        args.fpuset = literal_eval(args.fpuset)

    if args.output_file is None:
        args.output_file = sys.stdout
    else:
        args.output_file = open(args,output_file, "w")
        
    return args
