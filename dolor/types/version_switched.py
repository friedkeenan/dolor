import pak

from ..versions import VersionSwitcher

__all__ = [
    "VersionSwitchedType",
]

class VersionSwitchedType(pak.Type):
    """A type which changes based on a :class:`~.Version`.

    See Also
    --------
    :class:`~.VersionSwitcher`

    The values of the :class:`~.VersionSwitcher` must be typelike.

    :class:`dict` is also registered as typelike, converting to
    a :class:`VersionSwitchedType` everywhere a typelike is possible.

    Parameters
    ----------
    switch : :class:`dict`
        Forwarded onto :class:`~.VersionSwitcher`.
    """

    _switcher = None

    @classmethod
    def value_type(cls, *, ctx=None):
        return pak.Type(cls._switcher[ctx.version])

    @classmethod
    def _size(cls, *, ctx=None):
        return cls.value_type(ctx=ctx).size(ctx=ctx)

    @classmethod
    def _default(cls, *, ctx=None):
        return cls.value_type(ctx=ctx).default(ctx=ctx)

    @classmethod
    def _unpack(cls, buf, *, ctx=None):
        return cls.value_type(ctx=ctx).unpack(buf, ctx=ctx)

    @classmethod
    def _pack(cls, value, *, ctx=None):
        return cls.value_type(ctx=ctx).pack(value, ctx=ctx)

    @classmethod
    def _call(cls, switch):
        return cls.make_type(cls.__name__, _switcher=VersionSwitcher(switch))

pak.Type.register_typelike(dict, VersionSwitchedType)
