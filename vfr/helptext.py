from __future__ import absolute_import, division, print_function

from inspect import cleandoc

summary = cleandoc(
    """
    Test FPUs in verification rig, and evaluate tests.

    The program performs a set of measurements and evaluations on
    FPUs. Which measurements and evaluations are done, is defined by the
    "tasks" command line arguments. Tasks can represent bundles of
    activities, or can identify specific individual steps which can be
    repeated.

    Measurements access the FPUs physically. For these, the serial
    numbers of FPUs in relation to their logical ID in the EtherCAN
    driver are defined in a configuration file. The logical id is one
    less than the CAN ID configured by the DIP switch. The result of
    each measurement is stored in the database, regardless whether its
    evaluation is carried immediately now or later.

    By default, the evaluations are carried out on all measured FPUs, but
    it is possible to define a subset of present FPUs, or to re-evaluate
    previous measurements, by passing the desired serial numbers.

    It is important to understand that all measured data is associated
    with an FPUs serial number. This means that losing the serial number
    equals loss of the verification and calibration data. Care should
    be taken that serial numbers are not accidentally overwritten.
    Data in the database is never deleted, but always appended to. This
    includes repeated measurements.

    A third type of task is the {TASK_REPORT!r} task, which by default prints a
    terse summary of the evaluated results.

    The tasks which are carried out by default are the following:

    {DEFAULT_TASKS!r}

    CONFIGURATION FILE
    ==================

    The configuration file is an ASCII file which associates
    logical FPU IDs as used in the EtherCAN interface with
    a serial number. On initialization, the serial number is
    flashed on the FPU, and all captured data is associated with
    the serial number. The configuration file also contains
    the initial position of each FPU with which the protection
    database is initialized. The file content is a Python data structure
    which looks, for example, like this:

        [
        {{ 'serialnumber' : 'MP010', 'fpu_id' : 0, 'pos' : (-180, 0) }}
        {{ 'serialnumber' : 'MP001', 'fpu_id' : 1, 'pos' : (-180, 3.2) }}
        {{ 'serialnumber' : 'MP002', 'fpu_id' : 2, 'pos' : (-180, 0) }} ,
        {{ 'serialnumber' : 'MP003', 'fpu_id' : 3, 'pos' : (-180, 0) }}
        {{ 'serialnumber' : 'MP004', 'fpu_id' : 4, 'pos' : (-180, 0) }}
        {{ 'serialnumber' : 'MP005', 'fpu_id' : 5, 'pos' : (-180, 0) }}
        ]

    The structure is a list of dictionaries, one for each FPU. Each
    entry has the serial number under the key "serialnumber", the
    logical FPU id under the key "fpu_id", and the initial (alpha, beta)
    coordinates under the key "pos".

    OVERVIEW ON TASKS & OPERATIONS:
    ===============================

    1) INITIALIZATION & SET-UP
    --------------------------


    {TST_INITPOS!r:<20}  - Initialize the position database with the position
                            given in the initialization config file.
                            This task should only be done once.

    {TST_FLASH!r:<20}  - flash the serial numbers given in the initialization
                            config file to the FPUs according to the
                            given logical FPU ids.
                            Note that re-using a serial number will fail unless
                            the command line option "reuse-sn" is explicitly
                            passed. This is a safety measure to prevent overwriting
                            and destroying existing test data.

    {TST_INIT!r:<20}  - Initialize the position database _and_ flash the FPUs.

    {TST_GATEWAY_CONNECTION!r:<20}  - test connection to EtherCAN gateway (and,
                            implicitly, to the Ethernet switch).


    2) FUNCTIONAL TESTS
    -------------------

    {TASK_REWIND_FPUS!r:<20}  - rewind FPUs to position which is safe for datum scan

    {TASK_RESET_FPUS!r:<20}  - reset FPUs to clear any error state. This does not
                               clear the recorded position.

    {TST_DATUM!r:<20}  - test functionality of datum operation, and store result

    {TST_FUNCTIONAL!r:<20}  - perform all functional tests

    {TST_COLLDETECT!r:<20}  - test collision detection

    {TST_LIMITS!r:<20}  - test limit switch functionality

    {TST_LIMITS_ALPHA!r:<20}  - test limit switch functionality, alpha switches only
    {TST_LIMITS_BETA!r:<20}  - test limit switch functionality, beta switch only

    {TST_ALPHA_MAX!r:<20}  - search alpha max limit
    {TST_ALPHA_MIN!r:<20}  - search alpha min limit
    {TST_BETA_MAX!r:<20}  - search beta max limit
    {TST_BETA_MIN!r:<20}  - search beta min limit

    {TASK_SELFTEST!r:<20}  - self-test of verification rig (including fibre backlight illumination)

    {TASK_SELFTEST_NONFIBRE!r:<20}  - self-test of rig (without fibre)

    {TASK_REFERENCE!r:<20}  - move FPUs to datum position


    3) FPU CONFORMANCE TESTS AND MEASUREMENTS
    -----------------------------------------


    3a) TEST AND EVALUATION
    .......................

    {TST_DATUM_REP!r:<20}  - test datum repeatability

    {TST_MET_CAL!r:<20}  - test metrology calibration

    {TST_MET_HEIGHT!r:<20}  - measure and evaluate metrology height

    {TST_POS_REP!r:<20}  - test positional repeatability

    {TST_POS_VER!r:<20}  - perform positional verification tests

    {TST_PUP_ALGN!r:<20}  - perform pupil alignment tests


    3b) MEASUREMENT ALONE
    .....................

    These tests perform measurements on the hardware, while
    the image analysis and evaluation steps can be done later.

    {MEASURE_DATUM_REP!r:<20}  - measure, but don't evaluate datum
                            repeatability

    {MEASURE_MET_CAL!r:<20}  - measure, but don't evaluate metrology ca;ibration

    {MEASURE_MET_HEIGHT!r:<20}  - measure, but don't evaluate metrology height

    {MEASURE_POS_REP!r:<20}  - measure, but don't evaluate positional repeatability

    {MEASURE_POS_VER!r:<20}  - measure, but don't evaluate positional
                            verification. Note that this implicitly
                            requires to evaluate the positional repeatability.

    {MEASURE_PUP_ALGN!r:<20}  - measure, but don't evaluate pupil alignment

    {TASK_MEASURE_ALL!r:<20}  - measure everything, but don't evaluate specifications

    {TASK_MEASURE_NONFIBRE!r:<20}  - perform all measurements except those involving fibres


    3c) TIDYING UP

    {TASK_HOME_TURNTABLE!r:<20}  - move turntable to home position

    3d) EVALUATION ALONE
    ....................

    These evaluations operate on stored data and can be done
    without the hardware being present. They are provided
    so that it is possible to update and redo evaluations.

    {EVAL_DATUM_REP!r:<20}  - evaluate datum repeatability
    {EVAL_MET_CAL!r:<20}  - evaluate metrology calibration
    {EVAL_MET_HEIGHT!r:<20}  - evaluate metrology height
    {EVAL_POS_REP!r:<20}  - evaluate positional repeatability
    {EVAL_POS_VER!r:<20}  - evaluate positional verification
    {EVAL_PUP_ALGN!r:<20}  - evaluate pupil alignment
    {TASK_EVAL_ALL!r:<20}  - evaluate all measurements again (for example,
                            after code updates)
    {TASK_EVAL_NONFIBRE!r:<20}  - evaluate all non-fibre measurements



    4) RESULTS
    ----------

    {TASK_REPORT!r:<20}  - report results of all performed tests
    {TASK_DUMP!r:<20}  - dump content of last database entry for
                            each FPU and test



    ..................................................................
    """
)


examples = cleandoc(
    """
    -----------------------------------------------------------------




    Examples
    ========

    we assume we have a file name "fpus_batch1.cfg" with the content:

      ...........................................................
      [
      {{ 'serialnumber' : 'MP010', 'fpu_id' : 0, 'pos' : (-180, 0) }},
      {{ 'serialnumber' : 'MP001', 'fpu_id' : 1, 'pos' : (-180, 3.2) }},
      {{ 'serialnumber' : 'MP002', 'fpu_id' : 2, 'pos' : (-180, 0) }}  ,
      {{ 'serialnumber' : 'MP003', 'fpu_id' : 3, 'pos' : (-180, 0) }},
      {{ 'serialnumber' : 'MP004', 'fpu_id' : 4, 'pos' : (-180, 0) }},
      {{ 'serialnumber' : 'MP005', 'fpu_id' : 5, 'pos' : (-180, 0) }},
      ]
      ...........................................................

    The command

      ./vfrig {TASK_SELFTEST}

    will perform the self-test of the verification rig; "selftest_nonfibre"
    will test only the functions which do not need fibres to be present.

    The command

      ./vfrig -f fpus_batch1.cfg {TST_INITPOS} {TST_FLASH}

    will initialize the FPU by flashing the firmware with the serial numbers,
    and initializing the position database to the positions in the
    above config file.

    The command

      ./vfrig -f fpus_batch1.cfg {TST_INIT} {TST_FUNCTIONAL}

    will to the above, and also perform the functional tests.


    The command

      ./vfrig -f fpus_batch1.cfg

    will perform all the configured default tests, unless the functional
    tests fail, and print out a report on the result.


    This command:

    ./vfrig -f fpus_batch1.cfg   -S"['MP010']" {TST_DATUM_REP}


    will perform the datum repeatability test for the FPU with serial number 'MP010',
    and any tests which are required to do it.


    STOPPING THE HARDWARE
    ---------------------

    There are two key combinations to stop a running measurement:

    <Ctrl>-<\>   "QUIT" This key combination sends a Unix QUIT signal to the process,
                  which has the effect to exit the program when any ongoing
                  movement is finished, and before the next movement is started.
                  The turntable will be re-wound to its initial position.
                  Any measurement data which was not saved as this point is lost.
                  Data in the database will remain consistent.

                  This key combination should be used if a the measurement
                  process needs to be orderly stopped, the rig inspected,
                  or similar.

    <Ctrl>-<C>   "SIGINT" This key combination generates a Unix INTERRUPT signal.
                 When the Thorlabs stages are moving, the stages are stopped.
                 When FPUs are moving, the FPUs are sent an ABORT message,
                 which usually will immediately stop them.
                 After this, the program exits. If Python was started
                 interactively, the running script will be aborted, and
                 the interpreter will return to the command line.

                 Note that FPUs in ABORTED state need to execute a reset command
                 before they can be moved again, for safety reasons.

                 This key combination should only be used in an emergency
                 situation, if there is any ongoing hardware damage or
                 immediate danger of such damage. Note that the ABORT command
                 can reduce the precision of the FPU, because it can cause
                 a very sudden stop.

                 Data in the database will remain consistent.


    ENVIRONMENT
    -----------

    the following environment variables are evaluated:

    - VERIFICATION_ROOT_FOLDER   - This environment variable points to the image database and
                                   calibration data. It needs to be set if one tries to
                                   evaluate measurements on a different computer, and
                                   the path of that data is different from
                                   /moonsdata/verification.


   - VFR_LOGLEVEL                - This variable contains the numerical log level for
                                   messages which are logged to the console. The levels
                                   are as documented for the python logging module, in
                                   https://docs.python.org/2/library/logging.html?highlight=logging#levels .
                                   The default value is 30, which will log messages with
                                   level "INFO" or higher. The capability to change the level
                                   is primarily intended for development and debugging purposes,
                                   not for normal use.


    """
)
