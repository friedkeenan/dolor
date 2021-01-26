import io

from ..versions import Version, VersionSwitcher
from ..types import TypeContext, VarInt, RawByte, handle_dict_type

class PacketContext:
    def __init__(self, version=None):
        self.version = Version(version)

class Packet:
    id = None

    @classmethod
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)

        if hasattr(cls, "__annotations__"):
            to_change = {}

            for attr, attr_type in cls.__annotations__.items():
                new_type = handle_dict_type(attr_type)
                if new_type != attr_type:
                    to_change[attr] = new_type

                # Change this so type's constructor calls __set_name__?
                # Note: Names are set by type's constructor before
                # __init_subclass__ is called, so a metaclass would be needed.
                setattr(cls, attr, new_type.descriptor(attr))

            cls.__annotations__.update(to_change)
        else:
            cls.__annotations__ = {}

        if isinstance(cls.id, dict):
            cls.id = VersionSwitcher(cls.id)

    def __init__(self, *, buf=None, ctx=None, **kwargs):
        if buf is not None and isinstance(buf, (bytes, bytearray)):
            buf = io.BytesIO(buf)

        self._fields = {}
        for attr, attr_type in self.enumerate_fields():
            if buf is None:
                if attr in kwargs:
                    setattr(self, attr, kwargs[attr])
                else:
                    setattr(self, attr, attr_type.default(ctx=self.type_ctx(ctx)))
            else:
                setattr(self, attr, attr_type.unpack(buf, ctx=self.type_ctx(ctx)))

    def type_ctx(self, ctx):
        return TypeContext(self, ctx)

    def pack(self, *, ctx=None):
        return VarInt.pack(self.get_id(ctx=ctx), ctx=self.type_ctx(ctx)) + b"".join(y.pack(getattr(self, x), ctx=self.type_ctx(ctx)) for x, y in self.enumerate_fields())

    def _get_field(self, attr):
        return self._fields[attr]

    def _set_field(self, attr, value):
        self._fields[attr] = value

    def __repr__(self):
        ret = f"{type(self).__name__}("
        ret += ", ".join(f"{x}={repr(getattr(self, x))}" for x, _ in self.enumerate_fields())
        ret += ")"

        return ret

    @classmethod
    def enumerate_fields(cls):
        for attr, attr_type in cls.__annotations__.items():
            yield attr, attr_type

    @classmethod
    def unpack(cls, buf, *, ctx=None):
        return cls(buf=buf, ctx=ctx)

    @classmethod
    def get_id(cls, *, ctx=None):
        if isinstance(cls.id, VersionSwitcher):
            return cls.id[ctx.version]

        return cls.id

class GenericPacketMeta(type):
    """Used for overriding issubclass and isinstance checks."""

    def __subclasscheck__(self, subclass):
        if type(subclass) is not type(self):
            return False

        if self.id is None:
            return True

        return self.id == subclass.id

    def __instancecheck__(self, instance):
        return issubclass(type(instance), self)

    def __eq__(self, other):
        if not issubclass(other, GenericPacket):
            return False

        return self.id == other.id

    def __hash__(self):
        return hash(self.id)

class GenericPacket(Packet, metaclass=GenericPacketMeta):
    data: RawByte[None]

    def __new__(cls, id=None, **kwargs):
        if id is None:
            if cls.id is None:
                raise TypeError("Use of GenericPacket without setting its id")

            return super().__new__(cls)

        return type(f"{cls.__name__}({id:#x})", (cls,), dict(
            id = id,
        ))

# Classes used for inheritance to know where a packet is bound and what state it's used in
class ServerboundPacket(Packet):
    pass

class ClientboundPacket(Packet):
    pass

class HandshakingPacket(Packet):
    pass

class StatusPacket(Packet):
    pass

class LoginPacket(Packet):
    pass

class PlayPacket(Packet):
    pass
