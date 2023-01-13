"""This script includes general functions unrelated to any classes.

Functions
-------
deep_update

"""
import collections.abc


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
