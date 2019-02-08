from __future__ import print_function, division

import argparse

from fpu_constants import *

from vfr.conf import DEFAULT_TASKS


def parse_args():
    parser = argparse.ArgumentParser(description='test FPUs in verification rig')
    
    parser.add_argument('tasks',  nargs='+',
                        default=DEFAULT_TASKS, 
                        help="""list of tasks to perform (default: %(default)s)""")
    
    parser.add_argument('-f', '--setup-file',   default="fpus.cfg", type=str,
                        help='FPU configuration')

    parser.add_argument('-m', '--mockup',   default=False, action='store_true',
                        help='set gateway address to use mock-up gateway and FPU')

    parser.add_argument('-r', '--resetFPUs',   default=False, action='store_true',
                        help='reset all FPUs so that earlier aborts / collisions are ignored')

    parser.add_argument('-ra', '--alwaysResetFPUs',   default=False, action='store_true',
                        help='reset FPUs between each step of functional tests so that previous aborts / collisions are ignored')

    parser.add_argument('-R', '--re-initialize',   default=False, action='store_true',
                        help='re-initialize FPU counters even if entry exists')

    parser.add_argument('-s', '--reuse-serialnum', default=False, action='store_true',
                        help='reuse serial number')

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
    
    if args.mockup:
        args.gateway_address = "127.0.0.1"
        args.gateway_port = 4700

    return args
