from .. import util
from .type import Type
from .simple import UnsignedByte

class VarNum(Type):
    _default = 0
    bits = None

    @classmethod
    def _unpack(cls, buf, *, ctx=None):
        ret = 0

        for i in range(1 + cls.bits // 8):
            read = UnsignedByte.unpack(buf, ctx=ctx)
            value = read & 0x7f

            ret |= value << (7 * i)

            if read & 0x80 == 0:
                return util.to_signed(ret)

        raise ValueError(f"{cls.__name__} is too big")

    @classmethod
    def _pack(cls, value, *, ctx=None):
        ret = b""

        for i in range(1 + cls.bits // 8):
            tmp = value & 0x7f

            value = util.urshift(value, 7)
            if value != 0:
                tmp |= 0x80

            ret += UnsignedByte.pack(tmp, ctx=ctx)

            if value == 0:
                return ret

        raise ValueError(f"{cls.__name__} is too big")

class VarInt(VarNum):
    bits = 32

class VarLong(VarNum):
    bits = 64
