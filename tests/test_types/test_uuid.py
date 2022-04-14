import pak
import uuid

from dolor import *

test_uuid_string = pak.test.assert_type_marshal_func(
    types.UUIDString,

    (uuid.UUID(int=0), b"\x2400000000-0000-0000-0000-000000000000")
)
