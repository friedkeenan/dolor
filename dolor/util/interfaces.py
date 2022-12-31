"""Utilities for checking object interfaces."""

import os
import pak

__all__ = [
    "is_container",
    "is_pathlike",
]

def is_container(obj):
    """Checks if an object is a container.

    Parameters
    ----------
    obj
        The object to check.

        ``obj`` is a container if it can be
        used in the following expression::

            x in obj

    Returns
    -------
    :class:`bool`
        Whether ``obj`` is a container.

    Examples
    --------
    >>> import dolor
    >>> dolor.util.is_container([])
    True
    >>> dolor.util.is_container(range(5))
    True
    >>> dolor.util.is_container(x for x in range(5))
    True
    >>> dolor.util.is_container(1)
    False
    """

    return hasattr(obj, "__contains__") or pak.util.is_iterable(obj)

def is_pathlike(obj):
    """Checks if an object is pathlike.

    Parameters
    ----------
    obj
        The object to check.

        ``obj`` is pathlike if it can be passed to :func:`open`.

    Returns
    -------
    :class:`bool`
        Whether ``obj`` is pathlike.

    Examples
    --------
    >>> import dolor
    >>> dolor.util.is_pathlike("string path")
    True
    >>> from pathlib import Path
    >>> dolor.util.is_pathlike(Path("pathlib"))
    True
    """

    return isinstance(obj, (str, os.PathLike))
