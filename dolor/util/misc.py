"""Miscellaneous utilities."""

import zlib
import io

def get_subclasses(*args):
    """Gets the subclasses of the parameters.

    Parameters
    ----------
    *args : :class:`type`
        The types to get the subclasses of.

    Returns
    -------
    :class:`set`
        The subclasses of ``*args``.
    """

    ret = set()

    for arg in args:
        tmp = set(arg.__subclasses__())
        tmp |= get_subclasses(*tmp)
        ret |= tmp

    return ret

def default(value, default):
    """Defaults a variable.

    Parameters
    ----------
    value
        The value to potentially default.
    default
        The default value.

    Returns
    -------
    any
        If ``value`` is ``None``, then ``default`` is returned,
        else ``value`` is returned.
    """

    if value is None:
        return default

    return value

class ZlibDecompressFile(io.IOBase):
    """A simple read-only file object for decompressing zlib data.

    Parameters
    ----------
    f
        The file object to wrap.
    *args, **kwargs
        Forwarded to :func:`zlib.decompressobj`.
    """

    def __init__(self, f, *args, **kwargs):
        self.f = f
        self.decomp = zlib.decompressobj(*args, **kwargs)

    def read(self, size=-1):
        """Reads decompressed data from the wraped file object.

        Parameters
        ----------
        size : :class:`int`
            The amount of data to return. If -1, decompress
            all the data that's left.

        Returns
        -------
        :class:`bytes`
            The decompressed data.
        """

        if size < 0:
            return self.decomp.decompress(self.f.read(size))

        ret = b""
        while len(ret) < size:
            ret += self.decomp.decompress(self.f.read(1))

        return ret

    def close(self):
        """Closes the wrapped file object."""

        self.f.close()
