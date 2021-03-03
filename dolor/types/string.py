"""String-related types."""

import json

from .. import util
from .type import Type
from .numeric import VarInt
from .util import prepare_types

class String(Type):
    """A string.

    Parameters
    ----------
    max_length : :class:`int`
        The maximum length of the string. By default ``32767``.
    prefix : subclass of :class:`~.Type`, optional
        The type at the start of the data that
        tells how many bytes to read to get the
        string data. By default :class:`~.VarInt`.
    encoding : :class:`str`, optional
        What encoding to use for parsing the string data.
        By default ``"utf-8"``.
    """

    max_length = 32767
    prefix     = VarInt
    encoding   = "utf-8"

    _default = ""

    @classmethod
    def _unpack(cls, buf, *, ctx=None):
        length = cls.prefix.unpack(buf, ctx=ctx)

        if length > cls.max_length * 4:
            raise ValueError(f"Invalid data length ({length}) for String({cls.max_length})")

        ret = buf.read(length).decode(cls.encoding)

        if len(ret) > cls.max_length:
            raise ValueError(f"Invalid character length ({len(ret)}) for String({cls.max_length})")

        return ret

    @classmethod
    def _pack(cls, value, *, ctx=None):
        if len(value) > cls.max_length:
            raise ValueError(f"Invalid character length ({len(value)}) for String({cls.max_length})")

        data = value.encode(cls.encoding)
        if len(data) > cls.max_length * 4:
            raise ValueError(f"Invalid data length ({len(data)}) for String({cls.max_length})")

        return cls.prefix.pack(len(data), ctx=ctx) + data

    @classmethod
    @prepare_types
    def _call(cls, max_length, *, prefix: Type = None, encoding=None):
        prefix = util.default(prefix, cls.prefix)

        encoding = util.default(encoding, cls.encoding)

        return cls.make_type(f"String({max_length})",
            max_length = max_length,
            prefix     = prefix,
            encoding   = encoding,
        )

class Json(Type):
    """JSON data.

    Wraps :func:`json.loads` and `json.dumps` and
    :class:`String`.
    """

    _default = {}

    @classmethod
    def _unpack(cls, buf, *, ctx=None):
        return json.loads(String.unpack(buf, ctx=ctx))

    @classmethod
    def _pack(cls, value, *, ctx=None):
        return String.pack(json.dumps(value, separators=(",", ":")), ctx=ctx)

class Identifier(Type):
    """An identifier for a resource location."""

    class Identifier:
        """The value type of :class:`~.string.Identifier`.

        Parameters
        ----------
        id : :class:`str`, optional
            The namespaced location.

            See https://wiki.vg/Protocol#Identifier for
            details.
        """

        def __init__(self, id=None):
            if id is None:
                self.namespace = None
                self.name = None
            else:
                parts = id.split(":")

                if len(parts) == 1:
                    self.namespace = "minecraft"
                    self.name      = parts[0]
                elif len(parts) == 2:
                    self.namespace = parts[0]
                    self.name      = parts[1]
                else:
                    raise ValueError("Invalid identifier")

        def __str__(self):
            return f"{self.namespace}:{self.name}"

        def __repr__(self):
            return f'{type(self).__name__}("{self}")'

    _default = Identifier()

    def __set__(self, instance, value):
        if not isinstance(value, self.Identifier):
            value = self.Identifier(value)

        super().__set__(instance, value)

    @classmethod
    def _unpack(cls, buf, *, ctx=None):
        return cls.Identifier(String.unpack(buf, ctx=ctx))

    @classmethod
    def _pack(cls, value, *, ctx=None):
        return String.pack(str(value), ctx=ctx)
