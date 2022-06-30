"""Types that facilitate changes based on a :class:`~.Version`."""

import pak

from ..versions import VersionSwitcher

__all__ = [
    "VersionSwitchedType",
]

class VersionSwitchedType(pak.Type):
    """A type which changes based on a :class:`~.Version`.

    .. seealso::

        :class:`~.VersionSwitcher`

    :class:`dict` is also registered as typelike, converting to
    a :class:`VersionSwitchedType` everywhere a typelike is possible.

    Parameters
    ----------
    switch : :class:`dict`
        Forwarded onto :class:`~.VersionSwitcher`.

        The values must be typelike.
    """

    _switcher = None

    @classmethod
    def underlying_type(cls, *, ctx):
        """Gets the underlying type for the :class:`pak.TypeContext`.

        Parameters
        ----------
        ctx : :class:`pak.TypeContext`
            The context for the type.

        Returns
        -------
        subclass of :class:`pak.Type`
            The underlying type.
        """

        return pak.Type(cls._switcher[ctx.version])

    @classmethod
    def _size(cls, value, *, ctx):
        return cls.underlying_type(ctx=ctx).size(value, ctx=ctx)

    @classmethod
    def _alignment(cls, *, ctx):
        return cls.underlying_type(ctx=ctx).alignment(ctx=ctx)

    @classmethod
    def _default(cls, *, ctx):
        return cls.underlying_type(ctx=ctx).default(ctx=ctx)

    @classmethod
    def _unpack(cls, buf, *, ctx):
        return cls.underlying_type(ctx=ctx).unpack(buf, ctx=ctx)

    @classmethod
    def _pack(cls, value, *, ctx):
        return cls.underlying_type(ctx=ctx).pack(value, ctx=ctx)

    @classmethod
    def _call(cls, switch):
        return cls.make_type(cls.__name__, _switcher=VersionSwitcher(switch))

pak.Type.register_typelike(dict, VersionSwitchedType)
