import zlib
import io

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
