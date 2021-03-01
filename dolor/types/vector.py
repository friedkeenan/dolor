from .. import util
from .type import Type
from .numeric import UnsignedLong
from .version_switched import handle_dict_type

class Vector(Type):
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
            return f"{type(self).__name__}(x={self.x}, y={self.y}, z={self.z})"

    elem_type = None

    @classmethod
    def _default(cls, *, ctx=None):
        return cls.Vector(*([cls.elem_type.default(ctx=ctx)] * 3))

    @classmethod
    def _unpack(cls, buf, *, ctx=None):
        return cls.Vector(*[cls.elem_type.unpack(buf, ctx=ctx) for x in range(3)])

    @classmethod
    def _pack(cls, value, *, ctx=None):
        return b"".join(cls.elem_type.pack(x) for x in value)

    @classmethod
    def _call(cls, elem_type):
        elem_type = handle_dict_type(elem_type)

        return cls.make_type(f"{elem_type.__name__}Vector",
            elem_type = elem_type,
        )


class Position(Type):
    _default = Vector.Vector()

    @classmethod
    def _unpack(cls, buf, *, ctx=None):
        value = UnsignedLong.unpack(buf, ctx=ctx)

        return Vector.Vector(
            util.to_signed(value >> 38, bits=26),
            util.to_signed((value >> 26) & 0xfff, bits=12),
            util.to_signed(value & 0x3ffffff, bits=26),
        )

    @classmethod
    def _pack(cls, value, *, ctx=None):
        return UnsignedLong.pack(
            (value.x & 0x3ffffff) << 38 |
            (value.y &     0xfff) << 26 |
            (value.z & 0x3ffffff) <<  0,
        )
