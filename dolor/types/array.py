import inspect

from .type import Type
from .misc import RawByte

class Array(Type):
    elem_type = None
    size = None

    @classmethod
    def is_raw_byte(cls):
        return cls.elem_type == RawByte

    @classmethod
    def is_fixed_size(cls):
        return isinstance(cls.size, int)

    @classmethod
    def is_prefixed_by_type(cls):
        return isinstance(cls.size, type) and issubclass(cls.size, Type)

    @classmethod
    def has_size_function(cls):
        return inspect.isfunction(cls.size)

    @classmethod
    def should_read_until_end(cls):
        return cls.size is None

    @classmethod
    def real_size(cls, *, ctx=None):
        if cls.is_fixed_size():
            return cls.size

        if cls.is_prefixed_by_type():
            return cls.size.default(ctx=ctx)

        if cls.has_size_function():
            return cls.size(ctx.instance)

        return 0

    def __set__(self, instance, value):
        if self.is_raw_byte():
            value = bytearray(value)

        super().__set__(instance, value)

    @classmethod
    def default(cls, *, ctx=None):
        if cls.is_raw_byte():
            return bytearray(cls.real_size(ctx=ctx))

        return [cls.elem_type.default(ctx=ctx) for x in range(cls.real_size(ctx=ctx))]

    @classmethod
    def _unpack(cls, buf, *, ctx=None):
        if cls.should_read_until_end():
            if cls.is_raw_byte():
                return bytearray(buf.read())

            ret = []
            while True:
                try:
                    ret.append(cls.elem_type.unpack(buf, ctx=ctx))
                except:
                    return ret

        if cls.is_prefixed_by_type():
            size = cls.size.unpack(buf, ctx=ctx)

            if cls.is_raw_byte():
                return bytearray(buf.read(size))

            return [cls.elem_type.unpack(buf, ctx=ctx) for x in range(size)]

        if cls.is_raw_byte():
            return bytearray(buf.read(cls.real_size(ctx=ctx)))

        return [cls.elem_type.unpack(buf, ctx=ctx) for x in range(cls.real_size(ctx=ctx))]

    @classmethod
    def _pack(cls, value, *, ctx=None):
        if cls.should_read_until_end():
            if cls.is_raw_byte():
                return bytes(value)

            return b"".join(cls.elem_type.pack(x, ctx=ctx) for x in value)

        if cls.is_prefixed_by_type():
            prefix = cls.size.pack(len(value), ctx=ctx)

            if cls.is_raw_byte():
                return prefix + bytes(value)

            return prefix + b"".join(cls.elem_type.pack(x, ctx=ctx) for x in value)

        size = cls.real_size(ctx=ctx)

        if cls.is_raw_byte():
            return bytes(value[:size]) + bytes(max(0, size - len(value)))

        value = value[:size] + [cls.elem_type.default(ctx=ctx) for x in range(size - len(value))]

        return b"".join(cls.elem_type.pack(x, ctx=ctx) for x in value)

    @classmethod
    def _call(cls, elem_type, size=None):
        if isinstance(size, str):
            attr = size
            size = lambda x: getattr(x, attr)

        return type(f"{elem_type.__name__}Array", (cls,), dict(
            elem_type = elem_type,
            size      = size,
        ))
