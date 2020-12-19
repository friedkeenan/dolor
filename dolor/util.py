import zlib
import io
import os

def is_iterable(obj):
    try:
        iter(obj)
    except TypeError:
        return False
    else:
        return True

def is_container(obj):
    return hasattr(obj, "__contains__") or is_iterable(obj)

def is_pathlike(obj):
    return isinstance(obj, (str, os.PathLike))

def to_signed(val, bits=32):
    if val > (1 << (bits - 1)) - 1:
        val -= (1 << bits)

    return val

def to_unsigned(val, bits=32):
    if val < 0:
        val += (1 << bits)

    return val

def urshift(val, n, bits=32):
    return to_unsigned(val, bits) >> n

def get_subclasses(*args):
    ret = set()

    for arg in args:
        tmp = set(arg.__subclasses__())
        tmp |= get_subclasses(*tmp)
        ret |= tmp

    return ret

class ZlibDecompressFile(io.IOBase):
    def __init__(self, f, *args, **kwargs):
        self.f = f
        self.decomp = zlib.decompressobj(*args, **kwargs)

    def read(self, size=-1):
        if size < 0:
            return self.decomp.decompress(self.f.read(size))

        ret = b""
        while len(ret) < size:
            ret += self.decomp.decompress(self.f.read(1))

        return ret

    def close(self):
        self.f.close()
