"""Encryption used for authentication between the server and client."""

import os
import hashlib
from cryptography.hazmat.primitives.serialization import load_der_public_key, Encoding, PublicFormat
from cryptography.hazmat.primitives.asymmetric.padding import PKCS1v15
from cryptography.hazmat.primitives.asymmetric.rsa import generate_private_key
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

def gen_shared_secret():
    """Generates the shared secret to be encrypted and sent to the server.

    Returns
    -------
    :class:`bytes`
        The shared secret.
    """

    return os.urandom(0x10)

def gen_server_hash(server_id, shared_secret, public_key):
    """Generates the server hash for use in authentication.

    Parameters
    ----------
    server_id : :class:`str`
        The server id found in :class:`~.EncryptionRequestPacket`.
    shared_secret
        The shared secret gotten from :func:`gen_shared_secret`.
    public_key
        The public key found in :class:`~.EncryptionRequestPacket`.

    Returns
    -------
    :class:`str`
        The server hash.
    """

    h = hashlib.sha1()

    h.update(server_id.encode("ascii"))
    h.update(shared_secret)
    h.update(public_key)

    return f"{int.from_bytes(h.digest(), byteorder='big', signed=True):x}"

def encrypt_secret_and_token(public_key, shared_secret, verify_token):
    """Encrypts the secret and token with the server's public key.

    Parameters
    ----------
    public_key
        The public key found in :class:`~.EncryptionRequestPacket`.
    shared_secret
        The shared secret gotten from :func:`gen_shared_secret`.
    verify_token
        The verify token found in :class:`~.EncryptionRequestPacket`.

    Returns
    -------
    enc_secret : :class:`bytes`
        The encrypted shared secret.
    enc_token : :class:`bytes`
        The encrypted verify token.
    """

    key = load_der_public_key(public_key)

    enc_secret = key.encrypt(bytes(shared_secret), PKCS1v15())
    enc_token  = key.encrypt(bytes(verify_token),  PKCS1v15())

    return enc_secret, enc_token

def gen_cipher(shared_secret):
    """Generates a :class:`cryptography.hazmat.primitives.ciphers.Cipher` from a shared secret.

    Parameters
    ----------
    shared_secret
        The shared secret gotten from :func:`gen_shared_secret`.

    Returns
    -------
    :class:`cryptography.hazmat.primitives.ciphers.Cipher`
        The cipher based on the shared secret.
    """

    return Cipher(algorithms.AES(shared_secret), modes.CFB8(shared_secret))

def format_public_key(public_key):
    """Formats a public key to DER format.

    Parameters
    ----------
    public_key
        The unformatted public key.

    Returns
    -------
    :class:`bytes`
        The DER formatted public key.
    """

    return public_key.public_bytes(Encoding.DER, PublicFormat.SubjectPublicKeyInfo)

def gen_private_public_keys():
    """Generates the private and public keys used by the server.

    Returns
    -------
    private_key : :class:`cryptography.hazmat.primitives.asymmetric.rsa.RSAPrivateKey`
        The private key.
    public_key : :class:`bytes`
        The public key, already formatted with :func:`format_public_key`.
    """

    private_key = generate_private_key(0x10001, 1024)
    public_key  = private_key.public_key()

    return private_key, format_public_key(public_key)

def gen_verify_token():
    """Generates the verify token sent to the client.

    Returns
    -------
    :class:`bytes`
        The verify token.
    """

    return os.urandom(0x4)

def decrypt_secret_and_token(private_key, enc_secret, enc_token):
    """Decrypts the shared secret and token with the server's private key.

    Parameters
    ----------
    private_key
        The private key generated with :func:`gen_private_public_keys`.
    enc_secret
        The encrypted shared secret found in :class:`~.EncryptionResponsePacket`.
    enc_token
        The encrypted verify token found in :class:`~.EncryptionResponsePacket`.

    Returns
    -------
    shared_secret : :class:`bytes`
        The decrypted shared secret.
    verify_token : :class:`bytes`
        The decrypted verify token.
    """

    shared_secret = private_key.decrypt(bytes(enc_secret), PKCS1v15())
    verify_token  = private_key.decrypt(bytes(enc_token),  PKCS1v15())

    return shared_secret, verify_token

# TODO: Inherit from asyncio.StreamReader, asyncio.StreamWriter?
class EncryptedStream:
    """An asyncio stream that wraps another stream and decrypts/encrypts it.

    Parameters
    ----------
    f
        The stream to wrap.
    decryptor
        The decryptor used to decrypt data read from the stream.
    encryptor
        The encryptor used to encrypt data written to the stream.
    """

    def __init__(self, f, decryptor, encryptor):
        self.f = f

        self.decryptor = decryptor
        self.encryptor = encryptor

    async def read(self, length=-1):
        """Reads and decrypts data from the wrapped stream.

        Parameters
        ----------
        length : :class:`int`, optional
            The maximum of how many bytes to read.
            If -1, all data will be read.

        Returns
        -------
        :class:`bytes`
            The decrypted data.
        """

        return self.decryptor.update(await self.f.read(length))

    async def readexactly(self, length):
        """Reads and decrypts an exact amount of data from the wrapped stream.

        Parameters
        ----------
        length : :class:`int`
            The length to read.

        Returns
        -------
        :class:`bytes`
            The decrypted data.

        Raises
        ------
        :exc:`asyncio.IncompleteReadError`
            If EOF is reached before ``length`` can be read.
        """

        return self.decryptor.update(await self.f.readexactly(length))

    def write(self, data):
        """Encrypts and writes data to the wrapped stream.

        Should be used along with the :meth:`drain` method.

        Parameters
        ----------
        data : :class:`bytes`
            The data to write.
        """

        return self.f.write(self.encryptor.update(data))

    async def drain(self):
        """Waits until it is appropriate to resume writing to the stream."""

        await self.f.drain()

    def is_closing(self):
        """Checks if the stream is closed or being closed.

        Returns
        -------
        :class:`bool`
            Whether the stream is closed or being closed.
        """

        return self.f.is_closing()

    def close(self):
        """Closes the stream.

        Should be used along with the :meth:`wait_closed` method.
        """

        self.f.close()

    async def wait_closed(self):
        """Waits until the stream is closed."""

        await self.f.wait_closed()
