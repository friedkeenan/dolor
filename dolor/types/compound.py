import collections

from .type import Type
from .version_switched import handle_dict_type

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
        return b"".join(x.pack(value[i]) for i, x in enumerate(cls.elems.values()))

    @classmethod
    def _call(cls, name=None, **elems):
        if name is None:
            name = cls.__name__

        elems = {x: handle_dict_type(y) for x, y in elems.items()}

        return cls.make_type(name,
            elems      = elems,
            value_type = collections.namedtuple(name, elems.keys()),
        )
