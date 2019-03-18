from __future__ import print_function, division

from inspect import cleandoc


summary = cleandoc(
    """
    Test FPUs in verification rig, and evaluate tests.
    
    The program performs a set of measurements and evaluations on
    FPUs. Which measurements and evaluations are done, is defined by the
    "tasks" command line arguments. Tasks can represent bundles of
    activities, or can identify specific individual steps which can be
    repeated.
    
    Measurements access the FPUs physically. For these, the serial numbers
    of FPUs in relation to their logical ID are defined in a configuration
    file. The result of each measurement is stored in the database,
    regardless whether its evaluation is carried immediately now or later.
    
    By default, the evaluations are carried out on all measured FPUs, but
    it is possible to define a subset of present FPUs, or to re-evaluate
    previous measurements.

    A third type of task is the "report" task, which by default prints a
    terse summary of the evaluated results.
    
    Overview on tasks & operations:
    

    1) INITIALIZATION & SET-UP
    ==========================
    
    {TST_INIT!r:<20}  - Initialize the position database with the position
                            given in the initialization config file.
                            This task should only be done once.

    {TST_FLASH!r:<20}  - flash the serial numbers given in the initialization
                            config file to the FPUs according to the
                            given logical FPU ids. 
                            Note that re-using a serial number will fail unless
                            the command line option "reuse-sn" is explicitly 
                            passed. This is a safety measure to prevent overwriting
                            and destroying existing test data.
    
    {TST_GATEWAY_CONNECTION!r:<20}  - test connection to EtherCAN gateway (and, 
                            implicitly, to the Ethernet switch).


    2) FUNCTIONAL TESTS
    ===================

    {TST_DATUM!r:<20}  - test functionality of datum operation, and store result

    {TST_FUNCTIONAL!r:<20}  - perform all functional tests

    {TST_COLLDETECT!r:<20}  - test collision detection

    {TST_LIMITS!r:<20}  - test limit switch functionality

    {TASK_SELFTEST!r:<20}  - self-test of verification rig (including fibre backlight illumination)

    {TASK_SELFTEST_NONFIBRE!r:<20}  - self-test of rig (without fibre)

    {TASK_REFERENCE!r:<20}  - move FPUs to datum position


    3) FPU CONFORMANCE TESTS AND MEASUREMENTS
    =========================================


    3a) TEST AND EVALUATION
    -----------------------

    {TST_DATUM_REP!r:<20}  - test datum repeatability

    {TST_MET_CAL!r:<20}  - test metrology calibration

    {TST_MET_HEIGHT!r:<20}  - measure and evaluate metrology height

    {TST_POS_REP!r:<20}  - test positional repeatability

    {TST_POS_VER!r:<20}  - perform positional verification tests

    {TST_PUPIL_ALGN!r:<20}  - perform pupil alignment tests


    3b) MEASUREMENT ALONE
    ---------------------

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

    {MEASURE_PUPIL_ALGN!r:<20}  - measure, but don't evaluate pupil alignment

    {MEASURE_ALL!r:<20}  - measure, but don't evaluate all specifications


    3c) EVALUATION ALONE
    --------------------

    These evaluations operate on stored data and can be done 
    without the hardware being present. They are provided
    so that it is possible to update and redo evaluations.

    {EVAL_DATUM_REP!r:<20}  - evaluate datum repeatability
    {EVAL_MET_CAL!r:<20}  - evaluate metrology calibration
    {EVAL_MET_HEIGHT!r:<20}  - evaluate metrology height
    {EVAL_POS_REP!r:<20}  - evaluate positional repeatability
    {EVAL_POS_VER!r:<20}  - evaluate positional verification
    {EVAL_PUPIL_ALGN!r:<20}  - evaluate pupil alignment
    {TASK_EVAL_ALL!r:<20}  - evaluate all measurements again (for example,
                            after code updates)



    4) RESULTS
    ==========

    {TASK_REPORT!r:<20}  - report results of all performed tests
    {TASK_DUMP!r:<20}  - dump content of last database entry for 
                            each FPU and test



    ..................................................................
    """
)
