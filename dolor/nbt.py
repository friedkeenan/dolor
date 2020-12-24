import abc
import io
import struct
import gzip
import inspect

from . import util
from . import types

class Tag(abc.ABC):
    id   = None

    # Must not require a type context
    type = None

    @classmethod
    def from_id(cls, id):
        for tag in util.get_subclasses(cls):
            if tag.id is not None and tag.id == id:
                return tag

        return None

    def __init__(self, value=None, *, root_name=None):
        if value is None:
            value = self.type.default()

        self.value     = value
        self.root_name = root_name

    def pack(self):
        if self.root_name is not None:
            return String(self.root_name).pack() + self._pack(self.value)

        return self._pack(self.value)

    def __repr__(self):
        ret = f"{type(self).__name__}("

        if self.root_name is not None:
            ret += f"root_name={repr(self.root_name)}, "

        return ret + f"{repr(self.value)})"

    @classmethod
    def unpack(cls, buf, *, root=False):
        if isinstance(buf, (bytes, bytearray)):
            buf = io.BytesIO(buf)

        if root:
            root_name = String.unpack(buf).value
        else:
            root_name = None

        ret = cls._unpack(buf)

        ret.root_name = root_name

        return ret

    @classmethod
    def _unpack(cls, buf):
        return cls(cls.type.unpack(buf))

    @classmethod
    def _pack(cls, value):
        return cls.type.pack(value)

class End(Tag):
    id   = 0
    type = types.EmptyType

class Byte(Tag):
    id   = 1
    type = types.Byte

class Short(Tag):
    id   = 2
    type = types.Short

class Int(Tag):
    id   = 3
    type = types.Int

class Long(Tag):
    id   = 4
    type = types.Long

class Float(Tag):
    id   = 5
    type = types.Float

class Double(Tag):
    id   = 6
    type = types.Double

class ByteArray(Tag):
    id   = 7
    type = types.Byte[types.Int]

class String(Tag):
    id = 8

    # Would be nicer to use Java's wack modified utf-8 but ew
    type = types.String(prefix=types.UnsignedShort, max_length=65535)

class List(Tag):
    id = 9

    tag = None

    def __new__(cls, tag_or_value=None, *args, **kwargs):
        if not isinstance(tag_or_value, type):
            if cls.tag is None:
                raise TypeError(f"Use of {cls.__name__} without setting its tag")

            return super().__new__(cls)

        return type(f"{cls.__name__}({tag_or_value.__name__})", (cls,), dict(
            tag = tag_or_value,
        ))

    def __init__(self, value=None, *, root_name=None):
        if value is None:
            value = []

        self.value     = value
        self.root_name = root_name

    def __getitem__(self, index):
        return self.value[index]

    def __setitem__(self, index, value):
        self.value[index] = value

    def __delitem__(self, index):
        del self.value[index]

    @classmethod
    def _unpack(cls, buf):
        id  = types.UnsignedByte.unpack(buf)
        tag = Tag.from_id(id)

        new_cls = cls(tag)

        size = Int.unpack(buf).value

        return new_cls([tag.unpack(buf).value for x in range(size)])

    @classmethod
    def _pack(cls, value):
        return types.UnsignedByte.pack(cls.tag.id) + Int(len(value)).pack() + b"".join(cls.tag(x).pack() for x in value)

class Compound(Tag):
    id = 10

    def __init__(self, value=None, *, root_name=None):
        if value is None:
            value = {}

        self.value     = value
        self.root_name = root_name

    def __getitem__(self, key):
        return self.value[key]

    def __setitem__(self, key, value):
        self.value[key] = value

    def __delitem__(self, key):
        del self.value[key]

    @classmethod
    def _unpack(cls, buf):
        fields = {}

        while True:
            id  = types.UnsignedByte.unpack(buf)
            tag = Tag.from_id(id)

            if tag == End:
                return cls(fields)

            name  = String.unpack(buf).value
            value = tag.unpack(buf)

            fields[name] = value

    @classmethod
    def _pack(cls, value):
        return b"".join(types.UnsignedByte.pack(y.id) + String(x).pack() + y.pack() for x, y in value.items()) + types.UnsignedByte.pack(End.id)

class IntArray(Tag):
    id   = 11
    type = types.Int[types.Int]

class LongArray(Tag):
    id   = 12
    type = types.Long[types.Int]

def load(f):
    should_close = False

    if isinstance(f, (bytes, bytearray)):
        f = io.BytesIO(f)
    elif util.is_pathlike(f):
        f = open(f, "rb")
        should_close = True

    magic = f.read(2)
    f.seek(-2, 1)

    # Quick and dirty magic checking, I'm sorry
    if magic == b"\x1f\x8b":
        f = gzip.GzipFile(fileobj=f)
    elif magic in (b"\x78\x01", b"\x78\x5e", b"\x78\x9c", b"\x78\xda"):
        f = util.ZlibDecompressFile(f)

    id  = types.UnsignedByte.unpack(f)
    tag = Tag.from_id(id)

    ret = tag.unpack(f, root=True)

    if should_close:
        f.close()

    return ret

def dump(obj, f=None, *, compression=None):
    if compression is not None and not inspect.isfunction(compression):
        compression = compression.compress

    data = types.UnsignedByte.pack(obj.id) + obj.pack()

    if compression is not None:
        data = compression(data)

    if f is None:
        return data

    return f.write(data)
