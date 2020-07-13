import io
import copy
import struct
import math
import uuid
import json
from . import util

class Type:
    zero = None

    def __init__(self, buf=None):
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
        """

        raise NotImplementedError

    def __bytes__(self):
        """
        Should return the bytes that corresponds
        to self.value.
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
    zero = []

    elem_type = None
    len_attr = None

    def __init__(self, buf=None, num_elems=None):
        if isinstance(self.len_attr, int):
            self.num_elems = self.len_attr
        else:
            self.num_elems = num_elems

        self.len_obj = None

        super().__init__(buf)

    def unpack(self, buf):
        if self.is_prefixed_by_type():
            self.len_obj = self.len_attr(buf)
            self.num_elems = self.len_obj.value

        if self.num_elems is not None:
            return [self.elem_type(buf).value for x in range(self.num_elems)]

        ret = []
        while True:
            try:
                ret.append(self.elem_type(buf).value)
            except:
                return ret

    def __bytes__(self):
        ret =  b"".join(bytes(self.elem_type(x)) for x in self.value)

        if self.is_prefixed_by_type():
            if self.len_obj is None:
                self.len_obj = self.len_attr(len(self.value))
            else:
                self.len_obj.value = len(self.value)

            ret = bytes(self.len_obj) + ret

        return ret

    @classmethod
    def is_prefixed_by_type(cls):
        return isinstance(cls.len_attr, type) and issubclass(cls.len_attr, Type)

def Array(elem_type, len_attr=None):
    return type(f"{elem_type.__name__}Array", (BaseArray,), {"elem_type": elem_type, "len_attr": len_attr})

class BaseRawByteArray(BaseArray):
    zero = bytearray()

    def unpack(self, buf):
        if self.is_prefixed_by_type():
            self.len_obj = self.len_attr(buf)
            self.num_elems = self.len_obj.value

        return bytearray(buf.read(self.num_elems))

    def __bytes__(self):
        ret = bytes(self.value)

        if self.is_prefixed_by_type():
            if self.len_obj is None:
                self.len_obj = self.len_attr(len(self.value))
            else:
                self.len_obj.value = len(self.value)

            ret = bytes(self.len_obj) + ret

        return ret

def RawByteArray(len_attr=None):
    return type("RawByteArray", (BaseRawByteArray,), {"len_attr": len_attr})

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
        return self.Vector(*([self.elem_type(buf).value] * 3))

    def __bytes__(self):
        return b"".join(bytes(self.elem_type(x)) for x in self.value)

def Vector(elem_type):
    return type(f"{elem_type.__name__}Vector", (BaseVector,), {"elem_type": elem_type})

class BaseEnum(Type):
    elem_type = None
    enum_type = None

    def unpack(self, buf):
        return self.enum_type(self.elem_type(buf).value)

    def __bytes__(self):
        return bytes(self.elem_type(self.value.value))

def Enum(elem_type, enum_type):
    return type(f"{elem_type.__name__}Enum", (BaseEnum,), {
        "zero":      tuple(enum_type.__members__.values())[0],
        "elem_type": elem_type,
        "enum_type": enum_type,
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
        length = VarInt(buf).value
        return buf.read(length).decode("utf8")

    def __bytes__(self):
        ret = self.value.encode("utf8")
        ret = bytes(VarInt(len(ret))) + ret
        return ret

class Json(Type):
    zero = {}

    def unpack(self, buf):
        return json.loads(String(buf).value)

    def __bytes__(self):
        return bytes(String(json.dumps(self.value, separators=(",", ":"))))

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
        return uuid.UUID(bytes=buf.read(16))

    def __bytes__(self):
        return self.value.bytes

class UUIDString(UUID):
    def unpack(self, buf):
        return uuid.UUID(String(buf).value)

    def __bytes__(self):
        return bytes(String(str(self.value)))

class Identifier(Type):
    class RealIdentifier:
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
            return f'Identifier("{self}")'

    zero = RealIdentifier()

    def unpack(self, buf):
        return self.RealIdentifier(String(buf).value)

    def __bytes__(self):
        return bytes(String(str(self.value)))