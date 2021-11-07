"""Contains :class:`util.StructuredDict <.util.structured_dict.StructuredDict>`."""

import collections
from dataclasses import dataclass

from .misc import default

__all__ = [
    "StructuredDict",
]

class StructuredDict(collections.abc.MutableMapping):
    """A mutable mapping with specified keys/attributes.

    Subclasses should specify their structure using annotations,
    in the same fashion as with :mod:`dataclasses`.

    Key/value pairs are passed to the constructor
    as keyword arguments, or inside a mapping, passed
    as the first positional argument.

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

    @classmethod
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)

        # Modifies the class in place.
        dataclass(cls)

        # Transform '__init__' to have a mapping argument and keyword arguments.
        old_init = cls.__init__

        # TODO: Match signature, along with annotations, appropriately
        def new_init(self, _items=None, **kwargs):
            old_init(self, **default(_items, {}), **kwargs)

        cls.__init__ = new_init

    def __iter__(self):
        return iter(self.__dataclass_fields__)

    def __len__(self):
        return len(self.__dataclass_fields__)

    def __getitem__(self, item):
        return getattr(self, item)

    def __setitem__(self, item, value):
        setattr(self, item, value)

    def __delitem__(self, item):
        delattr(self, item)
