"""Utilities related to binary bits."""

def bit(n):
    """
    Parameters
    ----------
    n : :class:`int`
        The bit to set.

    Returns
    ------
    :class:`int`
        The number with the nth bit set.

    Examples
    --------
    >>> import dolor
    >>> dolor.util.bit(0)
    1
    >>> dolor.util.bit(1)
    2
    >>> dolor.util.bit(2)
    4
    """

    return (1 << n)

def to_signed(val, bits=32):
    """Converts a number to its signed counterpart.

    Parameters
    ----------
    val : :class:`int`
        The value to convert.
    bits : :class:`int`, optional
        How many bits to use when converting
        ``val`` to its signed counterpart.

    Returns
    -------
    :class:`int`
        ``val``'s signed counterpart.

    Examples
    --------
    >>> import dolor
    >>> dolor.util.to_signed(2**32 - 1)
    -1
    >>> dolor.util.to_signed(2**64 - 1, 64)
    -1
    """

    if val > bit(bits - 1) - 1:
        val -= bit(bits)

    return val

def to_unsigned(val, bits=32):
    """Converts a number to its unsigned counterpart.

    Parameters
    ----------
    val : :class:`int`
        The value to convert.
    bits : :class:`int`, optional
        How many bits to use when converting
        ``val`` to its unsigned counterpart.

    Returns
    -------
    :class:`int`
        ``val``'s unsigned counterpart.

    Examples
    --------
    >>> import dolor
    >>> dolor.util.to_unsigned(-1)
    4294967295
    >>> dolor.util.to_unsigned(-1, 64)
    18446744073709551615
    """

    if val < 0:
        val += bit(bits)

    return val

def urshift(val, n, bits=32):
    """Performs an unsigned right shift on a number.

    Parameters
    ----------
    val : :class:`int`
        The value to shift.
    n : :class:`int`
        How many bits to shift ``val``.
    bits : :class:`int`, optional
        How many bits should be used for the "unsigned"
        part of "unsigned right shift".

    Returns
    -------
    :class:`int`
        The resulting unsigned right shifted number.

    Examples
    --------
    >>> import dolor
    >>> dolor.util.urshift(2, 1)
    1
    >>> dolor.util.urshift(-1, 1)
    2147483647
    >>> dolor.util.urshift(-1, 1, 64)
    9223372036854775807
    """

    return to_unsigned(val, bits) >> n
