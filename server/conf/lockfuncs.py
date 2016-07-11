"""

Lockfuncs

Lock functions are functions available when defining lock strings,
which in turn limits access to various game systems.

All functions defined globally in this module are assumed to be
available for use in lockstrings to determine access. See the
Evennia documentation for more info on locks.

A lock function is always called with two arguments, accessing_obj and
accessed_obj, followed by any number of arguments. All possible
arguments should be handled with *args, **kwargs. The lock function
should handle all eventual tracebacks by logging the error and
returning False.

Lock functions in this module extend (and will overload same-named)
lock functions from evennia.locks.lockfuncs.

"""

def tellfalse(accessing_obj, accessed_obj, *args, **kwargs):
    """
    called in lockstring with tellfalse().
    A simple logger that always returns false. Prints to stdout
    for simplicity, should use utils.logger for real operation.
    """
    print "%s tried to access %s. Access denied." % (accessing_obj, accessed_obj)
    return False

from random import *

def half(accessing_obj, accessed_obj, *args, **kwargs):
    if random() > 0.5:
	return False
    return True

def on_path(accessing_obj, accessed_obj, *args, **kwargs):
    """
    called in lockstring with on_path() and returns False
    when accessing_obj is on a path (inside an exit).
    """
    if accessing_obj.location == None:
        return True # Nowhere is not on a path.
    destination = accessing_obj.location.destination
    return False if destination == None else True

def on_exit(accessing_obj, accessed_obj, *args, **kwargs):
    """
    called in lockstring with on_exit() and returns True
    only when accessing_obj is on an exit within the room.
    """
    location = accessing_obj.location
    reached = accessing_obj.db.reached
    print("args=%s, reached=%s, in location=%s" % (args[0], reached, location))

    if not location or not reached:
        return False # Nowhere is not on an path.
    else:
        if args:
            return True if args[0] in accessing_obj.db.reached else False
        else:
            return False

def no_back(accessing_obj, accessed_obj, *args, **kwargs):
    """
    called in lockstring with no_back() and returns True
    when accessing_obj unable to go back. (May be a trap!)
    """
    return False

def no_home(accessing_obj, accessed_obj, *args, **kwargs):
    """
    called in lockstring with no_home() and returns False
    when accessing_obj unable to go home. (May already be home)
    """
    return True

def roll(accessing_obj, accessed_obj, *args, **kwargs):
    return True if args else False