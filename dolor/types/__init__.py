import io
import copy
import struct
import math
import uuid
import json
from .. import util

class Type:
    # The value that should be returned
    # when __init__ is called with no arguments
    zero = None

    def __init__(self, buf=None, *, ctx=None):
        self.ctx = ctx

        if buf is None:
            # deepcopy because self.zero could be mutable
            self.value = copy.deepcopy(self.zero)
        else:
            if isinstance(buf, (bytes, bytearray)):
                buf = io.BytesIO(buf)

            if isinstance(buf, io.IOBase):
                self.value = self.unpack(buf)
            else:
                self.value = buf

    def __repr__(self):
        return f"{type(self).__name__}({repr(self.value)})"

    def unpack(self, buf):
        """
        Should return the value that corresponds
        to the raw data in the buffer.

        If the unpacking needs to change based on
        the protocol version, use self.ctx.pro.
        """

        raise NotImplementedError

    def __bytes__(self):
        """
        Should return the bytes that corresponds
        to self.value.

        If the unpacking needs to change based on
        the protocol version, use self.ctx.pro.
        """

        raise NotImplementedError

    def __len__(self):
        return len(bytes(self))

    def __add__(self, other):
        return TypeSum(self, other)

class TypeSum:
    def __init__(self, *types):
        self.types = list(types)

    def __repr__(self):
        return f"{type(self).__name__}({', '.join(repr(x) for x in self.types)})"

    def __bytes__(self):
        return b"".join(bytes(x) for x in self.types)

    def __len__(self):
        return sum(len(x) for x in self.types)

    def __getitem__(self, idx):
        if isinstance(idx, slice):
            return type(self)(*self.types[idx])

        return self.types[idx]

    def __setitem__(self, idx, value):
        self.types[idx] = value

    def __add__(self, other):
        if isinstance(other, Type):
            return type(self)(*self.types, other)

        return type(self)(*self.types, *other.types)

class SimpleType(Type):
    """
    Essentially just a struct wrapper
    """

    zero = 0
    fmt = None

    def unpack(self, buf):
        ret = struct.unpack(f">{self.fmt}", buf.read(struct.calcsize(self.fmt)))

        if len(ret) == 1:
            return ret[0]

        return ret

    def __bytes__(self):
        if hasattr(self.value, "__iter__"):
            return struct.pack(f">{self.fmt}", *self.value)

        return struct.pack(f">{self.fmt}", self.value)

class Boolean(SimpleType):
    zero = False
    fmt = "?"

class Byte(SimpleType):
    fmt = "b"

class UnsignedByte(SimpleType):
    fmt = "B"

class Short(SimpleType):
    fmt = "h"

class UnsignedShort(SimpleType):
    fmt = "H"

class Int(SimpleType):
    fmt = "i"

class Long(SimpleType):
    fmt = "q"

class Float(SimpleType):
    fmt = "f"

class Double(SimpleType):
    fmt = "d"

class BaseArray(Type):
    elem_type = None
    len_attr = None

    def __init__(self, buf=None, *, ctx=None, num_elems=None):
        if self.is_fixed_len():
            self.num_elems = self.len_attr
        else:
            self.num_elems = num_elems

        self.len_obj = None

        super().__init__(buf, ctx=ctx)

    def unpack(self, buf):
        if self.is_prefixed_by_type():
            self.len_obj = self.len_attr(buf, ctx=self.ctx)
            self.num_elems = self.len_obj.value

        if self.num_elems is not None:
            return [self.elem_type(buf, ctx=self.ctx).value for x in range(self.num_elems)]

        ret = []
        while True:
            try:
                ret.append(self.elem_type(buf, ctx=self.ctx).value)
            except:
                return ret

    def __bytes__(self):
        if self.is_fixed_len():
            self.value = self.value[:self.len_attr]

        ret =  b"".join(bytes(self.elem_type(x, ctx=self.ctx)) for x in self.value)

        if self.is_prefixed_by_type():
            if self.len_obj is None:
                self.len_obj = self.len_attr(len(self.value), ctx=self.ctx)
            else:
                self.len_obj.value = len(self.value)

            ret = bytes(self.len_obj) + ret

        return ret

    @classmethod
    def is_prefixed_by_type(cls):
        return isinstance(cls.len_attr, type) and issubclass(cls.len_attr, Type)

    @classmethod
    def is_fixed_len(cls):
        return isinstance(cls.len_attr, int)

def Array(elem_type, len_attr=None):
    attrs = {
        "elem_type": elem_type,
        "len_attr":  len_attr,
    }

    if isinstance(len_attr, int):
        # Context not passed, shouldn't be a problem
        # for zero values but not the cleanest.
        attrs["zero"] = [elem_type().value] * len_attr
    else:
        attrs["zero"] = []

    return type(f"{elem_type.__name__}Array", (BaseArray,), attrs)

class BaseRawByteArray(BaseArray):
    # Override all of __init__ so that RawByteArrays
    # behave the way you expect when prefixed by a type
    def __init__(self, buf=None, *, ctx=None, num_elems=None):
        self.ctx = ctx

        if self.is_fixed_len():
            self.num_elems = self.len_attr
        else:
            self.num_elems = num_elems

        if buf is None:
            # deepcopy because self.zero is mutable
            self.value = copy.deepcopy(self.zero)
        else:
            if isinstance(buf, io.IOBase):
                self.value = self.unpack(buf)
            else:
                self.value = buf

        self.len_obj = None

    @property
    def value(self):
        return self._value

    # So you can set the value to a bytes object
    @value.setter
    def value(self, value):
        self._value = bytearray(value)

    def unpack(self, buf):
        if self.is_prefixed_by_type():
            self.len_obj = self.len_attr(buf, ctx=self.ctx)
            self.num_elems = self.len_obj.value

        return bytearray(buf.read(self.num_elems))

    def __bytes__(self):
        if self.is_fixed_len():
            return bytes(self.value[:self.len_attr])

        ret = b""
        if self.is_prefixed_by_type():
            if self.len_obj is None:
                self.len_obj = self.len_attr(len(self.value), ctx=self.ctx)
            else:
                self.len_obj.value = len(self.value)

            ret = bytes(self.len_obj)

        ret += bytes(self.value)

        return ret

def RawByteArray(len_attr=None):
    attrs = {"len_attr": len_attr}

    if isinstance(len_attr, int):
        attrs["zero"] = bytearray(len_attr)
    else:
        attrs["zero"] = bytearray()

    return type("RawByteArray", (BaseRawByteArray,), attrs)

class BaseVector(Type):
    class Vector:
        def __init__(self, x=0, y=0, z=0):
            self.x = x
            self.y = y
            self.z = z

        def __neg__(self):
            return type(self)(-self.x, -self.y, -self.z)

        def __add__(self, other):
            return type(self)(self.x + other.x, self.y + other.y, self.z + other.z)

        def __sub__(self, other):
            return self + -other

        def __mul__(self, other):
            return type(self)(self.x * other, self.y * other, self.z * other)

        def __rmul__(self, other):
            return self * other

        def __truediv__(self, other):
            return self * (1 / other)

        def __floordiv__(self, other):
            return type(self)(self.x // other, self.y // other, self.z // other)

        def __iter__(self):
            yield self.x
            yield self.y
            yield self.z

        def __repr__(self):
            return f"{type(self).__name__}({self.x}, {self.y}, {self.z})"

    zero = Vector()
    elem_type = None

    def unpack(self, buf):
        return self.Vector(*([self.elem_type(buf, ctx=self.ctx).value] * 3))

    def __bytes__(self):
        return b"".join(bytes(self.elem_type(x, ctx=self.ctx)) for x in self.value)

def Vector(elem_type):
    return type(f"{elem_type.__name__}Vector", (BaseVector,), {"elem_type": elem_type})

class BaseEnum(Type):
    elem_type = None
    enum_type = None

    def unpack(self, buf):
        return self.enum_type(self.elem_type(buf, ctx=self.ctx).value)

    def __bytes__(self):
        return bytes(self.elem_type(self.value.value, ctx=self.ctx))

def Enum(elem_type, enum_type):
    return type(f"{elem_type.__name__}Enum", (BaseEnum,), {
        "zero":      tuple(enum_type.__members__.values())[0],
        "elem_type": elem_type,
        "enum_type": enum_type,
    })

class BaseCompound(Type):
    class BaseValue:
        def __init__(self, elems):
            self.elems = elems

        def __getattr__(self, attr):
            if attr == "elems":
                return object.__getattribute__(self, attr)

            if attr not in self.elems:
                raise AttributeError

            return self.elems[attr]

        def __setattr__(self, attr, value):
            if attr == "elems":
                object.__setattr__(self, attr, value)
                return

            if attr not in self.elems:
                raise AttributeError

            self.elems[attr] = value

        def __repr__(self):
            ret = f"{type(self).__name__}("
            ret += ", ".join(f"{x}={repr(y)}" for x, y in self.elems.items())
            ret += ")"

            return ret

    elems = None
    value_type = None

    def unpack(self, buf):
        elem_values = {}

        for attr, attr_type in self.elems.items():
            elem_values[attr] = attr_type(buf, ctx=self.ctx).value

        return self.value_type(elem_values)

    def __bytes__(self):
        ret = TypeSum()

        for attr, attr_type in self.elems.items():
            ret += attr_type(getattr(self.value, attr), ctx=self.ctx)

        return bytes(ret)

def Compound(name="Compound", **kwargs):
    value_type = type(name, (BaseCompound.BaseValue,), {})

    return type(name, (BaseCompound,), {
        "elems":      kwargs,
        "value_type": value_type,

        # Context not passed, shouldn't be a problem
        # for zero values but not the cleanest.
        "zero": value_type({x: y().value for x, y in kwargs.items()}),
    })

class VarInt(Type):
    zero = 0

    def unpack(self, buf):
        ret = 0

        for i in range(5):
            read = buf.read(1)[0]
            value = read & 0x7f
            ret |= value << (7 * i)

            if read & 0x80 == 0:
                return util.to_signed(ret)

        raise ValueError("VarInt is too big")

    def __bytes__(self):
        value = self.value
        ret = b""

        while True:
            temp = value & 0x7f

            value = util.urshift(value, 7)
            if value != 0:
                temp |= 0x80

            ret += struct.pack("B", temp)

            if value == 0:
                return ret

class VarLong(Type):
    zero = 0

    def unpack(self, buf):
        ret = 0

        for i in range(5):
            read = buf.read(1)[0]
            value = read & 0x7f
            ret |= value << (7 * i)

            if read & 0x80 == 0:
                return util.to_signed(ret, bits=64)

        raise ValueError("VarLong is too big")

    def __bytes__(self):
        value = self.value
        ret = b""

        while True:
            temp = value & 0x7f

            value = util.urshift(value, 7, bits=64)
            if value != 0:
                temp |= 0x80

            ret += struct.pack("B", temp)

            if value == 0:
                return ret

class String(Type):
    zero = ""

    def unpack(self, buf):
        length = VarInt(buf, ctx=self.ctx).value
        return buf.read(length).decode("utf-8")

    def __bytes__(self):
        ret = self.value.encode("utf-8")
        ret = bytes(VarInt(len(ret), ctx=self.ctx)) + ret

        return ret

class Json(Type):
    zero = {}

    def unpack(self, buf):
        return json.loads(String(buf, ctx=self.ctx).value)

    def __bytes__(self):
        return bytes(String(json.dumps(self.value, separators=(",", ":")), ctx=self.ctx))

class Position(Type):
    zero = BaseVector.Vector()

    def unpack(self, buf):
        val = struct.unpack(">Q", buf.read(8))[0]
        return BaseVector.Vector(util.to_signed(val >> 38, bits=26),
                                 util.to_signed((val >> 26) & 0xFFF, bits=12),
                                 util.to_signed(val & 0x3ffffff, bits=26))

    def __bytes__(self):
        val = ((self.value.x & 0x3FFFFFF) << 38) | ((self.value.y & 0xFFF) << 26) | (self.value.z & 0x3FFFFFF)
        return struct.pack(">Q", val)

class Angle(Type):
    zero = 0

    def unpack(self, buf):
        return math.tau * UnsignedByte(buf).value / 256

    def __bytes__(self):
        return bytes(UnsignedByte(round(256 * (self.value % math.tau) / math.tau)))

class UUID(Type):
    zero = uuid.UUID(int=0)

    def unpack(self, buf):
        return uuid.UUID(bytes=buf.read(0x10))

    def __bytes__(self):
        return self.value.bytes

class UUIDString(UUID):
    def unpack(self, buf):
        return uuid.UUID(String(buf, ctx=self.ctx).value)

    def __bytes__(self):
        return bytes(String(str(self.value), ctx=self.ctx))

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

    zero = Identifier()

    def unpack(self, buf):
        return self.Identifier(String(buf, ctx=self.ctx).value)

    def __bytes__(self):
        return bytes(String(str(self.value), ctx=self.ctx))

from .chat import *