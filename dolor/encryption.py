import os
import hashlib
from cryptography.hazmat.primitives.serialization import load_der_public_key, Encoding, PublicFormat
from cryptography.hazmat.primitives.asymmetric.padding import PKCS1v15
from cryptography.hazmat.primitives.asymmetric.rsa import generate_private_key
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

def gen_shared_secret():
    return os.urandom(0x10)

def gen_server_hash(server_id, shared_secret, public_key):
    h = hashlib.sha1()

    h.update(server_id.encode("ascii"))
    h.update(shared_secret)
    h.update(public_key)

    return f"{int.from_bytes(h.digest(), byteorder='big', signed=True):x}"

def encrypt_secret_and_token(public_key, shared_secret, verify_token):
    key = load_der_public_key(public_key)

    enc_secret = key.encrypt(bytes(shared_secret), PKCS1v15())
    enc_token  = key.encrypt(bytes(verify_token),  PKCS1v15())

    return enc_secret, enc_token

def gen_cipher(shared_secret):
    return Cipher(algorithms.AES(shared_secret), modes.CFB8(shared_secret))

def format_public_key(public_key):
    return public_key.public_bytes(Encoding.DER, PublicFormat.SubjectPublicKeyInfo)

def gen_private_public_keys():
    private_key = generate_private_key(0x10001, 1024)
    public_key  = private_key.public_key()

    return private_key, format_public_key(public_key)

def gen_verify_token():
    return os.urandom(0x4)

def decrypt_secret_and_token(private_key, enc_secret, enc_token):
    shared_secret = private_key.decrypt(bytes(enc_secret), PKCS1v15())
    verify_token  = private_key.decrypt(bytes(enc_token),  PKCS1v15())

    return shared_secret, verify_token

# Don't inherit from io.IOBase because async file object
class EncryptedFileObject:
    def __init__(self, f, decryptor, encryptor):
        self.f = f

        self.decryptor = decryptor
        self.encryptor = encryptor

    async def read(self, length=-1):
        return self.decryptor.update(await self.f.read(length))

    async def readexactly(self, length):
        return self.decryptor.update(await self.f.readexactly(length))

    def write(self, b):
        return self.f.write(self.encryptor.update(b))

    async def drain(self):
        await self.f.drain()

    def write_eof(self):
        self.f.write_eof()

    def is_closing(self):
        return self.f.is_closing()

    def close(self):
        self.f.close()

    async def wait_closed(self):
        await self.f.wait_closed()
