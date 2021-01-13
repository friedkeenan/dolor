"""Code for interfacing with Mojang's Yggdrasil API."""

import aiohttp
import uuid

class YggdrasilError(Exception):
    """An error from the Yggdrasil API."""

    def __init__(self, status, info):
        self.status = status
        self.info   = info

        msg = f"[{self.status}] {self.info['error']}"

        error_message = self.info.get("errorMessage")
        if error_message is not None:
            msg += f": {error_message}"

        cause = self.info.get("cause")
        if cause is not None:
            msg += f" (Cause: {cause})"

        super().__init__(msg)

class AuthenticationToken:
    """An abstraction over the Yggdrasil API.

    Parameters
    ----------
    access_token : :class:`str`, optional
        The client's access token.
    client_token : :class:`str`, optional
        The client's client token. Must be present if `access_token` is specified.
    username : :class:`str`, optional
        The client's username.
    password : :class:`str`, optional
        The client's password. Must be present if `username` is specified.

    Attributes
    ----------
    profile : :class:`Profile` or None
        The authentication token's associated profile.
    """

    auth_server = "https://authserver.mojang.com"
    headers     = {"content-type": "application/json"}

    agent = {
        "name":    "Minecraft",
        "version": 1,
    }

    class Profile:
        """Represents the profile of an :class:`AuthenticationToken`."""

        def __init__(self, name, id):
            self.name = name
            self.id   = id

        @property
        def uuid(self):
            """A :class:`uuid.UUID` representation of the profile's id."""

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

    async def ensure(self, *, try_validate=False):
        """Ensures that the authentication token is authenticated.

        If :attr:`username` is populated, then :meth:`authenticate`
        will be run. Else, if `try_validate` is `True`, then it
        will see if the authentication token is valid by running
        :meth:`validate`. If it's not valid or `try_validate` is
        `False`, then :meth:`refresh` will be called.

        Parameters
        ----------
        try_validate : :class:`bool`
            Whether to try to validate before refreshing the token.
        """

        if self.username is not None:
            await self.authenticate()
        else:
            if not try_validate or not self.validate():
                await self.refresh()

    async def validate(self):
        """Checks whether the authentication token is valid.

        Requires the :attr:`access_token` attribute to be populated.

        Returns
        -------
        :class:`bool`
            Whether the authentication token is valid.
        """

        data = {
            "accessToken": self.access_token,
            "clientToken": self.client_token,
        }

        try:
            await self.make_request("validate", data, 204)
        except YggdrasilError:
            return False

        return True

    async def refresh(self):
        """Refreshes the authentication token.

        Requires the :attr:`access_token` attribute to be populated.

        Populates the :attr:`profile` attribute.
        """

        data = {
            "accessToken": self.access_token,
            "clientToken": self.client_token,
        }

        info = await self.make_request("refresh", data)

        self.access_token = info["accessToken"]
        self.client_token = info["clientToken"]
        self.profile      = self.Profile(info["selectedProfile"]["name"], info["selectedProfile"]["id"])

    async def authenticate(self, invalidate_prev=False):
        """Authenticates the authentication token.

        Requires the :attr:`username` attribute to be populated.

        Populates the :attr:`profile` attribute.

        Parameters
        ----------
        invalidate_prev : :class:`bool`
            Whether or not to invalidate previous access tokens.
        """

        data = {
            "agent":    self.agent,
            "username": self.username,
            "password": self.password,
        }

        if not invalidate_prev:
            data["clientToken"] = self.client_token or uuid.uuid4().hex

        info = await self.make_request("authenticate", data)

        self.access_token = info["accessToken"]
        self.client_token = info["clientToken"]
        self.profile      = self.Profile(info["selectedProfile"]["name"], info["selectedProfile"]["id"])

    async def signout(self):
        """Invalidates previous access tokens by using the username and password.

        Requires the :attr:`username` attribute to be populated.
        """

        data = {
            "username": self.username,
            "password": self.password,
        }

        await self.make_request("signout", data)

    async def invalidate(self):
        """Invalidates previous access tokens by using the access and client tokens.

        Requires the :attr:`access_token` attribute to be populated.
        """

        data = {
            "accessToken": self.access_token,
            "clientToken": self.client_token,
        }

        await self.make_request("invalidate", data)

    async def make_request(self, endpoint, data, ok_status_code=200):
        """A general function for making a request to the Yggdrasil API.

        Parameters
        ----------
        endpoint : :class:`str`
            The endpoint to make the request to.
        data : :class:`dict`
            The data to send.
        ok_status_code : :Class:`int`, optional
            The status code to expect. Any other will result
            in an :exc:`YggdrasilError`.

        Returns
        -------
        :class:`dict` or None
            The data received from the Yggdrasil API. None is
            returned if an :exc:`aiohttp.ContentTypeError`
            is raised when getting the data.

        Raises
        ------
        :exc:`YggdrasilError`
            If the returned status code is different than expected.
        """

        async with aiohttp.ClientSession() as s:
            async with s.post(f"{self.auth_server}/{endpoint}",
                json    = data,
                headers = self.headers,
            ) as resp:
                if resp.status != ok_status_code:
                    raise YggdrasilError(resp.status, await resp.json())

                try:
                    return await resp.json()
                except aiohttp.ContentTypeError:
                    return None
