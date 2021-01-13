"""Code for packet handling."""

import abc
import asyncio
import inspect

def packet_listener(*checkers, **kwargs):
    """Decorator for internal packet listeners, packet listeners that are methods.

    Parameters
    ----------
    checkers, kwargs
        See :meth:`PacketHandler.register_packet_listener`.

    Returns
    -------
    :class:`function`
        The actual decorator to be used.

    Examples
    --------
    >>> import dolor
    >>> class MyPacketHandler(dolor.packet_handler.PacketHandler):
    ...     @dolor.packet_listener(dolor.packets.Packet)
    ...     async def my_listener(self, p):
    ...         pass
    ...
    """

    def decorator(func):
        # Set the _packet_listener attribute to be later
        # recognized and registered by the class
        func._packet_listener = (checkers, kwargs)

        return func

    return decorator

class PacketHandler(abc.ABC):
    """A generic packet handler."""

    def __init__(self):
        self.packet_listeners = {}

        self.register_internal_listeners()

    def to_real_packet_checker(self, checker):
        """Turns a packet checker into a function that checks a packet.

        Parameters
        ----------
        checker
            See :meth:`register_packet_listener`.

        Returns
        -------
        :class:`function`
            A :class:`function` that returns a :class:`bool` and takes two arguments,
            the first being the relevant :class:`~.Connection`, and the second being
            the packet to check.
        """

        if isinstance(checker, type):
            # Packet class
            return lambda x, y: isinstance(y, checker)

        if isinstance(checker, int):
            # Packet id
            return lambda x, y: (y.get_id(ctx=x.ctx) == checker)

        if inspect.isfunction(checker) and len(inspect.signature(checker).parameters) == 1:
            return lambda x, y: checker(y)

        return checker

    def join_checkers(self, first, second):
        """Joins two real packet checkers into one.

        Parameters
        ----------
        first, second : :class:`function`
            A real packet checker returned from :meth:`to_real_packet_checker`.

        Returns
        -------
        :class:`function`
            See :meth:`to_real_packet_checker`.
        """

        return lambda x, y: (first(x, y) or second(x, y))

    def register_packet_listener(self, func, *checkers, **kwargs):
        """Registers a packet listener.

        Parameters
        ----------
        func : coroutine function
            The packet listener.
        checkers : subclass of :class:`~.Packet` or :class:`int` or :class:`function`
            If a subclass of :class:`~.Packet`, then the listener will be called if
            the packet is an instance of `checkers`.

            If an :class:`int`, then the listener will be called if the id of the
            packet is equal to `checkers`.

            If a :class:`function`, then `checkers` can either be a :class:`function`
            that returns a :class:`bool` and takes one argument, which represents the
            packet to check, or it can be a :class:`function` that returns a :class:`bool`
            and takes two arguments, the first being the relevant :class:`~.Connection`,
            and the second being the packet to check.
        kwargs
            Keyword arguments that must match the keyword arguments passed to
            :meth:`listeners_for_packet` for the packet listener to be included in
            its return.

        Raises
        ------
        :exc:`TypeError`
            If `func` isn't a coroutine function.
        :exc:`ValueError`
            If no `checkers` are specified.
        """

        if not asyncio.iscoroutinefunction(func):
            raise TypeError(f"Packet listener {func.__name__} isn't a coroutine function")

        if len(checkers) == 0:
            raise ValueError("No checkers passed")

        real_checker = None
        for c in checkers:
            real_c = self.to_real_packet_checker(c)

            if real_checker is None:
                real_checker = real_c
            else:
                real_checker = self.join_checkers(real_checker, real_c)

        self.packet_listeners[func] = (real_checker, kwargs)

    def unregister_packet_listener(self, func):
        """Unregisters a packet listener.

        Parameters
        ----------
        func : coroutine function
            The listener registered with :meth:`register_packet_listener`.
        """

        self.packet_listeners.pop(func)

    def external_packet_listener(self, *checkers, **kwargs):
        """Decorator for external packet listeners.

        For internal packet listeners, packet listeners that are methods,
        see :func:`packet_listener`.

        Parameters
        ----------
        checkers, kwargs
            See :meth:`register_packet_listener`.

        Returns
        -------
        :class:`function`
            The actual decorator to be used.

        Examples
        --------
        >>> import dolor
        >>> class MyPacketHandler(dolor.packet_handler.PacketHandler):
        ...     pass
        ...
        >>> handler = MyPacketHandler()
        >>> @handler.external_packet_listener
        ... def my_listener(p):
        ...     pass
        ...
        """

        def dec(func):
            self.register_packet_listener(func, *checkers, **kwargs)

            return func

        return dec

    def register_internal_listeners(self):
        """Registers internal packet listeners.

        See :func:`packet_listener`.

        Called on :meth:`__init__`.
        """

        for attr in dir(self):
            func = getattr(self, attr)

            # If the function was decorated with
            # the packet_listener function, then it
            # will have the _packet_listener attribute
            if hasattr(func, "_packet_listener"):
                self.register_packet_listener(func, *func._packet_listener[0], **func._packet_listener[1])

    def listeners_for_packet(self, c, p, **kwargs):
        """Gets the packet listeners for a packet.

        Parameters
        ----------
        c : :class:`~.Connection`
            The relevant connection.
        p : :class:`~.Packet`
            The packet to check.
        kwargs
            The keyword arguments that should've been used to
            register the packet listener in :meth:`register_packet_listener`.

        Returns
        -------
        :class:`list`
            The list of packet listeners for the packet.
        """

        return [x for x, y in self.packet_listeners.items() if y[1] == kwargs and y[0](c, p)]
