import collections

from .. import util
from .type import Type
from .util import prepare_types

class Compound(Type):
    elems      = None
    value_type = None

    @classmethod
    def _default(cls, *, ctx=None):
        return cls.value_type(*(x.default(ctx=ctx) for x in cls.elems.values()))

    @classmethod
    def _unpack(cls, buf, *, ctx=None):
        return cls.value_type(*(x.unpack(buf, ctx=ctx) for x in cls.elems.values()))

    @classmethod
    def _pack(cls, value, *, ctx=None):
        return b"".join(x.pack(value[i], ctx=ctx) for i, x in enumerate(cls.elems.values()))

    @classmethod
    @prepare_types
    def _call(cls, name=None, **elems: Type):
        name = util.default(name, cls.__name__)

        return cls.make_type(name,
            elems      = elems,
            value_type = collections.namedtuple(name, elems.keys()),
        )
