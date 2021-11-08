"""Types relating to strings."""

import collections
import dataclasses
import json
import pak

from .numeric import VarInt
from .. import util

__all__ = [
    "StringLengthError",
    "String",
    "JSON",
    "StructuredJSON",
    "Identifier",
]

class StringLengthError(Exception):
    """An error indicating an invalid length of a :class:`String`.

    Parameters
    ----------
    string_cls : subclass of :class:`String`
        The subclass for which the error was raised.
    length_type : :class:`str`
        The type of length that is invalid.

        ``"data"`` for when the length of the data is invalid,
        ``"string"`` for when the length of the decoded string is invalid.
    invalid_length : :class:`int`
        The invalid length for which the error was raised.
    """

    def __init__(self, string_cls, length_type, invalid_length):
        super().__init__(
            f"Invalid {length_type} length ({invalid_length}) for String with max length {string_cls.max_length}"
        )

class String(pak.Type):
    """A string of characters.

    Parameters
    ----------
    max_length : :class:`int`
        The maximum length of the string.

        If exceeded, a :exc:`StringLengthError` is raised.

        By default ``32767``.
    prefix : typelike
        The type at the beginning of the raw data representing
        the length of the string in bytes.

        By default :class:`types.VarInt <.VarInt>`.
    encoding : :class:`str`
        The encoding to use for the string.

        By default ``"utf-8"``.
    """

    _default = ""

    prefix     = VarInt
    encoding   = "utf-8"
    max_length = 32767

    @classmethod
    def _unpack(cls, buf, *, ctx=None):
        length = cls.prefix.unpack(buf, ctx=ctx)

        if length > cls.max_length * 4:
            raise StringLengthError(cls, "data", length)

        str_data = buf.read(length).decode(cls.encoding)
        str_len  = len(str_data)

        if str_len > cls.max_length:
            raise StringLengthError(cls, "string", str_len)

        return str_data

    @classmethod
    def _pack(cls, value, *, ctx=None):
        value_len = len(value)

        if value_len > cls.max_length:
            raise StringLengthError(cls, "string", value_len)

        data     = value.encode(cls.encoding)
        data_len = len(data)

        if data_len > cls.max_length * 4:
            raise StringLengthError(cls, "data", data_len)

        return cls.prefix.pack(data_len, ctx=ctx) + data

    @classmethod
    @pak.Type.prepare_types
    def _call(cls, max_length, *, prefix: pak.Type = None, encoding=None):
        return cls.make_type(
            f"String({max_length})",

            max_length = max_length,
            prefix     = util.default(prefix,   cls.prefix),
            encoding   = util.default(encoding, cls.encoding),
        )

class JSON(pak.Type):
    """JSON data.

    Wraps :func:`json.loads` and :func:`json.dumps`
    for unpacking and packing respectively.
    """

    _default = {}

    @classmethod
    def _unpack(cls, buf, *, ctx=None):
        return json.loads(String.unpack(buf, ctx=ctx))

    @classmethod
    def _pack(cls, value, *, ctx=None):
        # Specify separators to get as compact as possible.
        return String.pack(json.dumps(value, separators=(",", ":")), ctx=ctx)

class StructuredJSON(pak.Type):
    """Structured JSON data.

    :meta no-undoc-members:

    .. seealso::

        :class:`util.StructuredDict <.StructuredDict>`

    The annotations of subclasses should be made in the fashion of
    :mod:`dataclasses`, and are applied to the :class:`util.StructuredDict <.StructuredDict>`
    value type.

    If the type of an annotation is a mapping, then any :class:`dict` values
    in the JSON data will be passed to said type's constructor, allowing you
    to use :class:`util.StructuredDicts <.util.structured_dict.StructuredDict>`
    as types of annotations.

    The value type of the resulting :class:`StructuredJSON` subclass can be accessed
    through either the :meth:`value_type` method or as an attribute of the same name
    as the subclass.

    Examples
    --------
    >>> import dolor
    >>> class Example(dolor.types.StructuredJSON):
    ...     key: int
    ...
    >>> Example.value_type() is Example.Example
    True
    >>> Example.Example(key=1)
    Example(key=1)
    """

    @classmethod
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)

        # TODO: In Python 3.10+ we can use 'inspect.getannotations'.
        annotations = getattr(cls, "__annotations__", {})

        # Make sure we propagate on the annotation fields.
        unique_sentinel = object()
        attrs           = {}
        for key in annotations.keys():
            attr = getattr(cls, key, unique_sentinel)

            if attr is not unique_sentinel:
                attrs[key] = attr

        # Set value type as an attribute with the same name.
        setattr(cls, cls.__name__, cls.make_type(
            cls.__name__,
            (util.StructuredDict,),

            __annotations__ = annotations,
            __qualname__    = f"{cls.__qualname__}.{cls.__name__}",

            **attrs,
        ))

    def __set__(self, instance, value):
        if not isinstance(value, self.value_type()):
            value = self.value_type(value)

        super().__set__(instance, value)

    @classmethod
    def value_type(cls):
        """A generic way to get the value type of a :class:`StructuredJSON`."""

        return getattr(cls, cls.__name__)

    @classmethod
    def _default(cls, *, ctx=None):
        return cls.value_type()()

    @classmethod
    def _unpack(cls, buf, *, ctx=None):
        value = JSON.unpack(buf, ctx=ctx)

        value_type = cls.value_type()

        for key in list(value.keys()):
            value_for_key = value[key]
            if isinstance(value_for_key, dict):
                type_for_key = value_type.__dataclass_fields__[key].type
                value[key]   = type_for_key(value_for_key)

        return value_type(value)

    @classmethod
    def _pack(cls, value, *, ctx=None):
        value = dict(value)

        for key in list(value.keys()):
            value_for_key = value[key]
            if isinstance(value_for_key, collections.abc.Mapping):
                value[key] = dict(value_for_key)

        return JSON.pack(value, ctx=ctx)

class Identifier(pak.Type):
    """An identifier for a resource location.

    .. note::

        This type has no default value.
    """

    class Identifier:
        """The value type of :class:`~.string.Identifier`.

        Parameters
        ----------
        id : :class:`str` or :class:`Identifier.Identifier`
            The namespaced resource location.

            See https://wiki.vg/Protocol#Identifier for details.

        Raises
        ------
        :exc:`ValueError`
            If the identifier has more than one colon (``:``).
        """

        def __init__(self, id):
            if isinstance(id, Identifier.Identifier):
                self.namespace = id.namespace
                self.name      = id.name
            else:
                components = id.split(":")

                # TODO: Use pattern matching when Python 3.9 support is dropped

                num_components = len(components)

                if num_components == 1:
                    self.namespace = "minecraft"
                    self.name      = components[0]
                elif num_components == 2:
                    self.namespace, self.name = components
                else:
                    raise ValueError(f"Invalid Identifier: {id}")

        def __eq__(self, other):
            return (self.namespace, self.name) == (other.namespace, other.name)

        def __hash__(self):
            return hash((self.namespace, self.name))

        def __str__(self):
            return f"{self.namespace}:{self.name}"

        def __repr__(self):
            return f"{type(self).__name__}({self})"

    def __set__(self, instance, value):
        # Setting the value to a 'str' will convert it to our value type.
        super().__set__(instance, type(self).Identifier(value))

    @classmethod
    def _unpack(cls, buf, *, ctx=None):
        return cls.Identifier(String.unpack(buf, ctx=ctx))

    @classmethod
    def _pack(cls, value, *, ctx=None):
        return String.pack(str(value), ctx=ctx)
