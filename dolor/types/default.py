from .type import Type
from .version_switched import handle_dict_type

class Default(Type):
    @classmethod
    def _call(cls, elem_type, default):
        elem_type = handle_dict_type(elem_type)

        return type(f"{cls.__name__}{elem_type.__name__}", (cls, elem_type), dict(
            _default   = default,
        ))
