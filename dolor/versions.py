"""Version handling."""

import inspect

from . import util

class Version:
    """A version of Minecraft.

    :meta no-undoc-members:

    Parameters
    ----------
    name : :class:`str` or :class:`int` or :class:`Version` or ``None``
        If :class:`str`, then the version's name.

        If :class:`int`, then the version's protocol version.
        The name of the version will be looked up using
        :meth:`name_from_proto`.

        If :class:`Version`, the :attr:`name` and :attr:`proto`
        attributes will be copied.

        If ``None``, then it will behave as if you had passed
        :meth:`latest` as ``name``.
    proto : :class:`int`, optional
        The version's protocol version. If unspecified, it will
        look up the protocol version from :attr:`supported_versions`.
    check_supported : :class:`bool`, optional
        Whether or not to check if the version is supported.
        Will be ignored if ``name`` is ``None``.

    Attributes
    ----------
    name : :class:`str`
        The version's name.
    proto : :class:`int`
        The version's protocol version.
    supported_versions : :class:`dict`
        A chronologically-ordered dictionary with version names as keys
        and the corresponding protocol version as values.
    """

    PRERELEASE = util.bit(30)

    supported_versions = {
        "1.15.2":      578,

        "20w06a":      701,
        "20w07a":      702,
        "20w08a":      703,
        "20w09a":      704,
        "20w10a":      705,
        "20w11a":      706,
        "20w12a":      707,
        "20w13a":      708,
        "20w13b":      709,
        # Skip 20w14∞ (April Fools snapshot)
        "20w14a":      710,
        "20w15a":      711,
        "20w16a":      712,
        "20w17a":      713,
        "20w18a":      714,
        "20w19a":      715,
        "20w20a":      716,
        "20w20b":      717,
        "20w21a":      718,
        "20w22a":      719,

        "1.16-pre1":   721,
        "1.16-pre2":   722,
        "1.16-pre3":   725,
        "1.16-pre4":   727,
        "1.16-pre5":   729,
        "1.16-pre6":   730,
        "1.16-pre7":   732,
        "1.16-pre8":   733,

        "1.16-rc1":    734,

        "1.16":        735,

        "1.16.1":      736,

        "20w27a":      738,
        "20w28a":      740,
        "20w29a":      741,
        "20w30a":      743,

        "1.16.2-pre1": 744,
        "1.16.2-pre2": 746,
        "1.16.2-pre3": 748,

        "1.16.2-rc1":  749,
        "1.16.2-rc2":  750,

        "1.16.2":      751,

        "1.16.3-rc1":  752,

        "1.16.3":      753,

        "1.16.4-pre1": PRERELEASE | 1,
        "1.16.4-pre2": PRERELEASE | 2,

        "1.16.4-rc1":  PRERELEASE | 3,

        "1.16.4":      754,

        "1.16.5":      754,

        "20w45a":      PRERELEASE | 5,
        "20w46a":      PRERELEASE | 6,
        "20w48a":      PRERELEASE | 7,
        "20w49a":      PRERELEASE | 8,
        "20w51a":      PRERELEASE | 9,
    }

    # Cached so it doesn't need to be
    # regenerated on every comparison
    _supported_versions_list = list(supported_versions.values())

    @classmethod
    def latest(cls):
        """Gets the latest supported version.

        Returns
        -------
        :class:`Version`
            The latest supported version.
        """

        return cls(cls._supported_versions_list[-1])

    @classmethod
    def name_from_proto(cls, proto):
        """Gets the version name corresponding to the protocol version.

        Parameters
        ----------
        proto : :class:`int`
            The protocol version.

        Returns
        -------
        :class:`str`
            The corresponding version name.

        Raises
        ------
        :exc:`ValueError`
            If no corresponding version name can be found.
        """

        # Prefers later version names when
        # protocol versions are equal.

        for name, proto_version in reversed(cls.supported_versions.items()):
            if proto == proto_version:
                return name

        raise ValueError(f"No version name corresponds to protocol version {proto}")

    def __init__(self, name, proto=-1, *, check_supported=False):
        if name is None:
            name = self.latest()

        if isinstance(name, Version):
            proto = name.proto
            name  = name.name

        if isinstance(name, int):
            proto = name
            name  = self.name_from_proto(name)

        if check_supported and name not in self.supported_versions:
            raise ValueError(f"Unsupported version: {name}")

        self.name = name

        if proto < 0:
            self.proto = self.supported_versions.get(self.name, -1)
        else:
            self.proto = proto

    def __eq__(self, other):
        """Checks whether a version is equal to another.

        Parameters
        ----------
        other : :class:`Version` or :class:`str`
            The other version.

        Returns
        -------
        :class:`bool`
            Whether the version is equal to ``other``.

        Examples
        --------
        >>> from dolor.versions import Version
        >>> Version("1.16.4") == Version("1.16.4")
        True
        >>> Version("1.16.4") == "1.16.4"
        True
        >>> Version("1.16.4") == "1.15.2"
        False
        """

        other = Version(other)

        return self.proto == other.proto

    def __ne__(self, other):
        return not self == other

    def __hash__(self):
        return hash(self.proto)

    def __gt__(self, other):
        """Checks whether a version is greater than another.

        Parameters
        ----------
        other : :class:`Version` or :class:`str`
            The other version.

        Returns
        -------
        :class:`bool`
            Whether the version is greater than ``other``.

        Examples
        --------
        >>> from dolor.versions import Version
        >>> Version("1.16.4") > Version("1.15.2")
        True
        >>> Version("1.16.4") > "1.15.2"
        True
        >>> Version("1.15.2") > "1.16.4"
        False
        """

        other = Version(other)
        versions = self._supported_versions_list

        return versions.index(self.proto) > versions.index(other.proto)

    def __ge__(self, other):
        return self == other or self > other

    def __lt__(self, other):
        """Checks whether a version is less than another.

        Parameters
        ----------
        other : :class:`Version` or :class:`str`
            The other version.

        Returns
        -------
        :class:`bool`
            Whether the version is less than ``other``.

        Examples
        --------
        >>> from dolor.versions import Version
        >>> Version("1.15.2") < Version("1.16.4")
        True
        >>> Version("1.15.2") < "1.16.4"
        True
        >>> Version("1.16.4") < "1.15.2"
        False
        """

        other = Version(other)
        versions = self._supported_versions_list

        return versions.index(self.proto) < versions.index(proto)

    def __le__(self, other):
        return self == other or self < other

    def __repr__(self):
        return f"{type(self).__name__}({repr(self.name)}, {repr(self.proto)})"

class VersionRange:
    """A range of versions.

    A version is contained in the range when it is greater
    than or equal to ``start`` and less than ``stop``. In more
    mathematical terms, the range is [``start``, ``stop``), just like
    the builtin :class:`range`.

    Parameters
    ----------
    start : :class:`Version` or :class:`str` or ``None``
        The lower bound of the range. If ``None``, then `start` will
        not be checked when seeing if a version is contained
        in the range.
    stop : :class:`Version` or :class:`str` or ``None``
        The upper bound of the range. If ``None``, then `stop` will
        not be checked when seeing if a version is contained
        in the range.

    Examples
    --------
    >>> from dolor.versions import VersionRange
    >>> "1.16" in VersionRange("1.15.2", "1.16.4")
    True
    >>> "1.16" in VersionRange(None, "1.16.4")
    True
    >>> "1.16" in VersionRange("1.15.2", None)
    True
    >>> "1.16" in VersionRange(None, None)
    True
    >>> "1.16" in VersionRange("1.16.2", "1.16.4")
    False
    >>> "1.15.2" in VersionRange("1.15.2", "1.16.4")
    True
    >>> "1.16.4" in VersionRange("1.15.2", "1.16.4")
    False
    """

    def __init__(self, start, stop):
        self.start = start
        self.stop  = stop

    def __contains__(self, value):
        value = Version(value)

        ret = True

        if self.start is not None:
            ret = ret and self.start <= value

        if self.stop is not None:
            ret = ret and value < self.stop

        return ret

class VersionSwitcher:
    """A class to simplify getting different values based on different versions.

    Parameters
    ----------
    switch : :class:`dict`
        A dictionary whose keys can be:

        - A :class:`function` which takes one argument (the version) and returns a :class:`bool`.
        - A :class:`str` which is the version's name.
        - A container (checked with :func:`~.is_container`) which contains versions.
        - ``None``, whose value will be the default if no other key fits a version.

    Examples
    --------
    >>> from dolor.versions import VersionSwitcher, VersionRange
    >>> switcher = VersionSwitcher({
    ...     (lambda v: v == "1.16.4"): 0,
    ...     "1.16.3": 1,
    ...     VersionRange("1.16", "1.16.3"): 2,
    ...     None: 4,
    ... })
    >>> switcher["1.16.4"]
    0
    >>> switcher["1.16.3"]
    1
    >>> switcher["1.16.1"]
    2
    >>> switcher["1.15.2"]
    4
    """

    def __init__(self, switch):
        for key in switch:
            if not inspect.isfunction(key) and not isinstance(key, str) and not util.is_container(key) and key is not None:
                raise TypeError(f"Invalid type for key: {key}")

        self.switch = switch

    def get(self, version):
        """Gets the appropriate value for the version."""

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
            elif util.is_container(key):
                if version in key:
                    return value

        return self.switch[None]

    def __getitem__(self, version):
        """Does the same as :meth:`get`."""

        return self.get(version)
