from dolor import *

def test_default():
    obj     = object()
    default = object()

    assert util.default(obj,  default) is obj
    assert util.default(None, default) is default

    # Make sure types which can be converted
    # to 'bool' are not defaulted.
    assert util.default(0, default) == 0
