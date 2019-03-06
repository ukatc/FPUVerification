from __future__ import print_function, division

from ast import literal_eval


KEY = "serial-number-set"


def _get_set(txn, key):
    val = txn.get(KEY)
        
    if val is None:
        val = "[]"
        
    existing_serial_numbers = set(literal_eval(val))
    

def  add_sns_to_set(env, vfdb, new_serialnumbers, verbosity=0):
    """Adds a serial number to the set of FPUs in the database.

    This is needed so that we can iterate over the records for all
    processed FPUs.

    """
    with env.begin(write=True, db=vfdb) as txn:
        existing_serial_numbers = _get_set(txn, KEY)

        new_set = set(new_serialnumbers)
        if not new_set.issubset(existing_serial_numbers):
            existing_serial_numbers.update(new_set)

            # we need to store this as list because
            # literal_eval cannot parse a set (in Python2.7)
            txn.put(KEY, repr(list(existing_serial_numbers)))
            if verbosity > 2:
                print("db: adding serial numbers %r to set of seen FPUs" % new_serialnumbers)
        
        
            
def  get_snset(env, vfdb, verbosity=0):
    """Gets the set of processed FPU serial numbers from the database.
    """
    with env.begin(db=vfdb) as txn:
        existing_serial_numbers = _get_set(txn, KEY)
        
    return existing_serial_numbers

