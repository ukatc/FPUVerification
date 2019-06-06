from __future__ import absolute_import, division, print_function

import logging
from vfr.task_config import (
    T,
    conditional_dependencies,
    task_dependencies,
    task_expansions,
    USERTASKS,
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


def expand_tasks(tasks, goal, expansion, delete=False):
    logger = logging.getLogger(__name__)
    if goal in tasks:
        logger.debug("[expanding %s to %r] ###" % (goal, expansion))

        if delete:
            logger.trace("deleting %s " % goal)
            tasks.remove(goal)

        tasks.update(expansion)

    return tasks


def resolve(tasks, rigparams, dbe):
    logger = logging.getLogger(__name__)
    tasks = set(tasks)

    fpuset = set(rigparams.measure_fpuset) | set(dbe.eval_fpuset)

    for tsk in tasks:
        if tsk not in USERTASKS:

            raise ValueError("invalid task name '%s'" % tsk)

    while True:

        last_tasks = tasks.copy()
        # check for expansions (replace user shorthands by detailed task breakdown)
        for tsk, expansion in task_expansions:
            tasks = expand_tasks(tasks, tsk, expansion, delete=True)

        # add dependencies (add tasks required to do a test)
        for tsk, expansion in task_dependencies:
            tasks = expand_tasks(tasks, tsk, expansion)

        # add conditional dependencies (add tests which need to be passed before,
        # and are not already passed by all FPUs)
        for tsk, testfun, cond_expansion in conditional_dependencies:
            if tsk in tasks:
                tfun = lambda fpu_id: testfun(dbe, fpu_id)
                if (not all_true(tfun, fpuset)) or rigparams.opts.repeat_passed_tests:
                    tasks = expand_tasks(tasks, tsk, cond_expansion, delete=True)

        # check for equality with last iteration
        # -- if equal, expansion is finished
        logger.debug("tasks = %r" % tasks)
        if tasks == last_tasks:
            break

    logger.info("resolved tasks = %r" % tasks)
    return tasks
