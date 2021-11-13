"""Asynchronous I/O utilities."""

import asyncio

class AsyncValueHolder:
    """An asynchronous value holder."""

    def __init__(self):
        self._event = asyncio.Event()

    async def get(self):
        """Gets the held value, waiting until a value is held.

        A value is not held until the :meth:`set` method is called.

        Returns
        -------
        any
            The held value.
        """

        await self._event.wait()

        return self._value

    def set(self, value):
        """Sets the held value.

        The held value should be acquired using the :meth:`get` method.

        Parameters
        ----------
        value
            The value to hold.
        """

        self._value = value

        self._event.set()
