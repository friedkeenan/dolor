"""Asyncio utilities."""

import asyncio

class AsyncValueHolder:
    """An asynchronous value holder."""

    def __init__(self):
        self.event = asyncio.Event()

    async def get(self):
        """Waits until a value is set using :meth:`set` and then returns that value.

        Returns
        -------
        any
            The value set using :meth:`set`.
        """

        await self.event.wait()

        return self.value

    def set(self, value):
        """Sets the value to be gotten with :meth:`get`."""

        self.value = value
        self.event.set()
