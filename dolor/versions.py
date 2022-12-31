"""Minecraft version handling."""

import collections
import inspect
import pak

from . import util

__all__ = [
    "Version",
    "VersionRange",
    "VersionSwitcher",
    "VersionSwitcherDynamicValue",
]

class Version(collections.abc.Mapping):
    """A Minecraft version.

    :meta no-undoc-members:

    Parameters
    ----------
    version : :class:`str` or :class:`int` or mapping or :class:`Version`
        If :class:`str`, then ``version`` is the name of the
        :class:`Version`. The name must correspond to a supported
        :class:`Version`.

        If :class:`int`, then ``version`` is the protocol
        number of the :class:`Version`. Whether the :class:`Version`
        is supported is not checked.

        If a mapping, then the ``"name"`` and ``"protocol"`` keys
        are used to initialize the :class:`Version`. Whether the
        :class:`Version` is supported is not checked.

        If :class:`Version`, then the :attr:`name` and :attr`protocol`
        attributes are copied to the resulting :class:`Version`.

    Raises
    ------
    :exc:`ValueError`
        If ``version`` is a :class:`str` and its represented
        :class:`Version` is not supported.

    Examples
    --------
    >>> import dolor
    >>> version = dolor.Version("1.12.2")
    >>> version
    Version('1.12.2', 340)
    >>> version == dolor.Version(340)
    True
    >>> version == dolor.Version({"name": "1.12.2", "protocol": 340})
    True
    >>> dict(version)
    {'name': '1.12.2', 'protocol': 340}
    >>> version == dolor.Version(version)
    True

    Attributes
    ----------
    name : :class:`str`
        The name of the :class:`Version`.
    protocol : :class:`int`
        The protocol number of the :class:`Version`.
    supported_versions : :class:`dict`
        A chronologically-ordered dictionary with :class:`Version`
        names as keys and corresponding protocol numbers as values.
    """

    __slots__ = ("_mutable_flag", "name", "protocol")

    PRERELEASE = pak.util.bit(30)

    # NOTE: This *must* be chronologically ordered.
    supported_versions = {
        "1.12.2": 340,
    }

    # Cached so it doesn't need to be regenerated on every comparison.
    _supported_protocols = list(supported_versions.values())

    @classmethod
    def latest(cls):
        """Gets the latest supported :class:`Version`.

        Returns
        -------
        :class:`Version`
            The latest supported :class:`Version`.
        """

        return cls(cls._supported_protocols[-1])

    @classmethod
    def name_from_protocol(cls, protocol):
        """Gets the :class:`Version` name corresponding to the protocol number.

        .. note::

            Later versions are preferred when protocols are equal.

        Parameters
        ----------
        protocol : :class:`int`
            The protocol number for the :class:`Version`.

        Returns
        -------
        :class:`str` or ``None``
            If :class:`str`, then the corresponding name of the :class:`Version`.

            If ``None``, then no corresponding name could be found.

        Examples
        --------
        >>> import dolor
        >>> dolor.Version.name_from_protocol(340)
        '1.12.2'
        >>> dolor.Version.name_from_protocol(-1) is None
        True
        """

        # TODO: Remove 'list' call when Python 3.7 is dropped.
        #
        # In 3.7, 'dict_items' is not reversible.
        for name, proto in reversed(list(cls.supported_versions.items())):
            if proto == protocol:
                return name

        return None

    def __init__(self, version):
        # Allow mutating attributes only during construction.
        self._mutable_flag = True

        if isinstance(version, Version):
            self.name     = version.name
            self.protocol = version.protocol
        elif isinstance(version, int):
            # Protocol number was passed.

            self.name     = self.name_from_protocol(version)
            self.protocol = version
        elif isinstance(version, collections.abc.Mapping):
            self.name     = version["name"]
            self.protocol = version["protocol"]
        else:
            protocol = self.supported_versions.get(version)
            if protocol is None:
                raise ValueError(f"Unsupported version: {version}")

            self.name     = version
            self.protocol = protocol

        self._mutable_flag = False

    def __setattr__(self, attr, value):
        if attr == "_mutable_flag" or self._mutable_flag:
            super().__setattr__(attr, value)
        else:
            raise AttributeError(f"Cannot set the '{attr}' attribute; Versions are immutable")

    def __iter__(self):
        return iter(("name", "protocol"))

    def __len__(self):
        return 2

    def __getitem__(self, item):
        return getattr(self, item)

    def __repr__(self):
        return f"{type(self).__name__}({repr(self.name)}, {repr(self.protocol)})"

    def __eq__(self, other):
        """Checks whether a version is equal to another.

        Parameters
        ----------
        other : versionlike
            The other :class:`Version`,

        Returns
        -------
        :class:`bool`
            Whether the :class:`Version` is equal to ``other``.

        Examples
        --------
        >>> import dolor
        >>> dolor.Version("1.12.2") == dolor.Version(340)
        True
        """

        other = Version(other)

        return self.protocol == other.protocol

    def __ne__(self, other):
        return not self == other

    def __hash__(self):
        return hash(self.protocol)

    # TODO: Examples for greater than and less than
    # when we support more than one version.

    @classmethod
    @pak.util.cache
    def _index_for_protocol(cls, protocol):
        return cls._supported_protocols.index(protocol)

    def __gt__(self, other):
        """Checks whether a version is greater than another.

        Parameters
        ----------
        other : versionlike
            The other :class:`Version`,

        Returns
        -------
        :class:`bool`
            Whether the :class:`Version` is greater than ``other``.
        """

        other = Version(other)

        return self._index_for_protocol(self.protocol) > self._index_for_protocol(other.protocol)

    def __ge__(self, other):
        return self == other or self > other

    def __le__(self, other):
        """Checks whether a version is less than another.

        Parameters
        ----------
        other : versionlike
            The other :class:`Version`,

        Returns
        -------
        :class:`bool`
            Whether the :class:`Version` is less than ``other``.
        """

        other = Version(other)

        return self._index_for_protocol(self.protocol) > self._index_for_protocol(other.protocol)

    def __le__(self, other):
        return self == other or self < other

class VersionRange:
    r"""A range of :class:`Version`\s.

    A :class:`Version` is contained within the range if
    it is greater than or equal to ``start`` and less
    than ``stop``. In more mathematical terms, the range
    is [``start``, ``stop``), just like the builtin :class:`range`.

    Parameters
    ----------
    start : versionlike or ``None``
        The lower bound of the range.

        If ``None``, then ``start`` will not be
        checked when seeing if a ;class:`Version`
        is contained within the range.
    stop : versionlike or ``None``
        The upper bound of the range.

        If ``None``, then ``stop`` will not be
        checked when seeing if a :class:`Version`
        is contained within the range.
    """

    # TODO: Add examples when we have more than one supported version.

    def __init__(self, start, stop):
        self.start = start
        self.stop  = stop

    def __contains__(self, version):
        version = Version(version)

        contained = True

        if self.start is not None:
            contained = contained and self.start <= version

        if self.stop is not None:
            contained = contained and version < self.stop

        return contained

class VersionSwitcher:
    r"""A utility to for getting different values based different :class:`Version`\s.

    Parameters
    ----------
    switch : :class:`dict`
        A dictionary whose keys can be:

        - A :class:`function` which takes one argument (the :class:`Version`) and returns a :class:`bool`, indicating whether the :class:`Version` matches.
        - A :class:`str` representing the :class:`Version` name.
        - A container (checked with :func:`util.is_container <.util.interfaces.is_container>`) which contains :class:`Version`\s.
        - ``None``, whose value will be the default if no other key matches.

    See Also
    --------
    :class:`types.VersionSwitchedType <.types.version_switched.VersionSwitchedType>`
    """

    # TODO: Examples when we have more than one supported version.

    def __init__(self, switch):
        # TODO: Do we want to support any versionlike key instead
        # of just 'str'? The explicitness of strings are nice.

        for key in switch.keys():
            if (
                not inspect.isfunction(key) and
                not isinstance(key, str)    and
                not util.is_container(key)  and
                not key is None
            ):
                raise TypeError(f"Invalid type for key of VersionSwitcher: {key}")

            self.switch = switch

    def get(self, version):
        """Gets the appropriate value for the :class:`Version`.

        Parameters
        ----------
        version : versionlike
            The :class:`Version` to switch over.

        Returns
        -------
        any
            The corresponding value from the :class:`VersionSwitcher`.
        """

        version = Version(version)

        for key, value in self.switch.items():
            if key is None:
                continue

            if inspect.isfunction(key):
                if key(version):
                    return value
            elif isinstance(key, str):
                if version == key:
                    return value
            else:
                if version in key:
                    return value

        return self.switch[None]

    def __getitem__(self, version):
        """Calls :meth:`get`."""

        return self.get(version)

class VersionSwitcherDynamicValue(pak.DynamicValue):
    """Converts a :class:`dict` to a :class:`VersionSwitcher` in various places."""

    _type = dict

    def __init__(self, switch):
        self.switcher = VersionSwitcher(switch)

    def get(self, *, ctx=None):
        return self.switcher[ctx.version]
