from .type import Type

class NBT(Type):
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
