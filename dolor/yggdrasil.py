import aiohttp
import uuid

class YggdrasilError(Exception):
    def __init__(self, status, info):
        self.status = status
        self.info = info

        msg = f"[{self.status}] {self.info['error']}: {self.info['errorMessage']}"

        cause = self.info.get("cause")
        if cause is not None:
            msg += f" (Cause: {cause}"

        super().__init__(msg)

class AuthenticationToken:
    auth_server = "https://authserver.mojang.com"
    headers = {"content-type": "application/json"}

    agent = {
        "name": "Minecraft",
        "version": 1,
    }

    class Profile:
        def __init__(self, name, id):
            self.name = name
            self.id = id

        def uuid(self):
            return uuid.UUID(hex=self.id)

    def __init__(self, *, access_token=None, client_token=None, username=None, password=None):
        if access_token is not None and client_token is None:
            raise ValueError("Access token without client token")

        if username is not None and password is None:
            raise ValueError("Username without password")

        if password is not None and username is None:
            raise ValueError("Password without username")

        self.access_token = access_token
        self.client_token = client_token
        self.username = username
        self.password = password

        self.profile = None

    async def ensure(self):
        if self.username is not None:
            await self.authenticate()
        else:
            # Refresh even with valid tokens so we get the player name
            await self.refresh()

    async def validate(self):
        data = {
            "accessToken": self.access_token,
            "clientToken": self.client_token,
        }

        try:
            await self.make_request("validate", data, 204)
            return True
        except YggdrasilError:
            return False

    async def refresh(self):
        data = {
            "accessToken": self.access_token,
            "clientToken": self.client_token,
        }

        info = await self.make_request("refresh", data)

        self.access_token = info["accessToken"]
        self.client_token = info["clientToken"]
        self.profile = self.Profile(info["selectedProfile"]["name"], info["selectedProfile"]["id"])

    async def authenticate(self, invalidate_prev=False):
        data = {
            "agent":    self.agent,
            "username": self.username,
            "password": self.password,
        }

        if not invalidate_prev:
            if self.client_token is None:
                data["clientToken"] = uuid.uuid4().hex
            else:
                data["clientToken"] = self.client_token

        info = await self.make_request("authenticate", data)

        self.access_token = info["accessToken"]
        self.client_token = info["clientToken"]
        self.profile = self.Profile(info["selectedProfile"]["name"], info["selectedProfile"]["id"])

    async def signout(self):
        data = {
            "username": self.username,
            "password": self.password,
        }

        await self.make_request("signout", data)

    async def invalidate(self):
        data = {
            "accessToken": self.access_token,
            "clientToken": self.client_token,
        }

        await self.make_request("invalidate", data)

    async def make_request(self, endpoint, data, ok_status_code=200):
        async with aiohttp.ClientSession() as s:
            async with s.post(f"{self.auth_server}/{endpoint}",
                json = data,
                headers = self.headers,
            ) as resp:
                if resp.status != ok_status_code:
                    raise YggdrasilError(resp.status, await resp.json())

                try:
                    return await resp.json()
                except aiohttp.ContentTypeError:
                    return None
