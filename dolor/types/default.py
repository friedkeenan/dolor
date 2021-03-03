"""Types manipulating default values."""

from .type import Type
from .util import prepare_types

class Defaulted(Type):
    """A type with a custom default value.

    The resulting type inherits from the specified
    type and the :class:`Defaulted` type, in that order.

    Parameters
    ----------
    elem_type : subclass of :class:`Type`
        The type to modify the default of.
    default
        The new default value.

    Examples
    --------
    >>> import dolor
    >>> d = dolor.types.Defaulted(dolor.types.VarInt, 1)
    >>> d
    <class 'dolor.types.default.DefaultedVarInt'>
    >>> d.default()
    1
    """

    @classmethod
    @prepare_types
    def _call(cls, elem_type: Type, default):
        return cls.make_type(f"{cls.__name__}{elem_type.__name__}", (elem_type, cls),
            _default = default,
        )
