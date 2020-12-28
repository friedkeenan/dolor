import abc
import asyncio
import inspect

def packet_listener(*checkers, **kwargs):
    """Decorator for packet listeners within a class."""

    def dec(func):
        # Set the _packet_listener attribute to be later
        # recognized and registered by the class
        func._packet_listener = (checkers, kwargs)

        return func

    return dec

class PacketHandler(abc.ABC):
    def __init__(self):
        self.packet_listeners = {}

        self.register_intrinsic_listeners()

    def to_real_packet_checker(self, checker):
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
        return lambda x, y: (first(x, y) or second(x, y))

    def register_packet_listener(self, func, *checkers, **kwargs):
        """
        Registers a packet listener.

        func is a coroutine function and each
        checker is either a packet class, a packet
        id, or a function that returns whether
        the listener should be called.
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
        """Unregisters a packet listener."""

        self.packet_listeners.pop(func)

    def external_packet_listener(self, *checkers, **kwargs):
        """Decorator for external packet listeners."""

        def dec(func):
            self.register_packet_listener(func, *checkers, **kwargs)

            return func

        return dec

    def register_intrinsic_listeners(self):
        for attr in dir(self):
            func = getattr(self, attr)

            # If the function was decorated with
            # the packet_listener function, then it
            # will have the _packet_listener attribute
            if hasattr(func, "_packet_listener"):
                self.register_packet_listener(func, *func._packet_listener[0], **func._packet_listener[1])

    def listeners_for_packet(self, c, p, **kwargs):
        return [x for x, y in self.packet_listeners.items() if y[1] == kwargs and y[0](c, p)]
