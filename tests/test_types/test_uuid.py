import pak
import uuid

from dolor import *

test_uuid_string = pak.test.type_behavior_func(
    types.UUIDString,

    (uuid.UUID(int=0), b"\x2400000000-0000-0000-0000-000000000000"),

    static_size = 36 + 1,
    default     = uuid.UUID(int=0),
)
