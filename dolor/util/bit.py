def bit(n):
    return (1 << n)

def to_signed(val, bits=32):
    if val > bit(bits - 1) - 1:
        val -= bit(bits)

    return val

def to_unsigned(val, bits=32):
    if val < 0:
        val += bit(bits)

    return val

def urshift(val, n, bits=32):
    return to_unsigned(val, bits) >> n
