"""Tools for handling :class:`Packets <.Packet>`."""

import asyncio
import inspect
from contextlib import asynccontextmanager

__all__ = [
    "packet_listener",
    "PacketHandler",
]

def packet_listener(*packet_checkers, **check_kwargs):
    """A decorator for :class:`~.Packet` listeners.

    Parameters
    ----------
    *packet_checkers
        The :class:`~.Packet` checkers.

        See :meth:`PacketHandler.register_packet_listener` for more details.
    **check_kwargs
        The keyword arguments to check against.

        See :meth:`PacketHandler.register_packet_listener` for more details.

    Examples
    --------
    >>> import dolor
    >>> class Example(dolor.PacketHandler):
    ...     @dolor.packet_listener(dolor.Packet)
    ...     async def listener_example(self, packet):
    ...         # Do things with 'packet' here.
    ...         pass
    ...
    >>> ex = Example()
    >>> ex.is_listener_registered(ex.listener_example)
    True
    """

    def decorator(listener):
        listener._packet_listener_data = (packet_checkers, check_kwargs)

        return listener

    return decorator

class PacketHandler:
    """An object which listens for :class:`Packets <.Packet>`.

    On construction, methods decorated with :func:`packet_listener` are
    passed to :meth:`register_packet_listener`.
    """

    def __init__(self):
        self._packet_listeners = {}
        self._listener_tasks   = []

        for _, attr in inspect.getmembers(self, lambda x: hasattr(x, "_packet_listener_data")):
            checkers, check_kwargs = attr._packet_listener_data

            self.register_packet_listener(attr, *checkers, **check_kwargs)

    @staticmethod
    def _to_real_checker(checker):
        # Transforms a checker into a function suitable for checking packets.

        # Packet class
        if isinstance(checker, type):
            return lambda conn, packet: isinstance(packet, checker)

        # Packet ID
        if isinstance(checker, int):
            return lambda conn, packet: (packet.id(ctx=conn.ctx) == checker)

        # Callable with only the packet as the parameter
        if len(inspect.signature(checker).parameters) == 1:
            return lambda conn, packet: checker(packet)

        return checker

    @staticmethod
    def _join_checkers(first, second):
        return lambda conn, packet: (first(conn, packet) or second(conn, packet))

    def register_packet_listener(self, listener, *packet_checkers, **check_kwargs):
        """Regisiters a :class:`~.Packet` listener.

        See Also
        --------
        :meth:`listeners_for_packet`

        Parameters
        ----------
        listener : coroutine function
            The function to call when an appropriate :class:`~.Packet` is received.
        *packet_checkers : subclass of :class:`~.Packet` or :class:`int` or callable
            How to determine if ``listener`` should be called.

            If a subclass of :class:`~.Packet`, then a :class:`~.Packet` passes the
            check if its an instance of the checker.

            If an :class:`int`, then a :class:`~.Packet` passes the check if its ID
            equals the checker.

            If a callable, then if it takes one parameter, that parameter should be
            the :class:`~.Packet` in question, and a :class:`bool` should be returned
            indicating whether the :class:`~.Packet` passes the check. If the callable
            takes two parameters, then the first should be the relevant
            :class:`~.Connection`, and the second should be the relevant :class:`~.Packet`.

            All ``*packet_checkers`` are combined so that if one of them passes, then
            ``listener`` should be called.
        **check_kwargs
            The keyword arguments to check against to see if ``listener`` is eligible
            to be called.

            The keyword arguments passed to :meth:`listeners_for_packet` must be equal
            to ``check_kwargs`` for ``listener`` to be eligible.

        Raises
        ------
        :exc:`TypeError`
            If ``listener`` is not a coroutine function or no ``*packet_checkers`` are specified.
        :exc:`ValueError`
            If ``listener`` is already registered.
        """

        if not asyncio.iscoroutinefunction(listener):
            raise TypeError(
                f"Function {listener.__qualname__} cannot be a packet listener since it is not a coroutine function"
            )

        if len(packet_checkers) == 0:
            raise TypeError("Must pass at least one packet checker")

        if self.is_listener_registered(listener):
            raise ValueError(f"Function {listener.__qualname__} is already a registered packet listener")

        cumulative_checker = None
        for checker in packet_checkers:
            real_checker = self._to_real_checker(checker)

            if cumulative_checker is None:
                cumulative_checker = real_checker
            else:
                cumulative_checker = self._join_checkers(cumulative_checker, real_checker)

        self._packet_listeners[listener] = (cumulative_checker, check_kwargs)

    def unregister_packet_listener(self, listener):
        """Unregisters a :class:`~.Packet` listener.

        Parameters
        ----------
        listener : coroutine function
            The :class:`~.Packet` listener passed to :meth:`register_packet_listener`.
        """

        self._packet_listeners.pop(listener)

    def is_listener_registered(self, listener):
        """Gets whether a :class:`~.Packet` listener is registered.

        Parameters
        ----------
        listener : coroutine function
            Possibly the :class:`~.Packet` listener passed to :meth:`register_packet_listener`.

        Returns
        -------
        :class:`bool`
            Whether ``listener`` is a registered :class:`~.Packet` listener.
        """

        return listener in self._packet_listeners

    def create_listener_task(self, coroutine):
        """Creates an asynchronous task for a :class:`~.Packet` listener.

        This method should be called when creating tasks for :class:`~.Packet`
        listeners, and :meth:`end_listener_tasks` called when all listening
        should end.

        Tasks should only be created in a :meth:`listener_task_context` managed
        context.

        Parameters
        ----------
        coroutine : coroutine object
            The coroutine to create the task for.

        Returns
        -------
        :class:`asyncio.Task`
            The created task.
        """

        async def coroutine_wrapper():
            try:
                await coroutine
            finally:
                # 'wrapper_task' is defined after this (and has to be).
                self._listener_tasks.remove(wrapper_task)

        wrapper_task = asyncio.create_task(coroutine_wrapper())
        self._listener_tasks.append(wrapper_task)

        return wrapper_task

    async def end_listener_tasks(self, *, timeout=1):
        """Ends any outstanding listener tasks created with :meth:`create_listener_task`.

        Parameters
        ----------
        timeout : :class:`int` or :class:`float` or ``None``
            How long to wait before canceling outstanding listener tasks.

            Passed to :func:`asyncio.wait_for`.
        """

        try:
            await asyncio.wait_for(asyncio.gather(*self._listener_tasks), timeout)
        except asyncio.TimeoutError:
            for task in self._listener_tasks:
                task.cancel()

    @asynccontextmanager
    async def listener_task_context(self, *, listen_sequentially):
        """A context manager in which listener tasks should be created.

        Parameters
        ----------
        should_listen_sequentially : :class:`bool`
            Whether the listeners should be called sequentially.

            If ``True``, listeners responding to the same :class:`~.Packet`
            will still be run asynchronously, however they will all be
            awaited before listening to another :class:`~.Packet`.

            Also when ``True``, the tasks are never canceled.
        """

        try:
            yield
        finally:
            if listen_sequentially:
                # Awaiting all tasks will clear '_listener_tasks'.
                await asyncio.gather(*self._listener_tasks)

    def listeners_for_packet(self, conn, packet, **kwargs):
        """Gets the listeners for a certain :class:`~.Packet`.

        Parameters
        ----------
        conn : :class:`~.Connection`
            The relevant :class:`~.Connection`.
        packet : :class:`~.Packet`
            The relevant :class:`~.Packet`.
        **kwargs
            The keyword arguments to compare against the ``**check_kwargs``
            passed to :meth:`register_packet_listener`.

        Returns
        -------
        :class:`list`
            The list of listeners for ``packet``.
        """

        return [
            listener

            for listener, (checker, check_kwargs) in self._packet_listeners.items()

            if check_kwargs == kwargs and checker(conn, packet)
        ]
