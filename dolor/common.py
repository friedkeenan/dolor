import asyncio
import io

from . import enums
from . import util
from . import encryption
from .types import VarInt
from .packets import HandshakingPacket, StatusPacket, LoginPacket, PlayPacket

versions = {
    "1.16.4": 754,
}

def gen_packet_info(state, bound, *, ctx=None):
    state_class = {
        enums.State.Handshaking: HandshakingPacket,
        enums.State.Status:      StatusPacket,
        enums.State.Login:       LoginPacket,
        enums.State.Play:        PlayPacket,
    }[state]

    ret = {}

    for c in util.get_subclasses(state_class) & util.get_subclasses(bound):
        id = c.get_id(ctx=ctx)

        if id is not None:
            ret[id] = c

    return ret

class ClientServerProtocol(asyncio.Protocol):
    def __init__(self, receiver):
        self.receiver = receiver

        self.buffer = bytearray()
        self.length = -1

    @property
    def ctx(self):
        try:
            return self.receiver.ctx
        except AttributeError:
            return None

    def connection_made(self, transport):
        self.receiver.connection_made(transport)

    def connection_lost(self, exc):
        self.receiver.connection_lost(exc)

    def data_received(self, data):
        self.buffer.extend(data)

        while len(self.buffer) >= self.length:
            buf = io.BytesIO(self.buffer)

            # Perform decryption in the protocol because
            # the length is also encrypted
            if self.receiver.decryptor is not None:
                buf = encryption.EncryptedFileObject(buf, self.receiver.decryptor, self.receiver.encryptor)

            if self.length < 0:
                try:
                    self.length = VarInt.unpack(buf, ctx=self.ctx)
                except:
                    return

                del self.buffer[:buf.tell()]

            if len(self.buffer) >= self.length:
                self.receiver.data_received(buf.read(self.length))

                del self.buffer[:self.length]
                self.length = -1

def packet_listener(*checkers):
    """Decorator for packet listeners within a class."""

    def dec(func):
        # Set the _checkers attribute to be later
        # recognized and registered by the class
        func._checkers = checkers

        return func

    return dec
