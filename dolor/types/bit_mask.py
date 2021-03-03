from .. import util
from .type import Type
from .util import prepare_types

class BitMask(Type):
    elem_type  = None
    value_type = None

    class BitMask:
        masks = None

        def __new__(cls, name=None, **kwargs):
            if cls.masks is not None:
                return super().__new__(cls)

            if isinstance(name, int):
                raise TypeError(f"Use of {cls.__name__} without setting its masks")

            if name is None:
                name = cls.__name__

            return type(name, (cls,), dict(
                masks = kwargs,
            ))

        def __init__(self, value=0, **kwargs):
            self.value = value

            for attr, value in kwargs.items():
                setattr(self, attr, value)

        def __getattr__(self, attr):
            if attr not in self.masks:
                raise AttributeError

            bits = self.masks[attr]

            if isinstance(bits, int):
                return (self.value & util.bit(bits)) != 0

            bit_range = util.bit(bits[1] - bits[0]) - 1

            return ((self.value & (bit_range << bits[0])) >> bits[0])

        def __setattr__(self, attr, value):
            if attr not in self.masks:
                super().__setattr__(attr, value)
            else:
                bits = self.masks[attr]

                if isinstance(bits, int):
                    if value:
                        self.value |= util.bit(bits)
                    else:
                        self.value &= ~util.bit(bits)
                else:
                    bit_range = util.bit(bits[1] - bits[0]) - 1

                    if value != (value & bit_range):
                        raise ValueError(f"Value {value} too wide for range {bits}")

                    self.value &= ~(bit_range << bits[0])
                    self.value |= (value << bits[0])

        def __repr__(self):
            return f"{type(self).__name__}({', '.join(f'{x}={getattr(self, x)}' for x in self.masks)})"

    @classmethod
    def _default(cls, *, ctx=None):
        return cls.value_type()

    @classmethod
    def _unpack(cls, buf, *, ctx=None):
        return cls.value_type(cls.elem_type.unpack(buf, ctx=ctx))

    @classmethod
    def _pack(cls, value, *, ctx=None):
        return cls.elem_type.pack(value.value, ctx=ctx)

    @classmethod
    @prepare_types
    def _call(cls, name, elem_type: Type, **masks):
        return cls.make_type(name,
            elem_type  = elem_type,
            value_type = cls.BitMask(name, **masks),
        )
