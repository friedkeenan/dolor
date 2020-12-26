from .type import Type

class BitFlag(Type):
    elem_type  = None
    value_type = None

    class BitFlag:
        flags = None

        def __new__(cls, name=None, **kwargs):
            if cls.flags is not None:
                return super().__new__(cls)

            if isinstance(name, int):
                raise TypeError(f"Use of {cls.__name__} without setting its flags")

            if name is None:
                name = cls.__name__

            return type(name, (cls,), dict(
                flags = kwargs,
            ))

        def __init__(self, value=0, **kwargs):
            self.value = value

            for attr, value in kwargs.items():
                setattr(self, attr, value)

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

        def __repr__(self):
            return f"{type(self).__name__}({', '.join(f'{x}={getattr(self, x)}' for x in self.flags)})"

    @classmethod
    def default(cls, *, ctx=None):
        return cls.value_type()

    @classmethod
    def _unpack(cls, buf, *, ctx=None):
        return cls.value_type(cls.elem_type.unpack(buf, ctx=ctx))

    @classmethod
    def _pack(cls, value, *, ctx=None):
        return cls.elem_type.pack(value.value, ctx=ctx)

    @classmethod
    def _call(cls, name_or_elem_type, elem_type=None, **flags):
        if not isinstance(name_or_elem_type, str):
            name      = cls.__name__
            elem_type = name_or_elem_type
        elif elem_type is None:
            raise ValueError("Must specify underlying type")
        else:
            name = name_or_elem_type

        return type(name, (cls,), dict(
            elem_type  = elem_type,
            value_type = cls.BitFlag(name, **flags),
        ))
