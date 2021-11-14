import inspect
import pytest

from ..util import ByteStream

from dolor import *

class _ClientTest(Client):
    received_data = None

    version = Version.latest()

    @classmethod
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)

        cls.version = Version(cls.version)

    def __init__(self):
        super().__init__("test", version=self.version)

    @property
    def sent_data(self):
        return self.writer.data

    async def startup(self):
        self.reader = ByteStream(self.received_data)
        self.writer = ByteStream()

def client_test(client_cls=None, *args, **kwargs):
    if client_cls is None:
        return lambda client_cls: test_client(client_cls, *args, **kwargs)

    new_cls = type(client_cls.__name__, (client_cls, _ClientTest), dict(
        __module__ = client_cls.__module__,
    ))

    @pytest.mark.asyncio
    async def test():
        await new_cls(*args, **kwargs).start()

    # Set variable in the caller's scope
    inspect.currentframe().f_back.f_globals[f"test_{client_cls.__name__}"] = test

    return new_cls
