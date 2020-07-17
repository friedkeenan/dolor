import io
from ..types import *
from .. import util

class PacketContext:
    def __init__(self, proto=None):
        self.proto = proto

class Packet:
    id = None
    fields = None

    def __init__(self, buf=None, *, ctx=None, **kwargs):
        self.raw = util.Raw(self)
        self.raw.ctx = ctx

        if buf is not None:
            if isinstance(buf, (bytes, bytearray)):
                buf = io.BytesIO(buf)

            for attr_name, attr_type in self.enumerate_fields():
                if issubclass(attr_type, BaseArray):
                    if isinstance(attr_type.len_attr, str):
                        value = attr_type(buf, num_elems=getattr(self, attr_type.len_attr))
                    else:
                        value = attr_type(buf)
                else:
                    value = attr_type(buf)

                setattr(self.raw, attr_name, value)
        else:
            for attr_name, attr_type in self.enumerate_fields():
                setattr(self.raw, attr_name, attr_type())

        for attr, value in kwargs.items():
            setattr(self, attr, value)

    def __getattribute__(self, attr):
        v = object.__getattribute__(self, attr)
        if isinstance(v, Type):
            return v.value
        return v

    def __setattr__(self, attr, value):
        # Need this to avoid enumerating fields before self.ctx is set
        if attr == "raw":
            object.__setattr__(self, attr, value)
            return

        for attr_name, attr_type in self.enumerate_fields():
            if attr_name == attr:
                setattr(self.raw, attr, attr_type(value))
                break
        else:
            object.__setattr__(self, attr, value)

    def __repr__(self):
        ret = f"{type(self).__name__}("
        ret += ", ".join(f"{field}={repr(getattr(self, field))}" for field, _ in self.enumerate_fields())
        ret += ")"

        return ret

    def __bytes__(self):
        """
        Packs the id and the fields
        into a bytes object
        """

        ret = VarInt(self.get_id(self.ctx))

        for attr_name, _ in self.enumerate_fields():
            tmp = getattr(self.raw, attr_name)

            # Set the appropriate length attribute for an array
            if isinstance(tmp, BaseArray):
                if isinstance(tmp.len_attr, str):
                    tmp_len = getattr(self.raw, tmp.len_attr)
                    tmp_len.value = len(tmp.value) # Will also affect the type in ret

            ret += tmp

        return bytes(ret)

    def enumerate_fields(self):
        return self.get_fields(self.ctx).items()

    @classmethod
    def get_id(cls, ctx):
        """
        Should return the packet ID.

        If the ID needs to change based on the
        protocol version, use ctx.proto.
        """

        return cls.id

    @classmethod
    def get_fields(cls, ctx):
        """
        Should return a dict of the form
        {
            "attribute": Type
        }

        If the fields need to change based on the
        protocol version, use ctx.proto.
        """

        return cls.fields

class BaseGenericPacket(Packet):
    fields = {"data": RawByteArray()}

    def __repr__(self):
        return f"{type(self).__name__}(id={self.id:#x}, data={repr(self.data)})"

def GenericPacket(id):
    return type("GenericPacket", (BaseGenericPacket,), {"id": id})

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