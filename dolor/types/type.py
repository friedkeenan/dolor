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
    ctx : :class:`~.PacketContext` or :class:`~.Version` or :class:`str` or :class:`int`, optional
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

        if ctx is None or isinstance(ctx, (Version, str, int)):
            self.version = Version(ctx)
        else:
            self.version = ctx.version

class Type(abc.ABC):
    """Base class for types of packet fields.

    This class is used for marshaling raw data (typically in
    packets) to and from values, and it has some interesting quirks.

    For one, calling their constructor doesn't really construct
    them, but rather make new types. Take :class:`~.string.String`
    for instance: It can take an argument for the string's maximum
    length::

        >>> import dolor
        >>> dolor.types.String.max_length
        32767
        >>> s = dolor.types.String(20)
        >>> s
        <class 'dolor.types.string.String(20)'>
        >>> s.max_length
        20

    To really get a :class:`Type` object, use the :meth:`descriptor`
    method, like so::

        >>> import dolor
        >>> dolor.types.VarInt.descriptor("attr_name") # doctest: +SKIP
        <dolor.types.numeric.VarInt object at 0x7fe5ad4e5490>

    You can also generate arrays of types like so::

        >>> import dolor
        >>> dolor.types.Short[1]
        <class 'dolor.types.array.Short[1]'>

    .. seealso::

        :meth:`__class_getitem__`

    To marshal data to a value, see the :meth:`unpack` method.

    To marshal a value to data, see the :meth:`pack` method.
    """

    _default = None

    @classmethod
    def __init_subclass__(cls, **kwargs):
        """Spiffs up subclasses.

        If the :attr:`_default` attribute is a
        :class:`dict`, then it changes it to a
        :class:`~.VersionSwitcher`.

        It also sets :meth:`__new__` to :meth:`_call`. If you
        want to initialize a :class:`Type`, see :meth:`descriptor`.
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
        >>> import dolor
        >>> dolor.types.VarInt[1]
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
    def unpack(cls, buf, *, ctx=None):
        """Gets the corresponding value from the buffer.

        Warnings
        --------
        Do **not** override this method. Instead override
        :meth:`_unpack`.

        Parameters
        ----------
        buf : file object or :class:`bytes` or :class:`bytearray`
            The buffer containing the raw data.
        ctx : :class:`TypeContext`, optional

        Returns
        -------
        any
            The corresponding value from the buffer.
        """

        buf = util.file_object(buf)

        return cls._unpack(buf, ctx=ctx)

    @classmethod
    def pack(cls, value, *, ctx=None):
        """Packs a value into raw data.

        Warnings
        --------
        Do **not** override this method. Instead override
        :meth:`pack`.

        Parameters
        ----------
        value
            The value to pack.
        ctx : :class:`TypeContext`, optional

        Returns
        -------
        :class:`bytes`
            The corresponding raw data.
        """

        return cls._pack(value, ctx=ctx)

    @classmethod
    @abc.abstractmethod
    def _unpack(cls, buf, *, ctx=None):
        """Gets the corresponding value from the buffer.

        To be overridden by subclasses.

        Warnings
        --------
        Do not use this method directly, **always** use
        :meth:`unpack` instead.

        Parameters
        ----------
        buf : file object
            The buffer containing the raw data.
        ctx : :class:`TypeContext`, optional

        Returns
        -------
        any
            The corresponding value from the buffer.
        """

        raise NotImplementedError

    @classmethod
    @abc.abstractmethod
    def _pack(cls, value, *, ctx=None):
        """Packs a value into raw data.

        To be overridden by subclasses.

        Warnings
        --------
        Do not use this method directly, **always** use
        :meth:`pack` instead.

        Parameters
        ----------
        value
            The value to pack.
        ctx : :class:`TypeContext`, optional

        Returns
        -------
        :class:`bytes`
            The corresponding raw data.
        """

        raise NotImplementedError

    @classmethod
    def make_type(cls, name, bases=None, **namespace):
        """Utility for generating new types.

        The generated type's :attr:`__module__` attribute is
        set to be the same as the origin type's. This is done to
        get around an issue where generated types would have
        their :attr:`__module__` attribute be ``"abc"`` because
        :class:`Type` inherits from :class:`abc.ABC`.

        Parameters
        ----------
        name : :class:`str`
            The generated type's name.
        bases : :class:`tuple`, optional
            The generated type's base classes. If unspecified, the
            origin type is the sole base class.
        **namespace
            The attributes and corresponding values of the generated
            type.

        Returns
        -------
        subclass of :class:`Type`
            The generated type.
        """

        if bases is None:
            bases = (cls,)

        namespace["__module__"] = cls.__module__

        return type(name, bases, namespace)

    @classmethod
    def _call(cls):
        # Called when the type's constructor is called.
        #
        # The arguments passed to the constructor get forwarded
        # to this method. typically overridden to enable
        # generating new types.

        raise NotImplementedError
