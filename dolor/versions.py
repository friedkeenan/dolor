import inspect

from . import util

class Version:
    PRERELEASE = util.bit(30)

    # Must be ordered chronologically
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

        "20w45a":      PRERELEASE | 5,
        "20w46a":      PRERELEASE | 6,
        "20w48a":      PRERELEASE | 7,
        "20w49a":      PRERELEASE | 8,
        "20w51a":      PRERELEASE | 9,

        None: -1,
    }

    @classmethod
    def latest(cls):
        for name in reversed(cls.supported_versions):
            if name is not None:
                return name

        return None

    @classmethod
    def name_from_proto(cls, proto):
        # Potential issue when versions have
        # overlapping protocol versions

        for name, proto_version in cls.supported_versions.items():
            if proto == proto_version:
                return name

        return None

    def __init__(self, name, proto=-1, *, check_supported=False):
        if isinstance(name, int):
            proto = name
            name  = self.name_from_proto(name)

        if check_supported and name is not None and name not in self.supported_versions:
            raise ValueError(f"Unsupported version: {name}. If you know what you are doing, pass None instead.")

        self.name = name

        if proto < 0:
            self.proto = self.supported_versions.get(self.name, -1)
        else:
            self.proto = proto

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

    def __repr__(self):
        return f"{type(self).__name__}({repr(self.name)}, {repr(self.proto)})"

class VersionRange:
    def __init__(self, start, stop):
        self.start = start
        self.stop  = stop

    def __contains__(self, value):
        if not isinstance(value, Version):
            value = Version(value)

        ret = True

        if self.start is not None:
            ret = ret and self.start <= value

        if self.stop is not None:
            ret = ret and value < self.stop

        return ret

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
