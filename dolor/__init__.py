try:
    import importlib.metadata as importlib_metadata
except ImportError:
    # TODO: Remove this when Python 3.7 support is dropped.
    import importlib_metadata

# Dynamically get version.
__version__ = importlib_metadata.version(__name__)

# Remove import from our exported variables
del importlib_metadata

from . import util
from . import types

from .versions import *
from .packets import *
