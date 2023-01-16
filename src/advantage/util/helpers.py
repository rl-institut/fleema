"""This script includes general functions unrelated to any classes.

Functions
-------
deep_update

"""
import collections.abc
import os
import sys


# see https://stackoverflow.com/questions/8391411/how-to-block-calls-to-print
# decorator used to block function printing to the console
def block_printing(func):
    def func_wrapper(*args, **kwargs):
        # block all printing to the console
        sys.stdout = open(os.devnull, "w")
        # call the method in question
        value = func(*args, **kwargs)
        # enable all printing to the console
        sys.stdout = sys.__stdout__
        # pass the return value of the method back
        return value

    return func_wrapper


def deep_update(source, overrides):
    """Update a nested dictionary or similar mapping.

    Modify ``source`` in place through recursion so only a key with its single value gets overwritten
    and not a nested dictionary.

    Parameters
    ----------
    source : dict
        Dictionary that receives the contents of overrides.
    overrides : dict
        Dictionary that writes its content into the source.

    Returns
    -------
    dict
        Updated Source.

    """
    for key, value in overrides.items():
        if isinstance(value, collections.abc.Mapping) and value:
            returned = deep_update(source.get(key, {}), value)
            source[key] = returned
        else:
            source[key] = overrides[key]
    return source
