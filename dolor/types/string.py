"""Types relating to strings."""

import json
import pak

from .numeric import VarInt
from .. import util

__all__ = [
    "StringLengthError",
    "String",
    "JSON",
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
    prefix : typelike
        The type at the beginning of the raw data representing
        the length of the string in bytes.
    encoding : :class:`str`
        The encoding to sue for the string.
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
            if isinstance(id, type(self)):
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
