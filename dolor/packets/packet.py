import io
from ..types import *

class Raw:
    def __init__(self, owner):
        self.owner = owner

    def __getattr__(self, attr):
        return self.owner.__dict__[attr]

class Packet:
    def __init__(self, buf=None, **kwargs):
        self.raw = Raw(self)

        if buf is not None:
            if isinstance(buf, (bytes, bytearray)):
                buf = io.BytesIO(buf)

            length = VarInt(buf).value
            buf = io.BytesIO(buf.read(length))

            id = VarInt(buf).value
            if id != self.id:
                raise ValueError(f"Incorrect packet ID for {type(self).__name__}: {hex(id)}")

            for attr_name, attr_type in self.enumerate_fields():
                if issubclass(attr_type, BaseArray):
                    if attr_type.len_attr is None:
                        value = attr_type(buf.read())
                    elif isinstance(attr_type.len_attr, int):
                        value = attr_type(buf)
                    else:
                        value = attr_type(buf, num_elems=getattr(self, attr_type.len_attr))
                else:
                    value = attr_type(buf)

                object.__setattr__(self, attr_name, value)

        for attr, value in kwargs.items():
            setattr(self, attr, value)

    def __getattribute__(self, attr):
        if attr == "raw":
            return self.__dict__["raw"]

        v = object.__getattribute__(self, attr)
        if isinstance(v, Type):
            return v.value
        return v

    def __setattr__(self, attr, value):
        if attr == "raw":
            return object.__setattr__(self, attr, value)

        for attr_name, attr_type in self.enumerate_fields():
            if attr_name == attr:
                object.__setattr__(self, attr, attr_type(value))
                break
        else:
            object.__setattr__(self, attr, value)

    def __repr__(self):
        ret = f"{type(self).__name__}("
        ret += ", ".join(f"{field}={repr(getattr(self, field))}" for field,_ in self.enumerate_fields())
        ret += ")"

        return ret

    def __bytes__(self):
        ret = bytes(VarInt(self.id)) + b"".join(bytes(getattr(self.raw, x[0])) for x in self.enumerate_fields())
        ret = bytes(VarInt(len(ret))) + ret
        return ret

    def enumerate_fields(self):
        for field in self.fields:
            items = tuple(field.items())
            yield items[0][0], items[0][1]

    @property
    def id(self):
        """
        Should return the packet ID.

        If the ID needs to change based on the
        protocol version, self.proto should be
        set before accessing this.
        """

        raise NotImplementedError
    
    def fields(self):
        """
        Should return a list of the form
        [
            {"attribute": Type}
        ]

        If the fields need to change based on the
        protocol version, self.proto should be
        set before accessing this.
        """

        raise NotImplementedError

# Classes used for inheritance to know where a packet is bound and what state it's used in
class ServerboundPacket(Packet):
    pass

class ClientboundPacket(Packet):
    pass

class HandshakingPacket(Packet):
    pass

class PlayPacket(Packet):
    pass

class StatusPacket(Packet):
    pass

class LoginPacket(Packet):
    pass