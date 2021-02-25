"""Utilities for checking object interfaces."""

import os
import io

def is_iterable(obj):
    """Checks if an object is iterable.

    Parameters
    ----------
    obj
        The object to check. ``obj`` is iterable if it can
        be used in the following expression::

            for x in obj:
                pass

    Returns
    -------
    :class:`bool`
        Whether ``obj`` is iterable.
    """

    try:
        iter(obj)
    except TypeError:
        return False
    else:
        return True

def is_container(obj):
    """Checks if an object is a container.

    Parameters
    ----------
    obj
        The object to check. ``obj`` is a container if it
        can be used in the following expression::

            x in obj

    Returns
    -------
    :class:`bool`
        Whether ``obj`` is a container.
    """
    return hasattr(obj, "__contains__") or is_iterable(obj)

def is_pathlike(obj):
    """Checks if an object is pathlike.

    Parameters
    ----------
    obj
        The object to check.

    Returns
    -------
    :class:`bool`
        Whether ``obj`` is pathlike.
    """

    return isinstance(obj, (str, os.PathLike))

def file_object(obj):
    """Converts an object to a file object.

    Parameters
    ----------
    obj : file object or :class:`bytes` or :class:`bytearray`
        The object to convert.
    """

    if isinstance(obj, (bytes, bytearray)):
        return io.BytesIO(obj)

    return obj
