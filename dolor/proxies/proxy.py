import asyncio
import aiohttp

from .. import enums
from .. import encryption
from .. import connection
from ..packet_handler import PacketHandler, packet_listener
from ..versions import Version
from ..types import Chat
from ..packets import PacketContext, ServerboundPacket, ClientboundPacket, serverbound, clientbound
from ..yggdrasil import AuthenticationToken

class ClientProxyConnection(connection.Connection):
    def __init__(self, proxy, reader, writer):
        self.ctx = PacketContext(Version(None))

        super().__init__(serverbound)

        self.proxy = proxy

        self.reader = reader
        self.writer = writer

        self.server = None

    async def write_packet(self, *args, **kwargs):
        p = await super().write_packet(*args, **kwargs)

        await self.proxy.listen_to_packet(self, self.server, p, bound=clientbound, outgoing=True)

        return p

    def close(self):
        super().close()

        if self.server is not None and not self.server.is_closing():
            self.server.close()

class ServerProxyConnection(connection.Connection):
    def __init__(self, proxy, client, reader, writer):
        self.ctx = PacketContext(Version(None))

        super().__init__(clientbound)

        self.proxy  = proxy
        self.client = client

        self.reader = reader
        self.writer = writer

    async def write_packet(self, *args, **kwargs):
        p = await super().write_packet(*args, **kwargs)

        await self.proxy.listen_to_packet(self.client, self, p, bound=serverbound, outgoing=True)

        return p

    def close(self):
        super().close()

        if not self.client.is_closing():
            self.client.close()

class Proxy(PacketHandler):
    session_server = "https://sessionserver.mojang.com/session/minecraft"

    ClientConnection = ClientProxyConnection
    ServerConnection = ServerProxyConnection

    def __init__(self, server_address, server_port=25565, *,
        lang_file = None,

        host_address = "localhost",
        host_port    = 25565,

        auth = None,
    ):
        self.server_address = server_address
        self.server_port    = server_port

        self.host_address = host_address
        self.host_port    = host_port

        self.auth = auth

        self.srv         = None
        self.connections = []

        if lang_file is not None:
            Chat.Chat.load_translations(lang_file)

        super().__init__()

    def register_packet_listener(self, func, *checkers, bound=None, outgoing=False):
        if bound is None:
            if all(isinstance(x, type) and issubclass(x, ServerboundPacket) for x in checkers):
                bound = serverbound
            elif all(isinstance(x, type) and issubclass(x, ClientboundPacket) for x in checkers):
                bound = clientbound
            else:
                ValueError("Bound should have been specified")

        super().register_packet_listener(func, *checkers, bound=bound, outgoing=outgoing)

    async def listen_to_packet(self, c, s, p, *, bound, outgoing):
        if bound is serverbound:
            conn = s if outgoing else c
        else:
            conn = c if outgoing else s

        listeners = self.listeners_for_packet(conn, p, bound=bound, outgoing=outgoing)

        results = await asyncio.gather(*(x(c, s, p) for x in listeners))

        if not outgoing:
            results = [x for x in results if x is not None]

            if all(results):
                if bound is serverbound:
                    await s.write_packet(p)
                else:
                    await c.write_packet(p)

    async def listen(self, c, s):
        if isinstance(c, self.ServerConnection):
            tmp = c
            c   = s
            s   = tmp

            conn  = s
            bound = clientbound
        else:
            conn  = c
            bound = serverbound

        while self.is_serving() and not c.is_closing() and not s.is_closing():
            p = await conn.read_packet()
            if p is None:
                break

            await self.listen_to_packet(c, s, p, bound=bound, outgoing=False)

    async def new_connection(self, c_reader, c_writer):
        c = self.ClientConnection(self, c_reader, c_writer)

        s_reader, s_writer = await asyncio.open_connection(self.server_address, self.server_port)
        s = self.ServerConnection(self, c, s_reader, s_writer)

        c.server = s

        async with c, s:
            self.connections.append(c)

            try:
                await asyncio.gather(self.listen(c, s), self.listen(s, c))
            finally:
                self.connections.remove(c)

    def is_serving(self):
        return self.srv is not None and self.srv.is_serving()

    def close(self):
        if self.srv is not None:
            self.srv.close()

    async def wait_closed(self):
        if self.srv is not None:
            await self.srv.wait_closed()

    def __del__(self):
        self.close()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_value, exc_tb):
        self.close()
        await self.wait_closed()

    async def startup(self):
        self.srv = await asyncio.start_server(self.new_connection, self.host_address, self.host_port)

    async def on_start(self):
        await self.srv.serve_forever()

    async def start(self):
        await self.startup()

        async with self:
            await self.on_start()

    def run(self):
        try:
            asyncio.run(self.start())
        except KeyboardInterrupt:
            self.close()

    async def send_server_hash(self, c, server_hash):
        async with aiohttp.ClientSession() as s:
            async with s.post(f"{self.session_server}/join",
                json = {
                    "accessToken":     c.auth_token.access_token,
                    "selectedProfile": c.auth_token.profile.id,
                    "serverId":        server_hash,
                },
                headers = {"content-type": "application/json"},
            ) as resp:
                if resp.status != 204:
                    raise ValueError("Invalid status code from session server")

    # Default packet listeners

    @packet_listener(serverbound.HandshakePacket)
    async def _on_handshake(self, c, s, p):
        c.ctx = s.ctx = PacketContext(Version(p.proto_version))

        c.current_state = s.current_state = p.next_state

        p.server_address = self.server_address
        p.server_port    = self.server_port

        await s.write_packet(p)

        return False

    @packet_listener(serverbound.LoginStartPacket)
    async def _on_login_start(self, c, s, p):
        c.name = p.name

    @packet_listener(clientbound.EncryptionRequestPacket)
    async def _on_encryption_request(self, c, s, p):
        # Handle authentication and encryption ourselves so
        # that the client never receives the EncryptionRequestPacket,
        # and thus thinks that the server is an offline
        # server, so it doesn't try to authenticate while
        # still allowing us to read its packets.
        #
        # We *could* generate our own private/public keys
        # to get the client's shared secret, but then it
        # would use the proxy's public key to calculate
        # the server hash instead of the server's public
        # key, leading to authentication failing.

        if c.name in self.auth:
            c.auth_token = AuthenticationToken(**self.auth[c.name])
        else:
            c.auth_token = AuthenticationToken(**self.auth)

        await c.auth_token.ensure(try_validate=True)

        shared_secret = encryption.gen_shared_secret()
        server_hash   = encryption.gen_server_hash(p.server_id, shared_secret, p.public_key)

        await self.send_server_hash(c, server_hash)

        enc_secret, enc_token = encryption.encrypt_secret_and_token(p.public_key, shared_secret, p.verify_token)

        await s.write_packet(serverbound.EncryptionResponsePacket,
            shared_secret = enc_secret,
            verify_token  = enc_token,
        )

        s.enable_encryption(shared_secret)

        return False

    @packet_listener(clientbound.SetCompressionPacket)
    async def _on_set_compression(self, c, s, p):
        # Write the packet before setting the compressing threshold
        # so that the packet gets sent uncompressed
        await c.write_packet(p)

        c.comp_threshold = s.comp_threshold = p.threshold

        return False

    @packet_listener(clientbound.LoginSuccessPacket)
    async def _on_login_success(self, c, s, p):
        c.current_state = s.current_state = enums.State.Play
