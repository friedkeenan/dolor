"""Contains :class:`util.StructuredDict <.util.structured_dict.StructuredDict>`."""

import collections
from dataclasses import dataclass

from .misc import default, UniqueSentinel

__all__ = [
    "StructuredDict",
]

class StructuredDict(collections.abc.MutableMapping):
    """A mutable mapping with specified keys/attributes.

    :meta no-undoc-members:

    Subclasses should specify their structure using annotations,
    in the same fashion as with :mod:`dataclasses`.

    Key/value pairs are passed to the constructor
    as keyword arguments, or inside a mapping, passed
    as the first positional argument.

    Attributes
    ----------
    UNSPECIFIED
        A unique object indicating that a key has
        been left unspecified.

        Should only be used as a default value,
        allowing that value to not be specified.

    Examples
    --------
    >>> import dolor
    >>> class Example(dolor.util.StructuredDict):
    ...     key:       int
    ...     other_key: str
    ...
    >>> ex = Example(key=1, other_key="example")
    >>> ex
    Example(key=1, other_key='example')
    >>> ex["key"]
    1
    >>> ex.key
    1
    >>> ex["key"] = 2
    >>> ex.key
    2
    >>> ex == Example({"key": 2, "other_key": "example"})
    True
    >>> dict(ex)
    {'key': 2, 'other_key': 'example'}
    """

    UNSPECIFIED = UniqueSentinel("UNSPECIFIED")

    @classmethod
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)

        # Modifies the class in place.
        #
        # Other arguments are passed to ensure we get
        # the methods from 'MutableMapping' and not from
        # the dataclass transformation.
        dataclass(cls, repr=False, eq=False)

        # Transform '__init__' to have a mapping argument and keyword arguments.
        old_init = cls.__init__

        # TODO: Match signature, along with annotations, appropriately
        #
        # NOTE: '_items' having a mutable default is okay since we
        # always take a copy of it.
        def new_init(self, _items={}, **kwargs):
            items = dict(_items, **kwargs)

            old_init(self, **items)

        cls.__init__ = new_init

    def __iter__(self):
        for field in self.__dataclass_fields__.keys():
            if hasattr(self, field):
                yield field

    def __len__(self):
        return sum(1 if hasattr(self, field) else 0 for field in self.__dataclass_fields__.keys())

    def __repr__(self):
        return (
            f"{type(self).__name__}("
            f"{', '.join(f'{key}={repr(value)}' for key, value in self.items())}"
            f")"
        )

    def __getattribute__(self, attr):
        # Make sure attributes which are marked as unspecified raise 'AttributeError's.

        value = super().__getattribute__(attr)

        if attr == "UNSPECIFIED":
            return value

        if value is self.UNSPECIFIED:
            raise AttributeError(f"'{type(self).__name__}' object has no attribute '{attr}'")

        return value

    def __getitem__(self, item):
        try:
            value = getattr(self, item)
        except AttributeError:
            raise KeyError(item)

        return value

    def __setitem__(self, item, value):
        setattr(self, item, value)

    def __delitem__(self, item):
        setattr(self, item, self.UNSPECIFIED)
