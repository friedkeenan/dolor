import inspect

from . import util

class Version:
    PRERELEASE = 1 << 30

    # Must be ordered chronologically
    supported_versions = {
        "1.16.4": 754,
    }

    @classmethod
    def name_from_proto(cls, proto):
        for name, proto_version in cls.supported_versions.items():
            if proto == proto_version:
                return name

        raise ValueError(f"Unsupported protocol version: {proto}")

    def __init__(self, name, *, check_supported=False):
        if isinstance(name, int):
            name = self.name_from_proto(name)

        if check_supported and name is not None and name not in self.supported_versions:
            raise ValueError(f"Unsupported version: {name}. If you know what you are doing, pass None instead.")

        self.name = name

    @property
    def proto(self):
        if self.name is None:
            return 0

        return self.supported_versions[self.name]

    @proto.setter
    def proto(self, value):
        try:
            self.name = self.name_from_proto(value)
        except ValueError as e:
            if self.name is not None:
                raise AttributeError(e.message)

    def __eq__(self, other):
        if isinstance(other, Version):
            other = other.name

        return self.name == other

    def __ne__(self, other):
        return not self == other

    def __gt__(self, other):
        if isinstance(other, Version):
            other = other.name

        versions = list(self.supported_versions)

        return versions.index(self.name) > versions.index(other)

    def __ge__(self, other):
        return self == other or self > other

    def __lt__(self, other):
        if isinstance(other, Version):
            other = other.name

        versions = list(self.supported_versions)

        return versions.index(self.name) < versions.index(other)

    def __le__(self, other):
        return self == other or self < other

class VersionRange:
    def __init__(self, start, stop):
        self.start = start
        self.stop  = stop

    def __contains__(self, value):
        if not isinstance(value, Version):
            value = Version(value)

        return self.start <= value and value < self.stop

class VersionSwitcher:
    def __init__(self, switch):
        for key in switch:
            if not inspect.isfunction(key) and not isinstance(key, str) and not util.is_container(key) and key is not None:
                raise TypeError(f"Invalid type for key: {key}")

        self.switch = switch

    def get(self, version):
        for key, value in self.switch.items():
            if key is None:
                continue

            if inspect.isfunction(key):
                if key(version):
                    return value
            elif isinstance(key, str):
                # Try to pass the index to the dictionary first instead?
                # Might result in looping over it twice implicitly
                if version == key:
                    return value
            elif util.is_container(key):
                if version in key:
                    return value

        return self.switch[None]

    def __getitem__(self, version):
        return self.get(version)
