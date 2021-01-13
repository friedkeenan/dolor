from .type import Type
from .version_switched import handle_dict_type

class Defaulted(Type):
    @classmethod
    def _call(cls, elem_type, default):
        elem_type = handle_dict_type(elem_type)

        return cls.make_type(f"{cls.__name__}{elem_type.__name__}", (cls, elem_type),
            _default   = default,
        )
