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
