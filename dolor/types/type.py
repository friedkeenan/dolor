import abc
import copy
import io

from ..versions import Version

class TypeContext:
    def __init__(self, instance=None, ctx=None):
        self.instance = instance

        if ctx is not None:
            if isinstance(ctx, Version):
                self.version = ctx
            elif isinstance(ctx, str):
                self.version = Version(ctx)
            else:
                self.version = ctx.version
        else:
            self.version = Version(None)

    def __eq__(self, other):
        return self.version == other.version and self.instance is other.instance

class Type(abc.ABC):
    _default = None

    def __new__(cls, *args, **kwargs):
        if "_name" in kwargs:
            return super().__new__(cls)

        return cls._call(*args, **kwargs)

    def __init__(self, *, _name=None):
        self._name = _name

    def __get__(self, instance, owner):
        if instance is None:
            return self

        return instance._get_field(self._name)

    def __set__(self, instance, value):
        instance._set_field(self._name, value)

    @classmethod
    def __class_getitem__(cls, index):
        from .array import Array

        return Array(cls, index)

    @classmethod
    def default(cls, *, ctx=None):
        """
        Returns the default value of the type.

        If cls._default isn't None, then a deepcopy
        of that value will be returned.
        """

        if cls._default is not None:
            # Deepcopy because the default could be mutable
            return copy.deepcopy(cls._default)

        raise NotImplementedError

    @classmethod
    @abc.abstractmethod
    def _unpack(cls, buf, *, ctx=None):
        """
        Should return the value that corresponds
        to the raw data in the buffer.
        """

        raise NotImplementedError

    @classmethod
    @abc.abstractmethod
    def _pack(cls, value, *, ctx=None):
        """
        Should return the bytes that corresponds
        to the value argument.
        """

        raise NotImplementedError

    @classmethod
    def unpack(cls, buf, *, ctx=None):
        if isinstance(buf, (bytes, bytearray)):
            buf = io.BytesIO(buf)

        return cls._unpack(buf, ctx=ctx)

    @classmethod
    def pack(cls, value, *, ctx=None):
        return cls._pack(value, ctx=ctx)

    @classmethod
    def _call(cls, *args, **kwargs):
        raise NotImplementedError
