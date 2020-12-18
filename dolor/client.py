import asyncio
import aiohttp
import time

from . import enums
from . import util
from . import encryption
from . import connection
from .packet_handler import packet_listener, PacketHandler
from .versions import Version
from .types import Chat
from .packets import PacketContext, ClientboundPacket, serverbound, clientbound
from .yggdrasil import AuthenticationToken

class Client(connection.Connection, PacketHandler):
    session_server = "https://sessionserver.mojang.com/session/minecraft"

    def __init__(self, version, address, port=25565, *,
        access_token = None,
        client_token = None,
        username     = None,
        password     = None,
        lang_file    = None,
    ):
        version  = Version(version, check_supported=True)
        self.ctx = PacketContext(version)

        self.address = address
        self.port    = port

        self.auth_token = AuthenticationToken(
            access_token = access_token,
            client_token = client_token,
            username     = username,
            password     = password,
        )

        if lang_file is not None:
            Chat.Chat.load_translations(lang_file)

        self.should_listen_sequentially = True

        # TODO: Figure out a way to do this with super
        connection.Connection.__init__(self, ClientboundPacket)
        PacketHandler.__init__(self)

    async def send_server_hash(self, server_hash):
        async with aiohttp.ClientSession() as s:
            async with s.post(f"{self.session_server}/join",
                json = {
                    "accessToken":     self.auth_token.access_token,
                    "selectedProfile": self.auth_token.profile.id,
                    "serverId":        server_hash,
                },
                headers = {"content-type": "application/json"},
            ) as resp:
                if resp.status != 204:
                    raise ValueError(f"Invalid status code from session server: {resp.status}")

    async def listen_step(self):
        p = await self.read_packet()
        if p is None:
            return

        tasks = []

        for func, checker in self.packet_listeners.items():
            if checker(self, p):
                if self.should_listen_sequentially:
                    tasks.append(func(p))
                else:
                    asyncio.create_task(func(p))

        if self.should_listen_sequentially:
            await asyncio.gather(*tasks)

    async def on_start(self):
        await self.login()

    async def start(self):
        self.reader, self.writer = await asyncio.open_connection(self.address, self.port)

        await self.on_start()

    def run(self):
        try:
            asyncio.run(self.start())
        except KeyboardInterrupt:
            self.close()

    async def status(self):
        if self.current_state != enums.State.Handshaking:
            raise ValueError(f"Invalid state: {self.current_state}")

        await self.write_packet(serverbound.HandshakePacket,
            proto_version  = self.ctx.version.proto,
            server_address = self.address,
            server_port    = self.port,
            next_state     = enums.State.Status,
        )

        self.current_state = enums.State.Status

        await self.write_packet(serverbound.RequestPacket)
        resp = await self.read_packet()

        await self.write_packet(serverbound.PingPacket,
            payload = int(time.time() * 1000),
        )
        pong = await self.read_packet()

        self.close()

        return resp.response, int(time.time() * 1000) - pong.payload

    async def login(self):
        if self.current_state != enums.State.Handshaking:
            raise ValueError(f"Invalid state: {self.current_state}")

        await self.auth_token.ensure()

        self.should_listen_sequentially = True

        await self.write_packet(serverbound.HandshakePacket,
            proto_version = self.ctx.version.proto,
            server_address = self.address,
            server_port = self.port,
            next_state = enums.State.Login,
        )

        self.current_state = enums.State.Login

        await self.write_packet(serverbound.LoginStartPacket,
            name = self.auth_token.profile.name,
        )

        while not self.is_closing():
            await self.listen_step()

    # Default packet listeners

    @packet_listener(clientbound.DisconnectLoginPacket, clientbound.DisconnectPlayPacket)
    async def _on_disconnect(self, p):
        print("Disconnected:", p.reason.flatten())

        self.close()
        await self.wait_closed()

    @packet_listener(clientbound.EncryptionRequestPacket)
    async def _on_encryption_request(self, p):
        shared_secret = encryption.gen_shared_secret()
        server_hash   = encryption.gen_server_hash(p.server_id, shared_secret, p.public_key)

        await self.send_server_hash(server_hash)

        enc_secret, enc_token = encryption.encrypt_secret_and_token(p.public_key, shared_secret, p.verify_token)

        await self.write_packet(serverbound.EncryptionResponsePacket,
            shared_secret = enc_secret,
            verify_token  = enc_token,
        )

        cipher = encryption.gen_cipher(shared_secret)
        self.reader = encryption.EncryptedFileObject(self.reader, cipher.decryptor(), None)
        self.writer = encryption.EncryptedFileObject(self.writer, None, cipher.encryptor())

    @packet_listener(clientbound.SetCompressionPacket)
    async def _on_set_compression(self, p):
        self.comp_threshold = p.threshold

    @packet_listener(clientbound.LoginSuccessPacket)
    async def _on_login_success(self, p):
        self.current_state = enums.State.Play

        self.should_listen_sequentially = False

    @packet_listener(clientbound.KeepAlivePacket)
    async def _on_keep_alive(self, p):
        await self.write_packet(serverbound.KeepAlivePacket,
            keep_alive_id = p.keep_alive_id,
        )
