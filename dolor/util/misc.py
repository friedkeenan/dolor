"""Miscellaneous utilities."""

def default(obj, default):
    """Gets the default for a variable if applicable.

    Parameters
    ----------
    obj
        The variable to default. If ``None``, then it will be defaulted.
    default
        The possible default value.

    Returns
    -------
    any
        If ``obj`` is ``None``, then ``default`` is returned. Otherwise
        ``obj`` is returned.
    """

    if obj is None:
        return default

    return obj
