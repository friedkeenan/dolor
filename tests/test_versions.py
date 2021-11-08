import pak

from dolor import *

def test_version_equality():
    canonical = Version("1.12.2")
    heretical = Version({"name": "test", "protocol": 340})

    assert heretical.name     == "test"
    assert heretical.protocol == 340

    assert canonical == heretical

# TODO: Test more versions in 'VersionSwitcher' tests when we support more versions.

def test_switcher_str():
    test = object()

    switcher = VersionSwitcher({
        "1.12.2": test
    })

    assert switcher["1.12.2"] is test

def test_switcher_func():
    test = object()

    switcher = VersionSwitcher({
        lambda v: v.protocol == 340: test
    })

    assert switcher["1.12.2"] is test

def test_switcher_container():
    test = object()

    switcher = VersionSwitcher({
        ("1.12.2",): test
    })

    assert switcher["1.12.2"] is test

def test_switcher_default():
    test = object()

    switcher = VersionSwitcher({
        None: test
    })

    assert switcher["1.12.2"] is test

def test_switcher_dynamic_value():
    class TestPacket(Packet):
        id = {
            "1.12.2": 1
        }

    ctx = PacketContext("1.12.2")

    assert TestPacket.id(ctx=ctx) == 1

    class TestType(pak.Type):
        _default = {
            "1.12.2": 2
        }

    assert TestType.default(ctx=pak.TypeContext(ctx=ctx)) == 2
