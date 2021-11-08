import pytest

from dolor import *

def test_invalid_key():
    class TestInvalid(util.StructuredDict):
        key: str

    with pytest.raises(TypeError):
        TestInvalid(invalid_key=0)

    with pytest.raises(TypeError):
        TestInvalid({"invalid_key": 0})

def test_unspecified_key():
    class TestUnspecified(util.StructuredDict):
        key: str = util.StructuredDict.UNSPECIFIED

    d = TestUnspecified()

    assert len(d)  == 0
    assert dict(d) == {}

    d["key"] = "test"

    assert len(d)  == 1
    assert dict(d) == {"key": "test"}

    assert d == TestUnspecified(key="test")

    d.pop("key")
    assert d == TestUnspecified()

    assert not hasattr(d, "key")
    with pytest.raises(KeyError, match="'key'"):
        d["key"]
