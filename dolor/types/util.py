"""Type utilities."""

import collections
import functools

from ..util import arg_annotations
from .type import Type
from .version import VersionSwitchedType

def prepare_type(obj):
    """Ensures an object is a :class:`~.Type`.

    Parameters
    ----------
    obj : subclass of :class:`~.Type` or :class:`collections.abc.Mapping`
        If a subclass of :class:`~.Type`, then that is simply returned.

        If a :class:`collections.abc.Mapping` (e.g. a :class:`dict`),
        then a :class:`~.VersionSwitchedType` is returned with
        ``obj`` as the switch.

        Otherwise an error is raised.

    Returns
    -------
    subclass of :class:`~.Type`
        The corresponding type.

    Raises
    ------
    :exc:`ValueError`
        If ``obj`` cannot be converted to a :class:`~.Type`.

    Examples
    --------
    >>> import dolor
    >>> dolor.types.prepare_type(dolor.types.VarInt)
    <class 'dolor.types.numeric.VarInt'>
    >>> dolor.types.prepare_type({})
    <class 'dolor.types.version.VersionSwitchedType'>
    """

    if isinstance(obj, collections.abc.Mapping):
        return VersionSwitchedType(obj)

    if isinstance(obj, type) and issubclass(obj, Type):
        return obj

    raise TypeError(f"Object cannot be converted to a Type: {obj}")

def prepare_types(func):
    """A decorator that passes certain arguments are passed through :func:`prepare_type`.

    Arguments annotated with :class:`~.Type` are passed through
    :func:`prepare_type` before being forwarded onto the function.
    This works for ``*args`` and ``**kwargs`` as well.
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        args_annotations, kwargs_annotations = arg_annotations(func, *args, **kwargs)

        new_args = [
            prepare_type(x) if y is Type
            else x

            for x, y in args_annotations
        ]

        new_kwargs = {}
        for name, (value, annotation) in kwargs_annotations.items():
            if annotation is Type:
                value = prepare_type(value)

            new_kwargs[name] = value

        return func(*new_args, **new_kwargs)

    return wrapper
