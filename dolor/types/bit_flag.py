from .type import Type

class BitFlag(Type):
    elem_type = None
    flags = None

    class BitFlag:
        def __init__(self, flags, value=0):
            self.flags = flags
            self.value = value

        def __getattr__(self, attr):
            if attr not in self.flags:
                raise AttributeError

            return self.value & (1 << self.flags[attr]) != 0

        def __setattr__(self, attr, value):
            if attr == "flags" or attr not in self.flags:
                super().__setattr__(attr, value)
            else:
                if value:
                    self.value |= (1 << self.flags[attr])
                else:
                    self.value &= ~(1 << self.flags[attr])

    @classmethod
    def default(cls, *, ctx=None):
        return cls.BitFlag(cls.flags)

    @classmethod
    def _unpack(cls, buf, *, ctx=None):
        return cls.BitFlag(cls.flags, cls.elem_type.unpack(buf, ctx=ctx))

    @classmethod
    def _pack(cls, value, *, ctx=None):
        return cls.elem_type.pack(value.value, ctx=ctx)

    @classmethod
    def _call(cls, elem_type, **flags):
        return type(cls.__name__, (cls,), dict(
            elem_type = elem_type,
            flags     = flags,
        ))
