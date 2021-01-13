from .type import *
from .simple import *
from .var_num import *
from .string import *
from .uuid import *
from .chat import *
from .array import *
from .vector import *
from .enum import *
from .bit_mask import *
from .compound import *
from .optional import *
from .default import *
from .version_switched import *
from .misc import *

# .nbt depends on ..nbt, which depends on this module,
# so only try to import it
try:
    from .nbt import *
except ImportError:
    pass

# Delete type to stop builtin conflict
from . import type
del type
