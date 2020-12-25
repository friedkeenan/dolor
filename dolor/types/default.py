from .type import Type

class Default(Type):
    @classmethod
    def _call(cls, elem_type, default):
        return type(f"{cls.__name__}{elem_type.__name__}", (cls, elem_type), dict(
            _default   = default,
        ))
