import uuid

from dolor import *

from ..util import assert_type_marshal_func

test_uuid_string = assert_type_marshal_func(
    types.UUIDString,

    (uuid.UUID(int=0), b"\x2400000000-0000-0000-0000-000000000000")
)
