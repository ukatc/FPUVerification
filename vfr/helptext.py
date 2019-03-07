from __future__ import print_function, division

summary="""\ 
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


"""
