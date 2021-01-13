"""Contains :class:`~.AttrDict`"""

import collections

class AttrDict(collections.abc.MutableMapping):
    """A wrapper around :class:`dict` that also lets you access keys as attributes.

    Parameters
    ----------
    name_or_elems : :class:`str` or :class:`dict`, optional
        If a :class:`str`, then it will generate a new type
        with that name that inherits from :class:`AttrDict`.

        If a :class:`dict`, then it will use it as its
        underlying dictionary.

        If unspecified, then the initial underlying dictionary
        will be empty.
    kwargs
        Will be used with :meth:`dict.update` to update
        the underlying dictionary.

    Examples
    --------
    >>> import dolor
    >>> MyAttrDict = dolor.util.AttrDict("MyAttrDict")
    >>> MyAttrDict.__name__
    'MyAttrDict'
    >>> x = MyAttrDict(y=0)
    >>> x.y
    0
    >>> x["y"]
    0
    """

    def __new__(cls, name_or_elems=None, **kwargs):
        if not isinstance(name_or_elems, str):
            return super().__new__(cls)

        return type(name_or_elems, (cls,), {})

    def __init__(self, elems=None, **kwargs):
        if elems is None:
            elems = {}

        elems.update(kwargs)

        self._elems = elems

    def __getitem__(self, key):
        return self._elems[key]

    def __setitem__(self, key, value):
        self._elems[key] = value

    def __delitem__(self, key):
        del self._elems[key]

    def __len__(self):
        return len(self._elems)

    def __iter__(self):
        return self._elems.__iter__()

    def __getattr__(self, attr):
        try:
            return self._elems[attr]
        except KeyError:
            raise AttributeError

    def __setattr__(self, attr, value):
        if attr == "_elems":
            super().__setattr__(attr, value)

            return

        self._elems[attr] = value

    def __delattr__(self, attr):
        if attr == "_elems":
            super().__delattr__(attr)

            return

        del self._elems[attr]

    def __repr__(self):
        return f"{type(self).__name__}({self._elems})"
