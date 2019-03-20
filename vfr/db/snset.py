from __future__ import print_function, division

from ast import literal_eval


KEY = "serial-number-set"


def _get_set(txn, key):
    val = txn.get(KEY)

    if val is None:
        val = "[]"

    existing_serial_numbers = set(literal_eval(val))

    return existing_serial_numbers


def add_sns_to_set(ctx, new_serialnumbers):
    """Adds a serial number to the set of FPUs in the database.

    This is needed so that we can iterate over the records for all
    processed FPUs.

    """
    verbosity = ctx.opts.verbosity

    with ctx.env.begin(write=True, db=ctx.vfdb) as txn:
        existing_serial_numbers = _get_set(txn, KEY)

        new_set = set(new_serialnumbers)
        if not new_set.issubset(existing_serial_numbers):
            existing_serial_numbers.update(new_set)

            # we need to store this as list because
            # literal_eval cannot parse a set (in Python2.7)
            txn.put(KEY, repr(list(existing_serial_numbers)))
            if verbosity > 2:
                print (
                    "db: adding serial numbers %r to set of seen FPUs"
                    % new_serialnumbers
                )


def get_snset(ctx):
    """Gets the set of processed FPU serial numbers from the database.
    """
    verbosity = ctx.opts.verbosity

    with env.begin(db=ctx.vfdb) as txn:
        existing_serial_numbers = _get_set(txn, KEY)

    return existing_serial_numbers
