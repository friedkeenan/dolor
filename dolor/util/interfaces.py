"""Utilities for checking object interfaces."""

import pak

__all__ = [
    "is_container",
]

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
