"""Miscellaneous utilities."""

import io
import inspect
import zlib

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

def arg_annotations(func, *args, **kwargs):
    """Maps function arguments to their annotations.

    Parameters
    ----------
    func : :class:`function`
        The function to take annotations from.
    *args, **kwargs
        The arguments to map annotations to.

    Returns
    -------
    args_annotations : :class:`list`
        The annotations for ``*args``, of the form
        ``[(value, annotation)]``.
    kwargs_annotations : :class:`dict`
        The annotations for ``*args``, of the form
        ``{name: (value, annotation)}``.
    """

    parameters = inspect.signature(func).parameters

    args_annotations   = []
    kwargs_annotations = {}

    i = 0
    for i, (arg, param) in enumerate(zip(args, parameters.values())):
        if param.kind == param.VAR_POSITIONAL:
            args_annotations += [(x, param.annotation) for x in args[i:]]
            break

        args_annotations.append((arg, param.annotation))
    else:
        if i < len(args) - 1:
            raise TypeError("Too many positional arguments")

    # Find the **kwargs parameter
    var_kwarg = None
    for param in parameters.values():
        if param.kind == param.VAR_KEYWORD:
            var_kwarg = param
            break

    for name, value in kwargs.items():
        param = parameters.get(name, var_kwarg)

        # If no corresponding parameter is found
        # and there's no var_kwarg
        if param is None:
            raise TypeError(f"Invalid keyword argument: {name}")

        if param.kind == param.POSITIONAL_ONLY:
            raise TypeError(f"Positional only argument: {name}")

        kwargs_annotations[name] = (value, param.annotation)

    return args_annotations, kwargs_annotations

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
