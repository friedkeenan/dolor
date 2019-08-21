def to_signed(val, bits=32):
    if val > 2**(bits - 1) - 1:
        val -= 2**bits
    return val

def to_unsigned(val, bits=32):
    if val < 0:
        val += 2**bits
    return val

def urshift(val, n, bits=32):
    return to_unsigned(val) >> n

def get_subclasses(*args):
    ret = set(args[0].__subclasses__())
    for arg in args[1:]:
        tmp = set(arg.__subclasses__())
        tmp |= get_subclasses(*tmp)
        ret |= tmp

    return ret