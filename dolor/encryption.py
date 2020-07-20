import os
import hashlib
import io
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.serialization import load_der_public_key
from cryptography.hazmat.primitives.asymmetric.padding import PKCS1v15
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

def gen_shared_secret():
    return os.urandom(0x10)

def gen_server_hash(server_id, shared_secret, pub_key):
    h = hashlib.sha1()

    h.update(server_id.encode("utf-8"))
    h.update(shared_secret)
    h.update(pub_key)

    return f"{int.from_bytes(h.digest(), byteorder='big', signed=True):x}"

def encrypt_secret_and_token(pub_key, shared_secret, verify_token):
    key = load_der_public_key(pub_key, default_backend())

    enc_secret = key.encrypt(bytes(shared_secret), PKCS1v15())
    enc_token = key.encrypt(bytes(verify_token), PKCS1v15())

    return enc_secret, enc_token

def gen_cipher(shared_secret):
    return Cipher(algorithms.AES(shared_secret), modes.CFB8(shared_secret), default_backend())

class EncryptedFileObject(io.IOBase):
    def __init__(self, f, decryptor, encryptor):
        self.f = f
        self.decryptor = decryptor
        self.encryptor = encryptor

    def read(self, length=-1):
        return self.decryptor.update(self.f.read(length))

    def write(self, b):
        return self.f.write(self.encryptor.update(b))
