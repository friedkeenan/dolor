"""Enumeration types."""

from .type import Type
from .util import prepare_types

class Enum(Type):
    r"""Matches values from other types to :class:`enum.Enum` values.

    The default value is the first member of the enum.

    Parameters
    ----------
    elem_type : subclass of :class:`~.Type`
        The base type to use to get the raw values.
    enum_type : subclass of :class:`enum.Enum`
        The enum type to translate values gotten
        using ``elem_type``.

    Examples
    --------
    >>> import enum
    >>> import dolor
    >>> class MyEnum(enum.Enum):
    ...     A = 0
    ...     B = 1
    ...
    >>> e = dolor.types.Enum(dolor.types.Byte, MyEnum)
    >>> e
    <class 'dolor.types.enum.ByteEnum(MyEnum)'>
    >>> e.default()
    <MyEnum.A: 0>
    >>> e.pack(MyEnum.B)
    b'\x01'
    >>> e.unpack(b"\x01")
    <MyEnum.B: 1>
    """

    elem_type = None
    enum_type = None

    @classmethod
    def _default(cls, *, ctx=None):
        return tuple(cls.enum_type.__members__.values())[0]

    @classmethod
    def _unpack(cls, buf, *, ctx=None):
        return cls.enum_type(cls.elem_type.unpack(buf, ctx=ctx))

    @classmethod
    def _pack(cls, value, *, ctx=None):
        return cls.elem_type.pack(value.value, ctx=ctx)

    @classmethod
    @prepare_types
    def _call(cls, elem_type: Type, enum_type):
        return cls.make_type(f"{elem_type.__name__}Enum({enum_type.__name__})",
            elem_type = elem_type,
            enum_type = enum_type,
        )
