from __future__ import absolute_import, division, print_function

from vfr.task_config import (
    T,
    conditional_dependencies,
    task_dependencies,
    task_expansions,
    usertasks,
)

assert T


def set_empty(set1):
    return len(set1) == 0


def all_true(testfun, sequence):
    passed = True
    for item in sequence:
        if not testfun(item):
            passed = False
            break

    return passed


def expand_tasks(tasks, goal, expansion, delete=False, verbosity=0):
    if goal in tasks:
        if verbosity > 2:
            print("[expanding %s to %r] ###" % (goal, expansion))

        if delete:
            print("deleting %s " % goal)
            tasks.remove(goal)

        tasks.update(expansion)

    return tasks


def resolve(tasks, rig, dbe):
    tasks = set(tasks)

    fpuset = set(rig.measure_fpuset) | set(dbe.eval_fpuset)

    for tsk in tasks:
        if tsk not in usertasks:

            raise ValueError("invalid task name '%s'" % tsk)

    verbosity = rig.opts.verbosity
    while True:

        last_tasks = tasks.copy()
        # check for expansions (replace user shorthands by detailed task breakdown)
        for tsk, expansion in task_expansions:
            tasks = expand_tasks(
                tasks, tsk, expansion, delete=True, verbosity=verbosity
            )

        # add dependencies (add tasks required to do a test)
        for tsk, expansion in task_dependencies:
            tasks = expand_tasks(tasks, tsk, expansion, verbosity=verbosity)

        # add conditional dependencies (add tests which need to be passed before,
        # and are not already passed by all FPUs)
        for tsk, testfun, cond_expansion in conditional_dependencies:
            if tsk in tasks:
                tfun = lambda fpu_id: testfun(dbe, fpu_id)
                if (not all_true(tfun, fpuset)) or rig.opts.repeat_passed_tests:
                    tasks = expand_tasks(
                        tasks, tsk, cond_expansion, delete=True, verbosity=verbosity
                    )

        # check for equality with last iteration
        # -- if equal, expansion is finished
        if verbosity > 4:
            print("tasks = ", tasks)
        if tasks == last_tasks:
            break

    return tasks
