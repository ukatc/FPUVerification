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


def expand_tasks(tasks, goal, expansion, delete=False):
    if goal in tasks:
        print("[expanding %s to %r] ###" % (goal, expansion))

        if delete:
            print("deleting %s " % goal)
            tasks.remove(goal)

        tasks.update(expansion)

    return tasks


def resolve(tasks, ctx):
    tasks = set(tasks)

    fpuset = set(ctx.measure_fpuset) | set(ctx.eval_fpuset)

    for tsk in tasks:
        if tsk not in usertasks:

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
                tfun = lambda fpu_id: testfun(ctx, fpu_id)
                if (not all_true(tfun, fpuset)) or ctx.opts.repeat_passed_tests:
                    tasks = expand_tasks(tasks, tsk, cond_expansion, delete=True)

        # check for equality with last iteration
        # -- if equal, expansion is finished
        print("tasks = ", tasks)
        if tasks == last_tasks:
            break

    return tasks
