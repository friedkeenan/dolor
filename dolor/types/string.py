import json

from .type import Type
from .var_num import VarInt
from .version_switched import handle_dict_type

class String(Type):
    prefix     = VarInt
    max_length = 32767
    length     = None

    encoding = "utf-8"

    _default = ""

    @classmethod
    def real_length(cls):
        if cls.length is None:
            return cls.max_length

        return cls.length

    @classmethod
    def _unpack(cls, buf, *, ctx=None):
        length = cls.prefix.unpack(buf, ctx=ctx)

        if length > cls.real_length() * 4:
            raise ValueError(f"Invalid data length ({length}) for String({cls.real_length()})")

        ret = buf.read(length).decode(cls.encoding)

        if len(ret) > cls.real_length():
            raise ValueError(f"Invalid character length ({len(ret)}) for String({cls.real_length()})")

        return ret

    @classmethod
    def _pack(cls, value, *, ctx=None):
        if len(value) > cls.real_length():
            raise ValueError(f"Invalid character length ({len(value)}) for String({cls.real_length()})")

        data = value.encode(cls.encoding)
        if len(data) > cls.real_length() * 4:
            raise ValueError(f"Invalid data length ({len(data)}) for String({cls.real_length()})")

        return cls.prefix.pack(len(data), ctx=ctx) + data

    @classmethod
    def _call(cls, length=None, *, max_length=None, prefix=None, encoding=None):
        max_length = max_length or cls.max_length
        length     = length or max_length

        if length > max_length:
            raise ValueError(f"String length ({length}) higher than maximum length of {max_length}")

        prefix = prefix or cls.prefix
        prefix = handle_dict_type(prefix)

        encoding = encoding or cls.encoding

        return cls.make_type(f"String({length})",
            max_length = max_length,
            length     = length,
            prefix     = prefix,
        )

class Json(Type):
    _default = {}

    @classmethod
    def _unpack(cls, buf, *, ctx=None):
        return json.loads(String.unpack(buf, ctx=ctx))

    @classmethod
    def _pack(cls, value, *, ctx=None):
        return String.pack(json.dumps(value, separators=(",", ":")), ctx=ctx)

class Identifier(Type):
    class Identifier:
        def __init__(self, id=None):
            if id is None:
                self.namespace = None
                self.name = None
            else:
                parts = id.split(":")

                if len(parts) == 1:
                    self.namespace = "minecraft"
                    self.name = parts[0]
                elif len(parts) == 2:
                    self.namespace = parts[0]
                    self.name = parts[1]
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
