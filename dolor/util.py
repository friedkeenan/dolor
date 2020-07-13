class Raw:
    def __init__(self, owner):
        object.__setattr__(self, "owner", owner)

    def __getattr__(self, attr):
        return object.__getattribute__(self.owner, attr)

    def __setattr__(self, attr, value):
        object.__setattr__(self.owner, attr, value)

def to_signed(val, bits=32):
    if val > 2**(bits - 1) - 1:
        val -= 2**bits

    return val

def to_unsigned(val, bits=32):
    if val < 0:
        val += 2**bits

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