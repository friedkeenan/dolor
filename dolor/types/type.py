"""Base code for types of packet fields."""

import abc
import inspect
import copy

from .. import util
from ..versions import Version, VersionSwitcher

class TypeContext:
    """The context for a :class:`Type`.

    Parameters
    ----------
    instance : :class:`~.Packet`, optional
        The packet instance that's being marshaled.
    ctx : :class:`~.PacketContext` or :class:`~.Version` or :class:`str`
        The context for the packet or the version to use for marshaling.

    Attributes
    ----------
    instance : :class:`~.Packet` or ``None``
        The packet instance that's being marshaled.
    version : :class:`~.Version`
        The version to use for marshaling.
    """

    def __init__(self, instance=None, ctx=None):
        self.instance = instance

        if ctx is None or isinstance(ctx, (Version, str)):
            self.version = Version(ctx)
        else:
            self.version = ctx.version

class Type(abc.ABC):
    """Base class for types of packet fields."""

    _default = None

    @classmethod
    def __init_subclass__(cls, **kwargs):
        """Spiffs up subclasses.

        If the :attr:`_default` attribute is a
        :class:`dict`, then it changes it to a
        :class:`~.VersionSwitcher`.

        It also sets :meth:`__new__` to :meth:`_call`. If you
        wish to initialize a :class:`Type`, see :meth:`descriptor`.
        """

        super().__init_subclass__(**kwargs)

        if isinstance(cls._default, dict):
            cls._default = VersionSwitcher(cls._default)

        # Set __new__ to _call's underlying function.
        # We don't just override __new__ instead of
        # _call so that it's more clear that calling
        # a Type is separate from actually initializing
        # an instance of Type.
        cls.__new__ = cls._call.__func__

    @classmethod
    def descriptor(cls, name):
        """Gets the descriptor form of the type.

        Parameters
        ----------
        name : :class:`str`
            The name of the packet field.

        Returns
        -------
        :class:`Type`
            The descriptor form of the type.
        """

        # Get the name here instead of in __set_name__
        # to avoid the need for a metaclass for Packet.

        self = object.__new__(cls)
        self.name = name

        return self

    def __get__(self, instance, owner=None):
        if instance is None:
            return self

        return instance._get_field(self.name)

    def __set__(self, instance, value):
        instance._set_field(self.name, value)

    @classmethod
    def __class_getitem__(cls, index):
        """Gets an :class:`~.Array` of the type.

        Examples
        --------
        >>> from dolor.types import *
        >>> VarInt[1]
        <class 'dolor.types.array.VarInt[1]'>
        """

        from .array import Array

        return Array(cls, index)

    @classmethod
    def default(cls, *, ctx=None):
        """Gets the default value of the type.

        If the :attr:`_default` attribute is a classmethod,
        then it should look like this::

            @classmethod
            def _default(cls, *, ctx=None):
                return my_default_value

        The return value of the classmethod will be returned from this method.

        If the :attr:`_default` attribute is a :class:`~.VersionSwitcher`,
        then the value for the corresponding version will be returned.

        Otherwise, if the :attr:`_default` attribute is any value
        other than ``None``, that value will be returned.

        Parameters
        ----------
        ctx : :class:`TypeContext`, optional

        Returns
        -------
        any
            The default value.

        Raises
        ------
        :exc:`NotImplementedError`
            If the :attr:`_default` attribute is ``None``.
        """

        if cls._default is None:
            raise NotImplementedError

        if inspect.ismethod(cls._default):
            return cls._default(ctx=ctx)

        if isinstance(cls._default, VersionSwitcher):
            default = cls._default[ctx.version]
        else:
            default = cls._default

        # Deepcopy because the default could be mutable
        return copy.deepcopy(default)

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
        buf = util.file_object(buf)

        return cls._unpack(buf, ctx=ctx)

    @classmethod
    def pack(cls, value, *, ctx=None):
        return cls._pack(value, ctx=ctx)

    @classmethod
    def make_type(cls, name, bases=None, **namespace):
        if bases is None:
            bases = (cls,)

        namespace["__module__"] = cls.__module__

        return type(name, bases, namespace)

    @classmethod
    def _call(cls):
        raise NotImplementedError
