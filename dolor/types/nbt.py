import abc

from .. import nbt
from .. import util
from .type import Type
from .string import Identifier

class NBT(Type):
    class Specialization(Type):
        tag       = None
        root_name = ""

        @classmethod
        @abc.abstractmethod
        def from_nbt(cls, data):
            raise NotImplementedError

        @classmethod
        @abc.abstractmethod
        def to_nbt(cls, value):
            raise NotImplementedError

        @classmethod
        def _unpack(cls, buf, *, ctx=None):
            data = nbt.load(buf)

            if not isinstance(data, cls.tag):
                raise ValueError(f"Expected {cls.tag}, got {type(data)}")

            if data.root_name != cls.root_name:
                raise ValueError(f"Mismatched root names; expected {repr(cls.root_name)}, got {repr(data.root_name)}")

            return cls.from_nbt(data)

        @classmethod
        def _pack(cls, value, *, ctx=None):
            data           = cls.to_nbt(value)
            data.root_name = cls.root_name

            return nbt.dump(data)

        @classmethod
        def _call(cls, *, root_name=""):
            return type(cls.__name__, (cls,), dict(
                root_name = root_name,
            ))

    class Default(Specialization):
        elem_tag = None

        @classmethod
        def from_nbt(cls, data):
            if issubclass(cls.elem_tag, NBT.Specialization):
                return cls.elem_tag.from_nbt(data)

            return data.value

        @classmethod
        def to_nbt(cls, value):
            if issubclass(cls.elem_tag, NBT.Specialization):
                return cls.elem_tag.to_nbt(value)

            return cls.elem_tag(value)

        @classmethod
        def _call(cls, elem_tag, default, *, root_name=""):
            return type(f"{cls.__name__}{elem_tag.__name__}", (cls,), dict(
                root_name = root_name,
                tag       = elem_tag.tag if issubclass(elem_tag, NBT.Specialization) else elem_tag,
                elem_tag  = elem_tag,
                _default  = default,
            ))

    class Boolean(Specialization):
        tag = nbt.Byte

        _default = False

        @classmethod
        def from_nbt(cls, data):
            return bool(data.value)

        @classmethod
        def to_nbt(cls, value):
            return cls.tag(int(value))

    class Identifier(Specialization):
        tag = nbt.String

        _default = Identifier.Identifier()

        @classmethod
        def from_nbt(cls, data):
            return Identifier.Identifier(data.value)

        @classmethod
        def to_nbt(cls, value):
            return cls.tag(str(value))

    class List(Specialization):
        tag = nbt.List

        list_tag = None

        _default = []

        @classmethod
        def from_nbt(cls, data):
            if issubclass(cls.list_tag, NBT.Specialization):
                return [cls.list_tag.from_nbt(cls.list_tag.tag(x)) for x in data.value]

            return data.value

        @classmethod
        def to_nbt(cls, value):
            if issubclass(cls.list_tag, NBT.Specialization):
                return nbt.List(cls.list_tag.tag)([cls.list_tag.to_nbt(x).value for x in value])

            return nbt.List(cls.list_tag)(value)

        @classmethod
        def _call(cls, tag, *, root_name=""):
            return type(f"{cls.__name__}({tag.__name__})", (cls,), dict(
                root_name = root_name,
                list_tag  = tag,
            ))

    class Optional(Specialization):
        """Used for marking fields in an NBT.Compound as optional"""

        @classmethod
        def from_nbt(cls, data):
            if issubclass(cls.tag, NBT.Specialization):
                return cls.tag.from_nbt(data)

            return data.value

        @classmethod
        def to_nbt(cls, value):
            if issubclass(cls.tag, NBT.Specialization):
                return cls.tag.to_nbt(value)

            return cls.tag(value)

        @classmethod
        def _call(cls, tag, *, root_name=""):
            return type(f"{cls.__name__}{tag.__name__}", (cls,), dict(
                root_name = root_name,
                tag       = tag,
            ))

    class Compound(Specialization):
        tag = nbt.Compound

        elems      = None
        value_type = None

        def __set__(self, instance, value):
            if isinstance(value, dict):
                value = self.value_type(value)

            super().__set__(instance, value)

        @classmethod
        def default(cls, *, ctx=None):
            defaults = {}

            for name, tag in cls.elems.items():
                if issubclass(tag, NBT.Optional):
                    continue
                elif issubclass(tag, NBT.Specialization):
                    defaults[name] = tag.default(ctx=ctx)
                else:
                    defaults[name] = tag().value

            return cls.value_type(defaults)

        @classmethod
        def from_nbt(cls, data):
            values = {}

            for name, tag in cls.elems.items():
                field = data.value.get(name)

                if field is None and issubclass(tag, NBT.Optional):
                    continue
                elif issubclass(tag, NBT.Specialization):
                    values[name] = tag.from_nbt(field)
                else:
                    if not isinstance(field, tag):
                        raise ValueError(f"Expected {tag}, got {type(field)}")

                    values[name] = field.value

            return cls.value_type(values)

        @classmethod
        def to_nbt(cls, value):
            data = cls.tag()

            for name, tag in cls.elems.items():
                field = value.get(name)

                if field is None and issubclass(tag, NBT.Optional):
                    continue
                elif issubclass(tag, NBT.Specialization):
                    data[name] = tag.to_nbt(field)
                else:
                    data[name] = tag(field)

            return data

        @classmethod
        def _call(cls, type_name=None, elems=None, *, root_name="", **kwargs):
            if type_name is None:
                type_name = cls.__name__

            if elems is None:
                elems = {}

            # Use fancy 3.9+ |= operator?
            elems.update(kwargs)

            return type(type_name, (cls,), dict(
                root_name  = root_name,
                elems      = elems,
                value_type = util.AttrDict(type_name)
            ))

    @classmethod
    def default(cls, *, ctx=None):
        return nbt.Compound(root_name="")

    @classmethod
    def _unpack(cls, buf, *, ctx=None):
        return nbt.load(buf)

    @classmethod
    def _pack(cls, value, *, ctx=None):
        return nbt.dump(value)
