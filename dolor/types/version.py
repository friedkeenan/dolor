from ..versions import VersionSwitcher
from .type import Type
from .misc import EmptyType

class VersionSwitchedType(Type):
    switcher = None

    @classmethod
    def value_type(cls, *, ctx=None):
        ret = cls.switcher[ctx.version]

        if ret is None:
            return EmptyType

        return ret

    @classmethod
    def _default(cls, *, ctx=None):
        return cls.value_type(ctx=ctx).default(ctx=ctx)

    @classmethod
    def _unpack(cls, buf, *, ctx=None):
        return cls.value_type(ctx=ctx).unpack(buf, ctx=ctx)

    @classmethod
    def _pack(cls, value, *, ctx=None):
        return cls.value_type(ctx=ctx).pack(value, ctx=ctx)

    @classmethod
    def _call(cls, switch):
        return cls.make_type(cls.__name__,
            switcher = VersionSwitcher(switch),
        )
