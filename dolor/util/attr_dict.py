import collections

class AttrDict(collections.abc.MutableMapping):
    def __new__(cls, name_or_elems=None, *args, **kwargs):
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
