import os

def is_iterable(obj):
    try:
        iter(obj)
    except TypeError:
        return False
    else:
        return True

def is_container(obj):
    return hasattr(obj, "__contains__") or is_iterable(obj)

def is_pathlike(obj):
    return isinstance(obj, (str, os.PathLike))
