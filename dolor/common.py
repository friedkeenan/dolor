import asyncio
import io

from . import encryption
from .types import *

versions = {
    "1.15.2": 578,
}

class Protocol(asyncio.Protocol):
    def __init__(self, receiver):
        self.receiver = receiver

        self.buffer = bytearray()
        self.length = 0

        self.length_buf = b""

    def connection_made(self, transport):
        self.receiver.connection_made()

    def connection_lost(self, exc):
        self.receiver.connection_lost(exc)

    def data_received(self, data):
        self.buffer.extend(data)

        while len(self.buffer) != 0 and len(self.buffer) >= self.length:
            buf = io.BytesIO(self.buffer)

            # Perform decryption in the protocol because
            # the length is also encrypted
            if self.receiver.decryptor is not None:
                buf = encryption.EncryptedFileObject(buf, self.receiver.decryptor, self.receiver.encryptor)

            if self.length <= 0:
                # Sorta manually read length because we're
                # not guaranteed to have a full VarInt
                while True:
                    tmp = buf.read(1)
                    if len(tmp) < 1:
                        return

                    del self.buffer[:1]
                    self.length_buf += tmp

                    if tmp[0] & 0x80 == 0:
                        self.length = VarInt(self.length_buf, ctx=self.receiver.ctx).value
                        self.length_buf = b""

                        break

                    if len(self.length_buf) >= 5:
                        raise ValueError("VarInt is too big")

            if len(self.buffer) >= self.length:
                self.receiver.data_received(buf.read(self.length))

                del self.buffer[:self.length]
                self.length = 0

def packet_listener(*checkers):
    """
    A decorator for packet
    listeners within a class.

    checkers is the same as in
    Client.register_packet_listener.
    """

    def dec(func):
        # Set the checkers attribute to be later
        # recognized and registered by the class
        func.checkers = checkers

        return func

    return dec
