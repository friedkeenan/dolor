import collections

from .type import Type

class NBT(Type):
    class Compound(Type):
        base = None

        root_name  = None
        elems      = None
        value_type = None

        @classmethod
        def default(cls, *, ctx=None):
            defaults = []

            for tag in cls.elems.values():
                if issubclass(tag, cls.base):
                    defaults.append(tag.default(ctx=ctx))
                else:
                    defaults.append(tag().value)

            return cls.value_type(*defaults)

        @classmethod
        def from_nbt(cls, compound):
            values = []

            for name, tag in cls.elems.items():
                if issubclass(tag, cls.base):
                    values.append(tag.from_nbt(compound[name]))
                else:
                    field = compound[name]

                    if not isinstance(field, tag):
                        raise ValueError(f"Expected {tag}, got {type(field)}")

                    values.append(field.value)

            return cls.value_type(*values)

        @classmethod
        def to_nbt(cls, value):
            from .. import nbt

            compound = nbt.Compound()

            for name, tag in cls.elems.items():
                field = getattr(value, name)

                if issubclass(tag, cls.base):
                    compound[name] = tag.to_nbt(field)
                else:
                    compound[name] = tag()

            return compound

        @classmethod
        def _unpack(cls, buf, *, ctx=None):
            from .. import nbt

            compound = nbt.load(buf)
            if not isinstance(compound, nbt.Compound):
                raise ValueError(f"Expected {nbt.compound}, got {type(compound)}")

            if compound.root_name != cls.root_name:
                raise ValueError(f"Mismatched root names; expected {repr(cls.root_name)}, got {repr(compound.root_name)}")

            return cls.from_nbt(compound)

        @classmethod
        def _pack(cls, value, *, ctx=None):
            from .. import nbt

            compound           = cls.to_nbt(value)
            compound.root_name = cls.root_name

            return nbt.dump(compound)

        @classmethod
        def _call(cls, name=None, *, root_name="", **elems):
            if name is None:
                name = cls.__name__

            return type(name, (cls,), dict(
                base = cls,

                root_name  = root_name,
                elems      = elems,
                value_type = collections.namedtuple(name, elems.keys())
            ))

    @classmethod
    def default(cls, *, ctx=None):
        from .. import nbt

        return nbt.Compound(root_name="")

    @classmethod
    def _unpack(cls, buf, *, ctx=None):
        from .. import nbt

        return nbt.load(buf)

    @classmethod
    def _pack(cls, value, *, ctx=None):
        from .. import nbt

        return nbt.dump(value)
